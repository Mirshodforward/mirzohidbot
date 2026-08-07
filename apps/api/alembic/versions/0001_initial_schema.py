"""Boshlang'ich sxema — hozirgi ishlab turgan bazaga aynan mos.

MUHIM: mavjud (production) bazada jadvallar allaqachon bor. U yerda migratsiyani
**ishga tushirmang**, faqat belgilang:

    alembic stamp 0001

Shundan keyin `alembic upgrade head` faqat yangi migratsiyalarni qo'llaydi.
Yangi/bo'sh bazada esa oddiy `alembic upgrade head` hammasini yaratadi.

Revision ID: 0001
Revises:
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("electricity_price_per_kw", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_phone", sa.String(length=16), nullable=True),
        sa.Column("owner_invite_token", sa.String(length=64), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("store_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monthly_amount", sa.BigInteger(), nullable=True),
        sa.Column("electricity_kw", sa.Integer(), nullable=True),
        sa.Column("debt_tok", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("debt_balance", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("rent_cycles_accrued", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rent_reminder_sent_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_invite_token"),
    )

    op.create_table(
        "store_chat_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("from_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("author_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_store_chat_messages_store_id", "store_chat_messages", ["store_id"]
    )

    op.create_table(
        "store_debt_payments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("debt_after", sa.BigInteger(), nullable=False),
        sa.Column("created_by_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_store_debt_payments_store_id", "store_debt_payments", ["store_id"]
    )

    op.create_table(
        "store_electricity_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("period_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_to", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reading_before", sa.Integer(), nullable=False),
        sa.Column("reading_after", sa.Integer(), nullable=False),
        sa.Column("delta_kw", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_store_electricity_logs_store_id", "store_electricity_logs", ["store_id"]
    )


def downgrade() -> None:
    op.drop_table("store_electricity_logs")
    op.drop_table("store_debt_payments")
    op.drop_table("store_chat_messages")
    op.drop_table("stores")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
    op.drop_table("app_settings")
