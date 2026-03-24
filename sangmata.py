"""
Module to query @SangMata_beta_bot via the userbot (Telethon).
Strategy: polling on iter_messages after sending, so we avoid
the problem of non-forwardable messages and blocked forwards.
"""
import asyncio
import logging
import re
from html import escape as he

from telethon.errors import FloodWaitError, RPCError

from userbot_client import userbot

logger = logging.getLogger(__name__)

SANGMATA_BOT   = "SangMata_beta_bot"


# ─────────────────────────────────────────────────────────────────────────────
# SangMata response formatter
# Converts the bot's Markdown-like output into clean HTML.
#
# SangMata uses:
#   **text**       → bold
#   `text`         → inline code  (timestamps like `[08/02/26 11:41:06]`)
#   plain lines    → kept as-is (escaped)
#
# Output structure we produce:
#   • Section headers (e.g. "Nomi", "Username") → bold + blockquote wrapper
#   • Timestamp entries                          → <code> + value on same line
#   • ID line at top                             → bold
# ─────────────────────────────────────────────────────────────────────────────

def _fmt_sangmata(raw: str) -> str:
    """
    Parses raw SangMata text (Markdown-ish) and returns clean HTML.
    Works message-by-message; call once per collected message then join.
    """
    lines = raw.splitlines()
    out: list[str] = []
    in_section = False  # True while we are inside a blockquote section

    def _close_section():
        nonlocal in_section
        if in_section:
            out.append("</blockquote>")
            in_section = False

    def _inline_fmt(text: str) -> str:
        """
        Converts inline Markdown tokens to HTML within a single line.
        Order matters: code first (to avoid double-escaping), then bold.
        """
        # We process the text token by token to avoid regex collisions.
        result = []
        i = 0
        while i < len(text):
            # ── inline code  `…` ──────────────────────────────────────
            if text[i] == "`":
                end = text.find("`", i + 1)
                if end != -1:
                    inner = he(text[i + 1:end])
                    result.append(f"<code>{inner}</code>")
                    i = end + 1
                    continue
            # ── bold  **…** ───────────────────────────────────────────
            if text[i:i+2] == "**":
                end = text.find("**", i + 2)
                if end != -1:
                    inner = he(text[i + 2:end])
                    result.append(f"<b>{inner}</b>")
                    i = end + 2
                    continue
            # ── plain character ───────────────────────────────────────
            result.append(he(text[i]))
            i += 1
        return "".join(result)

    for line in lines:
        stripped = line.strip()

        # Empty line → close any open section, add spacing
        if not stripped:
            _close_section()
            out.append("")
            continue

        # ── Detect section headers: lines that are purely **bold** ────
        # e.g.  **Nomi**  or  **Username**
        header_match = re.fullmatch(r"\*\*(.+?)\*\*", stripped)
        if header_match:
            _close_section()
            title = he(header_match.group(1))
            out.append(f"\n📌  <b>{title}</b>")
            out.append("<blockquote>")
            in_section = True
            continue

        # ── Detect pure numeric ID lines (top of message) ─────────────
        if re.fullmatch(r"\d{5,}", stripped):
            _close_section()
            out.append(f"🆔  <b><code>{stripped}</code></b>")
            continue

        # ── Detect "Cronologia per **ID**" lines ──────────────────────
        cronologia_match = re.match(r"(Cronologia per\s+)(\*\*.+?\*\*)(.*)", stripped)
        if cronologia_match:
            _close_section()
            prefix_text = he(cronologia_match.group(1))
            bold_part   = he(cronologia_match.group(2).strip("*"))
            rest        = he(cronologia_match.group(3))
            out.append(f"<i>{prefix_text}</i><b>{bold_part}</b>{rest}")
            continue

        # ── Everything else: format inline tokens ─────────────────────
        formatted = _inline_fmt(stripped)
        out.append(formatted)

    _close_section()

    # Clean up excessive blank lines (max 1 consecutive empty line)
    cleaned: list[str] = []
    prev_empty = False
    for line in out:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    return "\n".join(cleaned).strip()
POLL_INTERVAL  = 1.5   # seconds between each poll
POLL_ATTEMPTS  = 16    # max attempts → ~24 seconds total
COLLECT_EXTRA  = 3.0   # extra seconds to collect follow-up messages


async def _resolve_to_id(client, target: str) -> str:
    """
    Converts @username / t.me link to numeric ID string.
    Returns target unchanged if it is already a numeric ID.
    """
    target = target.strip()
    # Strip t.me links
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if target.startswith(prefix):
            target = "@" + target[len(prefix):]
            break

    if not target.startswith("@") and not target.lstrip("-").isdigit():
        target = f"@{target}"

    if target.startswith("@"):
        try:
            entity  = await client.get_entity(target)
            resolved = str(entity.id)
            logger.info(f"Resolved {target} → {resolved}")
            return resolved
        except Exception as e:
            logger.warning(f"Resolution of {target} failed: {e}. Using username as-is.")

    return target


async def _get_last_msg_id(client) -> int:
    """Returns the ID of the last message in the SangMata chat (0 if none)."""
    try:
        msgs = await client.get_messages(SANGMATA_BOT, limit=1)
        if msgs:
            return msgs[0].id
    except Exception as e:
        logger.warning(f"Unable to read SangMata history: {e}")
    return 0


async def _collect_new_messages(client, after_id: int) -> list[str]:
    """
    Reads all messages that arrived AFTER after_id in the SangMata chat
    and returns their texts in chronological order.
    Uses iter_messages (Telethon) — reads without forwarding, bypasses forward block.
    """
    messages = []
    try:
        async for msg in client.iter_messages(SANGMATA_BOT, limit=20):
            if msg.id <= after_id:
                break
            text = getattr(msg, "text", None) or getattr(msg, "message", None) or ""
            if text:
                messages.append((msg.id, text))
    except Exception as e:
        logger.warning(f"Error reading new SangMata messages: {e}")

    # iter_messages returns newest-first; sort ascending for chronological output
    messages.sort(key=lambda x: x[0])
    return [t for _, t in messages]


async def query_sangmata(target: str) -> str:
    if not userbot._started:
        await userbot.start()

    client = userbot.client

    # 1. Resolve username / link → numeric ID
    target = await _resolve_to_id(client, target)

    # 2. Record the last message ID before we send anything
    last_id_before = await _get_last_msg_id(client)
    logger.info(f"Last SangMata msg before sending: {last_id_before}")

    try:
        # 3. Send the target identifier to SangMata
        await client.send_message(SANGMATA_BOT, target)
        logger.info(f"Sent to SangMata: {target}")

        # 4. Poll until a new message appears (or timeout)
        new_texts: list[str] = []
        for attempt in range(POLL_ATTEMPTS):
            await asyncio.sleep(POLL_INTERVAL)
            new_texts = await _collect_new_messages(client, last_id_before)
            if new_texts:
                logger.info(f"SangMata responded after {attempt + 1} poll attempt(s)")
                break
        else:
            return "⏳ SangMata did not respond within the timeout. Try again in a few seconds."

        # 5. Extra wait to catch any follow-up messages in the same reply
        await asyncio.sleep(COLLECT_EXTRA)
        new_texts = await _collect_new_messages(client, last_id_before)

        if new_texts:
            combined = "\n\n".join(new_texts)
            low = combined.lower()

            if "no data available" in low or "nessun dato" in low:
                return "ℹ️ No data found for this user."

            if "quota" in low or "limit" in low:
                return (
                    "⚠️ <b>Daily limit reached.</b>\n\n"
                    "The service resets every day at <b>00:00 UTC</b>.\n"
                    "Try again tomorrow! 🕛"
                )

            # Format each message individually then join
            formatted_parts = [_fmt_sangmata(msg) for msg in new_texts]
            return "\n\n".join(p for p in formatted_parts if p)

        return "ℹ️ No information found for this user."

    except FloodWaitError as e:
        return f"⏳ Telegram rate limit — try again in {e.seconds} seconds."
    except RPCError as e:
        return f"❌ Telegram RPC error: {e}"
    except Exception as e:
        logger.exception("Unexpected error in query_sangmata")
        return f"❌ Unexpected error: {e}"