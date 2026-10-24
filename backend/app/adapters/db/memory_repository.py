"""In-memory repositories.

DEVELOPMENT AND TESTS ONLY. Data is lost on restart and is not shared between processes. The
production implementations are in `app.adapters.db.postgres`; these implement the same ports
and exist so the services can be tested, and the app run, without a database.

Single-threaded event loop: each method runs without awaiting, so check-then-write sequences
are atomic here. A real database must enforce uniqueness itself.
"""

from collections import Counter
from collections.abc import Iterable
from datetime import datetime

from app.adapters.db.cursor import SortKey, decode_cursor, encode_cursor
from app.domain.errors import (
    DuplicateIdempotencyKeyError,
    EmailAlreadyRegisteredError,
    ErrorCode,
)
from app.domain.models import Assessment, AssessmentPage, AssessmentStatus
from app.domain.operations import ModelVersionUsage, OutcomeCount
from app.domain.users import User


def _sort_key(assessment: Assessment) -> SortKey:
    return assessment.created_at, assessment.assessment_id


def _page(items: Iterable[Assessment], limit: int, cursor: str | None) -> AssessmentPage:
    ordered = sorted(items, key=_sort_key, reverse=True)
    if cursor is not None:
        after = decode_cursor(cursor)
        ordered = [a for a in ordered if _sort_key(a) < after]
    page = ordered[:limit]
    next_cursor = encode_cursor(_sort_key(page[-1])) if len(ordered) > limit else None
    return AssessmentPage(items=tuple(page), next_cursor=next_cursor)


class InMemoryAssessmentRepository:
    """Implements `AssessmentRepository` and `AssessmentAdminQueries`."""

    def __init__(self) -> None:
        self._by_id: dict[str, Assessment] = {}
        self._id_by_key: dict[tuple[str, str], str] = {}

    # --- AssessmentRepository ---------------------------------------------------------

    async def add(self, assessment: Assessment) -> None:
        if assessment.idempotency_key is not None:
            slot = (assessment.owner_id, assessment.idempotency_key)
            if slot in self._id_by_key:
                raise DuplicateIdempotencyKeyError(f"idempotency key already used: {slot[1]}")
            self._id_by_key[slot] = assessment.assessment_id
        self._by_id[assessment.assessment_id] = assessment

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        assessment = self._by_id.get(assessment_id)
        if assessment is None or assessment.owner_id != owner_id:
            return None
        return assessment

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        assessment_id = self._id_by_key.get((owner_id, key))
        return None if assessment_id is None else self._by_id[assessment_id]

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        return _page((a for a in self._by_id.values() if a.owner_id == owner_id), limit, cursor)

    async def count_since(self, owner_id: str, since: datetime) -> int:
        return sum(
            1 for a in self._by_id.values() if a.owner_id == owner_id and a.created_at >= since
        )

    # --- AssessmentAdminQueries -------------------------------------------------------

    async def get_any(self, assessment_id: str) -> Assessment | None:
        return self._by_id.get(assessment_id)

    async def list_all(
        self,
        *,
        status: AssessmentStatus | None,
        error_code: ErrorCode | None,
        owner_id: str | None,
        limit: int,
        cursor: str | None,
    ) -> AssessmentPage:
        matching = (
            a
            for a in self._by_id.values()
            if (status is None or a.status is status)
            and (error_code is None or a.error_code is error_code)
            and (owner_id is None or a.owner_id == owner_id)
        )
        return _page(matching, limit, cursor)

    async def model_version_usage(self) -> tuple[ModelVersionUsage, ...]:
        groups: dict[tuple[str, str], list[Assessment]] = {}
        for a in self._by_id.values():
            if a.result is not None:
                key = (a.result.model_version, a.result.image_check.validator_version)
                groups.setdefault(key, []).append(a)
        usage = [
            ModelVersionUsage(
                model_version=model,
                validator_version=validator,
                assessments=len(items),
                first_seen=min(a.created_at for a in items),
                last_seen=max(a.created_at for a in items),
            )
            for (model, validator), items in groups.items()
        ]
        return tuple(sorted(usage, key=lambda u: u.last_seen, reverse=True))

    async def outcome_counts(self, since: datetime) -> tuple[OutcomeCount, ...]:
        counts = Counter(
            (a.status, a.error_code) for a in self._by_id.values() if a.created_at >= since
        )
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0][0].value))
        return tuple(
            OutcomeCount(status=status, error_code=code, count=count)
            for (status, code), count in ranked
        )


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._id_by_email: dict[str, str] = {}

    async def add(self, user: User) -> None:
        if user.email in self._id_by_email:
            raise EmailAlreadyRegisteredError(f"email already registered: {user.email}")
        self._id_by_email[user.email] = user.user_id
        self._by_id[user.user_id] = user

    async def get(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    async def find_by_email(self, email: str) -> User | None:
        user_id = self._id_by_email.get(email)
        return None if user_id is None else self._by_id[user_id]
