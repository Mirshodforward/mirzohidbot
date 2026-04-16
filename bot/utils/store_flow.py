import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ_TASHKENT = ZoneInfo("Asia/Tashkent")

PHONE_RE = re.compile(r"^\+998\d{9}$")


def normalize_phone(raw: str) -> str | None:
    s = (raw or "").strip().replace(" ", "")
    if not s.startswith("+"):
        if s.startswith("998") and len(s) == 12:
            s = "+" + s
        elif re.fullmatch(r"9\d{8}", s):
            s = "+998" + s
    if PHONE_RE.match(s):
        return s
    return None


def tashkent_today_start() -> datetime:
    d = datetime.now(TZ_TASHKENT).date()
    return datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=TZ_TASHKENT)


def fmt_store_date(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.astimezone(TZ_TASHKENT).strftime("%d.%m.%Y")


def fmt_money(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n:,}".replace(",", " ")


def next_rent_payment_dt(store_date: datetime | None) -> datetime | None:
    """store_date dan boshlab har 30 kun — hozirdan keyingi birinchi to'lov sanasi."""
    if not store_date:
        return None
    tz = TZ_TASHKENT
    a = store_date.astimezone(tz) if store_date.tzinfo else store_date.replace(tzinfo=tz)
    now = datetime.now(tz)
    for k in range(5000):
        due = a + timedelta(days=30 * k)
        if due > now:
            return due
    return None


def fmt_next_payment(store_date: datetime | None) -> str:
    dt = next_rent_payment_dt(store_date)
    if not dt:
        return "—"
    return dt.astimezone(TZ_TASHKENT).strftime("%d.%m.%Y")


def fmt_datetime(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.astimezone(TZ_TASHKENT).strftime("%d.%m.%Y %H:%M")


def parse_manual_date(text: str) -> datetime | None:
    s = (text or "").strip()
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if not m:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try:
        d = datetime(year, month, day, 0, 0, 0, tzinfo=TZ_TASHKENT)
    except ValueError:
        return None
    return d


def parse_amount(text: str) -> int | None:
    s = re.sub(r"[\s_]", "", (text or "").strip())
    if not s.isdigit():
        return None
    v = int(s)
    if v < 0:
        return None
    return v


def parse_kw(text: str) -> int | None:
    s = (text or "").strip().lower().replace("kw", "").replace("квт", "").strip()
    s = re.sub(r"\s+", "", s)
    if not s.isdigit():
        return None
    v = int(s)
    if v < 0:
        return None
    return v
