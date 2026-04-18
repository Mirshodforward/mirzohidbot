"""
Bazadagi SQLAlchemy modellari bo'yicha barcha jadvallarni o'chirish (DROP).

Ehtiyot: barcha ma'lumotlar yo'qoladi. Keyin jadvallarni qayta yaratish uchun
botni ishga tushiring (init_db create_all + ALTER).

  python reset.py --yes
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.ext.asyncio import create_async_engine

from bot.config import get_settings
from bot.db.base import Base

# Metadata ga barcha jadvallar yuklansin
from bot.db.models import (  # noqa: F401
    Store,
    StoreChatMessage,
    StoreDebtPayment,
    StoreElectricityLog,
    User,
)


async def drop_all_tables() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bazadagi barcha jadvallarni o'chirish (DROP ALL).",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Operatsiyani tasdiqlash (bundsiz hech narsa qilinmaydi)",
    )
    args = parser.parse_args()

    if not args.yes:
        print(
            "Bu skript bazadagi modellar bo'yicha barcha jadvallarni o'chiradi.\n"
            "Davom etish uchun:  python reset.py --yes",
        )
        sys.exit(0)

    asyncio.run(drop_all_tables())
    print("Tayyor: barcha jadvallar o'chirildi.")
    print("Qayta yaratish: python main.py (yoki botni ishga tushiring) — init_db jadvallarni tiklaydi.")


if __name__ == "__main__":
    main()
