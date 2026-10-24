"""PostgreSQL schema, as SQLAlchemy Core tables.

This module is the single description of the tables. The first Alembic migration restates it
explicitly (migrations must never depend on code that will change later), so keep the two in
step: a change here needs a new migration.

Design notes:

* `assessments` keeps the columns operators filter on (status, error_code, model_version,
  validator_version, created_at) as real columns, and the bulky structured outcome
  (detections, coverage, advisory, image keys) as one JSONB document. Nobody queries inside it.
* The result summary is NOT stored; it is recomputed from the detections when read, so counts
  can never disagree with the boxes they came from.
* A CHECK constraint makes the "completed has a result, failed has an error" rule hold in the
  database as well as in code.
* Users are never deleted with their history (ON DELETE RESTRICT); deactivate instead.
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

metadata = sa.MetaData()

users = sa.Table(
    "users",
    metadata,
    sa.Column("user_id", sa.Uuid(as_uuid=False), primary_key=True),
    sa.Column("email", sa.Text, nullable=False),  # stored normalized (lower-case)
    sa.Column("password_hash", sa.Text, nullable=False),
    sa.Column("role", sa.Text, nullable=False),
    sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('user', 'admin')", name="ck_users_role"),
)
sa.Index("uq_users_email", users.c.email, unique=True)

assessments = sa.Table(
    "assessments",
    metadata,
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
    # none_as_null: Python None must become SQL NULL, not the JSON value `null`.
    sa.Column("result", JSONB(none_as_null=True)),
    sa.CheckConstraint("status IN ('completed', 'failed')", name="ck_assessments_status"),
    sa.CheckConstraint(
        "(status = 'completed' AND result IS NOT NULL AND error_code IS NULL"
        " AND model_version IS NOT NULL AND validator_version IS NOT NULL)"
        " OR (status = 'failed' AND result IS NULL AND error_code IS NOT NULL"
        " AND model_version IS NULL AND validator_version IS NULL)",
        name="ck_assessments_status_shape",
    ),
)
sa.Index(
    "ix_assessments_owner_created",
    assessments.c.owner_id,
    assessments.c.created_at.desc(),
    assessments.c.assessment_id.desc(),
)
sa.Index("ix_assessments_status_created", assessments.c.status, assessments.c.created_at.desc())
sa.Index(
    "uq_assessments_owner_idempotency",
    assessments.c.owner_id,
    assessments.c.idempotency_key,
    unique=True,
    postgresql_where=assessments.c.idempotency_key.is_not(None),
)
