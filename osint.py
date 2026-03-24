import asyncio
import logging
import re

from telethon.errors import (
    FloodWaitError,
    UsernameInvalidError,
    UsernameNotOccupiedError,
    UserPrivacyRestrictedError,
    PeerIdInvalidError,
    RPCError,
    ChatAdminRequiredError,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.types import (
    User,
    Channel,
    Chat,
    UserFull,
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    UserStatusOnline,
    UserStatusOffline,
    UserStatusRecently,
    UserStatusLastWeek,
    UserStatusLastMonth,
    UserStatusEmpty,
)

from userbot_client import userbot

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _parse_target(target: str):
    """Normalise: t.me link → username, @user → user, numeric string → int."""
    target = target.strip()
    match = re.match(r"(?:https?://)?t\.me/([^\s/]+)", target)
    if match:
        target = match.group(1)
    if target.startswith("@"):
        target = target[1:]
    if re.match(r"^-?\d+$", target):
        return int(target)
    return target


def _parse_status(status) -> dict:
    """
    Converts UserStatus → {"text": str, "was_online": datetime | None}
    text values: "online" | "offline" | "recently" | "last week" | "last month" | "unknown"
    """
    if status is None or isinstance(status, UserStatusEmpty):
        return {"text": "unknown", "was_online": None}
    if isinstance(status, UserStatusOnline):
        return {"text": "online", "was_online": None}
    if isinstance(status, UserStatusOffline):
        return {"text": "offline", "was_online": status.was_online}
    if isinstance(status, UserStatusRecently):
        return {"text": "recently", "was_online": None}
    if isinstance(status, UserStatusLastWeek):
        return {"text": "last week", "was_online": None}
    if isinstance(status, UserStatusLastMonth):
        return {"text": "last month", "was_online": None}
    return {"text": "unknown", "was_online": None}


def _parse_emoji_status(emoji_status) -> str | None:
    """Returns document_id of a Premium EmojiStatus, or None."""
    if emoji_status is None:
        return None
    doc_id = getattr(emoji_status, "document_id", None)
    return str(doc_id) if doc_id else None


def _parse_profile_color(color) -> str | None:
    """
    ProfileColor → color_id integer as string.
    Telegram maps color_id 0-6 to fixed palette colors.
    """
    if color is None:
        return None
    color_id = getattr(color, "color", None)
    if color_id is None:
        return None
    palette = {0: "red", 1: "orange", 2: "violet", 3: "green",
               4: "cyan", 5: "blue", 6: "pink"}
    return palette.get(color_id, str(color_id))


def _parse_reactions(available_reactions) -> list:
    """
    Parses available_reactions from a full chat object.
    Returns: ["all"] | ["😀", "👍", ...] | []
    """
    if available_reactions is None:
        return []
    type_name = type(available_reactions).__name__
    if type_name == "ChatReactionsAll":
        return ["all"]
    if type_name == "ChatReactionsSome":
        out = []
        for r in getattr(available_reactions, "reactions", []):
            emoticon = getattr(r, "emoticon", None)
            if emoticon:
                out.append(emoticon)
        return out
    if type_name == "ChatReactionsNone":
        return []
    return []


def _parse_banned_rights(rights) -> dict | None:
    """
    Parses a ChatBannedRights object into a readable dict of restrictions.
    Returns None if rights is None.
    """
    if rights is None:
        return None
    fields = [
        "view_messages", "send_messages", "send_media", "send_stickers",
        "send_gifs", "send_games", "send_inline", "embed_links",
        "send_polls", "change_info", "invite_users", "pin_messages",
        "manage_topics", "send_photos", "send_videos", "send_roundvideos",
        "send_audios", "send_docs", "send_plain",
    ]
    out = {}
    for f in fields:
        val = getattr(rights, f, None)
        if val is not None:
            out[f] = bool(val)
    until_date = getattr(rights, "until_date", None)
    if until_date:
        out["until_date"] = until_date
    return out


async def _safe_get_entity(identifier):
    """get_entity with automatic FloodWait retry."""
    try:
        return await userbot.client.get_entity(identifier)
    except FloodWaitError as e:
        logger.warning(f"FloodWait: waiting {e.seconds}s…")
        await asyncio.sleep(e.seconds)
        return await userbot.client.get_entity(identifier)
    except RPCError as e:
        logger.warning(f"get_entity failed for '{identifier}': {e}")
        return None


async def _get_full_user(entity: User):
    """GetFullUserRequest — bio, blocked, pinned_msg_id, personal_channel, bot_info, stories, etc."""
    try:
        return await userbot.client(GetFullUserRequest(entity))
    except Exception as e:
        logger.warning(f"GetFullUserRequest failed for {entity.id}: {e}")
        return None


async def _get_full_channel(entity):
    """GetFullChannelRequest — description, reactions, pts, banned_rights, stickerset, etc."""
    try:
        return await userbot.client(GetFullChannelRequest(entity))
    except Exception as e:
        logger.warning(f"GetFullChannelRequest failed for {entity.id}: {e}")
        return None


async def _get_full_chat(chat_id: int):
    """GetFullChatRequest — for basic groups."""
    try:
        return await userbot.client(GetFullChatRequest(chat_id))
    except Exception as e:
        logger.warning(f"GetFullChatRequest failed for {chat_id}: {e}")
        return None


async def _get_channel_participants(entity, filter_cls, limit: int = 50) -> list:
    """GetParticipantsRequest with a given filter (Admins / Bots)."""
    try:
        result = await userbot.client(
            GetParticipantsRequest(
                channel=entity,
                filter=filter_cls(),
                offset=0,
                limit=limit,
                hash=0,
            )
        )
        return result.users
    except (ChatAdminRequiredError, RPCError) as e:
        logger.warning(f"GetParticipantsRequest ({filter_cls.__name__}) failed: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# Main collector
# ═══════════════════════════════════════════════════════════════════════════

async def collect_osint_data(target: str) -> dict:
    """
    Collects ALL available OSINT data about a Telegram user, group or channel.

    USER fields:
      id, type, first_name, last_name, username, phone, bio, lang_code
      dc_id, profile_photos_count, profile_photos_ids
      is_bot, is_verified, is_premium, is_scam, is_fake, is_deleted,
      is_restricted, is_support, is_mutual_contact, stories_hidden,
      contact_require_premium, call_requests_disabled
      blocked, last_seen_status, last_seen_date
      emoji_status, profile_color
      personal_channel_id, pinned_msg_id
      bot_info {description, commands[], privacy_policy_url, inline_placeholder}
      common_groups

    CHANNEL / GROUP fields:
      id, type, title, username, description, member_count
      invite_link, linked_chat, slow_mode_delay
      is_public, is_megagroup, is_broadcast, is_verified,
      is_scam, is_fake, is_restricted, signatures_enabled, has_geo
      pinned_msg_id_chat, pts
      available_reactions, banned_rights, default_banned_rights
      migrated_from_chat_id, stickerset_short_name
      chat_photo_dc_id, location, stories_pinned
      admins[], bots[]
    """
    if not userbot._started:
        await userbot.start()

    parsed = _parse_target(target)

    # ── Resolve entity ──────────────────────────────────────────────────
    try:
        entity = await _safe_get_entity(parsed)
    except UsernameNotOccupiedError:
        raise ValueError(f"Username '{target}' does not exist.")
    except UsernameInvalidError:
        raise ValueError(f"Username '{target}' is not valid.")
    except PeerIdInvalidError:
        raise ValueError(
            f"ID '{target}' cannot be resolved.\n"
            "The userbot must share at least one group with this user, "
            "or the user must have a public username."
        )

    if entity is None:
        raise ValueError(f"No information found for '{target}'.")

    # ── Base data dict ──────────────────────────────────────────────────
    data: dict = {
        "id": entity.id,
        "type": None,
        # ── User ──────────────────────────────────────────────────────
        "first_name": None,
        "last_name": None,
        "username": None,
        "phone": None,
        "bio": None,
        "lang_code": None,
        "dc_id": None,
        "profile_photos_count": 0,
        "profile_photos_ids": [],
        "is_bot": False,
        "is_verified": False,
        "is_premium": False,
        "is_scam": False,
        "is_fake": False,
        "is_deleted": False,
        "is_restricted": False,
        "is_support": False,
        "is_mutual_contact": False,
        "stories_hidden": False,            # user hides stories from us
        "contact_require_premium": False,   # only premium users can message them
        "call_requests_disabled": False,    # voice calls disabled
        "blocked": False,                   # they blocked the userbot
        "last_seen_status": None,           # "online"|"offline"|"recently"|"last week"|"last month"|"unknown"
        "last_seen_date": None,             # datetime only when status == "offline"
        "emoji_status": None,               # document_id of Premium emoji (str)
        "profile_color": None,              # color name from Telegram palette
        "personal_channel_id": None,        # linked personal channel (Telegram 2024+)
        "pinned_msg_id": None,              # pinned message id in DM
        "bot_info": None,                   # {description, commands, privacy_policy_url, inline_placeholder}
        "common_groups": [],
        # ── Channel / Group ───────────────────────────────────────────
        "title": None,
        "description": None,
        "member_count": None,
        "invite_link": None,
        "linked_chat": None,
        "slow_mode_delay": None,
        "is_public": False,
        "is_megagroup": False,
        "is_broadcast": False,
        "signatures_enabled": False,
        "has_geo": False,
        "pinned_msg_id_chat": None,
        "pts": None,                        # update sequence number (proxy for activity)
        "available_reactions": [],          # ["all"] or ["😀", ...]
        "banned_rights": None,              # dict of per-permission bools
        "default_banned_rights": None,      # same structure, group default
        "migrated_from_chat_id": None,
        "stickerset_short_name": None,
        "chat_photo_dc_id": None,           # DC of the group/channel photo
        "location": None,                   # {"address": str, "lat": float, "lon": float}
        "stories_pinned": False,            # has pinned stories
        "admins": [],                       # [{id, username, first_name, last_name, is_bot}]
        "bots": [],                         # [{id, username, first_name}]
    }

    # ══════════════════════════════════════════════════════════════════
    # USER
    # ══════════════════════════════════════════════════════════════════
    if isinstance(entity, User):
        data["type"] = "user"
        data["first_name"] = entity.first_name
        data["last_name"] = entity.last_name
        data["username"] = entity.username
        data["lang_code"] = getattr(entity, "lang_code", None)
        data["phone"] = entity.phone   # str "393XXXXXXXX" or None

        # ── Flags on User object ───────────────────────────────────────
        data["is_bot"] = bool(entity.bot)
        data["is_verified"] = bool(entity.verified)
        data["is_premium"] = bool(getattr(entity, "premium", False))
        data["is_scam"] = bool(entity.scam)
        data["is_fake"] = bool(getattr(entity, "fake", False))
        data["is_deleted"] = bool(entity.deleted)
        data["is_restricted"] = bool(entity.restricted)
        data["is_support"] = bool(getattr(entity, "support", False))
        data["is_mutual_contact"] = bool(getattr(entity, "mutual_contact", False))

        # stories_hidden: user has hidden their stories from the userbot
        data["stories_hidden"] = bool(getattr(entity, "stories_hidden", False))

        # contact_require_premium: only premium users can write first message
        data["contact_require_premium"] = bool(
            getattr(entity, "contact_require_premium", False)
        )

        # DC ID from profile photo object
        if entity.photo:
            data["dc_id"] = getattr(entity.photo, "dc_id", None)

        # ── Last seen / online status ──────────────────────────────────
        status_parsed = _parse_status(getattr(entity, "status", None))
        data["last_seen_status"] = status_parsed["text"]
        data["last_seen_date"] = status_parsed["was_online"]

        # ── Premium emoji status ───────────────────────────────────────
        data["emoji_status"] = _parse_emoji_status(
            getattr(entity, "emoji_status", None)
        )

        # ── Profile color ──────────────────────────────────────────────
        data["profile_color"] = _parse_profile_color(
            getattr(entity, "color", None)
        )

        # ── GetFullUserRequest ─────────────────────────────────────────
        full = await _get_full_user(entity)
        if full:
            fu = full.full_user

            # Bio (raw, full, not truncated by Telethon)
            bio = getattr(fu, "about", None)
            data["bio"] = bio.strip() if bio else None

            # Blocked by this user
            data["blocked"] = bool(getattr(fu, "blocked", False))

            # Voice calls disabled
            data["call_requests_disabled"] = bool(
                getattr(fu, "call_requests_disabled", False)
            )

            # Pinned message in DM
            data["pinned_msg_id"] = getattr(fu, "pinned_msg_id", None)

            # Personal channel linked to profile (Telegram 2024+)
            data["personal_channel_id"] = getattr(fu, "personal_channel_id", None)

            # Bot info (only populated for bots)
            bot_info_raw = getattr(fu, "bot_info", None)
            if bot_info_raw:
                commands = []
                for cmd in getattr(bot_info_raw, "commands", []) or []:
                    commands.append({
                        "command": getattr(cmd, "command", ""),
                        "description": getattr(cmd, "description", ""),
                    })
                data["bot_info"] = {
                    "description": getattr(bot_info_raw, "description", None),
                    "privacy_policy_url": getattr(bot_info_raw, "privacy_policy_url", None),
                    "inline_placeholder": getattr(bot_info_raw, "inline_placeholder", None),
                    "commands": commands,
                }

        # ── Profile photos ─────────────────────────────────────────────
        try:
            photo_ids = []
            count = 0
            async for photo in userbot.client.iter_profile_photos(entity.id, limit=10):
                photo_ids.append(photo.id)
                if data["dc_id"] is None:
                    data["dc_id"] = getattr(photo, "dc_id", None)
                count += 1
            data["profile_photos_ids"] = photo_ids
            data["profile_photos_count"] = count
        except (UserPrivacyRestrictedError, RPCError) as e:
            logger.warning(f"Profile photos not accessible for {entity.id}: {e}")

        # ── Common groups ──────────────────────────────────────────────
        if not entity.bot:
            try:
                common_chats = await userbot.get_common_chats(entity)
                data["common_groups"] = [
                    {
                        "id": c.id,
                        "title": c.title,
                        "username": getattr(c, "username", None),
                    }
                    for c in common_chats[:20]
                ]
            except RPCError as e:
                logger.warning(f"Mutual groups not accessible for {entity.id}: {e}")

    # ══════════════════════════════════════════════════════════════════
    # CHANNEL / SUPERGROUP
    # ══════════════════════════════════════════════════════════════════
    elif isinstance(entity, Channel):
        data["type"] = "channel" if entity.broadcast else "group"
        data["title"] = entity.title
        data["username"] = entity.username
        data["is_public"] = bool(entity.username)
        data["is_megagroup"] = bool(entity.megagroup)
        data["is_broadcast"] = bool(entity.broadcast)
        data["is_verified"] = bool(getattr(entity, "verified", False))
        data["is_scam"] = bool(getattr(entity, "scam", False))
        data["is_fake"] = bool(getattr(entity, "fake", False))
        data["is_restricted"] = bool(getattr(entity, "restricted", False))
        data["signatures_enabled"] = bool(getattr(entity, "signatures", False))
        data["has_geo"] = bool(getattr(entity, "has_geo", False))
        data["stories_pinned"] = bool(getattr(entity, "stories_pinned", False))
        data["member_count"] = getattr(entity, "participants_count", None)

        # DC of channel/group photo
        if entity.photo:
            data["chat_photo_dc_id"] = getattr(entity.photo, "dc_id", None)

        # ── GetFullChannelRequest ──────────────────────────────────────
        full = await _get_full_channel(entity)
        if full:
            fc = full.full_chat

            about = getattr(fc, "about", None)
            data["description"] = about.strip() if about else None

            if data["member_count"] is None:
                data["member_count"] = getattr(fc, "participants_count", None)

            exported_invite = getattr(fc, "exported_invite", None)
            if exported_invite:
                data["invite_link"] = getattr(exported_invite, "link", None)

            data["slow_mode_delay"] = getattr(fc, "slowmode_seconds", None)
            data["pinned_msg_id_chat"] = getattr(fc, "pinned_msg_id", None)

            # pts — update sequence number, useful as proxy for channel activity
            data["pts"] = getattr(fc, "pts", None)

            # Available reactions
            data["available_reactions"] = _parse_reactions(
                getattr(fc, "available_reactions", None)
            )

            # Default banned rights (what regular members cannot do)
            data["default_banned_rights"] = _parse_banned_rights(
                getattr(fc, "default_banned_rights", None)
            )

            # Banned rights on the full_chat level (supergroup-wide restrictions)
            data["banned_rights"] = _parse_banned_rights(
                getattr(fc, "banned_rights", None)
            )

            # Migration source
            data["migrated_from_chat_id"] = getattr(fc, "migrated_from_chat_id", None)

            # Official sticker pack
            stickerset = getattr(fc, "stickerset", None)
            if stickerset:
                data["stickerset_short_name"] = getattr(stickerset, "short_name", None)

            # Location (geo-based group)
            location_raw = getattr(fc, "location", None)
            if location_raw and hasattr(location_raw, "geo_point"):
                geo = location_raw.geo_point
                data["location"] = {
                    "address": getattr(location_raw, "address", None),
                    "lat": getattr(geo, "lat", None),
                    "lon": getattr(geo, "long", None),
                }

            # Linked chat (channel ↔ discussion group)
            linked_id = getattr(fc, "linked_chat_id", None)
            if linked_id:
                try:
                    linked_entity = await _safe_get_entity(linked_id)
                    if linked_entity:
                        data["linked_chat"] = {
                            "id": linked_entity.id,
                            "title": linked_entity.title,
                            "username": getattr(linked_entity, "username", None),
                        }
                except Exception:
                    data["linked_chat"] = {
                        "id": linked_id, "title": "N/A", "username": None
                    }

            # Fallback member count
            if data["member_count"] is None and hasattr(full, "chats"):
                for c in full.chats:
                    if c.id == entity.id:
                        data["member_count"] = getattr(c, "participants_count", None)
                        break

        # ── Admins ─────────────────────────────────────────────────────
        admin_users = await _get_channel_participants(entity, ChannelParticipantsAdmins)
        for u in admin_users:
            data["admins"].append({
                "id": u.id,
                "username": getattr(u, "username", None),
                "first_name": getattr(u, "first_name", None),
                "last_name": getattr(u, "last_name", None),
                "is_bot": bool(getattr(u, "bot", False)),
            })

        # ── Bots ───────────────────────────────────────────────────────
        bot_users = await _get_channel_participants(entity, ChannelParticipantsBots)
        for u in bot_users:
            data["bots"].append({
                "id": u.id,
                "username": getattr(u, "username", None),
                "first_name": getattr(u, "first_name", None),
            })

    # ══════════════════════════════════════════════════════════════════
    # BASIC GROUP (Chat)
    # ══════════════════════════════════════════════════════════════════
    elif isinstance(entity, Chat):
        data["type"] = "group"
        data["title"] = entity.title
        data["member_count"] = getattr(entity, "participants_count", None)

        if entity.photo:
            data["chat_photo_dc_id"] = getattr(entity.photo, "dc_id", None)

        full = await _get_full_chat(entity.id)
        if full:
            fc = full.full_chat

            about = getattr(fc, "about", None)
            data["description"] = about.strip() if about else None

            exported_invite = getattr(fc, "exported_invite", None)
            if exported_invite:
                data["invite_link"] = getattr(exported_invite, "link", None)

            data["pinned_msg_id_chat"] = getattr(fc, "pinned_msg_id", None)

            data["available_reactions"] = _parse_reactions(
                getattr(fc, "available_reactions", None)
            )

            data["default_banned_rights"] = _parse_banned_rights(
                getattr(fc, "default_banned_rights", None)
            )

            # If this basic group has been migrated to a supergroup
            migrated_to = getattr(fc, "migrated_to", None)
            if migrated_to:
                data["migrated_from_chat_id"] = entity.id

    else:
        logger.warning(f"Unhandled entity type: {type(entity)}")
        data["type"] = "unknown"

    return data