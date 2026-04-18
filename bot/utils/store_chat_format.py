"""Admin ↔ magazin suhbati HTML (ajratilgan bloklar)."""

from __future__ import annotations

import html
from collections.abc import Sequence

from bot.db.models import StoreChatMessage

SEP = "\n\n────────\n\n"


def format_store_thread_html(
    messages: Sequence[StoreChatMessage],
    *,
    max_len: int = 3800,
    header: str | None = None,
) -> str:
    """Har xabar alohida: Admin / Magazin."""
    chunks: list[str] = []
    for m in messages:
        label = "<b>👤 Admin:</b>" if m.from_admin else "<b>🏪 Magazin:</b>"
        chunks.append(f"{label}\n{html.escape(m.body)}")
    body = SEP.join(chunks) if chunks else "<i>Hozircha yozuvlar yo'q.</i>"
    if header:
        body = f"{header}\n\n{body}"
    if len(body) <= max_len:
        return body
    while chunks and len(SEP.join(chunks)) + (len(header) + 2 if header else 0) > max_len:
        chunks.pop(0)
    body = SEP.join(chunks) if chunks else ""
    if header:
        body = f"{header}\n\n{body}"
    if len(body) > max_len:
        body = "…\n\n" + body[-max_len + 4 :]
    return body
