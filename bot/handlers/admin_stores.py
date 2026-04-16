"""Admin: magazin ro'yxati (Excel + inline), tahrirlash, tok tarixi."""

import html
from datetime import datetime

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import desc, select

from bot.db.models import Store, StoreElectricityLog
from bot.db.session import async_session_maker
from bot.filters import AdminFilter
from bot.keyboards import (
    ADMIN_BTN_LIST,
    BTN_CANCEL,
    admin_main_menu,
    cancel_keyboard,
)
from bot.states import EditStoreStates
from bot.utils.excel_stores import stores_to_xlsx_bytes
from bot.utils.store_flow import TZ_TASHKENT, fmt_datetime, parse_amount, parse_kw
from bot.utils.store_format import store_card_html

router = Router(name="admin_stores")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

PER_PAGE = 10
SUBACTIONS = frozenset({"nm", "mo", "kw", "lg"})


def _btn_label(name: str, max_len: int = 26) -> str:
    n = (name or "").strip()
    if len(n) <= max_len:
        return n or "—"
    return n[: max_len - 1] + "…"


def _list_kb(stores: list[Store], page: int) -> InlineKeyboardMarkup:
    total = len(stores)
    start = page * PER_PAGE
    chunk = stores[start : start + PER_PAGE]
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for s in chunk:
        row.append(
            InlineKeyboardButton(
                text=_btn_label(s.name),
                callback_data=f"as:{s.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"lp:{page - 1}"))
    if start + PER_PAGE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"lp:{page + 1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _store_detail_kb(sid: int, list_mid: int | None) -> InlineKeyboardMarkup:
    if list_mid is not None:
        m = str(list_mid)
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✏️ Nomi", callback_data=f"as:{sid}:nm:{m}"),
                    InlineKeyboardButton(text="💰 Oylik", callback_data=f"as:{sid}:mo:{m}"),
                ],
                [
                    InlineKeyboardButton(text="⚡ Tok", callback_data=f"as:{sid}:kw:{m}"),
                    InlineKeyboardButton(text="📜 Tarix", callback_data=f"as:{sid}:lg:{m}"),
                ],
                [InlineKeyboardButton(text="⬅️ Ro'yxat", callback_data=f"lb:{m}")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Nomi", callback_data=f"as:{sid}:nm"),
                InlineKeyboardButton(text="💰 Oylik", callback_data=f"as:{sid}:mo"),
            ],
            [
                InlineKeyboardButton(text="⚡ Tok", callback_data=f"as:{sid}:kw"),
                InlineKeyboardButton(text="📜 Tarix", callback_data=f"as:{sid}:lg"),
            ],
            [InlineKeyboardButton(text="⬅️ Ro'yxat", callback_data="lp:0")],
        ]
    )


def _log_back_kb(sid: int, list_mid: int | None) -> InlineKeyboardMarkup:
    if list_mid is not None:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Magazinga", callback_data=f"b:{sid}:{list_mid}")],
            ]
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Magazinga", callback_data=f"as:{sid}")],
        ]
    )


def _admin_store_text(s: Store) -> str:
    return (
        store_card_html(s, show_payment=True)
        + "\n\n<i>Telefon raqam tahrirda o'zgartirilmaydi.</i>"
    )


async def _load_stores_ordered() -> list[Store]:
    async with async_session_maker() as session:
        r = await session.execute(select(Store).order_by(Store.id.desc()))
        return list(r.scalars().all())


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_LIST)
async def admin_list_stores(message: Message) -> None:
    stores = await _load_stores_ordered()
    if not stores:
        await message.answer("Hozircha magazinlar yo'q.")
        return

    xlsx = stores_to_xlsx_bytes(stores)
    await message.answer_document(
        BufferedInputFile(xlsx, filename="magazinlar.xlsx"),
        caption=(
            "📊 <b>Magazinlar</b> — Excel fayl yuqorida.\n"
            "Pastdan magazinni tanlang (tahrirlash):"
        ),
        parse_mode=ParseMode.HTML,
        reply_markup=_list_kb(stores, 0),
    )


@router.callback_query(F.data.startswith("lb:"))
async def cb_list_back(callback: CallbackQuery, state: FSMContext) -> None:
    """Batafsil xabardan ro'yxat (Excel + inline) xabariga qaytish."""
    await state.clear()
    raw = (callback.data or "").strip()
    parts = raw.split(":")
    if len(parts) != 2 or not parts[1].isdigit():
        await callback.answer()
        return
    list_mid = int(parts[1])
    stores = await _load_stores_ordered()
    if not stores:
        await callback.answer("Ro'yxat bo'sh.", show_alert=True)
        return
    chat_id = callback.message.chat.id if callback.message else None
    if not chat_id or not callback.bot:
        await callback.answer()
        return
    try:
        await callback.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=list_mid,
            reply_markup=_list_kb(stores, 0),
        )
    except Exception:
        await callback.answer("Ro'yxat xabari yangilanmadi.", show_alert=True)
        return
    if callback.message:
        try:
            await callback.message.delete()
        except Exception:
            pass
    await callback.answer()


@router.callback_query(F.data.startswith("b:"))
async def cb_log_back_to_store(callback: CallbackQuery, state: FSMContext) -> None:
    """Tok tarixidan magazin kartochkasiga."""
    await state.clear()
    raw = (callback.data or "").strip()
    parts = raw.split(":")
    if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
        await callback.answer()
        return
    sid = int(parts[1])
    list_mid = int(parts[2])
    await callback.answer()
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
    if not s or not callback.message:
        return
    await callback.message.edit_text(
        _admin_store_text(s),
        parse_mode=ParseMode.HTML,
        reply_markup=_store_detail_kb(sid, list_mid),
    )


@router.callback_query(F.data.startswith("lp:"))
async def cb_list_page(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    raw = callback.data or ""
    try:
        page = int(raw.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    if page < 0:
        await callback.answer()
        return

    stores = await _load_stores_ordered()
    if not stores:
        if callback.message and callback.message.document:
            await callback.message.edit_caption(
                caption="Hozircha magazinlar yo'q.",
                reply_markup=None,
            )
        elif callback.message:
            await callback.message.edit_text("Hozircha magazinlar yo'q.", reply_markup=None)
        await callback.answer()
        return

    max_page = (len(stores) - 1) // PER_PAGE
    page = min(page, max_page)

    if callback.message:
        if callback.message.document:
            await callback.message.edit_reply_markup(reply_markup=_list_kb(stores, page))
        else:
            await callback.message.edit_text(
                "Tahrirlash uchun magazinni tanlang:",
                reply_markup=_list_kb(stores, page),
            )
    await callback.answer()


@router.callback_query(F.data.startswith("as:"))
async def cb_store_routes(callback: CallbackQuery, state: FSMContext) -> None:
    raw = (callback.data or "").strip()
    parts = raw.split(":")
    if len(parts) == 2 and parts[0] == "as" and parts[1].isdigit():
        await _store_open(callback, state, int(parts[1]))
        return
    if len(parts) >= 3 and parts[0] == "as" and parts[1].isdigit() and parts[2] in SUBACTIONS:
        list_mid: int | None = None
        if len(parts) > 3 and parts[3].isdigit():
            list_mid = int(parts[3])
        await _store_sub(callback, state, int(parts[1]), parts[2], list_mid)
        return
    await callback.answer("Noto'g'ri")


async def _store_open(callback: CallbackQuery, state: FSMContext, sid: int) -> None:
    await state.clear()
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
    if not s:
        if callback.message and callback.message.document:
            await callback.answer("Magazin topilmadi.", show_alert=True)
        elif callback.message:
            await callback.message.edit_text("Magazin topilmadi.")
            await callback.answer()
        else:
            await callback.answer()
        return

    if callback.message and callback.message.document:
        list_mid = callback.message.message_id
        await callback.message.answer(
            _admin_store_text(s),
            parse_mode=ParseMode.HTML,
            reply_markup=_store_detail_kb(sid, list_mid),
        )
        await callback.answer()
        return

    if callback.message:
        await callback.message.edit_text(
            _admin_store_text(s),
            parse_mode=ParseMode.HTML,
            reply_markup=_store_detail_kb(sid, None),
        )
    await callback.answer()


async def _store_sub(
    callback: CallbackQuery,
    state: FSMContext,
    sid: int,
    sub: str,
    list_mid: int | None = None,
) -> None:
    await callback.answer()
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
    if not s:
        if callback.message:
            await callback.message.edit_text("Magazin topilmadi.")
        return

    if sub == "lg":
        async with async_session_maker() as session:
            logs = (
                (
                    await session.execute(
                        select(StoreElectricityLog)
                        .where(StoreElectricityLog.store_id == sid)
                        .order_by(desc(StoreElectricityLog.id))
                        .limit(40)
                    )
                )
                .scalars()
                .all()
            )
        if not logs:
            body = "📜 <b>Tok tarixi</b>\n\nHozircha yozuvlar yo'q (yangi o'qim kiritilganda shu yerda ko'rinadi)."
        else:
            lines: list[str] = ["📜 <b>Tok iste'moli</b>\n"]
            for lg in logs:
                lines.append(
                    f"\n{fmt_datetime(lg.period_from)} → {fmt_datetime(lg.period_to)}\n"
                    f"{lg.reading_before} → {lg.reading_after} kW "
                    f"(<b>+{lg.delta_kw}</b> kW)\n"
                )
            body = "".join(lines)
        if callback.message:
            await callback.message.edit_text(
                body,
                parse_mode=ParseMode.HTML,
                reply_markup=_log_back_kb(sid, list_mid),
            )
        return

    await state.update_data(edit_store_id=sid)
    if sub == "nm":
        await state.set_state(EditStoreStates.name)
        prompt = "Yangi <b>magazin nomini</b> yozing:"
    elif sub == "mo":
        await state.set_state(EditStoreStates.monthly)
        prompt = "Yangi <b>oylik summani</b> yozing (so'm, faqat raqam):"
    else:  # kw
        await state.set_state(EditStoreStates.kw)
        cur = s.electricity_kw
        prompt = (
            "Yangi <b>hisoblagich ko'rsatkichini</b> yozing (kW, musbat butun son).\n"
            f"Hozirgi qiymat: <code>{cur if cur is not None else '—'}</code>\n\n"
            "Yangi qiymat avvalgisidan kichik bo'lmasin (hisoblagich orqaga qaytmaydi)."
        )

    uid = callback.from_user.id if callback.from_user else None
    if callback.message and uid:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.bot.send_message(
            uid,
            prompt,
            parse_mode=ParseMode.HTML,
            reply_markup=cancel_keyboard(),
        )


@router.message(EditStoreStates.name, F.text == BTN_CANCEL)
@router.message(EditStoreStates.monthly, F.text == BTN_CANCEL)
@router.message(EditStoreStates.kw, F.text == BTN_CANCEL)
async def edit_store_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_menu())


@router.message(EditStoreStates.name, F.text)
async def edit_store_name_commit(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.answer("Nom bo'sh bo'lmasin.")
        return
    data = await state.get_data()
    sid = data.get("edit_store_id")
    if not isinstance(sid, int):
        await state.clear()
        await message.answer("Sessiya buzildi.", reply_markup=admin_main_menu())
        return
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await state.clear()
            await message.answer("Magazin topilmadi.", reply_markup=admin_main_menu())
            return
        s.name = name
        await session.commit()
    await state.clear()
    await message.answer(
        f"✅ Nomi yangilandi: <b>{html.escape(name)}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_menu(),
    )


@router.message(EditStoreStates.monthly, F.text)
async def edit_store_monthly_commit(message: Message, state: FSMContext) -> None:
    amount = parse_amount(message.text or "")
    if amount is None:
        await message.answer("Faqat musbat butun son (masalan: <code>5000000</code>).")
        return
    data = await state.get_data()
    sid = data.get("edit_store_id")
    if not isinstance(sid, int):
        await state.clear()
        await message.answer("Sessiya buzildi.", reply_markup=admin_main_menu())
        return
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await state.clear()
            await message.answer("Magazin topilmadi.", reply_markup=admin_main_menu())
            return
        s.monthly_amount = amount
        await session.commit()
    await state.clear()
    await message.answer(
        "✅ Oylik summa yangilandi.",
        reply_markup=admin_main_menu(),
    )


@router.message(EditStoreStates.kw, F.text)
async def edit_store_kw_commit(message: Message, state: FSMContext) -> None:
    new_k = parse_kw(message.text or "")
    if new_k is None:
        await message.answer("Butun musbat son kiriting (masalan: <code>4197</code>).")
        return
    data = await state.get_data()
    sid = data.get("edit_store_id")
    if not isinstance(sid, int):
        await state.clear()
        await message.answer("Sessiya buzildi.", reply_markup=admin_main_menu())
        return

    now = datetime.now(TZ_TASHKENT)
    old_k: int | None = None
    period_from_out: datetime | None = None
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await state.clear()
            await message.answer("Magazin topilmadi.", reply_markup=admin_main_menu())
            return
        old_k = s.electricity_kw
        if old_k is not None:
            if new_k < old_k:
                await message.answer(
                    "Yangi ko'rsatkich oldingisidan kichik bo'lmasin "
                    "(hisoblagich orqaga qaytmaydi).",
                )
                return
            last_to = await session.scalar(
                select(StoreElectricityLog.period_to)
                .where(StoreElectricityLog.store_id == sid)
                .order_by(desc(StoreElectricityLog.id))
                .limit(1)
            )
            period_from = last_to or s.created_at
            if period_from is None:
                period_from = now
            elif period_from.tzinfo is None:
                period_from = period_from.replace(tzinfo=TZ_TASHKENT)
            else:
                period_from = period_from.astimezone(TZ_TASHKENT)
            period_from_out = period_from
            delta = new_k - old_k
            session.add(
                StoreElectricityLog(
                    store_id=sid,
                    period_from=period_from,
                    period_to=now,
                    reading_before=old_k,
                    reading_after=new_k,
                    delta_kw=delta,
                )
            )
        s.electricity_kw = new_k
        await session.commit()

    await state.clear()
    extra = ""
    if old_k is not None and period_from_out is not None:
        extra = (
            f"\n\n📈 Oxirgi davr: <code>{fmt_datetime(period_from_out)}</code> → "
            f"<code>{fmt_datetime(now)}</code>\n"
            f"Hisoblagich: {old_k} → {new_k} kW (<b>+{new_k - old_k}</b> kW)"
        )
    await message.answer(
        "✅ Hisoblagich yangilandi." + extra,
        parse_mode=ParseMode.HTML,
        reply_markup=admin_main_menu(),
    )
