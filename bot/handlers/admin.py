import asyncio
from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import CallbackQuery, Message
from sqlalchemy import func, select

from bot.db.models import Store, User
from bot.db.session import async_session_maker
from bot.filters import AdminFilter
from bot.keyboards import (
    ADMIN_BTN_LIST,
    ADMIN_BTN_MSG,
    ADMIN_BTN_NEW,
    ADMIN_BTN_REPORT,
    BTN_CANCEL,
    admin_main_menu,
    cancel_keyboard,
    store_date_keyboard,
)
from bot.states import AddStoreStates, BroadcastStates
from bot.utils.store_flow import (
    fmt_money,
    fmt_store_date,
    normalize_phone,
    parse_amount,
    parse_kw,
    parse_manual_date,
    tashkent_today_start,
)

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_NEW)
async def add_store_begin(message: Message, state: FSMContext) -> None:
    await state.set_state(AddStoreStates.owner_phone)
    await message.answer(
        "Magazin egasining telefon raqamini yuboring.\n"
        "Format: <code>+998941339383</code> (9 raqam, +998 bilan)",
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(AddStoreStates), F.text == BTN_CANCEL)
async def add_store_cancel_any(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.callback_query(AddStoreStates.date_choice, F.data == "store:date:auto")
async def add_store_date_auto(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    d = tashkent_today_start()
    await state.update_data(store_date=d.isoformat())
    await state.set_state(AddStoreStates.monthly_amount)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"Sanasi: <b>{d.strftime('%d.%m.%Y')}</b> (Asia/Toshkent, avto).\n\n"
            "Kelishilgan oylik summani yozing (so'm, faqat raqam):",
            reply_markup=cancel_keyboard(),
        )
    elif callback.from_user:
        await callback.bot.send_message(
            callback.from_user.id,
            f"Sanasi: <b>{d.strftime('%d.%m.%Y')}</b> (Asia/Toshkent, avto).\n\n"
            "Kelishilgan oylik summani yozing (so'm, faqat raqam):",
            reply_markup=cancel_keyboard(),
        )


@router.callback_query(AddStoreStates.date_choice, F.data == "store:date:manual")
async def add_store_date_manual(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.set_state(AddStoreStates.manual_date)
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            "Sanani <b>DD.MM.YYYY</b> formatida yozing (masalan: <code>15.04.2026</code>):",
            reply_markup=cancel_keyboard(),
        )
    elif callback.from_user:
        await callback.bot.send_message(
            callback.from_user.id,
            "Sanani <b>DD.MM.YYYY</b> formatida yozing (masalan: <code>15.04.2026</code>):",
            reply_markup=cancel_keyboard(),
        )


@router.message(AddStoreStates.owner_phone, F.text)
async def add_store_owner_phone(message: Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text or "")
    if not phone:
        await message.answer(
            "Noto'g'ri format. Masalan: <code>+998941339383</code> yoki <code>941339383</code>",
        )
        return
    await state.update_data(owner_phone=phone)
    await state.set_state(AddStoreStates.name)
    await message.answer("Magazin nomini yozing:")


@router.message(AddStoreStates.name, F.text)
async def add_store_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nom bo'sh bo'lmasin.")
        return
    await state.update_data(name=name)
    await state.set_state(AddStoreStates.address)
    await message.answer("Magazin manzilini yozing:")


@router.message(AddStoreStates.address, F.text)
async def add_store_address(message: Message, state: FSMContext) -> None:
    addr = (message.text or "").strip()
    if not addr:
        await message.answer("Manzil bo'sh bo'lmasin.")
        return
    await state.update_data(address=addr)
    await state.set_state(AddStoreStates.date_choice)
    await message.answer(
        "Hisobot sanasi: avtomatik <b>bugun (Asia/Toshkent)</b> yoki qo'lda kiriting.",
        reply_markup=store_date_keyboard(),
    )


@router.message(AddStoreStates.manual_date, F.text)
async def add_store_manual_date(message: Message, state: FSMContext) -> None:
    d = parse_manual_date(message.text or "")
    if not d:
        await message.answer("Format noto'g'ri. Masalan: <code>15.04.2026</code>")
        return
    await state.update_data(store_date=d.isoformat())
    await state.set_state(AddStoreStates.monthly_amount)
    await message.answer(
        f"Sanasi: <b>{d.strftime('%d.%m.%Y')}</b>.\n\n"
        "Kelishilgan oylik summani yozing (so'm, faqat raqam):",
    )


@router.message(AddStoreStates.monthly_amount, F.text)
async def add_store_monthly(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text or "")
    if amount is None:
        await message.answer("Faqat musbat butun son (masalan: <code>5000000</code>).")
        return
    await state.update_data(monthly_amount=amount)
    await state.set_state(AddStoreStates.electricity_kw)
    await message.answer(
        "Elektr hisoblagich ko'rsatkichi (kW, masalan: <code>4197</code> yoki <code>4197 kw</code>):",
    )


@router.message(AddStoreStates.electricity_kw, F.text)
async def add_store_kw_finish(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    kw = parse_kw(message.text or "")
    if kw is None:
        await message.answer("Butun musbat son kiriting (masalan: <code>4197</code>).")
        return

    data = await state.get_data()
    name = data.get("name")
    owner_phone = data.get("owner_phone")
    address = data.get("address")
    store_date_raw = data.get("store_date")
    monthly_amount = data.get("monthly_amount")

    if not all([name, owner_phone, address, store_date_raw, monthly_amount is not None]):
        await state.clear()
        await message.answer("Sessiya buzildi. Qaytadan boshlang.", reply_markup=admin_main_menu())
        return

    store_date = datetime.fromisoformat(store_date_raw)

    async with async_session_maker() as session:
        session.add(
            Store(
                name=name,
                owner_phone=owner_phone,
                address=address,
                store_date=store_date,
                monthly_amount=int(monthly_amount),
                electricity_kw=kw,
                created_by_telegram_id=message.from_user.id,
            )
        )
        await session.commit()

    await state.clear()
    await message.answer(
        "✅ Magazin yaratildi.\n\n"
        f"📛 {name}\n"
        f"📞 {owner_phone}\n"
        f"📍 {address}\n"
        f"📅 {fmt_store_date(store_date)}\n"
        f"💰 Oylik: {fmt_money(int(monthly_amount))} so'm\n"
        f"⚡ Elektr: {kw} kW",
        reply_markup=admin_main_menu(),
    )


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_REPORT)
async def report(message: Message) -> None:
    async with async_session_maker() as session:
        stores = await session.scalar(select(func.count()).select_from(Store))
        users = await session.scalar(select(func.count()).select_from(User))
        with_phone = await session.scalar(
            select(func.count()).select_from(User).where(User.phone_number.isnot(None))
        )

    text = (
        "📈 Hisobot\n\n"
        f"Magazinlar: {stores or 0}\n"
        f"Foydalanuvchilar (jami): {users or 0}\n"
        f"Kontakt ulaganlar: {with_phone or 0}"
    )
    await message.answer(text)


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_MSG)
async def messages_menu(message: Message, state: FSMContext) -> None:
    async with async_session_maker() as session:
        with_phone = await session.scalar(
            select(func.count()).select_from(User).where(User.phone_number.isnot(None))
        )
    await state.set_state(BroadcastStates.text)
    await message.answer(
        f"✉️ Xabarlar\n\n"
        f"Kontakt ulagan foydalanuvchilar: {with_phone or 0}\n\n"
        "Barcha ulangan foydalanuvchilarga yuboriladigan matnni yozing "
        "(bekor uchun tugmani bosing):",
        reply_markup=cancel_keyboard(),
    )


@router.message(BroadcastStates.text, F.text == BTN_CANCEL)
async def broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(BroadcastStates.text, F.text)
async def broadcast_send(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Matn bo'sh bo'lmasin.")
        return

    # Xabarlar rejimida pastki menyudagi tugmalar "matn" deb tutilib qolmasin
    if text in (
        ADMIN_BTN_LIST,
        ADMIN_BTN_NEW,
        ADMIN_BTN_REPORT,
        ADMIN_BTN_MSG,
    ):
        await state.clear()
        if text == ADMIN_BTN_LIST:
            from bot.handlers.admin_stores import admin_list_stores

            await admin_list_stores(message)
            return
        if text == ADMIN_BTN_NEW:
            await add_store_begin(message, state)
            return
        if text == ADMIN_BTN_REPORT:
            await report(message)
            return
        await messages_menu(message, state)
        return

    async with async_session_maker() as session:
        result = await session.execute(
            select(User.telegram_id).where(User.phone_number.isnot(None))
        )
        ids = [r[0] for r in result.all()]

    await state.clear()
    await message.answer(
        f"Yuborilmoqda: {len(ids)} ta foydalanuvchi...",
        reply_markup=admin_main_menu(),
    )

    ok, fail = 0, 0
    for uid in ids:
        try:
            await message.bot.send_message(uid, text)
            ok += 1
            await asyncio.sleep(0.04)
        except Exception:
            fail += 1

    await message.answer(
        f"Tugadi.\nMuvaffaqiyatli: {ok}\nYuborilmadi: {fail}",
        reply_markup=admin_main_menu(),
    )
