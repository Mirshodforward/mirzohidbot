from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select

from bot.config import is_admin
from bot.db.models import User
from bot.db.session import async_session_maker
from bot.keyboards import admin_main_menu, contact_request_keyboard, user_main_menu

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return

    tg = message.from_user

    has_phone = False
    async with async_session_maker() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg.id))
        db_user = result.scalar_one_or_none()
        if not db_user:
            session.add(
                User(
                    telegram_id=tg.id,
                    username=tg.username,
                    full_name=tg.full_name,
                )
            )
            await session.commit()
        else:
            has_phone = bool(db_user.phone_number)

    if is_admin(tg.id):
        await message.answer(
            "Xush kelibsiz, admin!\n\n"
            "Quyidagi bo'limlardan birini tanlang.",
            reply_markup=admin_main_menu(),
        )
        return

    if has_phone:
        await message.answer(
            "Assalomu alaykum!\n\n"
            "<b>Meni magazinim</b> — magazin va keyingi to'lov sanasi.\n"
            "<b>Adminga xabar</b> — yozma murojaat.",
            parse_mode=ParseMode.HTML,
            reply_markup=user_main_menu(),
        )
        return

    await message.answer(
        "Assalomu alaykum!\n\n"
        "Davom etish uchun iltimos, kontaktingizni ulashing.",
        reply_markup=contact_request_keyboard(),
    )
