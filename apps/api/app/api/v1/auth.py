"""Kirish: Mini App (initData) va sayt (telefon + bot kodi)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, or_, select

from app.config import get_settings
from app.config import is_admin as is_admin_id
from app.core.deps import COOKIE_NAME, CurrentUserDep, SessionDep
from app.core.security import (
    LOGIN_CODE_TTL_MIN,
    AuthError,
    create_access_token,
    verify_init_data,
)
from app.db.models import Store, User
from app.domain.store_flow import normalize_phone
from app.schemas.auth import (
    MeOut,
    RequestCodeIn,
    RequestCodeOut,
    TelegramLoginIn,
    TokenOut,
    VerifyCodeIn,
)
from app.services.login_codes import LoginCodeError, consume_code, issue_code

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str, max_age_sec: int) -> None:
    """Sayt uchun httpOnly cookie — JS o'qiy olmaydi, XSS'da o'g'irlanmaydi."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=max_age_sec,
        httponly=True,
        samesite="lax",
        secure=get_settings().public_base_url.startswith("https"),
        path="/",
    )


def _token_for(user: User) -> TokenOut:
    s = get_settings()
    ttl_sec = s.jwt_ttl_minutes * 60
    token = create_access_token(
        user_id=user.id,
        telegram_id=user.telegram_id,
        is_admin=bool(user.telegram_id and is_admin_id(user.telegram_id)),
    )
    return TokenOut(access_token=token, expires_in_sec=ttl_sec)


@router.post("/telegram", response_model=TokenOut)
async def login_telegram(
    payload: TelegramLoginIn, response: Response, session: SessionDep
) -> TokenOut:
    """Mini App kirishi. Frontend `WebApp.initData` ni shu yerga yuboradi."""
    try:
        identity = verify_init_data(payload.init_data)
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    user = await session.scalar(
        select(User).where(User.telegram_id == identity.telegram_id)
    )
    if user is None:
        user = User(
            telegram_id=identity.telegram_id,
            username=identity.username,
            full_name=identity.full_name,
        )
        session.add(user)
    else:
        user.username = identity.username or user.username
        user.full_name = identity.full_name or user.full_name
    await session.commit()
    await session.refresh(user)

    out = _token_for(user)
    _set_session_cookie(response, out.access_token, out.expires_in_sec)
    return out


@router.post("/request-code", response_model=RequestCodeOut)
async def request_code(payload: RequestCodeIn, session: SessionDep) -> RequestCodeOut:
    """Saytga kirish uchun bot orqali bir martalik kod yuboradi."""
    if not normalize_phone(payload.phone):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Telefon formati noto'g'ri. Masalan: +998941339383",
        )

    try:
        await issue_code(session, payload.phone)
        await session.commit()
    except Exception:
        await session.rollback()
        logger.exception("Kirish kodini yuborishda xatolik")

    # Javob har doim bir xil: raqam bazada bor-yo'qligi oshkor qilinmaydi.
    return RequestCodeOut(
        expires_in_sec=LOGIN_CODE_TTL_MIN * 60,
        message=(
            "Agar bu raqam botga ulangan bo'lsa, Telegramga kirish kodi yuborildi. "
            "Telegram xabarlaringizni tekshiring."
        ),
    )


@router.post("/verify-code", response_model=TokenOut)
async def verify_code(
    payload: VerifyCodeIn, response: Response, session: SessionDep
) -> TokenOut:
    try:
        user = await consume_code(session, payload.phone, payload.code)
        await session.commit()
    except LoginCodeError as exc:
        await session.commit()  # urinishlar sonini saqlab qolamiz
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    out = _token_for(user)
    _set_session_cookie(response, out.access_token, out.expires_in_sec)
    return out


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,  # `from __future__ import annotations` sababli — admin.py ga qarang
)
async def logout(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUserDep, session: SessionDep) -> MeOut:
    db_user = await session.get(User, user.id)
    count = 0
    conditions = []
    if user.telegram_id:
        conditions.append(Store.owner_telegram_id == user.telegram_id)
    if user.phone_number:
        key = normalize_phone(user.phone_number) or user.phone_number.strip()
        conditions.append(Store.owner_phone == key)
    if conditions:
        count = (
            await session.scalar(
                select(func.count()).select_from(Store).where(or_(*conditions))
            )
            or 0
        )
    if user.is_admin:
        count = await session.scalar(select(func.count()).select_from(Store)) or 0

    return MeOut(
        id=user.id,
        telegram_id=user.telegram_id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        username=db_user.username if db_user else None,
        is_admin=user.is_admin,
        store_count=count,
    )
