import asyncio
import logging
import sys
from pathlib import Path

# `python main.py` ni loyiha papkasidan emas, boshqa joydan chaqirilsa ham `bot` paketi topilsin
_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import get_settings
from bot.db.session import init_db
from bot.handlers import register_handlers
from bot.services.rent_worker import rent_background_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_token.strip():
        logging.error("BOT_TOKEN .env faylida bo'sh. Tokenni qo'shing.")
        sys.exit(1)

    await init_db()

    bot = Bot(
        token=settings.bot_token.strip(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())
    register_handlers(dp)

    asyncio.create_task(rent_background_loop(bot))
    logging.info("Bot ishga tushdi (rent fon vazifasi yoqilgan).")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
