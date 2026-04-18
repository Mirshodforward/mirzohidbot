from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class AppSettings(Base):
    """Bot bo'yicha umumiy sozlamalar (bitta qator, id=1)."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    # Barcha magazinlar uchun: 1 kW uchun so'm (admin belgilaydi)
    electricity_price_per_kw: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger(), unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_phone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    # Magazin egasiga yuboriladigan /start havolasi (inv_...), bir marta ulangach tozalanadi
    owner_invite_token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_amount: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    electricity_kw: Mapped[int | None] = mapped_column(Integer(), nullable=True)
    # Oxirgi hisoblagich yangilanishidagi iste'mol: yangi_o'qim - eski_o'qim (kW)
    debt_tok: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    # Oylik qarz (to'lanmagan + keyingi davrlar avto-qo'shilishi)
    debt_balance: Mapped[int] = mapped_column(BigInteger(), nullable=False, default=0)
    # Nechta 30 kunlik oylik davri allaqachon qarzga qo'shilgan (1 = birinchi oy yuklamasi)
    rent_cycles_accrued: Mapped[int] = mapped_column(Integer(), nullable=False, default=0)
    # Oxirgi eslatma yuborilgan kun (Toshkent sanasi) — kuniga 1 marta cheklov uchun vaqt belgisi
    rent_reminder_sent_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by_telegram_id: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StoreChatMessage(Base):
    """Admin ↔ magazin egasi suhbati (magazin bo'yicha)."""

    __tablename__ = "store_chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"),
        index=True,
    )
    from_admin: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    author_telegram_id: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StoreDebtPayment(Base):
    """Admin magazin qarzidan ayirgan to'lovlar (hisobot uchun)."""

    __tablename__ = "store_debt_payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    debt_after: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    created_by_telegram_id: Mapped[int] = mapped_column(BigInteger(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class StoreElectricityLog(Base):
    """Hisoblagich o'qimi o'zgarishi: davr va iste'mol (kW)."""

    __tablename__ = "store_electricity_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="CASCADE"),
        index=True,
    )
    period_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_to: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reading_before: Mapped[int] = mapped_column(Integer(), nullable=False)
    reading_after: Mapped[int] = mapped_column(Integer(), nullable=False)
    delta_kw: Mapped[int] = mapped_column(Integer(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
