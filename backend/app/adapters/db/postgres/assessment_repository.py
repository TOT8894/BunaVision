"""PostgreSQL implementation of `AssessmentRepository` and `AssessmentAdminQueries`.

Listing is keyset-paginated on (created_at, assessment_id), newest first, using the index
`ix_assessments_owner_created`; there is no OFFSET, so deep pages cost the same as the first.
Idempotency is enforced by the partial unique index `uq_assessments_owner_idempotency`:
the insert uses ON CONFLICT DO NOTHING on exactly that index, so a lost race is reported as
`DuplicateIdempotencyKeyError` and every other integrity failure stays a real error.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.adapters.db.cursor import decode_cursor, encode_cursor
from app.adapters.db.postgres.errors import database_errors
from app.adapters.db.postgres.serialization import result_from_json, result_to_json
from app.adapters.db.postgres.tables import assessments as t
from app.domain.errors import DuplicateIdempotencyKeyError, ErrorCode, PersistenceError
from app.domain.models import Assessment, AssessmentPage, AssessmentStatus
from app.domain.operations import ModelVersionUsage, OutcomeCount
from app.domain.taxonomy import DefectTaxonomy


class PostgresAssessmentRepository:
    def __init__(
        self, sessions: async_sessionmaker[AsyncSession], taxonomy: DefectTaxonomy
    ) -> None:
        self._sessions = sessions
        self._taxonomy = taxonomy

    # --- AssessmentRepository ---------------------------------------------------------

    async def add(self, assessment: Assessment) -> None:
        statement = pg_insert(t).values(**_to_values(assessment))
        if assessment.idempotency_key is not None:
            statement = statement.on_conflict_do_nothing(
                index_elements=[t.c.owner_id, t.c.idempotency_key],
                index_where=t.c.idempotency_key.is_not(None),
            )
        statement = statement.returning(t.c.assessment_id)
        with database_errors("adding an assessment"):
            async with self._sessions.begin() as session:
                inserted = (await session.execute(statement)).scalar_one_or_none()
        if inserted is None:
            raise DuplicateIdempotencyKeyError(
                f"idempotency key already used: {assessment.idempotency_key}"
            )

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        return await self._fetch_one(
            select(t).where(t.c.assessment_id == assessment_id, t.c.owner_id == owner_id),
            "loading an assessment",
        )

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        return await self._fetch_one(
            select(t).where(t.c.owner_id == owner_id, t.c.idempotency_key == key),
            "finding an assessment by idempotency key",
        )

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return await self._fetch_page(
            select(t).where(t.c.owner_id == owner_id), limit, cursor, "listing assessments"
        )

    async def count_since(self, owner_id: str, since: datetime) -> int:
        statement = select(func.count()).select_from(t).where(
            t.c.owner_id == owner_id, t.c.created_at >= since
        )
        with database_errors("counting recent assessments"):
            async with self._sessions() as session:
                return int((await session.execute(statement)).scalar_one())

    # --- AssessmentAdminQueries -------------------------------------------------------

    async def get_any(self, assessment_id: str) -> Assessment | None:
        return await self._fetch_one(
            select(t).where(t.c.assessment_id == assessment_id), "loading an assessment (admin)"
        )

    async def list_all(
        self,
        *,
        status: AssessmentStatus | None,
        error_code: ErrorCode | None,
        owner_id: str | None,
        limit: int,
        cursor: str | None,
    ) -> AssessmentPage:
        statement = select(t)
        if status is not None:
            statement = statement.where(t.c.status == status.value)
        if error_code is not None:
            statement = statement.where(t.c.error_code == error_code.value)
        if owner_id is not None:
            statement = statement.where(t.c.owner_id == owner_id)
        return await self._fetch_page(statement, limit, cursor, "listing all assessments")

    async def model_version_usage(self) -> tuple[ModelVersionUsage, ...]:
        statement = (
            select(
                t.c.model_version,
                t.c.validator_version,
                func.count().label("assessments"),
                func.min(t.c.created_at).label("first_seen"),
                func.max(t.c.created_at).label("last_seen"),
            )
            .where(t.c.status == AssessmentStatus.COMPLETED.value)
            .group_by(t.c.model_version, t.c.validator_version)
            .order_by(func.max(t.c.created_at).desc())
        )
        with database_errors("summarizing model versions"):
            async with self._sessions() as session:
                rows = (await session.execute(statement)).all()
        return tuple(
            ModelVersionUsage(
                model_version=row.model_version,
                validator_version=row.validator_version,
                assessments=row.assessments,
                first_seen=row.first_seen,
                last_seen=row.last_seen,
            )
            for row in rows
        )

    async def outcome_counts(self, since: datetime) -> tuple[OutcomeCount, ...]:
        count = func.count().label("count")
        statement = (
            select(t.c.status, t.c.error_code, count)
            .where(t.c.created_at >= since)
            .group_by(t.c.status, t.c.error_code)
            .order_by(count.desc(), t.c.status)
        )
        with database_errors("counting outcomes"):
            async with self._sessions() as session:
                rows = (await session.execute(statement)).all()
        try:
            return tuple(
                OutcomeCount(
                    status=AssessmentStatus(row.status),
                    error_code=None if row.error_code is None else ErrorCode(row.error_code),
                    count=row.count,
                )
                for row in rows
            )
        except ValueError as exc:
            raise PersistenceError(f"stored outcome has an unknown value: {exc!r}") from exc

    # --- Helpers ----------------------------------------------------------------------

    async def _fetch_one(self, statement: Select[Any], action: str) -> Assessment | None:
        with database_errors(action):
            async with self._sessions() as session:
                row = (await session.execute(statement)).first()
        return None if row is None else self._from_row(row)

    async def _fetch_page(
        self, statement: Select[Any], limit: int, cursor: str | None, action: str
    ) -> AssessmentPage:
        if cursor is not None:
            created_at, assessment_id = decode_cursor(cursor)
            statement = statement.where(
                tuple_(t.c.created_at, t.c.assessment_id) < (created_at, assessment_id)
            )
        # One extra row tells us whether another page exists without a second query.
        statement = statement.order_by(t.c.created_at.desc(), t.c.assessment_id.desc()).limit(
            limit + 1
        )
        with database_errors(action):
            async with self._sessions() as session:
                rows = (await session.execute(statement)).all()
        items = tuple(self._from_row(row) for row in rows[:limit])
        next_cursor = (
            encode_cursor((items[-1].created_at, items[-1].assessment_id))
            if len(rows) > limit
            else None
        )
        return AssessmentPage(items=items, next_cursor=next_cursor)

    def _from_row(self, row: Any) -> Assessment:
        try:
            return Assessment(
                assessment_id=row.assessment_id,
                owner_id=str(row.owner_id),
                status=AssessmentStatus(row.status),
                created_at=row.created_at,
                processing_time_ms=row.processing_time_ms,
                image_sha256=row.image_sha256,
                result=None if row.result is None else result_from_json(row.result, self._taxonomy),
                error_code=None if row.error_code is None else ErrorCode(row.error_code),
                idempotency_key=row.idempotency_key,
            )
        except ValueError as exc:
            raise PersistenceError(
                f"stored assessment row {row.assessment_id} is inconsistent: {exc!r}"
            ) from exc


def _to_values(assessment: Assessment) -> dict[str, Any]:
    result = assessment.result
    return {
        "assessment_id": assessment.assessment_id,
        "owner_id": assessment.owner_id,
        "status": assessment.status.value,
        "created_at": assessment.created_at,
        "processing_time_ms": assessment.processing_time_ms,
        "image_sha256": assessment.image_sha256,
        "idempotency_key": assessment.idempotency_key,
        "error_code": None if assessment.error_code is None else assessment.error_code.value,
        "model_version": None if result is None else result.model_version,
        "validator_version": None if result is None else result.image_check.validator_version,
        "result": None if result is None else result_to_json(result),
    }
