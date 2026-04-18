"""30 kunlik oylik sikllari bo'yicha qarzga oylik qo'shish (store_date + 30n)."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from bot.db.models import Store
from bot.db.session import async_session_maker
from bot.utils.store_flow import TZ_TASHKENT

RENT_PERIOD_DAYS = 30


def _anchor(store_date: datetime) -> datetime:
    tz = TZ_TASHKENT
    return store_date.astimezone(tz) if store_date.tzinfo else store_date.replace(tzinfo=tz)


def _now_tz(now: datetime) -> datetime:
    if now.tzinfo is None:
        return now.replace(tzinfo=TZ_TASHKENT)
    return now.astimezone(TZ_TASHKENT)


def apply_rent_accrual_to_store(store: Store, now: datetime) -> bool:
    """Store obyektini yangilaydi; saqlash kerak bo'lsa True."""
    if not store.store_date or store.monthly_amount is None:
        return False
    m = int(store.monthly_amount)
    if m <= 0:
        return False

    anchor = _anchor(store.store_date)
    now_tz = _now_tz(now)
    changed = False

    cycles = int(store.rent_cycles_accrued or 0)
    debt = int(store.debt_balance or 0)

    if cycles == 0:
        debt = m
        cycles = 1
        changed = True

    while cycles > 0:
        boundary = anchor + timedelta(days=RENT_PERIOD_DAYS * cycles)
        if now_tz < boundary:
            break
        debt += m
        cycles += 1
        changed = True

    if changed:
        store.debt_balance = debt
        store.rent_cycles_accrued = cycles
    return changed


async def refresh_all_store_rent_state() -> None:
    """Barcha magazinlar uchun qarzni yangilab, kerak bo'lsa bazaga yozadi."""
    now = datetime.now(TZ_TASHKENT)
    async with async_session_maker() as session:
        stores = list((await session.execute(select(Store))).scalars().all())
        dirty = False
        for s in stores:
            if apply_rent_accrual_to_store(s, now):
                dirty = True
        if dirty:
            await session.commit()
