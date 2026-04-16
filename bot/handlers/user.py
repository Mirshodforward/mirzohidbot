import html

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy import select

from bot.config import get_settings, is_admin
from bot.db.models import Store, User
from bot.db.session import async_session_maker
from bot.keyboards import (
    BTN_CANCEL,
    USER_BTN_MY_STORE,
    USER_BTN_TO_ADMIN,
    cancel_keyboard,
    user_main_menu,
)
from bot.states import UserToAdminStates
from bot.utils.store_flow import normalize_phone
from bot.utils.store_format import store_card_html

router = Router(name="user")


async def load_user_stores(telegram_id: int) -> list[Store]:
    async with async_session_maker() as session:
        u = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        if not u or not u.phone_number:
            return []
        raw = u.phone_number.strip()
        key = normalize_phone(raw) or raw
        r = await session.execute(
            select(Store).where(Store.owner_phone == key).order_by(Store.id.desc())
        )
        return list(r.scalars().all())


@router.message(F.contact)
async def on_contact(message: Message) -> None:
    if not message.from_user or not message.contact:
        return

    if is_admin(message.from_user.id):
        return

    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("Faqat o'zingizning kontaktingizni yuboring.")
        return

    raw_phone = (contact.phone_number or "").strip()
    normalized = normalize_phone(raw_phone)
    phone_to_save = normalized if normalized else raw_phone

    stores: list[Store] = []
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        row = result.scalar_one_or_none()
        if row:
            row.phone_number = phone_to_save
            row.username = message.from_user.username
            row.full_name = message.from_user.full_name
        else:
            session.add(
                User(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    full_name=message.from_user.full_name,
                    phone_number=phone_to_save,
                )
            )

        if normalized:
            q = await session.execute(
                select(Store)
                .where(Store.owner_phone == normalized)
                .order_by(Store.id.desc())
            )
            stores = list(q.scalars().all())

        await session.commit()

    parts: list[str] = []
    head = "Rahmat! Ma'lumotlaringiz qabul qilindi."
    if stores:
        head += "\n\n🏪 <b>Sizning magazingiz</b>"
    cur = head
    for s in stores:
        block = "\n\n" + store_card_html(s, show_payment=True)
        if len(cur) + len(block) > 3800:
            parts.append(cur)
            cur = block.lstrip("\n")
        else:
            cur += block
    parts.append(cur)

    for i, p in enumerate(parts):
        last = i == len(parts) - 1
        await message.answer(
            p,
            parse_mode=ParseMode.HTML,
            reply_markup=user_main_menu() if last else None,
        )


@router.message(StateFilter(default_state), F.text == USER_BTN_MY_STORE)
async def user_my_stores(message: Message) -> None:
    if not message.from_user or is_admin(message.from_user.id):
        return
    stores = await load_user_stores(message.from_user.id)
    if not stores:
        await message.answer(
            "Sizning telefon raqamingiz bilan bog'langan magazin topilmadi "
            "yoki kontakt hali ulangan emas. /start orqali kontaktingizni yuboring.",
        )
        return
    parts: list[str] = []
    cur = "🏪 <b>Mening magazinlarim</b>"
    for s in stores:
        block = "\n\n" + store_card_html(s, show_payment=True)
        if len(cur) + len(block) > 3800:
            parts.append(cur)
            cur = block.lstrip("\n")
        else:
            cur += block
    parts.append(cur)
    for p in parts:
        await message.answer(p, parse_mode=ParseMode.HTML)


@router.message(StateFilter(default_state), F.text == USER_BTN_TO_ADMIN)
async def user_to_admin_begin(message: Message, state: FSMContext) -> None:
    if not message.from_user or is_admin(message.from_user.id):
        return
    await state.set_state(UserToAdminStates.message)
    await message.answer(
        "Adminga yubormoqchi bo'lgan matningizni yozing.\n"
        "Bekor qilish uchun tugmani bosing.",
        reply_markup=cancel_keyboard(),
    )


@router.message(UserToAdminStates.message, F.text == BTN_CANCEL)
async def user_to_admin_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=user_main_menu())


@router.message(UserToAdminStates.message, F.text)
async def user_to_admin_send(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    if is_admin(message.from_user.id):
        return

    text = (message.text or "").strip()
    if text in (USER_BTN_TO_ADMIN, USER_BTN_MY_STORE):
        await message.answer(
            "Iltimos, adminga yubormoqchi bo'lgan matningizni yozing "
            "yoki bekor qiling.",
        )
        return
    if not text:
        await message.answer("Matn bo'sh bo'lmasin.")
        return

    admins = get_settings().admin_id_set
    if not admins:
        await state.clear()
        await message.answer(
            "Hozircha admin sozlanmagan. Keyinroq urinib ko'ring.",
            reply_markup=user_main_menu(),
        )
        return

    uf = message.from_user
    async with async_session_maker() as session:
        dbu = await session.scalar(select(User).where(User.telegram_id == uf.id))
    phone_line = ""
    if dbu and dbu.phone_number:
        phone_line = f"📞 {html.escape(dbu.phone_number)}\n"

    header = (
        f"📩 <b>Foydalanuvchi xabari</b>\n"
        f"👤 {html.escape(uf.full_name or '—')} "
        f"(@{html.escape(uf.username or '—')})\n"
        f"🆔 <code>{uf.id}</code>\n"
        f"{phone_line}\n"
        f"<b>Xabar:</b>\n{html.escape(text)}"
    )

    ok, fail = 0, 0
    for aid in admins:
        try:
            await message.bot.send_message(
                aid,
                header,
                parse_mode=ParseMode.HTML,
            )
            ok += 1
        except Exception:
            fail += 1

    await state.clear()
    if ok:
        await message.answer(
            "Xabaringiz adminlarga yuborildi.",
            reply_markup=user_main_menu(),
        )
    else:
        await message.answer(
            "Yuborishda xatolik. Keyinroq urinib ko'ring.",
            reply_markup=user_main_menu(),
        )


@router.message(UserToAdminStates.message, ~F.text)
async def user_to_admin_non_text(message: Message) -> None:
    await message.answer("Faqat matn yuboring yoki bekor qiling.")
