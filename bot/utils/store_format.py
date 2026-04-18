"""Magazin kartochkasi (HTML) — user va admin uchun."""

import html

from bot.db.models import Store
from bot.utils.store_flow import fmt_money, fmt_next_payment, fmt_store_date


def store_card_html(s: Store, *, show_payment: bool = False) -> str:
    nm = html.escape(s.name or "")
    addr = html.escape(s.address or "—")
    phone = html.escape(s.owner_phone or "—")
    debt = int(s.debt_balance or 0)
    block = (
        f"<b>#{s.id}</b> {nm}\n"
        f"📞 {phone}\n"
        f"📍 {addr}\n"
        f"📅 {fmt_store_date(s.store_date)}\n"
        f"💰 Oylik (kelishuv): {fmt_money(s.monthly_amount)} so'm\n"
        f"📌 Joriy qarz: <b>{fmt_money(debt)} so'm</b>\n"
        f"⚡ Hisoblagich: {s.electricity_kw if s.electricity_kw is not None else '—'} kW\n"
        f"🔌 Oxirgi tok iste'moli (to'lash): <b>{int(s.debt_tok or 0)}</b> kW "
        f"(<i>yangi − eski</i>)"
    )
    if show_payment:
        block += f"\n💳 Keyingi oylik to'lov: <b>{fmt_next_payment(s.store_date)}</b>"
    if s.description:
        block += f"\n📝 {html.escape(s.description)}"
    return block
