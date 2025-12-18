"""add processed_updates and telegram_users"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20251218_add_telegram_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_updates",
        sa.Column("update_id", sa.BigInteger(), primary_key=True),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "telegram_users",
        sa.Column("chat_id", sa.BigInteger(), primary_key=True),
        sa.Column("thread_id", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("telegram_users")
    op.drop_table("processed_updates")
