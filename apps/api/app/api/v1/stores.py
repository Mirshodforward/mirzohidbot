"""Magazin egasi (va admin) uchun o'qish endpointlari + chat."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import desc, select

from app.core.deps import CurrentUserDep, OwnedStoreDep, SessionDep, user_store_ids
from app.db.global_tok_price import get_electricity_price_per_kw
from app.db.models import Store, StoreChatMessage, StoreDebtPayment, StoreElectricityLog
from app.domain.store_flow import next_rent_payment_dt
from app.schemas.store import (
    ElectricityLogOut,
    MessageIn,
    MessageOut,
    PaymentOut,
    StoreOut,
)
from app.services.stores import refresh_all_stores

router = APIRouter(prefix="/stores", tags=["stores"])


async def _to_out(store: Store, price_per_kw: int | None) -> StoreOut:
    out = StoreOut.model_validate(store)
    out.next_payment_at = next_rent_payment_dt(store.store_date)
    out.electricity_price_per_kw = price_per_kw
    if price_per_kw is not None:
        out.electricity_due = int(store.debt_tok or 0) * price_per_kw
    return out


@router.get("", response_model=list[StoreOut])
async def list_stores(user: CurrentUserDep, session: SessionDep) -> list[StoreOut]:
    """Admin — barcha magazinlar; egasi — faqat o'ziniki."""
    stores = await refresh_all_stores(session)
    if not user.is_admin:
        allowed = set(await user_store_ids(user, session))
        stores = [s for s in stores if s.id in allowed]
    await session.commit()

    price = await get_electricity_price_per_kw()
    return [await _to_out(s, price) for s in stores]


@router.get("/{store_id}", response_model=StoreOut)
async def get_store(store: OwnedStoreDep, session: SessionDep) -> StoreOut:
    price = await get_electricity_price_per_kw()
    return await _to_out(store, price)


@router.get("/{store_id}/payments", response_model=list[PaymentOut])
async def store_payments(store: OwnedStoreDep, session: SessionDep) -> list[PaymentOut]:
    rows = await session.execute(
        select(StoreDebtPayment)
        .where(StoreDebtPayment.store_id == store.id)
        .order_by(desc(StoreDebtPayment.id))
        .limit(500)
    )
    return [PaymentOut.model_validate(r) for r in rows.scalars().all()]


@router.get("/{store_id}/electricity", response_model=list[ElectricityLogOut])
async def store_electricity(
    store: OwnedStoreDep, session: SessionDep
) -> list[ElectricityLogOut]:
    rows = await session.execute(
        select(StoreElectricityLog)
        .where(StoreElectricityLog.store_id == store.id)
        .order_by(desc(StoreElectricityLog.id))
        .limit(500)
    )
    return [ElectricityLogOut.model_validate(r) for r in rows.scalars().all()]


@router.get("/{store_id}/messages", response_model=list[MessageOut])
async def store_messages(store: OwnedStoreDep, session: SessionDep) -> list[MessageOut]:
    rows = await session.execute(
        select(StoreChatMessage)
        .where(StoreChatMessage.store_id == store.id)
        .order_by(StoreChatMessage.id.asc())
        .limit(500)
    )
    return [MessageOut.model_validate(r) for r in rows.scalars().all()]


@router.post(
    "/{store_id}/messages",
    response_model=MessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    payload: MessageIn,
    store: OwnedStoreDep,
    user: CurrentUserDep,
    session: SessionDep,
) -> MessageOut:
    """Suhbatga yozish. Boshqa tomonga Telegram orqali bildirishnoma ketadi."""
    if user.telegram_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Xabar yozish uchun avval Telegram akkauntingizni ulang.",
        )

    msg = StoreChatMessage(
        store_id=store.id,
        from_admin=user.is_admin,
        author_telegram_id=user.telegram_id,
        body=payload.body.strip(),
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)

    await _notify_counterpart(store, msg, user.is_admin)
    return MessageOut.model_validate(msg)


async def _notify_counterpart(
    store: Store, msg: StoreChatMessage, from_admin: bool
) -> None:
    """Yangi xabar haqida Telegramda xabar berish (xato bo'lsa ham 500 bermaymiz)."""
    import html
    import logging

    from app.bot.dispatcher import get_bot
    from app.config import get_settings
    from app.services.tg_send import send_message_safe

    log = logging.getLogger(__name__)
    name = html.escape((store.name or "—").strip())
    body = html.escape(msg.body)

    try:
        bot = get_bot()
        if from_admin:
            from app.db.session import async_session_maker
            from app.services.reminders import _owner_telegram_ids

            async with async_session_maker() as s:
                uids = await _owner_telegram_ids(s, store.owner_phone or "")
            text = f"🏬 <b>{name}</b>\n\n👤 <b>Admin:</b>\n{body}"
        else:
            uids = list(get_settings().admin_id_set)
            text = (
                f"📬 <b>Magazin javobi</b> — {name} (<code>#{store.id}</code>)\n\n{body}"
            )
        for uid in uids:
            await send_message_safe(bot, uid, text)
    except Exception:
        log.exception("Chat bildirishnomasi yuborilmadi: store=%s", store.id)
