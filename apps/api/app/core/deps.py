"""FastAPI dependency'lari: joriy foydalanuvchi, admin tekshiruvi, magazin egaligi."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import is_admin as is_admin_id
from app.core.security import AuthError, decode_access_token
from app.db.models import Store, User
from app.db.session import get_session
from app.domain.store_flow import normalize_phone

SessionDep = Annotated[AsyncSession, Depends(get_session)]

# `auto_error=False` — token yo'q bo'lsa 403 emas, o'zimiz 401 qaytaramiz.
_bearer = HTTPBearer(auto_error=False)

# Saytda token httpOnly cookie'da yuriladi (XSS'da o'g'irlanmaydi),
# Mini App'da esa Authorization sarlavhasida.
COOKIE_NAME = "mrz_session"


@dataclass(frozen=True)
class CurrentUser:
    id: int
    telegram_id: int | None
    phone_number: str | None
    full_name: str | None
    is_admin: bool


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    request: Request,
    session: SessionDep,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> CurrentUser:
    token = creds.credentials if creds else request.cookies.get(COOKIE_NAME)
    if not token:
        raise _unauthorized("Avtorizatsiya talab qilinadi.")

    try:
        payload = decode_access_token(token)
    except AuthError as exc:
        raise _unauthorized(str(exc)) from exc

    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError) as exc:
        raise _unauthorized("Token tarkibi noto'g'ri.") from exc

    user = await session.get(User, user_id)
    if user is None:
        raise _unauthorized("Foydalanuvchi topilmadi.")

    # Admin huquqi tokendan emas, har safar .env dan tekshiriladi — ADMIN_IDS
    # dan chiqarilgan odam eski tokeni bilan kira olmasin.
    admin = bool(user.telegram_id and is_admin_id(user.telegram_id))
    return CurrentUser(
        id=user.id,
        telegram_id=user.telegram_id,
        phone_number=user.phone_number,
        full_name=user.full_name,
        is_admin=admin,
    )


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


async def require_admin(user: CurrentUserDep) -> CurrentUser:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu amal faqat admin uchun.",
        )
    return user


AdminDep = Annotated[CurrentUser, Depends(require_admin)]


def _user_owns_store(user: CurrentUser, store: Store) -> bool:
    """Ikki mustaqil mezon: Telegram ID (invite havolasi orqali bog'langan)
    yoki telefon raqami mos kelishi — biri yetarli, telefon shart emas."""
    if user.telegram_id and store.owner_telegram_id == user.telegram_id:
        return True
    if user.phone_number and store.owner_phone:
        mine = normalize_phone(user.phone_number) or user.phone_number.strip()
        theirs = normalize_phone(store.owner_phone) or store.owner_phone.strip()
        if mine == theirs:
            return True
    return False


async def owned_store(store_id: int, user: CurrentUserDep, session: SessionDep) -> Store:
    """Magazinni qaytaradi; admin — hammasini, egasi — faqat o'zinikini."""
    store = await session.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Magazin topilmadi.")
    if user.is_admin:
        return store
    if not _user_owns_store(user, store):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bu magazin sizga tegishli emas.")
    return store


OwnedStoreDep = Annotated[Store, Depends(owned_store)]


async def user_store_ids(user: CurrentUser, session: AsyncSession) -> list[int]:
    conditions = []
    if user.telegram_id:
        conditions.append(Store.owner_telegram_id == user.telegram_id)
    if user.phone_number:
        key = normalize_phone(user.phone_number) or user.phone_number.strip()
        conditions.append(Store.owner_phone == key)
    if not conditions:
        return []
    rows = await session.execute(select(Store.id).where(or_(*conditions)))
    return [r[0] for r in rows.all()]
