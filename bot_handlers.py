import logging
from datetime import datetime
from html import escape as he

from sqlalchemy import select
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import BadRequest

from database import get_session, MessageLog, UserActivity, UserProfile, MessageMetadata, UserInteraction
from osint import collect_osint_data
from analytics import generate_group_report
from sangmata import query_sangmata
from user_profiling import get_user_profile_report

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _flag(value: bool) -> str:
    return "✅" if value else "❌"

def _val(v, fallback: str = "—") -> str:
    return str(v) if v is not None and v != "" else fallback

def _h(v, fallback: str = "—") -> str:
    if v is None or v == "":
        return fallback
    return he(str(v))

async def _send_or_edit(update, context, text, keyboard=None):
    """Edit the existing menu message, or send a new one."""
    chat_id = update.effective_chat.id
    msg_id = context.user_data.get("menu_msg_id")
    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                parse_mode="HTML",
                reply_markup=keyboard,
            )
            return
        except BadRequest as e:
            s = str(e).lower()
            if "message is not modified" in s:
                return
            if "message to edit not found" not in s and "not found" not in s:
                logger.warning(f"_send_or_edit: {e}")

    sent = await context.bot.send_message(
        chat_id, text, parse_mode="HTML", reply_markup=keyboard
    )
    context.user_data["menu_msg_id"] = sent.message_id


async def _answer_edit(query, text, keyboard=None):
    """Answer a callback query and edit its message."""
    await query.answer()
    try:
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"_answer_edit: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Keyboard builders
# ─────────────────────────────────────────────────────────────────────────────

def _kb_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔍  Search user",  callback_data="m:info"),
            InlineKeyboardButton("📋  ID history",    callback_data="m:hist"),
        ],
        [InlineKeyboardButton("📖  Help", callback_data="m:help")],
    ])

def _kb_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠  Home", callback_data="m:home")]
    ])

def _kb_result(username: str | None = None) -> InlineKeyboardMarkup:
    row = []
    if username:
        row.append(InlineKeyboardButton("🔗  Open profile", url=f"https://t.me/{username}"))
    row.append(InlineKeyboardButton("🏠  Home", callback_data="m:home"))
    return InlineKeyboardMarkup([row])

def _kb_pages(pages: list[str], current: int, prefix: str, extra_url: str | None = None) -> InlineKeyboardMarkup:
    """Navigation keyboard for paginated content."""
    total = len(pages)
    nav = []
    if current > 0:
        nav.append(InlineKeyboardButton("◀  Back", callback_data=f"{prefix}:{current - 1}"))
    if current < total - 1:
        nav.append(InlineKeyboardButton("Next  ▶", callback_data=f"{prefix}:{current + 1}"))

    rows = []
    if nav:
        rows.append(nav)

    bottom = []
    if extra_url:
        bottom.append(InlineKeyboardButton("🔗  Open", url=extra_url))
    bottom.append(InlineKeyboardButton("🏠  Home", callback_data="m:home"))
    rows.append(bottom)

    return InlineKeyboardMarkup(rows)


# ─────────────────────────────────────────────────────────────────────────────
# Paginator — splits a list of text blocks into pages ≤ 4096 chars
# ─────────────────────────────────────────────────────────────────────────────

def _paginate(header: str, blocks: list[str], max_len: int = 4000) -> list[str]:
    """
    Given a header and a list of content blocks, builds pages
    each fitting within max_len characters.
    """
    pages: list[str] = []
    current_blocks: list[str] = []
    current_len = len(header)

    for block in blocks:
        candidate = len(block) + 1  # +1 for newline
        if current_blocks and current_len + candidate > max_len:
            pages.append(header + "\n".join(current_blocks))
            current_blocks = [block]
            current_len = len(header) + len(block)
        else:
            current_blocks.append(block)
            current_len += candidate

    if current_blocks:
        pages.append(header + "\n".join(current_blocks))

    return pages or [header + "<i>No data available.</i>"]


def _page_footer(current: int, total: int) -> str:
    if total <= 1:
        return ""
    return f"\n\n<i>Page {current + 1} / {total}</i>"


# ─────────────────────────────────────────────────────────────────────────────
# Home / Help texts
# ─────────────────────────────────────────────────────────────────────────────

def _txt_home(first: str) -> str:
    return (
        f"👁  <b>OSINT &amp; Group Manager</b>\n\n"
        f"Hello <b>{he(first)}</b>! 👋\n\n"
        f"<b>Private — OSINT</b>\n"
        f"🔍  Analyze profiles, IDs and channels\n"
        f"📋  Username &amp; ID change history\n\n"
        f"<b>Groups — add me as admin</b>\n"
        f"📊  <code>/report</code>  —  group statistics\n"
        f"👤  <code>/profile</code>  —  user deep profile\n\n"
        f"<i>Select an action below:</i>"
    )

def _txt_help() -> str:
    return (
        f"📖  <b>Help</b>\n\n"
        f"<b>🔍 Search User</b>\n"
        f"  <code>/info @username</code>\n"
        f"  <code>/info 123456789</code>\n"
        f"  <code>/info https://t.me/username</code>\n\n"
        f"<b>📋 ID History</b>\n"
        f"  <code>/idstorici @username</code>\n"
        f"  <code>/idstorici 123456789</code>\n\n"
        f"<b>👤 Group Profile</b>  <i>(admin required)</i>\n"
        f"  <code>/profile @username</code>  or reply + <code>/profile</code>\n\n"
        f"<b>📊 Group Report</b>  <i>(admin required)</i>\n"
        f"  <code>/report</code>  — last 30 days\n\n"
        f"<i>💡 You can also use the menu buttons.</i>"
    )

def _txt_ask(mode: str) -> str:
    if mode == "info":
        return (
            f"🔍  <b>Search User</b>\n\n"
            f"Send the target identifier:\n"
            f"  • <code>@username</code>\n"
            f"  • <code>123456789</code>  <i>(numeric ID)</i>\n"
            f"  • <code>https://t.me/username</code>"
        )
    return (
        f"📋  <b>ID History</b>\n\n"
        f"Send the target identifier:\n"
        f"  • <code>@username</code>\n"
        f"  • <code>123456789</code>  <i>(numeric ID)</i>"
    )

def _txt_loading(target: str) -> str:
    return f"⏳  <b>Searching…</b>\n\n<code>{he(target)}</code>"


# ─────────────────────────────────────────────────────────────────────────────
# OSINT user formatter — paginated
# Returns: list of page strings + optional profile URL
# ─────────────────────────────────────────────────────────────────────────────

def _build_user_pages(data: dict) -> tuple[list[str], str | None]:
    name = f"{data.get('first_name') or ''} {data.get('last_name') or ''}".strip() or "—"
    username = data.get("username")
    username_display = f"@{he(username)}" if username else "—"
    profile_url = f"https://t.me/{username}" if username else None

    # ── Last seen ─────────────────────────────────────────────────────
    ls_status = data.get("last_seen_status") or "unknown"
    ls_date   = data.get("last_seen_date")
    ls_text   = f"{ls_status}  {ls_date.strftime('%d/%m/%Y %H:%M')}" if ls_date else ls_status

    # ── Phone ─────────────────────────────────────────────────────────
    phone_raw = data.get("phone")
    phone_str = f"+{he(str(phone_raw))}" if isinstance(phone_raw, str) and phone_raw else "<i>not public</i>"

    # ── Bio ───────────────────────────────────────────────────────────
    bio = he(data.get("bio") or "") or "<i>—</i>"

    # ── Page 1: Identity ──────────────────────────────────────────────
    page1_blocks = [
        f"👤  <b>USER PROFILE</b>\n",
        f"🆔  <b>ID</b>         <code>{data['id']}</code>\n"
        f"📛  <b>Name</b>       {_h(name)}\n"
        f"🔗  <b>Username</b>   {username_display}\n"
        f"📞  <b>Phone</b>      {phone_str}\n"
        f"🕐  <b>Last seen</b>  {he(ls_text)}\n"
        f"🌐  <b>DC</b>         DC{_val(data.get('dc_id'))}\n"
        f"🖼  <b>Photos</b>     {data.get('profile_photos_count', 0)}\n",
    ]

    if data.get("lang_code"):
        page1_blocks.append(f"🌐  <b>Language</b>    <code>{he(data['lang_code'])}</code>\n")
    if data.get("emoji_status"):
        page1_blocks.append(f"✨  <b>Status emoji</b> {he(data['emoji_status'])}\n")
    if data.get("bio"):
        page1_blocks.append(f"\n📝  <b>Bio</b>\n<blockquote>{bio}</blockquote>")

    # ── Page 2: Flags ─────────────────────────────────────────────────
    flags = [
        ("🤖  Bot",               data.get("is_bot", False)),
        ("✔️  Verified",          data.get("is_verified", False)),
        ("⭐  Premium",           data.get("is_premium", False)),
        ("🛠  Support",           data.get("is_support", False)),
        ("🤝  Mutual contact",    data.get("is_mutual_contact", False)),
        ("🚫  Blocked us",        data.get("blocked", False)),
        ("📕  Stories hidden",    data.get("stories_hidden", False)),
        ("💎  Require premium",   data.get("contact_require_premium", False)),
        ("📵  Calls disabled",    data.get("call_requests_disabled", False)),
        ("⚠️  Scam",              data.get("is_scam", False)),
        ("🎭  Fake",              data.get("is_fake", False)),
        ("🗑  Deleted",           data.get("is_deleted", False)),
        ("🔒  Restricted",        data.get("is_restricted", False)),
    ]
    flag_lines = "\n".join(f"{_flag(v)}  {label}" for label, v in flags)
    page2 = f"🏷  <b>FLAGS</b>\n\n{flag_lines}"

    # ── Page 3: Common groups ─────────────────────────────────────────
    common = data.get("common_groups", [])
    if common:
        g_lines = "\n".join(
            f"  {'🔹' if i % 2 == 0 else '🔸'}  {_h(g['title'])}"
            + (f"  <code>@{he(g['username'])}</code>" if g.get("username") else "")
            for i, g in enumerate(common)
        )
    else:
        g_lines = "  <i>No mutual groups found.</i>"
    page3 = f"👥  <b>MUTUAL GROUPS</b>  ({len(common)})\n\n{g_lines}"

    pages = ["\n".join(page1_blocks), page2, page3]

    # ── Page 4: Bot info (optional) ───────────────────────────────────
    if data.get("bot_info"):
        bi = data["bot_info"]
        desc = he(bi.get("description") or "—")
        cmds = bi.get("commands") or []
        cmd_text = "\n".join(
            f"  /{he(c['command'])}  —  {he(c['description'])}" for c in cmds
        ) if cmds else "  <i>No commands.</i>"
        bot_page = (
            f"🤖  <b>BOT INFO</b>\n\n"
            f"📝  <b>Description</b>\n{desc}\n\n"
            f"⌨️  <b>Commands</b>\n{cmd_text}"
        )
        pages.append(bot_page)

    return pages, profile_url


# ─────────────────────────────────────────────────────────────────────────────
# OSINT chat/channel formatter — paginated
# ─────────────────────────────────────────────────────────────────────────────

def _build_chat_pages(data: dict) -> tuple[list[str], str | None]:
    etype    = data.get("type", "chat")
    icon     = "📢" if etype == "channel" else "👥"
    label    = "CHANNEL" if etype == "channel" else "GROUP"
    username = data.get("username")
    uname_d  = f"@{he(username)}" if username else "—"
    profile_url = f"https://t.me/{username}" if username else None

    desc_raw = data.get("description") or ""
    desc     = he(desc_raw) if desc_raw else "<i>—</i>"

    # ── Page 1: Overview ──────────────────────────────────────────────
    linked      = data.get("linked_chat")
    linked_text = "—"
    if linked:
        linked_text = _h(linked["title"])
        if linked.get("username"):
            linked_text += f"  @{he(linked['username'])}"

    page1_lines = (
        f"{icon}  <b>{label}</b>\n\n"
        f"🆔  <b>ID</b>           <code>{data['id']}</code>\n"
        f"🏷  <b>Title</b>        {_h(data.get('title'))}\n"
        f"🔗  <b>Username</b>     {uname_d}\n"
        f"🌍  <b>Public</b>       {_flag(data.get('is_public', False))}\n"
        f"👥  <b>Members</b>      {_val(data.get('member_count'))}\n"
        f"🔗  <b>Linked chat</b>  {linked_text}\n"
    )
    if data.get("invite_link"):
        page1_lines += f"📨  <b>Invite link</b>  {_h(data.get('invite_link'))}\n"
    if desc_raw:
        page1_lines += f"\n📝  <b>Description</b>\n<blockquote>{desc}</blockquote>"

    # ── Page 2: Flags & settings ──────────────────────────────────────
    flags = [
        ("📣  Megagroup",       data.get("is_megagroup", False)),
        ("📢  Broadcast",       data.get("is_broadcast", False)),
        ("✔️  Verified",        data.get("is_verified", False)),
        ("⚠️  Scam",            data.get("is_scam", False)),
        ("🎭  Fake",            data.get("is_fake", False)),
        ("🔒  Restricted",      data.get("is_restricted", False)),
        ("✍️  Signatures",      data.get("signatures_enabled", False)),
        ("📍  Has geo",         data.get("has_geo", False)),
        ("📌  Stories pinned",  data.get("stories_pinned", False)),
    ]
    flag_lines = "\n".join(f"{_flag(v)}  {label}" for label, v in flags)

    extras = ""
    if data.get("slow_mode_delay"):
        extras += f"\n🐢  <b>Slow mode</b>  {data['slow_mode_delay']}s"
    if data.get("stickerset_short_name"):
        extras += f"\n🎭  <b>Sticker pack</b>  @{he(data['stickerset_short_name'])}"

    reactions = data.get("available_reactions") or []
    if reactions == ["all"]:
        react_text = "All reactions enabled"
    elif reactions:
        react_text = "  ".join(reactions[:20])
    else:
        react_text = "—"

    page2 = f"🏷  <b>FLAGS &amp; SETTINGS</b>\n\n{flag_lines}{extras}\n\n💬  <b>Reactions</b>\n{react_text}"

    # ── Page 3: Admins ────────────────────────────────────────────────
    admins = data.get("admins") or []
    if admins:
        admin_lines = "\n".join(
            f"  {'👑' if a.get('is_owner') else '🔹'}  "
            + (f"@{he(a['username'])}" if a.get("username") else _h(a.get("first_name")))
            + f"  <code>{a['id']}</code>"
            + ("  <i>[bot]</i>" if a.get("is_bot") else "")
            for a in admins
        )
    else:
        admin_lines = "  <i>No admin data available.</i>"
    page3 = f"👑  <b>ADMINS</b>  ({len(admins)})\n\n{admin_lines}"

    # ── Page 4: Bots ──────────────────────────────────────────────────
    bots = data.get("bots") or []
    if bots:
        bot_lines = "\n".join(
            f"  🤖  "
            + (f"@{he(b['username'])}" if b.get("username") else _h(b.get("first_name")))
            + f"  <code>{b['id']}</code>"
            for b in bots
        )
    else:
        bot_lines = "  <i>No bots in this chat.</i>"
    page4 = f"🤖  <b>BOTS</b>  ({len(bots)})\n\n{bot_lines}"

    return [page1_lines, page2, page3, page4], profile_url


# ─────────────────────────────────────────────────────────────────────────────
# Group report — paginated
# ─────────────────────────────────────────────────────────────────────────────

async def _build_report_pages(chat_id: int, days: int = 30) -> list[str]:
    from sqlalchemy import func
    from datetime import timedelta

    since = datetime.utcnow() - timedelta(days=days)

    async with get_session() as session:
        from sqlalchemy import select as sql_select

        total_msgs = await session.scalar(
            sql_select(func.count(MessageLog.id)).where(
                MessageLog.chat_id == chat_id,
                MessageLog.date >= since,
            )
        )
        active_users = await session.scalar(
            sql_select(func.count(func.distinct(MessageLog.user_id))).where(
                MessageLog.chat_id == chat_id,
                MessageLog.date >= since,
            )
        )
        result = await session.execute(
            sql_select(MessageLog.user_id, func.count(MessageLog.id).label("cnt"))
            .where(MessageLog.chat_id == chat_id, MessageLog.date >= since)
            .group_by(MessageLog.user_id)
            .order_by(func.count(MessageLog.id).desc())
            .limit(10)
        )
        top_rows = result.all()

    page1 = (
        f"📊  <b>GROUP REPORT</b>\n"
        f"<i>Last {days} days</i>\n\n"
        f"📨  <b>Total messages</b>   {total_msgs or 0}\n"
        f"👥  <b>Active users</b>     {active_users or 0}\n"
    )

    medals = ["🥇", "🥈", "🥉"]
    top_lines = ""
    for i, (uid, cnt) in enumerate(top_rows):
        medal = medals[i] if i < 3 else f"  {i + 1}."
        top_lines += f"\n{medal}  <code>{uid}</code>  —  {cnt} messages"

    page2 = (
        f"🏆  <b>TOP USERS</b>  <i>(by messages)</i>\n\n"
        f"{top_lines or '<i>No data available.</i>'}"
    )

    return [page1, page2]


# ─────────────────────────────────────────────────────────────────────────────
# User profile (group) — paginated
# ─────────────────────────────────────────────────────────────────────────────

def _build_profile_pages(report: dict, user_id: int) -> list[str]:
    if not report:
        return [f"❌  No data available for user <code>{user_id}</code>"]

    profile = report["profile"]
    stats   = report["message_stats"]
    name    = f"{profile.first_name or ''} {profile.last_name or ''}".strip() or "Unknown"
    uname   = f"@{profile.username}" if profile.username else "—"

    first_seen = report["first_seen"].strftime("%d/%m/%Y  %H:%M") if report["first_seen"] else "—"
    last_seen  = report["last_seen"].strftime("%d/%m/%Y  %H:%M")  if report["last_seen"]  else "—"
    days_active = 0
    if report["first_seen"] and report["last_seen"]:
        days_active = (report["last_seen"] - report["first_seen"]).days + 1

    # ── Page 1: Identity + activity ───────────────────────────────────
    page1 = (
        f"👤  <b>USER PROFILE</b>\n\n"
        f"🆔  <b>ID</b>         <code>{profile.user_id}</code>\n"
        f"📛  <b>Name</b>       {he(name)}\n"
        f"🔗  <b>Username</b>   {he(uname)}\n"
        f"🤖  <b>Bot</b>        {_flag(profile.is_bot)}\n"
        f"⭐  <b>Premium</b>    {_flag(getattr(profile, 'is_premium', False))}\n\n"
        f"📅  <b>First seen</b>  {first_seen}\n"
        f"🕐  <b>Last seen</b>   {last_seen}\n"
        f"📆  <b>Days active</b> {days_active}\n"
        f"📨  <b>Total msgs</b>  {report['total_messages']}"
    )

    # ── Page 2: Message stats ─────────────────────────────────────────
    page2 = (
        f"📊  <b>MESSAGE STATS</b>\n\n"
        f"💬  <b>Text only</b>       {stats['text_only']}\n"
        f"🖼  <b>With media</b>      {stats['with_media']}\n"
        f"@   <b>With mentions</b>   {stats['with_mention']}\n"
        f"#   <b>With hashtags</b>   {stats['with_hashtag']}\n"
        f"📏  <b>Avg. length</b>     {stats['avg_length']} chars\n\n"
        f"↩️  <b>Replies sent</b>     {report['replies_sent']}\n"
        f"↪️  <b>Replies received</b>  {report['replies_received']}"
    )

    # ── Page 3: Top activity hours ────────────────────────────────────
    top_hours = report.get("top_hours", [])
    hours_lines = "\n".join(
        f"  {'🌙' if h < 6 else '☀️' if h < 12 else '🌤' if h < 18 else '🌆'}  "
        f"{h:02d}:00  —  {count} messages"
        for h, count in top_hours
    ) or "  <i>No data.</i>"
    page3 = f"⏰  <b>TOP ACTIVITY HOURS</b>\n\n{hours_lines}"

    # ── Page 4: Interactions ──────────────────────────────────────────
    def _fmt_interaction_list(lst):
        if not lst:
            return "  <i>—</i>"
        return "\n".join(
            f"  🔹  {'@' + un if un and un != 'Unknown' else f'User {uid}'}  —  {count}"
            for uid, un, count in lst
        )

    page4 = (
        f"🤝  <b>INTERACTIONS</b>\n\n"
        f"<b>Replies to:</b>\n"
        f"{_fmt_interaction_list(report.get('most_replied_to', []))}\n\n"
        f"<b>Replied by:</b>\n"
        f"{_fmt_interaction_list(report.get('most_replies_from', []))}"
    )

    # ── Page 5: Recent messages ───────────────────────────────────────
    msgs = report.get("messages_detail", [])
    if msgs:
        msg_lines = []
        for i, msg in enumerate(msgs, 1):
            time_str = msg["date"].strftime("%d/%m  %H:%M") if msg["date"] else "—"
            preview  = he(msg["text"][:80]) if msg["text"] else "<i>[no text]</i>"
            media    = f"  <i>[{msg['media_type'].upper()}]</i>" if msg.get("media_type") else ""
            reply    = f"\n    ↩️ to @{msg['reply_to_username']}" if msg.get("reply_to_username") else ""
            msg_lines.append(f"  <b>{i}.</b>  {time_str}\n    {preview}{media}{reply}")
        msg_text = "\n\n".join(msg_lines)
    else:
        msg_text = "  <i>No messages logged.</i>"
    page5 = f"💬  <b>RECENT MESSAGES</b>\n\n{msg_text}"

    return [page1, page2, page3, page4, page5]


# ─────────────────────────────────────────────────────────────────────────────
# State storage helpers for paginated views
# ─────────────────────────────────────────────────────────────────────────────

def _store_pages(context, key: str, pages: list[str], extra_url: str | None = None):
    context.user_data[f"pages_{key}"] = pages
    context.user_data[f"url_{key}"]   = extra_url

def _get_pages(context, key: str) -> tuple[list[str], str | None]:
    return (
        context.user_data.get(f"pages_{key}", []),
        context.user_data.get(f"url_{key}"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await update.message.delete()
    except Exception:
        pass

    context.user_data.pop("awaiting_input", None)
    user = update.effective_user
    await _send_or_edit(update, context, _txt_home(user.first_name), _kb_home())


# ─────────────────────────────────────────────────────────────────────────────
# Inline button handler
# ─────────────────────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user  = update.effective_user
    data  = query.data

    # ── Home ──────────────────────────────────────────────────────────
    if data == "m:home":
        context.user_data.pop("awaiting_input", None)
        await _answer_edit(query, _txt_home(user.first_name), _kb_home())
        return

    # ── Input prompts ─────────────────────────────────────────────────
    if data in ("m:info", "m:hist"):
        mode = "info" if data == "m:info" else "idstorici"
        context.user_data["awaiting_input"] = mode
        await _answer_edit(query, _txt_ask(mode), _kb_back())
        return

    # ── Help ──────────────────────────────────────────────────────────
    if data == "m:help":
        await _answer_edit(query, _txt_help(), _kb_back())
        return

    # ── Paginated navigation  format: "pkey:page_index" ───────────────
    # Keys: "user", "chat", "report", "profile"
    for pkey in ("user", "chat", "report", "profile"):
        prefix = f"p:{pkey}"
        if data.startswith(f"{prefix}:"):
            idx = int(data.split(":")[-1])
            pages, extra_url = _get_pages(context, pkey)
            if not pages:
                await query.answer("Session expired. Please search again.", show_alert=True)
                return
            total = len(pages)
            page_text = pages[idx] + _page_footer(idx, total)
            kb = _kb_pages(pages, idx, prefix, extra_url)
            await _answer_edit(query, page_text, kb)
            return

    await query.answer()


# ─────────────────────────────────────────────────────────────────────────────
# OSINT runners
# ─────────────────────────────────────────────────────────────────────────────

async def _run_info(context, update_or_chat_id, msg_id_or_none, target):
    """Run OSINT info lookup and display paginated result."""
    # Resolve chat_id / message id
    if hasattr(update_or_chat_id, "effective_chat"):
        chat_id = update_or_chat_id.effective_chat.id
    else:
        chat_id = update_or_chat_id

    try:
        data = await collect_osint_data(target)
    except ValueError as e:
        err = f"❌  <b>Error</b>\n\n{he(str(e))}"
        if msg_id_or_none:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id_or_none,
                                                text=err, parse_mode="HTML", reply_markup=_kb_back())
        else:
            await context.bot.send_message(chat_id, err, parse_mode="HTML", reply_markup=_kb_back())
        return
    except Exception as e:
        logger.exception("Error in collect_osint_data")
        err = f"❌  <b>Unexpected error</b>\n\n<code>{he(str(e))}</code>"
        if msg_id_or_none:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id_or_none,
                                                text=err, parse_mode="HTML", reply_markup=_kb_back())
        else:
            await context.bot.send_message(chat_id, err, parse_mode="HTML", reply_markup=_kb_back())
        return

    entity_type = data.get("type", "unknown")
    if entity_type == "user":
        pages, profile_url = _build_user_pages(data)
        pkey = "user"
    else:
        pages, profile_url = _build_chat_pages(data)
        pkey = "chat"

    _store_pages(context, pkey, pages, profile_url)
    total  = len(pages)
    prefix = f"p:{pkey}"
    text   = pages[0] + _page_footer(0, total)
    kb     = _kb_pages(pages, 0, prefix, profile_url)

    if msg_id_or_none:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id_or_none,
                                                text=text, parse_mode="HTML", reply_markup=kb)
        except BadRequest:
            await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
    else:
        await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)


async def _run_idstorici(context, update_or_chat_id, msg_id_or_none, target):
    if hasattr(update_or_chat_id, "effective_chat"):
        chat_id = update_or_chat_id.effective_chat.id
    else:
        chat_id = update_or_chat_id

    try:
        response = await query_sangmata(target)
    except Exception as e:
        logger.exception("Error in ID history")
        err = f"❌  <b>Unexpected error</b>\n\n<code>{he(str(e))}</code>"
        if msg_id_or_none:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id_or_none,
                                                text=err, parse_mode="HTML", reply_markup=_kb_back())
        else:
            await context.bot.send_message(chat_id, err, parse_mode="HTML", reply_markup=_kb_back())
        return

    header = f"📋  <b>ID HISTORY</b>  —  <code>{he(target)}</code>\n\n"
    # Split into chunks of ~3800 chars preserving the header
    raw_lines = response.split("\n")
    pages: list[str] = []
    chunk: list[str] = []
    chunk_len = len(header)
    for line in raw_lines:
        if chunk_len + len(line) + 1 > 3800 and chunk:
            pages.append(header + "\n".join(chunk))
            chunk = [line]
            chunk_len = len(header) + len(line)
        else:
            chunk.append(line)
            chunk_len += len(line) + 1
    if chunk:
        pages.append(header + "\n".join(chunk))
    if not pages:
        pages = [header + "<i>No data returned.</i>"]

    _store_pages(context, "hist", pages)
    total  = len(pages)
    prefix = "p:hist"
    text   = pages[0] + _page_footer(0, total)
    kb     = _kb_pages(pages, 0, prefix)

    if msg_id_or_none:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id_or_none,
                                                text=text, parse_mode="HTML", reply_markup=kb)
        except BadRequest:
            await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)
    else:
        await context.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb)

    # Register "hist" as a valid pkey for button_handler
    for pkey in ("hist",):
        context.user_data[f"pages_{pkey}"] = pages
        context.user_data[f"url_{pkey}"]   = None


# ─────────────────────────────────────────────────────────────────────────────
# Private text — input after menu prompt
# ─────────────────────────────────────────────────────────────────────────────

async def private_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mode = context.user_data.get("awaiting_input")
    if not mode:
        return

    target  = update.message.text.strip()
    chat_id = update.effective_chat.id
    msg_id  = context.user_data.get("menu_msg_id")

    try:
        await update.message.delete()
    except Exception:
        pass

    context.user_data.pop("awaiting_input", None)

    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=_txt_loading(target), parse_mode="HTML"
            )
        except Exception:
            pass

    if mode == "info":
        await _run_info(context, chat_id, msg_id, target)
    else:
        await _run_idstorici(context, chat_id, msg_id, target)


# ─────────────────────────────────────────────────────────────────────────────
# /info  /osint  /idstorici
# ─────────────────────────────────────────────────────────────────────────────

async def _cmd_dispatch(update, context, mode):
    try:
        await update.message.delete()
    except Exception:
        pass

    chat_id = update.effective_chat.id
    msg_id  = context.user_data.get("menu_msg_id")

    if not context.args:
        context.user_data["awaiting_input"] = mode
        await _send_or_edit(update, context, _txt_ask(mode), _kb_back())
        return

    target = context.args[0]
    if msg_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=msg_id,
                text=_txt_loading(target), parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        sent = await context.bot.send_message(
            chat_id, _txt_loading(target), parse_mode="HTML"
        )
        context.user_data["menu_msg_id"] = sent.message_id
        msg_id = sent.message_id

    if mode == "info":
        await _run_info(context, chat_id, msg_id, target)
    else:
        await _run_idstorici(context, chat_id, msg_id, target)


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_dispatch(update, context, "info")

async def idstorici_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _cmd_dispatch(update, context, "idstorici")


# ─────────────────────────────────────────────────────────────────────────────
# /profile  (group only)
# ─────────────────────────────────────────────────────────────────────────────

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❌  This command only works in groups.")
        return

    try:
        bot_member = await chat.get_member(context.bot.id)
    except Exception:
        await update.message.reply_text("❌  The bot is not in the group.")
        return

    if bot_member.status not in ("administrator", "creator"):
        await update.message.reply_text("❌  The bot is not an administrator.")
        return

    # Resolve target user
    if update.message.reply_to_message and update.message.reply_to_message.from_user:
        target_user_id = update.message.reply_to_message.from_user.id
    else:
        if not context.args:
            await update.message.reply_text(
                "❌  Usage: <code>/profile @username</code>  or reply to a message.",
                parse_mode="HTML"
            )
            return
        target = context.args[0]
        if target.lstrip("@").isdigit():
            target_user_id = int(target.lstrip("@"))
        else:
            from sqlalchemy import select as sql_select
            from database import UserProfile as UP
            async with get_session() as session:
                result = await session.execute(
                    sql_select(UP).where(UP.username == target.lstrip("@"))
                )
                profile = result.scalar_one_or_none()
                if not profile:
                    await update.message.reply_text(f"❌  User <code>{he(target)}</code> not found.", parse_mode="HTML")
                    return
                target_user_id = profile.user_id

    loading = await update.message.reply_text("⏳  <b>Generating profile…</b>", parse_mode="HTML")

    try:
        report = await get_user_profile_report(chat.id, target_user_id)
        if not report:
            await loading.edit_text(
                f"❌  No data for user <code>{target_user_id}</code> in this group.",
                parse_mode="HTML"
            )
            return

        pages  = _build_profile_pages(report, target_user_id)
        total  = len(pages)
        prefix = "p:profile"
        _store_pages(context, "profile", pages)

        # Store pages in user_data keyed by chat so they survive across messages
        context.user_data["pages_profile"] = pages
        context.user_data["url_profile"]   = None

        text = pages[0] + _page_footer(0, total)
        kb   = _kb_pages(pages, 0, prefix)
        await loading.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.exception("Error generating profile")
        await loading.edit_text(
            f"❌  Error:\n<code>{he(str(e))}</code>", parse_mode="HTML"
        )


# ─────────────────────────────────────────────────────────────────────────────
# /report  (group only)
# ─────────────────────────────────────────────────────────────────────────────

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❌  This command only works in groups.")
        return

    try:
        bot_member = await chat.get_member(context.bot.id)
    except Exception:
        return
    if bot_member.status not in ("administrator", "creator"):
        await update.message.reply_text("❌  The bot is not an administrator.")
        return

    loading = await update.message.reply_text("⏳  <b>Generating report…</b>", parse_mode="HTML")

    try:
        pages  = await _build_report_pages(chat.id, days=30)
        total  = len(pages)
        prefix = "p:report"
        _store_pages(context, "report", pages)

        text = pages[0] + _page_footer(0, total)
        kb   = _kb_pages(pages, 0, prefix)
        await loading.edit_text(text, parse_mode="HTML", reply_markup=kb)

    except Exception as e:
        logger.exception("Error generating report")
        await loading.edit_text(
            f"❌  Error:\n<code>{he(str(e))}</code>", parse_mode="HTML"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Group message logging
# ─────────────────────────────────────────────────────────────────────────────

async def group_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return
    try:
        bot_member = await chat.get_member(context.bot.id)
    except Exception:
        return
    if bot_member.status not in ("administrator", "creator"):
        return

    user = update.effective_user
    if not user:
        return

    message = update.effective_message
    msg_date = (
        datetime.fromtimestamp(message.date.timestamp())
        if message.date else datetime.utcnow()
    )

    async with get_session() as session:
        session.add(MessageLog(
            chat_id=chat.id, user_id=user.id, date=msg_date,
            message_id=message.message_id, text=message.text or None,
        ))

        media_type = None
        if message.photo:       media_type = "photo"
        elif message.video:     media_type = "video"
        elif message.document:  media_type = "document"
        elif message.audio:     media_type = "audio"
        elif message.voice:     media_type = "voice"
        elif message.sticker:   media_type = "sticker"

        text_length  = len(message.text) if message.text else 0
        has_mention  = bool(message.text and "@" in message.text)
        has_hashtag  = bool(message.text and "#" in message.text)

        reply_to_user_id    = None
        reply_to_message_id = None
        if message.reply_to_message:
            reply_to_message_id = message.reply_to_message.message_id
            if message.reply_to_message.from_user:
                reply_to_user_id = message.reply_to_message.from_user.id

        session.add(MessageMetadata(
            chat_id=chat.id, message_id=message.message_id,
            user_id=user.id, reply_to_message_id=reply_to_message_id,
            reply_to_user_id=reply_to_user_id, media_type=media_type,
            text_length=text_length, has_mention=has_mention,
            has_hashtag=has_hashtag, message_date=msg_date,
        ))

        result  = await session.execute(select(UserProfile).where(UserProfile.user_id == user.id))
        profile = result.scalar_one_or_none()
        now     = datetime.utcnow()
        if profile:
            profile.username   = user.username
            profile.first_name = user.first_name
            profile.last_name  = user.last_name
            profile.updated_at = now
        else:
            session.add(UserProfile(
                user_id=user.id, username=user.username,
                first_name=user.first_name, last_name=user.last_name,
                is_bot=user.is_bot,
            ))

        result   = await session.execute(
            select(UserActivity).where(
                UserActivity.user_id == user.id, UserActivity.chat_id == chat.id
            )
        )
        activity = result.scalar_one_or_none()
        if activity:
            activity.total_messages += 1
            activity.last_seen       = now
        else:
            session.add(UserActivity(
                user_id=user.id, chat_id=chat.id,
                total_messages=1, first_seen=now, last_seen=now,
            ))

        if reply_to_user_id and reply_to_user_id != user.id:
            result = await session.execute(
                select(UserInteraction).where(
                    UserInteraction.chat_id       == chat.id,
                    UserInteraction.from_user_id  == user.id,
                    UserInteraction.to_user_id    == reply_to_user_id,
                    UserInteraction.interaction_type == "reply",
                )
            )
            interaction = result.scalar_one_or_none()
            if interaction:
                interaction.count            += 1
                interaction.last_interaction  = now
            else:
                session.add(UserInteraction(
                    chat_id=chat.id, from_user_id=user.id,
                    to_user_id=reply_to_user_id, interaction_type="reply",
                    count=1, last_interaction=now,
                ))


# ─────────────────────────────────────────────────────────────────────────────
# Handler registration
# ─────────────────────────────────────────────────────────────────────────────

def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info",     info_command,      filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("osint",    info_command,      filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("idstorici", idstorici_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("profile",  profile_command,   filters=filters.ChatType.GROUPS))
    application.add_handler(CommandHandler("report",   report_command,    filters=filters.ChatType.GROUPS))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND,
        private_text_handler,
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS,
        group_message_handler,
    ))