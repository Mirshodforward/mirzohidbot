"""Magazin egasi uchun Telegram /start taklif havolasi."""

from __future__ import annotations

import secrets


def new_invite_start_arg() -> str:
    """Telegram /start parametri (64 belgidan oshmasin)."""
    # inv_ (4) + 32 hex = 36
    return "inv_" + secrets.token_hex(16)


def telegram_me_link(bot_username: str, start_arg: str) -> str:
    u = (bot_username or "").strip().lstrip("@")
    return f"https://t.me/{u}?start={start_arg}"
