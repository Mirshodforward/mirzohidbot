"""Admin endpointlari: magazin CRUD, to'lov, hisoblagich, tok narxi, broadcast."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select

from app.bot.formatting.store_invite import new_invite_start_arg, telegram_me_link
from app.core.deps import AdminDep, SessionDep
from app.db.global_tok_price import (
    get_electricity_price_per_kw,
    set_electricity_price_per_kw,
)
from app.db.models import Store, User
from app.domain.store_flow import next_rent_payment_dt, normalize_phone, tashkent_today_start
from app.schemas.store import (
    BroadcastIn,
    BroadcastOut,
    ElectricityPriceIn,
    ElectricityPriceOut,
    ElectricityReadingIn,
    PaymentIn,
    PaymentOut,
    StoreCreatedOut,
    StoreCreateIn,
    StoreOut,
    StoreUpdateIn,
)
from app.services.stores import (
    StoreError,
    apply_electricity_reading,
    apply_payment,
    get_store_locked,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _bad(exc: StoreError) -> HTTPException:
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


async def _out(store: Store) -> StoreOut:
    price = await get_electricity_price_per_kw()
    out = StoreOut.model_validate(store)
    out.next_payment_at = next_rent_payment_dt(store.store_date)
    out.electricity_price_per_kw = price
    if price is not None:
        out.electricity_due = int(store.debt_tok or 0) * price
    return out


@router.post("/stores", response_model=StoreCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_store(
    payload: StoreCreateIn, admin: AdminDep, session: SessionDep
) -> StoreCreatedOut:
    phone = normalize_phone(payload.owner_phone)
    if not phone:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Telefon formati noto'g'ri. Masalan: +998941339383",
        )

    invite = new_invite_start_arg()
    store = Store(
        name=payload.name.strip(),
        owner_phone=phone,
        address=payload.address.strip(),
        description=payload.description,
        store_date=payload.store_date or tashkent_today_start(),
        monthly_amount=payload.monthly_amount,
        electricity_kw=payload.electricity_kw,
        # Birinchi oy darrov qarzga yoziladi (bot oqimidagi bilan bir xil).
        debt_balance=payload.monthly_amount,
        rent_cycles_accrued=1,
        owner_invite_token=invite,
        created_by_telegram_id=admin.telegram_id or 0,
    )
    session.add(store)
    await session.commit()
    await session.refresh(store)

    link: str | None = None
    try:
        from app.bot.dispatcher import get_bot

        me = await get_bot().get_me()
        if me.username:
            link = telegram_me_link(me.username, invite)
    except Exception:  # bot mavjud bo'lmasa ham magazin yaratilgan bo'lsin
        link = None

    return StoreCreatedOut(store=await _out(store), invite_link=link, invite_token=invite)


@router.patch("/stores/{store_id}", response_model=StoreOut)
async def update_store(
    store_id: int, payload: StoreUpdateIn, admin: AdminDep, session: SessionDep
) -> StoreOut:
    try:
        store = await get_store_locked(session, store_id)
    except StoreError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        if value is not None:
            setattr(store, field, value.strip() if isinstance(value, str) else value)
    await session.commit()
    await session.refresh(store)
    return await _out(store)


# `response_model=None` majburiy: shu faylda `from __future__ import annotations`
# yoqilgan, shuning uchun `-> None` FastAPI ga `NoneType` klassi bo'lib ko'rinadi
# va u buni javob modeli deb hisoblaydi (204 esa tanaga ega bo'lmasligi kerak).
@router.delete(
    "/stores/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def delete_store(store_id: int, admin: AdminDep, session: SessionDep) -> None:
    store = await session.get(Store, store_id)
    if store is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Magazin topilmadi.")
    await session.delete(store)
    await session.commit()


@router.post(
    "/stores/{store_id}/payments",
    response_model=PaymentOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_payment(
    store_id: int, payload: PaymentIn, admin: AdminDep, session: SessionDep
) -> PaymentOut:
    """Qarzdan to'lovni ayiradi (bot dagi '➖ Ayirish' bilan bir xil mantiq)."""
    try:
        result = await apply_payment(
            session,
            store_id,
            payload.amount,
            created_by_telegram_id=admin.telegram_id or 0,
        )
    except StoreError as exc:
        await session.rollback()
        raise _bad(exc) from exc
    await session.commit()
    return PaymentOut.model_validate(result.payment)


@router.post("/stores/{store_id}/electricity", response_model=StoreOut)
async def add_electricity_reading(
    store_id: int, payload: ElectricityReadingIn, admin: AdminDep, session: SessionDep
) -> StoreOut:
    try:
        await apply_electricity_reading(session, store_id, payload.reading)
    except StoreError as exc:
        await session.rollback()
        raise _bad(exc) from exc
    await session.commit()

    store = await session.get(Store, store_id)
    return await _out(store)  # type: ignore[arg-type]


@router.get("/settings/electricity-price", response_model=ElectricityPriceOut)
async def read_electricity_price(admin: AdminDep) -> ElectricityPriceOut:
    return ElectricityPriceOut(price_per_kw=await get_electricity_price_per_kw())


@router.put("/settings/electricity-price", response_model=ElectricityPriceOut)
async def write_electricity_price(
    payload: ElectricityPriceIn, admin: AdminDep
) -> ElectricityPriceOut:
    await set_electricity_price_per_kw(payload.price_per_kw)
    return ElectricityPriceOut(price_per_kw=payload.price_per_kw)


@router.post("/broadcast", response_model=BroadcastOut)
async def broadcast_message(
    payload: BroadcastIn, admin: AdminDep, session: SessionDep
) -> BroadcastOut:
    """Kontakt ulagan barcha foydalanuvchilarga xabar (flood-control bilan)."""
    from app.bot.dispatcher import get_bot
    from app.services.tg_send import broadcast as tg_broadcast

    rows = await session.execute(
        select(User.telegram_id).where(User.phone_number.isnot(None))
    )
    ids = [r[0] for r in rows.all()]
    ok, blocked, failed = await tg_broadcast(get_bot(), ids, payload.text)
    return BroadcastOut(sent=ok, blocked=blocked, failed=failed)


@router.get("/stats")
async def stats(admin: AdminDep, session: SessionDep) -> dict:
    stores = await session.scalar(select(func.count()).select_from(Store)) or 0
    users = await session.scalar(select(func.count()).select_from(User)) or 0
    linked = (
        await session.scalar(
            select(func.count()).select_from(User).where(User.phone_number.isnot(None))
        )
        or 0
    )
    total_debt = await session.scalar(select(func.coalesce(func.sum(Store.debt_balance), 0)))
    return {
        "stores": stores,
        "users": users,
        "linked_users": linked,
        "total_debt": int(total_debt or 0),
        "generated_at": datetime.now().isoformat(),
    }
