"""
Run this script ONCE to generate a valid Telethon session string.
Then paste the output into USERBOT_STRING_SESSION in your .env / config.py.

Usage:
    pip install telethon
    python generate_session.py
"""
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("Enter API_ID: "))
API_HASH = input("Enter API_HASH: ").strip()

async def main():
    async with TelegramClient(StringSession(), API_ID, API_HASH) as client:
        await client.start()
        session_string = client.session.save()
        print("\n✅ Your Telethon session string (save this in USERBOT_STRING_SESSION):\n")
        print(session_string)
        print()

asyncio.run(main())