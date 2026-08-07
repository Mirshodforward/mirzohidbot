"""Saytga telefon orqali kirish: bot bir martalik kod yuboradi.

SMS shluzi kerak emas — foydalanuvchi allaqachon botda, kod o'sha yerga boradi.
Bu bepul va SMS'dan ishonchliroq.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    LOGIN_CODE_MAX_ATTEMPTS,
    LOGIN_CODE_TTL_MIN,
    generate_login_code,
    hash_login_code,
    verify_login_code,
)
from app.db.models import LoginCode, User
from app.domain.store_flow import normalize_phone
from app.services.tg_send import SendResult, send_message_safe

logger = logging.getLogger(__name__)


class LoginCodeError(Exception):
    pass


async def _find_user_by_phone(session: AsyncSession, phone: str) -> User | None:
    key = normalize_phone(phone) or phone.strip()
    return await session.scalar(
        select(User).where(
            or_(User.phone_number == key, User.phone_number == phone.strip())
        )
    )


async def issue_code(session: AsyncSession, phone: str) -> bool:
    """Kod yaratib botga yuboradi. Qaytadi: haqiqatan yuborildimi.

    Chaqiruvchi bu natijani foydalanuvchiga **oshkor qilmasligi** kerak —
    aks holda raqamlarni bittalab tekshirib, kim ro'yxatda borligini bilib olish
    mumkin bo'ladi.
    """
    user = await _find_user_by_phone(session, phone)
    if user is None or not user.telegram_id:
        logger.info("Kirish kodi so'raldi, lekin raqam topilmadi: %s", phone)
        return False

    key = normalize_phone(phone) or phone.strip()

    # Eski, ishlatilmagan kodlarni bekor qilamiz — bir vaqtda bittasi amal qiladi.
    await session.execute(
        update(LoginCode)
        .where(LoginCode.phone_number == key, LoginCode.consumed_at.is_(None))
        .values(consumed_at=datetime.now(UTC))
    )

    code = generate_login_code()
    session.add(
        LoginCode(
            phone_number=key,
            code_hash=hash_login_code(code),
            expires_at=datetime.now(UTC) + timedelta(minutes=LOGIN_CODE_TTL_MIN),
        )
    )
    await session.flush()

    from app.bot.dispatcher import get_bot

    text = (
        "🔐 <b>Saytga kirish kodi</b>\n\n"
        f"<code>{code}</code>\n\n"
        f"Kod {LOGIN_CODE_TTL_MIN} daqiqa amal qiladi.\n"
        "<i>Agar siz kirmoqchi bo'lmagan bo'lsangiz — bu xabarni e'tiborsiz qoldiring "
        "va kodni hech kimga bermang.</i>"
    )
    res = await send_message_safe(get_bot(), user.telegram_id, text)
    if res is not SendResult.OK:
        logger.warning("Kirish kodi yuborilmadi: user=%s natija=%s", user.id, res)
        return False
    return True


async def consume_code(session: AsyncSession, phone: str, code: str) -> User:
    """Kodni tekshirib, foydalanuvchini qaytaradi. Xato bo'lsa LoginCodeError."""
    key = normalize_phone(phone) or phone.strip()
    now = datetime.now(UTC)

    row = await session.scalar(
        select(LoginCode)
        .where(LoginCode.phone_number == key, LoginCode.consumed_at.is_(None))
        .order_by(LoginCode.id.desc())
        .limit(1)
        .with_for_update()
    )
    if row is None:
        raise LoginCodeError("Kod topilmadi. Yangi kod so'rang.")

    expires = row.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    if expires < now:
        row.consumed_at = now
        raise LoginCodeError("Kod muddati tugagan. Yangi kod so'rang.")

    if row.attempts >= LOGIN_CODE_MAX_ATTEMPTS:
        row.consumed_at = now
        raise LoginCodeError("Urinishlar soni tugadi. Yangi kod so'rang.")

    if not verify_login_code(code, row.code_hash):
        # Brute-force'ga qarshi: har xato urinish sanaladi va limitga yetganda
        # kod butunlay kuyadi.
        row.attempts += 1
        raise LoginCodeError(
            f"Kod noto'g'ri. Qolgan urinishlar: {LOGIN_CODE_MAX_ATTEMPTS - row.attempts}"
        )

    row.consumed_at = now
    user = await _find_user_by_phone(session, key)
    if user is None:
        raise LoginCodeError("Foydalanuvchi topilmadi.")
    return user
