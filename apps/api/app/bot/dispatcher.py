"""Bot va Dispatcher singleton'lari.

Endi bot alohida jarayon emas — FastAPI ichida yashaydi. Shu sababli API
routerlari ham xabar yubora oladi (masalan saytga kirish kodi) va **bitta**
`getUpdates`/webhook manbai bo'ladi: `TelegramConflictError` sababi yo'qoladi.
"""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import get_settings

logger = logging.getLogger(__name__)

_bot: Bot | None = None
_dp: Dispatcher | None = None


def get_bot() -> Bot:
    global _bot
    if _bot is None:
        token = get_settings().bot_token.strip()
        if not token:
            raise RuntimeError("BOT_TOKEN sozlanmagan (.env).")
        _bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


def get_dispatcher() -> Dispatcher:
    global _dp
    if _dp is None:
        # DIQQAT: MemoryStorage restartda FSM holatini yo'qotadi. Bir nechta
        # worker ishlatilsa ham holat bo'linib ketadi. Redis qo'shilganda
        # shu yerni RedisStorage ga almashtirish yetarli.
        from app.bot.handlers import register_handlers

        _dp = Dispatcher(storage=MemoryStorage())
        register_handlers(_dp)
        logger.info("Aiogram dispatcher tayyor.")
    return _dp


async def close_bot() -> None:
    global _bot
    if _bot is not None:
        await _bot.session.close()
        _bot = None
