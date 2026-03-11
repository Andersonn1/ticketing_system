"""add manual triage fields

Revision ID: c8a7e7d8f1b2
Revises: b4d94f2c7a1d
Create Date: 2026-03-11 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "c8a7e7d8f1b2"
down_revision = "b4d94f2c7a1d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("ticket", sa.Column("manual_summary", sa.Text(), nullable=True))
    op.add_column("ticket", sa.Column("manual_response", sa.Text(), nullable=True))
    op.add_column(
        "ticket",
        sa.Column(
            "manual_next_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("ticket", "manual_next_steps")
    op.drop_column("ticket", "manual_response")
    op.drop_column("ticket", "manual_summary")
