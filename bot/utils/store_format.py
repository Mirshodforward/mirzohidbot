"""Magazin kartochkasi (HTML) — user va admin uchun."""

import html

from bot.db.models import Store
from bot.utils.store_flow import fmt_money, fmt_next_payment, fmt_store_date


def store_card_html(
    s: Store,
    *,
    show_payment: bool = False,
    tok_price_per_kw: int | None = None,
) -> str:
    nm = html.escape(s.name or "")
    addr = html.escape(s.address or "—")
    phone = html.escape(s.owner_phone or "—")
    debt = int(s.debt_balance or 0)
    tok_kw = int(s.debt_tok or 0)
    kw = s.electricity_kw
    kw_line = f"{kw} kW" if kw is not None else "—"
    price_kw = int(tok_price_per_kw) if tok_price_per_kw is not None else None

    lines: list[str] = [
        f"<b>#{s.id}</b> {nm}",
        "",
        f"📞 {phone}",
        f"📍 {addr}",
        f"📅 {fmt_store_date(s.store_date)}",
        f"⚡ Hisoblagich ko'rsatkichi: {kw_line}",
    ]
    if price_kw is not None:
        lines.append(f"💵 Umumiy tok narxi: <b>{fmt_money(price_kw)}</b> so'm / kW")
    lines.append(f"💰 Oylik (kelishuv): {fmt_money(s.monthly_amount)} so'm")
    lines.append("")
    if show_payment:
        lines.append(f"💳 Keyingi oylik to'lov: <b>{fmt_next_payment(s.store_date)}</b>")
    lines.append(f"🔌 Oxirgi tok iste'moli (to'lash): <b>{tok_kw}</b> kW")
    if price_kw is not None:
        tok_sum = tok_kw * price_kw
        lines.append(
            f"💡 Tok uchun to'lash: <b>{fmt_money(tok_sum)}</b> so'm "
            f"({fmt_money(price_kw)} × {tok_kw} kW)"
        )
    lines.append(f"📌 Magazinchi qarzi: <b>{fmt_money(debt)} so'm</b>")
    if s.description:
        lines.append(f"📝 {html.escape(s.description)}")
    return "\n".join(lines)
