from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


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
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    store_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    monthly_amount: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    electricity_kw: Mapped[int | None] = mapped_column(Integer(), nullable=True)
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
