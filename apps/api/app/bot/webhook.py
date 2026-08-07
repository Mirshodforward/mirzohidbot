"""Telegram webhook — FastAPI route.

Polling o'rniga webhook: bitta jarayon, bitta update manbai. `getUpdates`
konflikti (ikkita nusxa update'larni bo'lishib olishi) shu bilan yo'qoladi.

Xavfsizlik ikki qatlam:
  1. Yo'lning o'zida maxfiy qism bor (`/telegram/webhook/<WEBHOOK_SECRET>`).
  2. Telegram `X-Telegram-Bot-Api-Secret-Token` sarlavhasini qaytaradi —
     uni ham solishtiramiz.
"""

from __future__ import annotations

import hmac
import logging

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.bot.dispatcher import get_bot, get_dispatcher
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["telegram"])

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


def register_webhook_route(app) -> None:
    """Yo'l maxfiy qismga bog'liq bo'lgani uchun dinamik ro'yxatdan o'tkaziladi."""
    settings = get_settings()

    @app.post(settings.webhook_path, include_in_schema=False)
    async def telegram_webhook(  # noqa: ANN202
        request: Request,
        x_telegram_bot_api_secret_token: str = Header(default=""),
    ):
        if not hmac.compare_digest(
            x_telegram_bot_api_secret_token or "", settings.webhook_secret
        ):
            logger.warning("Webhook: noto'g'ri secret token, rad etildi.")
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")

        data = await request.json()
        update = Update.model_validate(data, context={"bot": get_bot()})
        # Telegram javobni 60 sekundgacha kutadi; xatolik bo'lsa ham 200 qaytarish
        # kerak, aks holda o'sha update qayta-qayta yuboriladi (cheksiz sikl).
        try:
            await get_dispatcher().feed_update(get_bot(), update)
        except Exception:
            logger.exception("Update qayta ishlanmadi: update_id=%s", data.get("update_id"))
        return {"ok": True}


def _masked_webhook_url() -> str:
    """Log uchun: yo'lning maxfiy qismi ko'rsatilmaydi.

    To'liq URL ichida WEBHOOK_SECRET bor — uni jurnalga yozish sirni
    journalctl'ni o'qiy oladigan har kimga oshkor qiladi.
    """
    settings = get_settings()
    return settings.public_base_url.rstrip("/") + "/telegram/webhook/***"


async def setup_webhook() -> None:
    settings = get_settings()
    bot = get_bot()
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret,
        drop_pending_updates=False,
        allowed_updates=get_dispatcher().resolve_used_update_types(),
    )
    logger.info("Webhook o'rnatildi: %s", _masked_webhook_url())


async def setup_menu_button() -> None:
    """Xabar maydoni yonidagi doimiy "Menu" tugmasini Mini App ga bog'laydi.

    Buni BotFather'da qo'lda qilish ham mumkin, lekin shu yerda avtomatik
    o'rnatilsa domen o'zgarganda esdan chiqmaydi.
    """
    from aiogram.types import MenuButtonWebApp, WebAppInfo

    from app.bot.keyboards import miniapp_url

    url = miniapp_url("/app")
    if not url:
        logger.info("PUBLIC_BASE_URL HTTPS emas — Menu tugmasi o'rnatilmadi.")
        return
    try:
        await get_bot().set_chat_menu_button(
            menu_button=MenuButtonWebApp(text="Kabinet", web_app=WebAppInfo(url=url))
        )
        logger.info("Telegram Menu tugmasi Mini App ga bog'landi: %s", url)
    except Exception:
        logger.exception("Menu tugmasi o'rnatilmadi")


async def teardown_webhook() -> None:
    try:
        await get_bot().delete_webhook(drop_pending_updates=False)
        logger.info("Webhook o'chirildi.")
    except Exception:
        logger.exception("Webhook o'chirilmadi")
