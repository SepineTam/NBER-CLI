"""add read status table

Revision ID: 20260708_0001
Revises:
Create Date: 2026-07-08 00:00:00.000000
"""

from __future__ import annotations

from alembic import op

revision = "20260708_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS read_status (
            paper_id VARCHAR NOT NULL,
            is_read BOOLEAN NOT NULL,
            updated_at VARCHAR NOT NULL,
            PRIMARY KEY (paper_id)
        )
        """
    )
    op.execute("PRAGMA user_version = 3")


def downgrade() -> None:
    op.drop_table("read_status")
    op.execute("PRAGMA user_version = 2")
