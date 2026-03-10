"""Initial service ticket table."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_service_tickets"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the service_tickets table."""
    op.create_table(
        "service_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "urgency",
            sa.Enum(
                "High",
                "Medium",
                "Low",
                name="service_urgency",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "Hardware",
                "Software",
                "Network",
                "Security",
                "Other",
                name="service_category",
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "first_occurrence", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "received_error_message",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("error_message_details", sa.Text(), nullable=True),
        sa.Column("assignee", sa.String(length=255), nullable=False),
    )


def downgrade() -> None:
    """Drop the service_tickets table."""
    op.drop_table("service_tickets")
