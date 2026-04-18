"""Magazin kartochkasi (HTML) — user va admin uchun."""

import html

from bot.db.models import Store
from bot.utils.store_flow import fmt_money, fmt_next_payment, fmt_store_date


def store_card_html(s: Store, *, show_payment: bool = False) -> str:
    nm = html.escape(s.name or "")
    addr = html.escape(s.address or "—")
    phone = html.escape(s.owner_phone or "—")
    debt = int(s.debt_balance or 0)
    tok_kw = int(s.debt_tok or 0)
    kw = s.electricity_kw
    kw_line = f"{kw} kW" if kw is not None else "—"

    lines: list[str] = [
        f"<b>#{s.id}</b> {nm}",
        "",
        f"📞 {phone}",
        f"📍 {addr}",
        f"📅 {fmt_store_date(s.store_date)}",
        f"⚡ Hisoblagich ko'rsatkichi: {kw_line}",
        f"💰 Oylik (kelishuv): {fmt_money(s.monthly_amount)} so'm",
        "",
    ]
    if show_payment:
        lines.append(f"💳 Keyingi oylik to'lov: <b>{fmt_next_payment(s.store_date)}</b>")
    lines.append(f"🔌 Oxirgi tok iste'moli (to'lash): <b>{tok_kw}</b> kW")
    lines.append(f"📌 Magazinchi qarzi: <b>{fmt_money(debt)} so'm</b>")
    if s.description:
        lines.append(f"📝 {html.escape(s.description)}")
    return "\n".join(lines)
