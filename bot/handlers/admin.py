from datetime import datetime

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
import html

from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy import desc, func, select

from bot.db.models import Store, StoreDebtPayment, StoreElectricityLog, User
from bot.db.session import async_session_maker
from bot.filters import AdminFilter
from bot.db.global_tok_price import get_electricity_price_per_kw, set_electricity_price_per_kw
from bot.keyboards import (
    ADMIN_BTN_LIST,
    ADMIN_BTN_NEW,
    ADMIN_BTN_REPORT,
    ADMIN_BTN_TOK_PRICE,
    BTN_CANCEL,
    admin_main_menu,
    cancel_keyboard,
    store_date_keyboard,
)
from bot.states import AddStoreStates, AdminTokPriceStates
from bot.utils.store_invite import new_invite_start_arg, telegram_me_link
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


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_TOK_PRICE)
async def admin_tok_price_begin(message: Message, state: FSMContext) -> None:
    cur = await get_electricity_price_per_kw()
    if cur is not None:
        head = f"Hozirgi <b>umumiy</b> tok narxi: <b>{fmt_money(cur)}</b> so'm / kW.\n\n"
    else:
        head = "Hozircha umumiy tok narxi kiritilmagan.\n\n"
    await state.set_state(AdminTokPriceStates.amount)
    await message.answer(
        head
        + "Barcha magazinlar uchun bitta kW narxidagi summani yozing "
        "(so'm, butun son, masalan <code>1000</code>).\n"
        "<code>0</code> — tok pullik deb hisoblanmaydi.",
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_keyboard(),
    )


@router.message(AdminTokPriceStates.amount, F.text == BTN_CANCEL)
async def admin_tok_price_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(AdminTokPriceStates.amount, F.text)
async def admin_tok_price_commit(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text or "")
    if amount is None:
        await message.answer("Faqat butun son (masalan: <code>1000</code> yoki <code>0</code>).")
        return
    await set_electricity_price_per_kw(amount)
    await state.clear()
    await message.answer(
        f"✅ Umumiy tok narxi yangilandi: <b>{fmt_money(amount)}</b> so'm / kW. "
        "Bu narx barcha magazinlar uchun qo'llaniladi.",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_menu(),
    )


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

    m = int(monthly_amount)
    invite_arg = new_invite_start_arg()
    async with async_session_maker() as session:
        st = Store(
            name=name,
            owner_phone=owner_phone,
            address=address,
            store_date=store_date,
            monthly_amount=m,
            electricity_kw=kw,
            debt_balance=m,
            rent_cycles_accrued=1,
            owner_invite_token=invite_arg,
            created_by_telegram_id=message.from_user.id,
        )
        session.add(st)
        await session.commit()

    me = await message.bot.get_me()
    uname = (me.username or "").strip()
    link_line = ""
    if uname:
        link = telegram_me_link(uname, invite_arg)
        link_line = (
            f"\n\n🔗 <b>Magazin egasiga havola</b> (nusxa olib yuboring):\n"
            f'<a href="{html.escape(link)}">{html.escape(link)}</a>\n\n'
            "Egachi havolani bosganda bot ochiladi va kontakt ulashadi — "
            "yuborilgan raqam admin kiritgan telefon bilan mos bo'lishi kerak."
        )
    else:
        link_line = (
            f"\n\n🔗 Botda @username yo'q — havola yaratilmadi. "
            f"Egachi qo'lda yuborsin: <code>/start {html.escape(invite_arg)}</code>"
        )

    await state.clear()
    await message.answer(
        "✅ Magazin yaratildi.\n\n"
        f"📛 {name}\n"
        f"📞 {owner_phone}\n"
        f"📍 {address}\n"
        f"📅 {fmt_store_date(store_date)}\n"
        f"💰 Oylik: {fmt_money(int(monthly_amount))} so'm\n"
        f"⚡ Elektr: {kw} kW"
        + link_line,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_menu(),
    )


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_REPORT)
async def report(message: Message) -> None:
    from bot.utils.excel_stores import admin_report_xlsx_bytes
    from bot.utils.rent_accrual import refresh_all_store_rent_state

    await refresh_all_store_rent_state()
    async with async_session_maker() as session:
        stores = await session.scalar(select(func.count()).select_from(Store))
        users = await session.scalar(select(func.count()).select_from(User))
        with_phone = await session.scalar(
            select(func.count()).select_from(User).where(User.phone_number.isnot(None))
        )
        store_rows = list(
            (await session.execute(select(Store).order_by(Store.id.desc()))).scalars().all()
        )
        pay_result = await session.execute(
            select(
                StoreDebtPayment.id,
                StoreDebtPayment.store_id,
                Store.name,
                StoreDebtPayment.amount,
                StoreDebtPayment.debt_after,
                StoreDebtPayment.created_at,
                StoreDebtPayment.created_by_telegram_id,
            )
            .join(Store, Store.id == StoreDebtPayment.store_id)
            .order_by(desc(StoreDebtPayment.id))
            .limit(8000)
        )
        pay_rows = [tuple(row) for row in pay_result.all()]

        elec_result = await session.execute(
            select(
                StoreElectricityLog.id,
                StoreElectricityLog.store_id,
                Store.name,
                StoreElectricityLog.period_from,
                StoreElectricityLog.period_to,
                StoreElectricityLog.reading_before,
                StoreElectricityLog.reading_after,
                StoreElectricityLog.delta_kw,
                StoreElectricityLog.created_at,
            )
            .join(Store, Store.id == StoreElectricityLog.store_id)
            .order_by(desc(StoreElectricityLog.id))
            .limit(8000)
        )
        elec_rows = [tuple(row) for row in elec_result.all()]

    text = (
        "📈 Hisobot\n\n"
        f"Magazinlar: {stores or 0}\n"
        f"Foydalanuvchilar (jami): {users or 0}\n"
        f"Kontakt ulaganlar: {with_phone or 0}\n\n"
        "Excel: <b>Magazinlar</b> (tok qarz kW), "
        "<b>Qarzdan ayirishlar</b>, <b>Tok tarixi</b>."
    )
    await message.answer(text, parse_mode=ParseMode.HTML)
    global_tok = await get_electricity_price_per_kw()
    xlsx = admin_report_xlsx_bytes(store_rows, pay_rows, elec_rows, global_tok)
    await message.answer_document(
        BufferedInputFile(xlsx, filename="magazinlar_hisoboti.xlsx"),
        caption="📊 Magazinlar + qarz + tok tarixi (kW)",
    )
