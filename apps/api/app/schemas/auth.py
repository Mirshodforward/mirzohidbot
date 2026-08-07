from pydantic import BaseModel, Field


class TelegramLoginIn(BaseModel):
    """Mini App: `window.Telegram.WebApp.initData` xom holida."""

    init_data: str = Field(min_length=1, max_length=8192)


class RequestCodeIn(BaseModel):
    """Sayt: telefon raqamiga bot orqali kod yuborish."""

    phone: str = Field(min_length=9, max_length=20)


class RequestCodeOut(BaseModel):
    # Raqam bazada bor-yo'qligi oshkor qilinmaydi (enumeratsiyaga qarshi):
    # javob har doim bir xil.
    sent: bool = True
    expires_in_sec: int
    message: str


class VerifyCodeIn(BaseModel):
    phone: str = Field(min_length=9, max_length=20)
    code: str = Field(min_length=4, max_length=8)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_sec: int


class MeOut(BaseModel):
    id: int
    telegram_id: int | None
    phone_number: str | None
    full_name: str | None
    username: str | None
    is_admin: bool
    store_count: int
