from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import get_settings
from bot.db.base import Base
from bot.db.models import (  # noqa: F401 — metadata.create_all
    AppSettings,
    Store,
    StoreChatMessage,
    StoreDebtPayment,
    StoreElectricityLog,
    User,
)

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    echo=False,
)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


_STORE_ALTER = [
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS owner_phone VARCHAR(16)",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS address TEXT",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS store_date TIMESTAMPTZ",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS monthly_amount BIGINT",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS electricity_kw INTEGER",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS debt_balance BIGINT NOT NULL DEFAULT 0",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS rent_cycles_accrued INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS rent_reminder_sent_for TIMESTAMPTZ",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS debt_tok INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stores ADD COLUMN IF NOT EXISTS owner_invite_token VARCHAR(64)",
    "ALTER TABLE stores DROP COLUMN IF EXISTS electricity_price_per_kw",
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _STORE_ALTER:
            await conn.execute(text(stmt))
