import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
API_ID: int = int(os.getenv("API_ID", "0"))
API_HASH: str = os.getenv("API_HASH", "")
USERBOT_STRING_SESSION: str = os.getenv("USERBOT_STRING_SESSION", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data.db")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env file")
if not API_ID:
    raise ValueError("API_ID not set in .env file")
if not API_HASH:
    raise ValueError("API_HASH not set in .env file")
