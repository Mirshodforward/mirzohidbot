"""Telefonni ixtiyoriy qilish: egani Telegram ID orqali ham bog'lash.

Magazin egasi endi telefon raqami mos kelmasa/berilmagan bo'lsa ham, taklif
havolasi (=magazin ID) orqali to'g'ridan-to'g'ri Telegram ID bilan bog'lanadi.

Revision ID: 0003
Revises: 0002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "stores", sa.Column("owner_telegram_id", sa.BigInteger(), nullable=True)
    )
    op.create_index(
        "ix_stores_owner_telegram_id", "stores", ["owner_telegram_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_stores_owner_telegram_id", table_name="stores")
    op.drop_column("stores", "owner_telegram_id")
