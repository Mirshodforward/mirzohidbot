"""
PostgreSQL bazasining to'liq zaxirasi (pg_dump).

`.env` dagi DATABASE_URL dan ulanadi (masalan:
postgresql+asyncpg://user:pass@localhost:5432/mirzohid_db).

Ishlatish:
  python backup.py
  python backup.py --dir ./backups

Talab: `pg_dump` tizimda mavjud bo'lishi kerak (PostgreSQL client).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_root = str(Path(__file__).resolve().parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from sqlalchemy.engine import make_url

from bot.config import get_settings


def _db_params(database_url: str) -> dict[str, str | int]:
    u = make_url(database_url)
    return {
        "host": u.host or "localhost",
        "port": int(u.port or 5432),
        "user": u.username or "postgres",
        "password": u.password or "",
        "database": u.database or "postgres",
    }


def run_backup(out_dir: Path) -> Path:
    settings = get_settings()
    raw_url = (settings.database_url or "").strip()
    if not raw_url:
        raise SystemExit("DATABASE_URL .env faylida topilmadi.")

    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise SystemExit(
            "pg_dump topilmadi.\n"
            "PostgreSQL client o'rnating (masalan: postgresql-client) "
            "va bin papkani PATH ga qo'shing."
        )

    cfg = _db_params(raw_url)
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_name = str(cfg["database"])
    out_path = out_dir / f"{db_name}_{ts}.sql"

    env = os.environ.copy()
    if cfg["password"]:
        env["PGPASSWORD"] = str(cfg["password"])

    cmd = [
        pg_dump,
        "-h",
        str(cfg["host"]),
        "-p",
        str(cfg["port"]),
        "-U",
        str(cfg["user"]),
        "-d",
        db_name,
        "--no-owner",
        "--no-acl",
        "-f",
        str(out_path),
    ]

    print(
        f"Zaxira olinmoqda: {cfg['user']}@{cfg['host']}:{cfg['port']}/{db_name}"
    )
    print(f"Papka: {out_dir}")

    try:
        subprocess.run(cmd, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"pg_dump xato bilan tugadi (kod {exc.returncode}).") from exc
    finally:
        env.pop("PGPASSWORD", None)

    size = out_path.stat().st_size
    print(f"Tayyor: {out_path} ({size:,} bayt)")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DATABASE_URL bo'yicha PostgreSQL to'liq zaxirasi.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path("backups"),
        help="Zaxira saqlanadigan papka (default: backups)",
    )
    args = parser.parse_args()
    run_backup(args.dir.resolve())


if __name__ == "__main__":
    main()
