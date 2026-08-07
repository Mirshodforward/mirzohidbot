"""Magazin biznes-mantig'i — **bot ham, API ham shu yerdan foydalanadi**.

Qarz bilan ishlash ilgari faqat bot handlerlarida edi; API qo'shilganda uni
nusxalash eng tez yo'l bo'lardi, lekin ikki nusxa muqarrar bir-biridan uzilib
qoladi. Shuning uchun barcha yozish amallari shu modulga yig'ildi.

Har bir funksiya tayyor `AsyncSession` oladi va **commit qilmaydi** — chaqiruvchi
tranzaksiya chegarasini o'zi belgilaydi (API'da bitta so'rov = bitta tranzaksiya).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Store, StoreDebtPayment, StoreElectricityLog
from app.domain.rent import apply_rent_accrual_to_store
from app.domain.store_flow import TZ_TASHKENT


class StoreError(Exception):
    """Biznes qoidasi buzildi (routerda 400 ga aylanadi)."""


async def get_store_locked(session: AsyncSession, store_id: int) -> Store:
    """Magazinni qulflab oladi va qarz sikllarini yangilaydi.

    `with_for_update` majburiy: qarz "o'qi → o'zgartir → yoz" ketma-ketligi
    bilan yangilanadi, qulfsiz holda bot va API bir vaqtda kelib bir oylik
    summani ikki marta qo'shib yuborishi mumkin.
    """
    store = await session.get(Store, store_id, with_for_update=True)
    if store is None:
        raise StoreError("Magazin topilmadi.")
    apply_rent_accrual_to_store(store, datetime.now(TZ_TASHKENT))
    return store


@dataclass(frozen=True)
class PaymentResult:
    paid: int
    debt_before: int
    debt_after: int
    payment: StoreDebtPayment


async def apply_payment(
    session: AsyncSession,
    store_id: int,
    amount: int,
    *,
    created_by_telegram_id: int,
) -> PaymentResult:
    """Qarzdan to'lovni ayiradi. Qarzdan ortiq summa qarz miqdoricha kesiladi."""
    if amount <= 0:
        raise StoreError("Summa musbat bo'lishi kerak.")

    store = await get_store_locked(session, store_id)
    debt_before = int(store.debt_balance or 0)
    if debt_before <= 0:
        raise StoreError("Qarz hozir 0 — ayirish mumkin emas.")

    paid = min(amount, debt_before)
    debt_after = debt_before - paid
    store.debt_balance = debt_after

    payment = StoreDebtPayment(
        store_id=store_id,
        amount=paid,
        debt_after=debt_after,
        created_by_telegram_id=created_by_telegram_id,
    )
    session.add(payment)
    await session.flush()
    return PaymentResult(
        paid=paid, debt_before=debt_before, debt_after=debt_after, payment=payment
    )


@dataclass(frozen=True)
class ElectricityResult:
    reading_before: int | None
    reading_after: int
    delta_kw: int
    period_from: datetime | None
    period_to: datetime
    log: StoreElectricityLog | None


async def apply_electricity_reading(
    session: AsyncSession, store_id: int, reading: int
) -> ElectricityResult:
    """Yangi hisoblagich o'qimini yozadi va davr iste'molini hisoblaydi."""
    if reading < 0:
        raise StoreError("Ko'rsatkich manfiy bo'lmaydi.")

    now = datetime.now(TZ_TASHKENT)
    store = await get_store_locked(session, store_id)
    before = store.electricity_kw

    if before is None:
        # Birinchi o'qim — iste'mol yo'q, faqat boshlang'ich qiymat.
        store.electricity_kw = reading
        store.debt_tok = 0
        return ElectricityResult(None, reading, 0, None, now, None)

    if reading < before:
        raise StoreError(
            f"Yangi ko'rsatkich ({reading}) oldingisidan ({before}) kichik bo'lmasin — "
            "hisoblagich orqaga qaytmaydi."
        )

    last_to = await session.scalar(
        select(StoreElectricityLog.period_to)
        .where(StoreElectricityLog.store_id == store_id)
        .order_by(desc(StoreElectricityLog.id))
        .limit(1)
    )
    period_from = last_to or store.created_at or now
    if period_from.tzinfo is None:
        period_from = period_from.replace(tzinfo=TZ_TASHKENT)
    else:
        period_from = period_from.astimezone(TZ_TASHKENT)

    delta = reading - before
    store.electricity_kw = reading
    store.debt_tok = delta

    log = StoreElectricityLog(
        store_id=store_id,
        period_from=period_from,
        period_to=now,
        reading_before=before,
        reading_after=reading,
        delta_kw=delta,
    )
    session.add(log)
    await session.flush()
    return ElectricityResult(before, reading, delta, period_from, now, log)


async def refresh_all_stores(session: AsyncSession) -> list[Store]:
    """Barcha magazinlarni qulflab, qarz sikllarini yangilaydi va qaytaradi."""
    rows = await session.execute(
        select(Store).order_by(Store.id.desc()).with_for_update()
    )
    stores = list(rows.scalars().all())
    now = datetime.now(TZ_TASHKENT)
    for s in stores:
        apply_rent_accrual_to_store(s, now)
    return stores
