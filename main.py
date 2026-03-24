import asyncio
import logging

from telegram.ext import Application

from config import BOT_TOKEN
from bot_handlers import register_handlers
from userbot_client import userbot
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    # 1. Initialize database
    await init_db()
    logger.info("Database initialized")

    # 2. Start Pyrogram userbot
    await userbot.start()

    # 3. Configure and start the official bot
    bot_app = Application.builder().token(BOT_TOKEN).build()
    register_handlers(bot_app)

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)

    logger.info("✅ Bot running — press Ctrl+C to stop")

    try:
        # Mantieni il processo attivo fino a interruzione
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Interrupt received, closing...")
    finally:
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await userbot.stop()
        logger.info("Bot stopped correctly")


if __name__ == "__main__":
    asyncio.run(main())
