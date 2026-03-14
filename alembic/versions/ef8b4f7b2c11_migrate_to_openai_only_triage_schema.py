"""migrate to openai only triage schema

Revision ID: ef8b4f7b2c11
Revises: c8a7e7d8f1b2
Create Date: 2026-03-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op
from src.db.types import Vector

revision = "ef8b4f7b2c11"
down_revision = "c8a7e7d8f1b2"
branch_labels = None
depends_on = None


OLD_CATEGORY_ENUM = postgresql.ENUM(
    "HARDWARE",
    "SOFTWARE",
    "NETWORK",
    "SECURITY",
    "OTHER",
    name="service_category",
)
NEW_CATEGORY_ENUM = postgresql.ENUM(
    "NETWORK",
    "ACCOUNT_ACCESS",
    "PASSWORD_RESET",
    "HARDWARE_ISSUE",
    "SOFTWARE_ISSUE",
    "PRINTER_ISSUE",
    "EMAIL_ISSUE",
    "SECURITY_CONCERN",
    "STUDENT_DEVICE",
    "CLASSROOM_TECHNOLOGY",
    "UNKNOWN",
    name="service_category_v2",
)
SERVICE_DEPARTMENT_ENUM = postgresql.ENUM(
    "HELPDESK",
    "NETWORK_TEAM",
    "DEVICE_SUPPORT",
    "SYSTEMS_ADMIN",
    "SECURITY_TEAM",
    name="service_department",
)


def upgrade() -> None:
    bind = op.get_bind()
    NEW_CATEGORY_ENUM.create(bind, checkfirst=True)
    SERVICE_DEPARTMENT_ENUM.create(bind, checkfirst=True)

    op.execute(
        """
        ALTER TABLE ticket
        ALTER COLUMN category TYPE service_category_v2
        USING (
            CASE category::text
                WHEN 'HARDWARE' THEN 'HARDWARE_ISSUE'
                WHEN 'SOFTWARE' THEN 'SOFTWARE_ISSUE'
                WHEN 'NETWORK' THEN 'NETWORK'
                WHEN 'SECURITY' THEN 'SECURITY_CONCERN'
                ELSE 'UNKNOWN'
            END
        )::service_category_v2
        """
    )
    op.execute("DROP TYPE service_category")
    op.execute("ALTER TYPE service_category_v2 RENAME TO service_category")
    op.alter_column("ticket", "category", server_default=sa.text("'UNKNOWN'"))

    op.add_column(
        "ticket",
        sa.Column(
            "department",
            postgresql.ENUM(
                "HELPDESK",
                "NETWORK_TEAM",
                "DEVICE_SUPPORT",
                "SYSTEMS_ADMIN",
                "SECURITY_TEAM",
                name="service_department",
                create_type=False,
            ),
            nullable=True,
        ),
    )
    op.alter_column("ticket", "ai_response", new_column_name="ai_recommended_action")
    op.add_column("ticket", sa.Column("ai_missing_information", sa.Text(), nullable=True))
    op.add_column("ticket", sa.Column("ai_reasoning", sa.Text(), nullable=True))
    op.add_column("ticket", sa.Column("ai_processing_ms", sa.Integer(), nullable=True))
    op.drop_column("ticket", "ai_next_steps")

    op.drop_index("idx_ticket_embedding_embedding", table_name="ticket_embedding")
    op.drop_index("idx_kb_chunk_embedding", table_name="kb_chunk")
    op.alter_column(
        "kb_chunk",
        "embedding",
        existing_type=Vector(768),
        type_=Vector(1536),
        postgresql_using="NULL::vector(1536)",
    )
    op.alter_column(
        "ticket_embedding",
        "embedding",
        existing_type=Vector(768),
        type_=Vector(1536),
        postgresql_using="NULL::vector(1536)",
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
    bind = op.get_bind()
    old_category_enum = postgresql.ENUM(
        "HARDWARE",
        "SOFTWARE",
        "NETWORK",
        "SECURITY",
        "OTHER",
        name="service_category_v1",
    )
    old_category_enum.create(bind, checkfirst=True)

    op.drop_index("idx_ticket_embedding_embedding", table_name="ticket_embedding")
    op.drop_index("idx_kb_chunk_embedding", table_name="kb_chunk")
    op.alter_column(
        "kb_chunk",
        "embedding",
        existing_type=Vector(1536),
        type_=Vector(768),
        postgresql_using="NULL::vector(768)",
    )
    op.alter_column(
        "ticket_embedding",
        "embedding",
        existing_type=Vector(1536),
        type_=Vector(768),
        postgresql_using="NULL::vector(768)",
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

    op.add_column(
        "ticket",
        sa.Column(
            "ai_next_steps",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.drop_column("ticket", "ai_processing_ms")
    op.drop_column("ticket", "ai_reasoning")
    op.drop_column("ticket", "ai_missing_information")
    op.alter_column("ticket", "ai_recommended_action", new_column_name="ai_response")
    op.drop_column("ticket", "department")

    op.execute(
        """
        ALTER TABLE ticket
        ALTER COLUMN category TYPE service_category_v1
        USING (
            CASE category::text
                WHEN 'HARDWARE_ISSUE' THEN 'HARDWARE'
                WHEN 'SOFTWARE_ISSUE' THEN 'SOFTWARE'
                WHEN 'NETWORK' THEN 'NETWORK'
                WHEN 'SECURITY_CONCERN' THEN 'SECURITY'
                ELSE 'OTHER'
            END
        )::service_category_v1
        """
    )
    op.execute("DROP TYPE service_category")
    op.execute("ALTER TYPE service_category_v1 RENAME TO service_category")
    op.alter_column("ticket", "category", server_default=sa.text("'OTHER'"))

    SERVICE_DEPARTMENT_ENUM.drop(bind, checkfirst=True)
