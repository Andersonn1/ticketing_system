"""align ticket schema for async llm

Revision ID: b4d94f2c7a1d
Revises: 58d62f36c3d0
Create Date: 2026-03-11 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.db.types import Vector

revision = "b4d94f2c7a1d"
down_revision = "58d62f36c3d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("DROP TABLE IF EXISTS service_tickets CASCADE")
    op.execute("DROP TYPE IF EXISTS service_urgency")

    sa.Enum("STUDENT", "FACULTY", "ALUM", "VENDOR", "OTHER", name="user_role").create(op.get_bind(), checkfirst=True)
    sa.Enum("OPEN", "PENDING", "CLOSED", name="service_status").create(op.get_bind(), checkfirst=True)
    sa.Enum("HIGH", "MEDIUM", "LOW", name="service_priority").create(op.get_bind(), checkfirst=True)
    sa.Enum("HIGH", "MEDIUM", "LOW", name="ai_confidence").create(op.get_bind(), checkfirst=True)

    op.create_table(
        "ticket",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("requestor_name", sa.String(length=250), nullable=False),
        sa.Column("requestor_email", sa.String(length=275), nullable=False),
        sa.Column(
            "user_role",
            postgresql.ENUM(
                "STUDENT",
                "FACULTY",
                "ALUM",
                "VENDOR",
                "OTHER",
                name="user_role",
                create_type=False,
            ),
            server_default=sa.text("'OTHER'"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=125), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "OPEN",
                "PENDING",
                "CLOSED",
                name="service_status",
                create_type=False,
            ),
            server_default=sa.text("'OPEN'"),
            nullable=False,
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "HIGH",
                "MEDIUM",
                "LOW",
                name="service_priority",
                create_type=False,
            ),
            server_default=sa.text("'LOW'"),
            nullable=False,
        ),
        sa.Column(
            "category",
            postgresql.ENUM(
                "HARDWARE",
                "SOFTWARE",
                "NETWORK",
                "SECURITY",
                "OTHER",
                name="service_category",
                create_type=False,
            ),
            server_default=sa.text("'OTHER'"),
            nullable=False,
        ),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("ai_response", sa.Text(), nullable=True),
        sa.Column(
            "ai_next_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "ai_confidence",
            postgresql.ENUM(
                "HIGH",
                "MEDIUM",
                "LOW",
                name="ai_confidence",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "ai_trace",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("source_name", sa.String(length=250), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_name"),
    )

    op.create_table(
        "ticket_embedding",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("ticket_id", sa.BigInteger(), nullable=False),
        sa.Column("combined_text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["ticket_id"], ["ticket.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticket_id"),
    )

    op.create_index(
        "idx_kb_chunk_embedding",
        "kb_chunk",
        ["embedding"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 50},
    )
    op.create_index(
        "idx_ticket_embedding_embedding",
        "ticket_embedding",
        ["embedding"],
        unique=False,
        postgresql_using="ivfflat",
        postgresql_ops={"embedding": "vector_cosine_ops"},
        postgresql_with={"lists": 50},
    )


def downgrade() -> None:
    op.drop_index("idx_ticket_embedding_embedding", table_name="ticket_embedding")
    op.drop_index("idx_kb_chunk_embedding", table_name="kb_chunk")
    op.drop_table("ticket_embedding")
    op.drop_table("kb_chunk")
    op.drop_table("ticket")
    sa.Enum("HIGH", "MEDIUM", "LOW", name="ai_confidence").drop(op.get_bind(), checkfirst=True)
    sa.Enum("HIGH", "MEDIUM", "LOW", name="service_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum("OPEN", "PENDING", "CLOSED", name="service_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum("STUDENT", "FACULTY", "ALUM", "VENDOR", "OTHER", name="user_role").drop(op.get_bind(), checkfirst=True)
