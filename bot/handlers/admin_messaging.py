"""Admin xabarlar: barchaga / bitta magazinga; suhbat tarixi (Admin / Magazin)."""

from __future__ import annotations

import asyncio
import html

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import func, or_, select

from bot.db.models import Store, StoreChatMessage, User
from bot.db.session import async_session_maker
from bot.filters import AdminFilter
from bot.keyboards import (
    ADMIN_BTN_LIST,
    ADMIN_BTN_MSG,
    ADMIN_BTN_NEW,
    ADMIN_BTN_REPORT,
    BTN_CANCEL,
    MSG_BROADCAST_ALL,
    MSG_MENU_BACK,
    MSG_TO_ONE_STORE,
    admin_main_menu,
    cancel_keyboard,
    msg_mode_keyboard,
)
from bot.states import AdminToStoreStates, BroadcastStates
from bot.utils.store_chat_format import format_store_thread_html
from bot.utils.store_flow import normalize_phone

router = Router(name="admin_messaging")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

PER_PAGE = 10

_MENU_TEXTS = frozenset(
    {
        ADMIN_BTN_LIST,
        ADMIN_BTN_NEW,
        ADMIN_BTN_REPORT,
        ADMIN_BTN_MSG,
        MSG_BROADCAST_ALL,
        MSG_TO_ONE_STORE,
        MSG_MENU_BACK,
    }
)


def _btn_short(name: str, max_len: int = 28) -> str:
    n = (name or "").strip()
    if len(n) <= max_len:
        return n or "—"
    return n[: max_len - 1] + "…"


def _msg_pick_kb(stores: list[Store], page: int) -> InlineKeyboardMarkup:
    total = len(stores)
    start = page * PER_PAGE
    chunk = stores[start : start + PER_PAGE]
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for s in chunk:
        row.append(
            InlineKeyboardButton(
                text=_btn_short(s.name),
                callback_data=f"sms:{s.id}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"msp:{page - 1}"))
    if start + PER_PAGE < total:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"msp:{page + 1}"))
    if nav:
        rows.append(nav)
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _load_stores() -> list[Store]:
    from bot.handlers.admin_stores import _load_stores_ordered

    return await _load_stores_ordered()


async def _thread_messages(session, store_id: int) -> list[StoreChatMessage]:
    r = await session.execute(
        select(StoreChatMessage)
        .where(StoreChatMessage.store_id == store_id)
        .order_by(StoreChatMessage.id.asc())
        .limit(200)
    )
    return list(r.scalars().all())


async def _owner_telegram_ids(session, owner_phone: str | None) -> list[int]:
    raw = (owner_phone or "").strip()
    if not raw:
        return []
    key = normalize_phone(raw) or raw
    r = await session.execute(
        select(User.telegram_id).where(
            or_(User.phone_number == key, User.phone_number == raw)
        )
    )
    return [row[0] for row in r.all()]


@router.message(StateFilter(default_state), F.text == ADMIN_BTN_MSG)
async def messages_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    async with async_session_maker() as session:
        with_phone = await session.scalar(
            select(func.count()).select_from(User).where(User.phone_number.isnot(None))
        )
    await message.answer(
        f"✉️ <b>Xabarlar</b>\n\n"
        f"Kontakt ulagan foydalanuvchilar: {with_phone or 0}\n\n"
        "Rejimni tanlang:\n"
        "• <b>Barchaga</b> — barcha ulangan foydalanuvchilarga bir xil matn.\n"
        "• <b>Magazinga</b> — bitta magazin egasiga; suhbat "
        "(<b>Admin</b> / <b>Magazin</b>) saqlanadi.",
        parse_mode=ParseMode.HTML,
        reply_markup=msg_mode_keyboard(),
    )


@router.message(StateFilter(default_state), F.text == MSG_MENU_BACK)
async def msg_menu_back_from_default(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu.", reply_markup=admin_main_menu())


@router.message(StateFilter(default_state), F.text == MSG_BROADCAST_ALL)
async def start_broadcast_all(message: Message, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.text)
    await message.answer(
        "📢 <b>Barchaga yuborish</b>\n\n"
        "Yuboriladigan matnni yozing (bekor uchun tugmani bosing):",
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_keyboard(),
    )


@router.message(StateFilter(default_state), F.text == MSG_TO_ONE_STORE)
async def start_store_pick(message: Message, state: FSMContext) -> None:
    stores = await _load_stores()
    if not stores:
        await message.answer("Hozircha magazinlar yo'q.", reply_markup=msg_mode_keyboard())
        return
    await message.answer(
        "🏪 <b>Magazinga yuborish</b>\n\n"
        "Magazinni tanlang:",
        parse_mode=ParseMode.HTML,
        reply_markup=_msg_pick_kb(stores, 0),
    )


@router.callback_query(F.data.startswith("msp:"))
async def cb_msg_store_page(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    raw = (callback.data or "").strip()
    try:
        page = int(raw.split(":", 1)[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    if page < 0 or not callback.message:
        await callback.answer()
        return
    stores = await _load_stores()
    if not stores:
        await callback.message.edit_text("Hozircha magazinlar yo'q.", reply_markup=None)
        await callback.answer()
        return
    max_page = (len(stores) - 1) // PER_PAGE
    page = min(page, max_page)
    await callback.message.edit_reply_markup(reply_markup=_msg_pick_kb(stores, page))
    await callback.answer()


@router.callback_query(F.data.startswith("sms:"))
async def cb_msg_store_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    raw = (callback.data or "").strip()
    parts = raw.split(":")
    if len(parts) != 2 or not parts[1].isdigit() or not callback.from_user:
        await callback.answer()
        return
    sid = int(parts[1])
    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await callback.answer("Magazin topilmadi.", show_alert=True)
            return
        msgs = await _thread_messages(session, sid)
    await state.set_state(AdminToStoreStates.waiting_text)
    await state.update_data(target_store_id=sid)
    header = (
        f"🏬 <b>{html.escape((s.name or '').strip() or '—')}</b> "
        f"(<code>#{sid}</code>)\n\n<b>Suhbat tarixi:</b>"
    )
    body = format_store_thread_html(msgs, header=header, max_len=3600)
    await callback.answer()
    if callback.message:
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
    uid = callback.from_user.id
    await callback.bot.send_message(
        uid,
        body + "\n\n<i>Quyidagi xabarda yangi matnni yuboring (bekor tugmasi bilan chiqish).</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=cancel_keyboard(),
    )


@router.message(BroadcastStates.text, F.text == BTN_CANCEL)
async def broadcast_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=msg_mode_keyboard())


@router.message(BroadcastStates.text, F.text == MSG_MENU_BACK)
async def broadcast_back_main(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu.", reply_markup=admin_main_menu())


@router.message(BroadcastStates.text, F.text)
async def broadcast_send(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Matn bo'sh bo'lmasin.")
        return

    if text in _MENU_TEXTS:
        await state.clear()
        if text == ADMIN_BTN_LIST:
            from bot.handlers.admin_stores import admin_list_stores

            await admin_list_stores(message)
            return
        if text == ADMIN_BTN_NEW:
            from bot.handlers.admin import add_store_begin

            await add_store_begin(message, state)
            return
        if text == ADMIN_BTN_REPORT:
            from bot.handlers.admin import report

            await report(message)
            return
        if text == ADMIN_BTN_MSG:
            await messages_menu(message, state)
            return
        if text == MSG_BROADCAST_ALL:
            await start_broadcast_all(message, state)
            return
        if text == MSG_TO_ONE_STORE:
            await start_store_pick(message, state)
            return
        await message.answer("Asosiy menyu.", reply_markup=admin_main_menu())
        return

    async with async_session_maker() as session:
        result = await session.execute(
            select(User.telegram_id).where(User.phone_number.isnot(None))
        )
        ids = [r[0] for r in result.all()]

    await state.clear()
    await message.answer(
        f"Yuborilmoqda: {len(ids)} ta foydalanuvchi...",
        reply_markup=msg_mode_keyboard(),
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
        reply_markup=msg_mode_keyboard(),
    )


@router.message(AdminToStoreStates.waiting_text, F.text == BTN_CANCEL)
async def admin_to_store_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=msg_mode_keyboard())


@router.message(AdminToStoreStates.waiting_text, F.text == MSG_MENU_BACK)
async def admin_to_store_cancel_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu.", reply_markup=admin_main_menu())


@router.message(AdminToStoreStates.waiting_text, F.text)
async def admin_to_store_commit(message: Message, state: FSMContext) -> None:
    if not message.from_user:
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("Matn bo'sh bo'lmasin.")
        return
    if text in _MENU_TEXTS:
        await state.clear()
        if text == ADMIN_BTN_MSG:
            await messages_menu(message, state)
        elif text == MSG_TO_ONE_STORE:
            await start_store_pick(message, state)
        elif text == MSG_BROADCAST_ALL:
            await start_broadcast_all(message, state)
        elif text == ADMIN_BTN_LIST:
            from bot.handlers.admin_stores import admin_list_stores

            await admin_list_stores(message)
        elif text == ADMIN_BTN_NEW:
            from bot.handlers.admin import add_store_begin

            await add_store_begin(message, state)
        elif text == ADMIN_BTN_REPORT:
            from bot.handlers.admin import report

            await report(message)
        else:
            await message.answer("Asosiy menyu.", reply_markup=admin_main_menu())
        return

    data = await state.get_data()
    sid = data.get("target_store_id")
    if not isinstance(sid, int):
        await state.clear()
        await message.answer("Sessiya buzildi.", reply_markup=msg_mode_keyboard())
        return

    reply_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Javob berish",
                    callback_data=f"stjr:{sid}",
                )
            ],
        ]
    )

    async with async_session_maker() as session:
        s = await session.get(Store, sid)
        if not s:
            await state.clear()
            await message.answer("Magazin topilmadi.", reply_markup=msg_mode_keyboard())
            return
        session.add(
            StoreChatMessage(
                store_id=sid,
                from_admin=True,
                author_telegram_id=message.from_user.id,
                body=text,
            )
        )
        await session.commit()
        msgs = await _thread_messages(session, sid)
        uids = await _owner_telegram_ids(session, s.owner_phone)

    header = (
        f"🏬 <b>{html.escape((s.name or '').strip() or '—')}</b> "
        f"(<code>#{sid}</code>)\n\n<b>Suhbat:</b>"
    )
    body = format_store_thread_html(msgs, header=header, max_len=3800)

    ok, fail = 0, 0
    for uid in uids:
        try:
            await message.bot.send_message(
                uid,
                body,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_kb,
            )
            ok += 1
        except Exception:
            fail += 1

    await state.clear()
    if uids:
        await message.answer(
            f"Yuborildi: {ok} ta foydalanuvchi." + (f" Yuborilmadi: {fail}" if fail else ""),
            reply_markup=msg_mode_keyboard(),
        )
    else:
        await message.answer(
            "Xabar bazaga saqlandi, lekin egasi uchun Telegram akkaunt "
            "(kontakt) topilmadi — egasi botda telefon ulamagan bo'lishi mumkin.",
            reply_markup=msg_mode_keyboard(),
        )
