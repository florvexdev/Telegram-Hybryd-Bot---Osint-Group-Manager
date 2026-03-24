import logging
from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.sessions import StringSession
from config import API_ID, API_HASH, USERBOT_STRING_SESSION

logger = logging.getLogger(__name__)


def _build_session() -> StringSession:
    """
    Safely builds a StringSession from USERBOT_STRING_SESSION.

    Handles three cases:
      1. Empty / not set        -> fresh session (prompts for phone on first start)
      2. Valid Telethon string  -> reused directly
      3. Invalid string (e.g. old Pyrogram session) -> warning, starts fresh

    To generate a valid Telethon session string run once interactively:
        python generate_session.py
    (see below) then paste the output into USERBOT_STRING_SESSION in your .env/config.
    """
    raw = (USERBOT_STRING_SESSION or "").strip()
    if not raw:
        logger.info("USERBOT_STRING_SESSION not set — starting a fresh session.")
        return StringSession()
    try:
        return StringSession(raw)
    except (ValueError, Exception) as e:
        logger.warning(
            f"USERBOT_STRING_SESSION is not a valid Telethon session string ({e}). "
            "Likely an old Pyrogram session. Starting fresh — you will be prompted "
            "to log in. Save the new session string printed at startup."
        )
        return StringSession()


class UserbotWrapper:
    def __init__(self) -> None:
        self.client = TelegramClient(
            _build_session(),
            api_id=API_ID,
            api_hash=API_HASH,
        )
        self._started = False

    async def start(self) -> None:
        if not self._started:
            await self.client.start()
            self._started = True
            saved = self.client.session.save()
            if saved:
                logger.info(
                    "Userbot started. Save this in USERBOT_STRING_SESSION:\n%s", saved
                )
            else:
                logger.info("Userbot (Telethon) started successfully.")

    async def stop(self) -> None:
        if self._started:
            await self.client.disconnect()
            self._started = False
            logger.info("Userbot stopped.")

    async def get_entity_info(self, identifier):
        """Gets info about a user/group/channel via username, ID or link."""
        try:
            return await self.client.get_entity(identifier)
        except RPCError as e:
            logger.error(f"Error get_entity_info for '{identifier}': {e}")
            raise

    async def get_profile_photos(self, user_id, limit: int = 5) -> list:
        """Retrieves photo objects from a user's profile."""
        photos = []
        try:
            async for photo in self.client.iter_profile_photos(user_id, limit=limit):
                photos.append(photo)
        except RPCError as e:
            logger.warning(f"Unable to retrieve profile photos for {user_id}: {e}")
        return photos

    async def get_common_chats(self, user_entity) -> list:
        """Returns shared groups with a user via raw MTProto call."""
        from telethon.tl.functions.messages import GetCommonChatsRequest
        try:
            result = await self.client(
                GetCommonChatsRequest(user_id=user_entity, max_id=0, limit=20)
            )
            return result.chats
        except RPCError as e:
            logger.warning(f"Unable to retrieve common groups: {e}")
            return []


# Global instance shared between modules
userbot = UserbotWrapper()