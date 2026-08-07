"""Telegramga xavfsiz yuborish: flood-control (429), bloklangan chatlar, tarmoq xatolari.

Loyihada har joyda `try: ... except Exception: pass` ishlatilgan edi — natijada
429 (Too Many Requests) xatosi ham "yuborilmadi" deb jimgina yutilardi va
xabar umuman yetib bormasdi. Bu modul o'sha yagona to'g'ri yo'lni beradi.
"""

from __future__ import annotations

import asyncio
import logging
from enum import StrEnum

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)

logger = logging.getLogger(__name__)

# Telegram: bitta botdan turli chatlarga ~30 xabar/sek. Xavfsiz oraliq.
SEND_GAP_SEC = 0.05
MAX_ATTEMPTS = 3


class SendResult(StrEnum):
    OK = "ok"
    BLOCKED = "blocked"  # bot bloklangan / chat yo'q — qayta urinish foydasiz
    FAILED = "failed"  # vaqtinchalik xato — keyingi urinishda yuborish mumkin


async def send_message_safe(bot: Bot, chat_id: int, text: str, **kwargs) -> SendResult:
    """Bitta xabar. 429 bo'lsa kutib qayta uradi, blok bo'lsa BLOCKED qaytaradi."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            await bot.send_message(chat_id, text, **kwargs)
            return SendResult.OK
        except TelegramRetryAfter as exc:
            wait = float(getattr(exc, "retry_after", 1) or 1) + 0.5
            logger.warning(
                "Flood control (429): chat=%s, %.1f sek kutilmoqda", chat_id, wait
            )
            await asyncio.sleep(wait)
        except TelegramForbiddenError:
            logger.info("Bot bloklangan yoki chat yopiq: chat=%s", chat_id)
            return SendResult.BLOCKED
        except TelegramBadRequest as exc:
            low = str(exc).lower()
            if "chat not found" in low or "user is deactivated" in low:
                logger.info("Chat topilmadi/o'chirilgan: chat=%s", chat_id)
                return SendResult.BLOCKED
            logger.warning("Yuborilmadi (bad request) chat=%s: %s", chat_id, exc)
            return SendResult.FAILED
        except TelegramNetworkError as exc:
            logger.warning(
                "Tarmoq xatosi chat=%s (urinish %s/%s): %s",
                chat_id,
                attempt,
                MAX_ATTEMPTS,
                exc,
            )
            await asyncio.sleep(1.5 * attempt)
        except Exception:
            logger.exception("Kutilmagan yuborish xatosi: chat=%s", chat_id)
            return SendResult.FAILED
    logger.error("Xabar yuborilmadi (%s urinish): chat=%s", MAX_ATTEMPTS, chat_id)
    return SendResult.FAILED


async def broadcast(
    bot: Bot,
    chat_ids: list[int],
    text: str,
    *,
    gap: float = SEND_GAP_SEC,
    **kwargs,
) -> tuple[int, int, int]:
    """Ko'p chatga yuborish. Qaytaradi: (ok, blocked, failed)."""
    ok = blocked = failed = 0
    for chat_id in chat_ids:
        res = await send_message_safe(bot, chat_id, text, **kwargs)
        if res is SendResult.OK:
            ok += 1
        elif res is SendResult.BLOCKED:
            blocked += 1
        else:
            failed += 1
        if gap:
            await asyncio.sleep(gap)
    return ok, blocked, failed
