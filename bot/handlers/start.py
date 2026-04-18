import html

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy import select

from bot.config import is_admin
from bot.db.models import Store, User
from bot.db.session import async_session_maker
from bot.keyboards import admin_main_menu, contact_request_keyboard, user_main_menu
from bot.states import InviteLinkStates

router = Router(name="start")


def _start_payload(message: Message) -> str | None:
    raw = (message.text or "").strip()
    if not raw.startswith("/start"):
        return None
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return

    tg = message.from_user
    await state.clear()

    payload = _start_payload(message)
    if payload and payload.startswith("inv_") and not is_admin(tg.id):
        async with async_session_maker() as session:
            st = await session.scalar(
                select(Store).where(Store.owner_invite_token == payload)
            )
        if not st:
            await message.answer(
                "❌ Havola yaroqsiz yoki allaqachon ishlatilgan.\n\n"
                "Yordam uchun admin bilan bog'laning.",
            )
            return
        await state.set_state(InviteLinkStates.waiting_contact)
        await state.update_data(invite_store_id=st.id, invite_token=payload)
        exp = html.escape((st.owner_phone or "").strip() or "—")
        nm = html.escape((st.name or "").strip() or "—")
        await message.answer(
            f"🏪 <b>{nm}</b>\n\n"
            "Magazingizni botga bog'lash uchun quyidagi tugma orqali "
            "<b>o'sha telefon raqamli</b> kontaktingizni yuboring.\n\n"
            f"Kutilayotgan raqam: <code>{exp}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=contact_request_keyboard(),
        )
        return

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
