"""Engine, sessiya fabrikasi va "yagona nusxa" qulfi.

Sxema endi **Alembic** bilan boshqariladi (`alembic upgrade head`) — ilgari
shu yerda turgan `create_all` + `ALTER ... IF NOT EXISTS` ro'yxati olib tashlandi.
"""

from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()


def async_url(raw: str) -> str:
    """`postgresql://` ham, `postgresql+asyncpg://` ham ishlashi uchun."""
    url = make_url((raw or "").strip().strip('"').strip("'"))
    if url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+asyncpg")
    return url.render_as_string(hide_password=False)


def sync_url(raw: str) -> str:
    """Alembic uchun sinxron variant (psycopg)."""
    url = make_url((raw or "").strip().strip('"').strip("'"))
    if url.drivername.startswith("postgresql+asyncpg"):
        url = url.set(drivername="postgresql+psycopg")
    elif url.drivername in ("postgresql", "postgres"):
        url = url.set(drivername="postgresql+psycopg")
    return url.render_as_string(hide_password=False)


engine = create_async_engine(
    async_url(settings.database_url),
    echo=False,
    pool_pre_ping=True,
)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency."""
    async with async_session_maker() as session:
        yield session


# ---------------------------------------------------------------------------
# Yagona nusxa qulfi (single-instance lock)
#
# Ikki maqsad:
#  1. Polling rejimida ikkita bot nusxasi bir vaqtda `getUpdates` qilsa Telegram
#     `TelegramConflictError` beradi va update'lar ikki jarayon o'rtasida
#     tasodifiy bo'linadi — xabarlar "yo'qoladi".
#  2. Uvicorn bir nechta worker bilan ishga tushsa, scheduler har bir workerda
#     nusxalanib, qarzni bir necha marta hisoblab yuboradi.
#
# Postgres advisory lock ikkalasini ham hal qiladi: qulfni faqat bitta jarayon
# oladi, faqat o'sha jarayon fon vazifalarini yuritadi.
# ---------------------------------------------------------------------------

_LOCK_KEY = 0x4D52_5A48  # "MRZH"
_lock_conn: AsyncConnection | None = None


async def acquire_single_instance_lock() -> bool:
    """True — qulf olindi; False — boshqa nusxa allaqachon ushlab turibdi."""
    global _lock_conn
    if _lock_conn is not None:
        return True
    conn = await engine.connect()
    await conn.execution_options(isolation_level="AUTOCOMMIT")
    try:
        got = await conn.scalar(text("SELECT pg_try_advisory_lock(:k)"), {"k": _LOCK_KEY})
    except Exception:
        await conn.close()
        raise
    if not got:
        await conn.close()
        return False
    _lock_conn = conn
    return True


async def release_single_instance_lock() -> None:
    global _lock_conn
    conn, _lock_conn = _lock_conn, None
    if conn is None:
        return
    try:
        await conn.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": _LOCK_KEY})
    except Exception:
        pass
    finally:
        await conn.close()
