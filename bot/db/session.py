from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import get_settings
from bot.db.base import Base
from bot.db.models import Store, StoreElectricityLog, User  # noqa: F401 — metadata.create_all

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
]


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in _STORE_ALTER:
            await conn.execute(text(stmt))
