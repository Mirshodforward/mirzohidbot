"""Autentifikatsiya primitivlari: Telegram initData, JWT, bir martalik kodlar."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl

import jwt

from app.config import get_settings

# initData shu muddatdan eski bo'lsa qabul qilinmaydi (replay hujumiga qarshi).
INIT_DATA_MAX_AGE_SEC = 24 * 60 * 60

LOGIN_CODE_TTL_MIN = 5
LOGIN_CODE_MAX_ATTEMPTS = 5


class AuthError(Exception):
    """initData yoki token yaroqsiz."""


@dataclass(frozen=True)
class TelegramIdentity:
    telegram_id: int
    username: str | None
    full_name: str | None


# ---------------------------------------------------------------------------
# Telegram Mini App initData
# ---------------------------------------------------------------------------


def verify_init_data(init_data: str, *, bot_token: str | None = None) -> TelegramIdentity:
    """`window.Telegram.WebApp.initData` ni tekshiradi.

    Algoritm (Telegram hujjati bo'yicha):
        secret = HMAC_SHA256(key="WebAppData", msg=bot_token)
        hash   = HMAC_SHA256(key=secret, msg=data_check_string)

    `data_check_string` — `hash` dan tashqari barcha maydonlar `k=v` ko'rinishida,
    alifbo tartibida, `\\n` bilan birlashtirilgan.
    """
    token = (bot_token or get_settings().bot_token).strip()
    if not token:
        raise AuthError("BOT_TOKEN sozlanmagan.")
    if not init_data:
        raise AuthError("initData bo'sh.")

    # `parse_qsl` bo'sh qiymatlarni ham saqlashi kerak — aks holda hash mos kelmaydi.
    pairs = parse_qsl(init_data, keep_blank_values=True)
    data = dict(pairs)

    received_hash = data.pop("hash", "")
    if not received_hash:
        raise AuthError("initData ichida hash yo'q.")

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received_hash):
        raise AuthError("initData imzosi noto'g'ri.")

    auth_date = data.get("auth_date")
    if auth_date:
        try:
            age = time.time() - int(auth_date)
        except ValueError as exc:
            raise AuthError("auth_date noto'g'ri.") from exc
        if age > INIT_DATA_MAX_AGE_SEC:
            raise AuthError("initData muddati o'tgan, ilovani qayta oching.")

    raw_user = data.get("user")
    if not raw_user:
        raise AuthError("initData ichida user yo'q.")
    try:
        user = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise AuthError("initData.user JSON emas.") from exc

    tg_id = user.get("id")
    if not isinstance(tg_id, int):
        raise AuthError("initData.user.id yo'q.")

    full_name = " ".join(
        p for p in (user.get("first_name"), user.get("last_name")) if p
    ).strip()
    return TelegramIdentity(
        telegram_id=tg_id,
        username=user.get("username"),
        full_name=full_name or None,
    )


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------


def create_access_token(
    *,
    user_id: int,
    telegram_id: int | None,
    is_admin: bool,
    ttl_minutes: int | None = None,
) -> str:
    s = get_settings()
    now = datetime.now(UTC)
    ttl = ttl_minutes if ttl_minutes is not None else s.jwt_ttl_minutes
    payload = {
        "sub": str(user_id),
        "tg": telegram_id,
        "adm": bool(is_admin),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    s = get_settings()
    try:
        return jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("Token muddati tugagan.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("Token yaroqsiz.") from exc


# ---------------------------------------------------------------------------
# Bir martalik kirish kodi
# ---------------------------------------------------------------------------


def generate_login_code() -> str:
    """6 xonali kod. `secrets` — taxmin qilib bo'lmaydigan."""
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_login_code(code: str) -> str:
    return hashlib.sha256(code.strip().encode()).hexdigest()


def verify_login_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_login_code(code), code_hash)
