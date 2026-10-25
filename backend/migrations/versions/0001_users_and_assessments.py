"""users and assessments

Revision ID: 0001
Revises:
Create Date: 2026-10-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Uuid(as_uuid=False), primary_key=True),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
    )
    op.create_index("uq_users_email", "users", ["email"], unique=True)

    op.create_table(
        "assessments",
        sa.Column("assessment_id", sa.Text, primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=False),
            sa.ForeignKey("users.user_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processing_time_ms", sa.Integer, nullable=False),
        sa.Column("image_sha256", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.Text),
        sa.Column("error_code", sa.Text),
        sa.Column("model_version", sa.Text),
        sa.Column("validator_version", sa.Text),
        sa.Column("result", postgresql.JSONB(none_as_null=True)),
        sa.CheckConstraint("status IN ('completed', 'failed')", name="ck_assessments_status"),
        sa.CheckConstraint(
            "(status = 'completed' AND result IS NOT NULL AND error_code IS NULL"
            " AND model_version IS NOT NULL AND validator_version IS NOT NULL)"
            " OR (status = 'failed' AND result IS NULL AND error_code IS NOT NULL"
            " AND model_version IS NULL AND validator_version IS NULL)",
            name="ck_assessments_status_shape",
        ),
    )
    op.create_index(
        "ix_assessments_owner_created",
        "assessments",
        ["owner_id", sa.text("created_at DESC"), sa.text("assessment_id DESC")],
    )
    op.create_index(
        "ix_assessments_status_created",
        "assessments",
        ["status", sa.text("created_at DESC")],
    )
    op.create_index(
        "uq_assessments_owner_idempotency",
        "assessments",
        ["owner_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_table("assessments")
    op.drop_table("users")
