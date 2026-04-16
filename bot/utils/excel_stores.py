from io import BytesIO

from openpyxl import Workbook

from bot.db.models import Store
from bot.utils.store_flow import TZ_TASHKENT, fmt_store_date


def stores_to_xlsx_bytes(stores: list[Store]) -> bytes:
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Magazinlar"
    ws.append(
        [
            "ID",
            "Nomi",
            "Telefon",
            "Manzil",
            "Hisobot sanasi",
            "Oylik (so'm)",
            "Tok kW",
            "Yaratilgan",
        ]
    )
    for s in stores:
        created = "—"
        if s.created_at:
            created = s.created_at.astimezone(TZ_TASHKENT).strftime("%d.%m.%Y %H:%M")
        ws.append(
            [
                s.id,
                s.name,
                s.owner_phone or "",
                s.address or "",
                fmt_store_date(s.store_date),
                s.monthly_amount if s.monthly_amount is not None else "",
                s.electricity_kw if s.electricity_kw is not None else "",
                created,
            ]
        )

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()
