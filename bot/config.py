from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# `bot/` dan bir daraja yuqori — loyiha ildizi (main.py va .env shu yerda)
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    bot_token: str = ""
    admin_ids: str = ""

    @property
    def admin_id_set(self) -> set[int]:
        raw = (self.admin_ids or "").strip()
        if not raw:
            return set()
        out: set[int] = set()
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.add(int(part))
            except ValueError:
                continue
        return out


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_id_set
