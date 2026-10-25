"""In-memory `AssessmentRepository`. Development and tests only.

Also the reference behaviour for a real database adapter (DynamoDB or PostgreSQL):

* `add` is atomic and enforces (owner_id, idempotency_key) uniqueness.
* `get` returns a record only to its owner.
* Listing is newest first, paginated by an OPAQUE cursor. The cursor here encodes an insertion
  sequence number; a database adapter would encode its own sort key (created_at, id).
"""

import base64
import binascii
import json

from app.domain.errors import InvalidRequestError, PersistenceError
from app.domain.errors import DuplicateIdempotencyKeyError
from app.domain.models import Assessment, AssessmentPage


class InMemoryAssessmentRepository:
    def __init__(self) -> None:
        self._rows: list[tuple[int, Assessment]] = []  # insertion order = sequence order
        self._by_id: dict[str, Assessment] = {}
        self._by_key: dict[tuple[str, str], Assessment] = {}
        self._next_seq = 1

    async def add(self, assessment: Assessment) -> None:
        if assessment.assessment_id in self._by_id:
            raise PersistenceError(f"assessment id {assessment.assessment_id} already exists")
        if assessment.idempotency_key is not None:
            slot = (assessment.owner_id, assessment.idempotency_key)
            if slot in self._by_key:
                raise DuplicateIdempotencyKeyError(f"key already used: {slot}")
            self._by_key[slot] = assessment
        self._rows.append((self._next_seq, assessment))
        self._next_seq += 1
        self._by_id[assessment.assessment_id] = assessment

    async def get(self, assessment_id: str, owner_id: str) -> Assessment | None:
        found = self._by_id.get(assessment_id)
        return found if found is not None and found.owner_id == owner_id else None

    async def find_by_idempotency_key(self, owner_id: str, key: str) -> Assessment | None:
        return self._by_key.get((owner_id, key))

    async def list_for_owner(
        self, owner_id: str, *, limit: int, cursor: str | None
    ) -> AssessmentPage:
        before = _decode_cursor(cursor) if cursor is not None else None
        mine = [
            (seq, item)
            for seq, item in reversed(self._rows)
            if item.owner_id == owner_id and (before is None or seq < before)
        ]
        page, rest = mine[:limit], mine[limit:]
        next_cursor = _encode_cursor(page[-1][0]) if rest else None
        return AssessmentPage(items=tuple(item for _, item in page), next_cursor=next_cursor)


def _encode_cursor(seq: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"s": seq}).encode()).decode()


def _decode_cursor(cursor: str) -> int:
    try:
        value = json.loads(base64.urlsafe_b64decode(cursor.encode()))["s"]
    except (binascii.Error, ValueError, KeyError, TypeError, UnicodeError) as exc:
        raise InvalidRequestError(f"bad cursor: {exc!r}", public_message="Invalid cursor.") from exc
    if not isinstance(value, int) or value < 1:
        raise InvalidRequestError("bad cursor value", public_message="Invalid cursor.")
    return value
