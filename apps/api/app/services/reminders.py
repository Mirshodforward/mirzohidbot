"""Qarz hisoblash va kunlik to'lov eslatmasi.

Vaqtni endi **APScheduler** boshqaradi (`app/services/scheduler.py`), bu modul
faqat "nima qilish" ni biladi. Har ikkala funksiya ham **idempotent**: bir kunda
necha marta chaqirilsa ham eslatma bir marta ketadi (`rent_reminder_sent_for`).
"""

from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime

from aiogram import Bot
from sqlalchemy import or_, select

from app.config import get_settings
from app.db.models import Store, User
from app.db.session import async_session_maker
from app.domain.rent import apply_rent_accrual_to_store
from app.domain.store_flow import (
    TZ_TASHKENT,
    fmt_money,
    normalize_phone,
    rent_reminder_eligible,
)
from app.services.tg_send import SEND_GAP_SEC, SendResult, send_message_safe

logger = logging.getLogger(__name__)


async def _owner_telegram_ids(session, store: Store) -> list[int]:
    """Egani topish: to'g'ridan-to'g'ri bog'langan Telegram ID (havola orqali)
    va/yoki telefon raqami mos keladigan foydalanuvchilar — telefon shart emas."""
    ids: set[int] = set()
    if store.owner_telegram_id:
        ids.add(store.owner_telegram_id)

    raw = (store.owner_phone or "").strip()
    if raw:
        key = normalize_phone(raw) or raw
        r = await session.execute(
            select(User.telegram_id).where(
                or_(User.phone_number == key, User.phone_number == raw)
            )
        )
        ids.update(row[0] for row in r.all())
    return list(ids)


def _reminder_text(
    store_name: str, due_dt: datetime, now_tz: datetime, debt: int, phase: str
) -> str:
    hour = get_settings().reminder_hour
    nm = html.escape((store_name or "Magazin").strip())
    due_s = due_dt.strftime("%d.%m.%Y")
    if phase == "approaching":
        days_left = max(0, (due_dt.date() - now_tz.date()).days)
        return (
            f"🏪 <b>{nm}</b>\n\n"
            f"Keyingi oylik to'lovi: <b>{due_s}</b> "
            f"(taxminiy qolgan kunlar: <b>{days_left}</b>).\n\n"
            f"Hozirgi qarzingiz: <b>{fmt_money(debt)} so'm</b>.\n\n"
            f"Muddatgacha to'lang. Bu eslatma <b>har kuni</b> soat {hour:02d}:00 da "
            "(Toshkent vaqti) yuboriladi."
        )
    return (
        f"🏪 <b>{nm}</b>\n\n"
        f"⚠️ <b>Qarz to'lovi bo'yicha eslatma.</b>\n"
        f"Keyingi hisoblangan muddat: <b>{due_s}</b>.\n\n"
        f"Hozirgi qarzingiz: <b>{fmt_money(debt)} so'm</b>.\n\n"
        "Iltimos, qarzni to'lang. Qarz qolmaganiga qadar bu xabar "
        f"<b>har kuni</b> soat {hour:02d}:00 da yuboriladi."
    )


async def run_rent_accrual_pass(now: datetime | None = None) -> None:
    """Barcha magazinlarda 30 kunlik sikllarni qarzga qo'shadi."""
    now = now or datetime.now(TZ_TASHKENT)
    async with async_session_maker() as session:
        stores = list(
            (await session.execute(select(Store).with_for_update())).scalars().all()
        )
        dirty = False
        for s in stores:
            if apply_rent_accrual_to_store(s, now):
                dirty = True
        if dirty:
            await session.commit()


async def send_due_reminders(bot: Bot, *, enforce_hour: bool = False) -> int:
    """Bugun hali eslatma olmagan qarzdor magazinlarga yuboradi.

    `enforce_hour=True` — catch-up chaqiruvi uchun: belgilangan soat kelmagan
    bo'lsa hech narsa qilinmaydi. Cron chaqiruvida kerak emas.

    Qaytadi: eslatma ketgan magazinlar soni.
    """
    now_tz = datetime.now(TZ_TASHKENT)
    if enforce_hour and now_tz.hour < get_settings().reminder_hour:
        return 0

    today = now_tz.date()
    sent_total = 0

    async with async_session_maker() as session:
        stores = list((await session.execute(select(Store))).scalars().all())
        for s in stores:
            debt = int(s.debt_balance or 0)
            if debt <= 0:
                if s.rent_reminder_sent_for is not None:
                    s.rent_reminder_sent_for = None
                continue

            last = s.rent_reminder_sent_for
            if last is not None:
                last_tz = (
                    last.astimezone(TZ_TASHKENT)
                    if last.tzinfo
                    else last.replace(tzinfo=TZ_TASHKENT)
                )
                if last_tz.date() == today:
                    continue

            if not s.owner_phone and not s.owner_telegram_id:
                logger.warning(
                    "Eslatma yuborilmadi: magazin #%s (%s) — egasi hali botga ulanmagan.",
                    s.id,
                    s.name,
                )
                continue

            eligible, due_dt, phase = rent_reminder_eligible(s.store_date, now_tz, debt)
            if not eligible or not due_dt or not phase:
                continue

            uids = await _owner_telegram_ids(session, s)
            if not uids:
                logger.warning(
                    "Eslatma yuborilmadi: magazin #%s (%s) — egasi botda "
                    "kontakt/havola orqali hali ulanmagan.",
                    s.id,
                    s.name,
                )
                continue

            text = _reminder_text(
                s.name or "", due_dt.astimezone(TZ_TASHKENT), now_tz, debt, phase
            )
            delivered = False
            retryable = False
            for uid in uids:
                res = await send_message_safe(bot, uid, text)
                if res is SendResult.OK:
                    delivered = True
                elif res is SendResult.FAILED:
                    retryable = True
                await asyncio.sleep(SEND_GAP_SEC)

            if delivered:
                sent_total += 1
                s.rent_reminder_sent_for = now_tz
            elif not retryable:
                # Hamma qabul qiluvchi botni bloklagan — qayta urinish behuda.
                logger.warning(
                    "Magazin #%s: barcha egalari botni bloklagan, bugunga belgilandi.",
                    s.id,
                )
                s.rent_reminder_sent_for = now_tz
            else:
                logger.warning(
                    "Magazin #%s: eslatma yuborilmadi, catch-up da qayta urinamiz.", s.id
                )

        await session.commit()

    if sent_total:
        logger.info("Kunlik eslatma yuborildi: %s ta magazin.", sent_total)
    return sent_total
