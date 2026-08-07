"""Bitta joydagi sozlama — bot ham, API ham, scheduler ham shu yerdan o'qiydi."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/app/config.py -> apps/api/app -> apps/api -> apps -> repo ildizi
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILES = (_REPO_ROOT / ".env", _REPO_ROOT / "apps" / "api" / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Baza ---
    database_url: str

    # --- Telegram bot ---
    bot_token: str = ""
    admin_ids: str = ""

    # --- Web / Mini App ---
    # Tashqi HTTPS manzil: Telegram webhook va Mini App shu domenga uradi.
    public_base_url: str = "http://localhost:8000"
    # Frontend manzili — CORS uchun (vergul bilan bir nechta bo'lishi mumkin).
    cors_origins: str = "http://localhost:3000"

    # JWT imzo kaliti. PRODUCTIONDA albatta o'zgartiring:
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    jwt_secret: str = "CHANGE-ME-INSECURE-DEV-SECRET"
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 60 * 24 * 30  # 30 kun

    # Webhook yo'lidagi maxfiy qism — tashqaridan soxta update yubormasliklari uchun.
    webhook_secret: str = "CHANGE-ME-WEBHOOK-SECRET"
    # Bo'sh bo'lsa bot polling rejimida ishlaydi (lokal ishlab chiqish uchun qulay).
    use_webhook: bool = False

    # --- Eslatma ---
    reminder_hour: int = 9  # Asia/Tashkent
    reminder_minute: int = 0

    # --- Zaxira (backup.py / send.py) ---
    backup_bot_token: str = ""
    backup_send_chat_id: str = ""

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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in (self.cors_origins or "").split(",") if o.strip()]

    @property
    def webhook_path(self) -> str:
        return f"/telegram/webhook/{self.webhook_secret}"

    @property
    def webhook_url(self) -> str:
        return self.public_base_url.rstrip("/") + self.webhook_path


@lru_cache
def get_settings() -> Settings:
    return Settings()


def is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_id_set
