"""Fon rejimida: qarzni avto yangilash + to'lov sanasidan 3 kun oldin eslatma."""

from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy import or_, select

from bot.db.models import Store, User
from bot.db.session import async_session_maker
from bot.utils.rent_accrual import apply_rent_accrual_to_store
from bot.utils.store_flow import (
    TZ_TASHKENT,
    fmt_money,
    normalize_phone,
    rent_reminder_eligible,
)

logger = logging.getLogger(__name__)

INTERVAL_SEC = 3600


async def _owner_telegram_ids(session, owner_phone: str) -> list[int]:
    raw = (owner_phone or "").strip()
    if not raw:
        return []
    key = normalize_phone(raw) or raw
    r = await session.execute(
        select(User.telegram_id).where(
            or_(User.phone_number == key, User.phone_number == raw)
        )
    )
    return [row[0] for row in r.all()]


async def _send_rent_reminders(bot: Bot, now: datetime) -> None:
    now_tz = now.astimezone(TZ_TASHKENT) if now.tzinfo else now.replace(tzinfo=TZ_TASHKENT)
    async with async_session_maker() as session:
        stores = list((await session.execute(select(Store))).scalars().all())
        for s in stores:
            debt = int(s.debt_balance or 0)
            if debt <= 0:
                if s.rent_reminder_sent_for is not None:
                    s.rent_reminder_sent_for = None
                continue
            if not s.owner_phone:
                continue

            eligible, due_dt, phase = rent_reminder_eligible(s.store_date, now_tz, debt)
            if not eligible or not due_dt or not phase:
                continue

            due_dt = due_dt.astimezone(TZ_TASHKENT)
            last = s.rent_reminder_sent_for
            if last is not None:
                last_d = last.astimezone(TZ_TASHKENT).date()
                if last_d == now_tz.date():
                    continue

            uids = await _owner_telegram_ids(session, s.owner_phone)
            nm = html.escape((s.name or "Magazin").strip())
            due_s = due_dt.strftime("%d.%m.%Y")
            if phase == "approaching":
                days_left = max(0, (due_dt.date() - now_tz.date()).days)
                text = (
                    f"🏪 <b>{nm}</b>\n\n"
                    f"Keyingi oylik to'lovi: <b>{due_s}</b> "
                    f"(taxminiy qolgan kunlar: <b>{days_left}</b>).\n\n"
                    f"Hozirgi qarzingiz: <b>{fmt_money(debt)} so'm</b>.\n\n"
                    "Muddatgacha to'lang. Bu eslatma <b>har kuni</b> "
                    "yuboriladi (Toshkent vaqti bo'yicha kuniga 1 marta)."
                )
            else:
                text = (
                    f"🏪 <b>{nm}</b>\n\n"
                    f"⚠️ <b>Qarz to'lovi bo'yicha eslatma.</b>\n"
                    f"Keyingi hisoblangan muddat: <b>{due_s}</b>.\n\n"
                    f"Hozirgi qarzingiz: <b>{fmt_money(debt)} so'm</b>.\n\n"
                    "Iltimos, qarzni to'lang. Qarz qolmaganiga qadar "
                    "bu xabar <b>har kuni</b> yuboriladi (kuniga 1 marta)."
                )
            sent_any = False
            for uid in uids:
                try:
                    await bot.send_message(uid, text)
                    sent_any = True
                except Exception:
                    logger.debug("Eslatma yuborilmadi uid=%s", uid, exc_info=True)
            if sent_any:
                s.rent_reminder_sent_for = now_tz
        await session.commit()


async def run_rent_accrual_pass(now: datetime | None = None) -> None:
    now = now or datetime.now(TZ_TASHKENT)
    async with async_session_maker() as session:
        stores = list((await session.execute(select(Store))).scalars().all())
        dirty = False
        for s in stores:
            if apply_rent_accrual_to_store(s, now):
                dirty = True
        if dirty:
            await session.commit()


async def rent_background_loop(bot: Bot) -> None:
    await asyncio.sleep(30)
    while True:
        try:
            now = datetime.now(TZ_TASHKENT)
            await run_rent_accrual_pass(now)
            await _send_rent_reminders(bot, now)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("rent_background_loop xatolik")
        await asyncio.sleep(INTERVAL_SEC)
