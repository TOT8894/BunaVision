import unittest
from datetime import UTC, datetime, timedelta

from app.adapters.db.cursor import decode_cursor, encode_cursor
from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.domain.errors import DuplicateIdempotencyKeyError, ErrorCode, InvalidRequestError
from app.domain.models import Assessment

T0 = datetime(2026, 10, 21, 8, 0, 0, tzinfo=UTC)


def failed(assessment_id: str, owner: str = "o", at: datetime = T0) -> Assessment:
    return Assessment.failed(
        assessment_id=assessment_id, owner_id=owner, created_at=at,
        processing_time_ms=1, image_sha256="x", error_code=ErrorCode.INFERENCE_FAILED,
    )


class CursorTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        key = (T0, "asmt_1")
        self.assertEqual(decode_cursor(encode_cursor(key)), key)

    def test_rejects_garbage_and_naive_timestamps(self) -> None:
        for bad in ("!!!", "e30=", encode_cursor((T0.replace(tzinfo=None), "x"))):
            with self.subTest(bad=bad), self.assertRaises(InvalidRequestError):
                decode_cursor(bad)


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_is_scoped_to_the_owner(self) -> None:
        repo = InMemoryAssessmentRepository()
        await repo.add(failed("a1", owner="alice"))
        self.assertIsNotNone(await repo.get("a1", "alice"))
        self.assertIsNone(await repo.get("a1", "bob"))
        self.assertIsNone(await repo.get("missing", "alice"))

    async def test_list_is_newest_first_scoped_and_paginated(self) -> None:
        repo = InMemoryAssessmentRepository()
        for i in range(5):
            await repo.add(failed(f"a{i}", at=T0 + timedelta(seconds=i)))
        await repo.add(failed("other", owner="someone-else", at=T0 + timedelta(hours=1)))

        first = await repo.list_for_owner("o", limit=2, cursor=None)
        second = await repo.list_for_owner("o", limit=2, cursor=first.next_cursor)
        last = await repo.list_for_owner("o", limit=2, cursor=second.next_cursor)

        self.assertEqual([a.assessment_id for a in first.items], ["a4", "a3"])
        self.assertEqual([a.assessment_id for a in second.items], ["a2", "a1"])
        self.assertEqual([a.assessment_id for a in last.items], ["a0"])
        self.assertIsNone(last.next_cursor)

    async def test_exact_page_boundary_has_no_dangling_cursor(self) -> None:
        repo = InMemoryAssessmentRepository()
        for i in range(2):
            await repo.add(failed(f"a{i}", at=T0 + timedelta(seconds=i)))
        page = await repo.list_for_owner("o", limit=2, cursor=None)
        self.assertEqual(len(page.items), 2)
        self.assertIsNone(page.next_cursor)

    async def test_idempotency_key_is_unique_per_owner(self) -> None:
        repo = InMemoryAssessmentRepository()
        # Only the idempotency key matters here, so a keyed failed-status record is enough.
        a = Assessment(
            assessment_id="a1", owner_id="alice", status=failed("x").status,
            created_at=T0, processing_time_ms=1, image_sha256="x", result=None,
            error_code=ErrorCode.INFERENCE_FAILED, idempotency_key="k",
        )
        await repo.add(a)
        with self.assertRaises(DuplicateIdempotencyKeyError):
            await repo.add(_clone(a, "a2"))
        await repo.add(_clone(a, "a3", owner="bob"))  # another owner may reuse the key
        found = await repo.find_by_idempotency_key("alice", "k")
        self.assertIsNotNone(found)
        self.assertEqual(found.assessment_id, "a1")  # type: ignore[union-attr]


def _clone(a: Assessment, new_id: str, owner: str | None = None) -> Assessment:
    return Assessment(
        assessment_id=new_id, owner_id=owner or a.owner_id, status=a.status,
        created_at=a.created_at, processing_time_ms=a.processing_time_ms,
        image_sha256=a.image_sha256, result=a.result, error_code=a.error_code,
        idempotency_key=a.idempotency_key,
    )


if __name__ == "__main__":
    unittest.main()
