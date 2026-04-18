import html

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.config import get_settings, is_admin
from bot.db.global_tok_price import get_electricity_price_per_kw
from bot.db.models import Store, StoreChatMessage, User
from bot.db.session import async_session_maker
from bot.keyboards import (
    BTN_CANCEL,
    USER_BTN_MY_STORE,
    USER_BTN_TO_ADMIN,
    cancel_keyboard,
    contact_request_keyboard,
    user_main_menu,
)
from bot.states import InviteLinkStates, OwnerStoreReplyStates, UserToAdminStates
from bot.utils.rent_accrual import refresh_all_store_rent_state
from bot.utils.store_flow import normalize_phone
from bot.utils.store_chat_format import format_store_thread_html
from bot.utils.store_format import store_card_html

router = Router(name="user")


async def _user_owns_store(telegram_id: int, store_id: int) -> bool:
    stores = await load_user_stores(telegram_id)
    return any(s.id == store_id for s in stores)


@router.message(InviteLinkStates.waiting_contact, F.contact)
async def on_contact_invite_link(message: Message, state: FSMContext) -> None:
    if not message.from_user or not message.contact:
        return
    if is_admin(message.from_user.id):
        return
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("Faqat o'zingizning kontaktingizni yuboring.")
        return

    data = await state.get_data()
    sid = data.get("invite_store_id")
    token = data.get("invite_token")
    if not isinstance(sid, int) or not isinstance(token, str):
        await state.clear()
        await message.answer("Sessiya buzildi. /start dan qayta kiring.")
        return

    raw_phone = (contact.phone_number or "").strip()
    normalized = normalize_phone(raw_phone)
    phone_to_save = normalized if normalized else raw_phone

    async with async_session_maker() as session:
        st = await session.get(Store, sid)
        if not st or st.owner_invite_token != token:
            await state.clear()
            await message.answer("Havola endi yaroqli emas. Admin bilan bog'laning.")
            return
        expected_key = normalize_phone(st.owner_phone or "") or (st.owner_phone or "").strip()
        contact_key = normalized if normalized else phone_to_save.strip()
        if not expected_key or contact_key != expected_key:
            await message.answer(
                f"Bu magazin uchun kutilayotgan raqam: <code>{html.escape(st.owner_phone or '—')}</code>.\n"
                "Iltimos, aynan shu raqamli kontaktni yuboring.",
                parse_mode=ParseMode.HTML,
            )
            return

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
        st.owner_invite_token = None
        await session.commit()

    await state.clear()
    await refresh_all_store_rent_state()
    stores: list[Store] = []
    if normalized:
        async with async_session_maker() as session:
            q = await session.execute(
                select(Store)
                .where(Store.owner_phone == normalized)
                .order_by(Store.id.desc())
            )
            stores = list(q.scalars().all())
    parts: list[str] = []
    head = "✅ Magazingiz botga ulandi!"
    if stores:
        head += "\n\n🏪 <b>Sizning magazingiz</b>"
    tok_p = await get_electricity_price_per_kw()
    cur = head
    for s in stores:
        block = "\n\n" + store_card_html(s, show_payment=True, tok_price_per_kw=tok_p)
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


@router.message(InviteLinkStates.waiting_contact, ~F.contact)
async def on_invite_need_contact(message: Message) -> None:
    await message.answer(
        "Kontaktni yuboring (tugma orqali) — magazinni bog'lash uchun zarur.",
        reply_markup=contact_request_keyboard(),
    )


async def load_user_stores(telegram_id: int) -> list[Store]:
    await refresh_all_store_rent_state()
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


@router.message(StateFilter(default_state), F.contact)
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

        await session.commit()

    await refresh_all_store_rent_state()
    stores: list[Store] = []
    if normalized:
        async with async_session_maker() as session:
            q = await session.execute(
                select(Store)
                .where(Store.owner_phone == normalized)
                .order_by(Store.id.desc())
            )
            stores = list(q.scalars().all())
    parts: list[str] = []
    head = "Rahmat! Ma'lumotlaringiz qabul qilindi."
    if stores:
        head += "\n\n🏪 <b>Sizning magazingiz</b>"
    tok_p = await get_electricity_price_per_kw()
    cur = head
    for s in stores:
        block = "\n\n" + store_card_html(s, show_payment=True, tok_price_per_kw=tok_p)
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
    tok_p = await get_electricity_price_per_kw()
    for s in stores:
        block = "\n\n" + store_card_html(s, show_payment=True, tok_price_per_kw=tok_p)
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


@router.callback_query(F.data.startswith("stjr:"))
async def owner_store_reply_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not callback.from_user or is_admin(callback.from_user.id):
        await callback.answer()
        return
    raw = (callback.data or "").strip()
    parts = raw.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer()
        return
    sid = int(parts[1])
    if not await _user_owns_store(callback.from_user.id, sid):
        await callback.answer("Bu magazin sizga tegishli emas.", show_alert=True)
        return
    await state.set_state(OwnerStoreReplyStates.waiting_reply)
    await state.update_data(reply_store_id=sid)
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    uid = callback.from_user.id
    await callback.bot.send_message(
        uid,
        "✍️ Javobingizni yozing (bekor tugmasi bilan chiqish).",
        reply_markup=cancel_keyboard(),
    )


@router.message(OwnerStoreReplyStates.waiting_reply, F.text == BTN_CANCEL)
async def owner_store_reply_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=user_main_menu())


@router.message(OwnerStoreReplyStates.waiting_reply, F.text)
async def owner_store_reply_commit(message: Message, state: FSMContext) -> None:
    if not message.from_user or is_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if text in (USER_BTN_MY_STORE, USER_BTN_TO_ADMIN):
        await message.answer("Javob tugatish uchun bekor tugmasidan foydalaning.")
        return
    if not text:
        await message.answer("Matn bo'sh bo'lmasin.")
        return
    data = await state.get_data()
    sid = data.get("reply_store_id")
    if not isinstance(sid, int):
        await state.clear()
        await message.answer("Sessiya buzildi.", reply_markup=user_main_menu())
        return
    if not await _user_owns_store(message.from_user.id, sid):
        await state.clear()
        await message.answer("Ruxsat yo'q.", reply_markup=user_main_menu())
        return

    admins = get_settings().admin_id_set
    if not admins:
        await state.clear()
        await message.answer(
            "Admin sozlanmagan. Keyinroq urinib ko'ring.",
            reply_markup=user_main_menu(),
        )
        return

    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await state.clear()
            await message.answer("Magazin topilmadi.", reply_markup=user_main_menu())
            return
        session.add(
            StoreChatMessage(
                store_id=sid,
                from_admin=False,
                author_telegram_id=message.from_user.id,
                body=text,
            )
        )
        await session.commit()
        msgs = (
            await session.execute(
                select(StoreChatMessage)
                .where(StoreChatMessage.store_id == sid)
                .order_by(StoreChatMessage.id.asc())
                .limit(200)
            )
        ).scalars().all()

    header = (
        f"📬 <b>Magazin javobi</b> — "
        f"{html.escape((s.name or '').strip() or '—')} "
        f"(<code>#{sid}</code>)\n"
        f"👤 {html.escape(message.from_user.full_name or '—')} "
        f"<code>{message.from_user.id}</code>\n\n<b>Suhbat:</b>"
    )
    body = format_store_thread_html(list(msgs), header=header, max_len=3900)

    ok = 0
    for aid in admins:
        try:
            await message.bot.send_message(aid, body, parse_mode=ParseMode.HTML)
            ok += 1
        except Exception:
            pass

    await state.clear()
    if ok:
        await message.answer(
            "Javobingiz adminlarga yuborildi.",
            reply_markup=user_main_menu(),
        )
    else:
        await message.answer(
            "Yuborishda xatolik. Keyinroq urinib ko'ring.",
            reply_markup=user_main_menu(),
        )


@router.message(OwnerStoreReplyStates.waiting_reply, ~F.text)
async def owner_store_reply_non_text(message: Message) -> None:
    await message.answer("Faqat matn yuboring yoki bekor qiling.")
