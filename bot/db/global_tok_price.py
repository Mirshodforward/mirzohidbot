"""Umumiy tok narxi (so'm/kW) — barcha magazinlar uchun."""

from bot.db.models import AppSettings
from bot.db.session import async_session_maker


async def get_electricity_price_per_kw() -> int | None:
    async with async_session_maker() as session:
        row = await session.get(AppSettings, 1)
        if row is None or row.electricity_price_per_kw is None:
            return None
        return int(row.electricity_price_per_kw)


async def set_electricity_price_per_kw(value: int) -> None:
    async with async_session_maker() as session:
        row = await session.get(AppSettings, 1)
        if row is None:
            session.add(AppSettings(id=1, electricity_price_per_kw=value))
        else:
            row.electricity_price_per_kw = value
        await session.commit()
