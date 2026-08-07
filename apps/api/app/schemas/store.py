from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.store_flow import PHONE_RE


class StoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    address: str | None = None
    owner_phone: str | None = None
    store_date: datetime | None = None
    monthly_amount: int | None = None
    electricity_kw: int | None = None
    debt_tok: int = 0
    debt_balance: int = 0
    created_at: datetime | None = None

    # Hisoblanadigan maydonlar (DB da yo'q) — routerda to'ldiriladi.
    next_payment_at: datetime | None = None
    electricity_price_per_kw: int | None = None
    electricity_due: int | None = None


class StoreCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    owner_phone: str = Field(pattern=PHONE_RE.pattern)
    address: str = Field(min_length=1)
    monthly_amount: int = Field(ge=0)
    electricity_kw: int = Field(ge=0)
    store_date: datetime | None = None  # berilmasa — bugun (Toshkent)
    description: str | None = None


class StoreUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    address: str | None = Field(default=None, min_length=1)
    monthly_amount: int | None = Field(default=None, ge=0)
    description: str | None = None


class StoreCreatedOut(BaseModel):
    store: StoreOut
    invite_link: str | None = None
    invite_token: str | None = None


class PaymentIn(BaseModel):
    amount: int = Field(gt=0, description="Qarzdan ayiriladigan summa (so'm)")


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: int
    amount: int
    debt_after: int
    created_at: datetime
    created_by_telegram_id: int


class ElectricityReadingIn(BaseModel):
    reading: int = Field(ge=0, description="Hisoblagichning yangi ko'rsatkichi (kW)")


class ElectricityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: int
    period_from: datetime
    period_to: datetime
    reading_before: int
    reading_after: int
    delta_kw: int
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    store_id: int
    from_admin: bool
    body: str
    created_at: datetime


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class BroadcastIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class BroadcastOut(BaseModel):
    sent: int
    blocked: int
    failed: int


class ElectricityPriceIn(BaseModel):
    price_per_kw: int = Field(ge=0)


class ElectricityPriceOut(BaseModel):
    price_per_kw: int | None
