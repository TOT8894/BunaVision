import unittest
from datetime import UTC, datetime

from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.domain.errors import ErrorCode, InvalidRequestError, PersistenceError
from app.domain.models import Assessment


def failed(assessment_id: str, owner: str = "o") -> Assessment:
    return Assessment.failed(
        assessment_id=assessment_id, owner_id=owner, created_at=datetime.now(UTC),
        processing_time_ms=1, image_sha256="x", error_code=ErrorCode.INFERENCE_FAILED,
    )


class RepositoryTests(unittest.IsolatedAsyncioTestCase):
    async def test_get_is_owner_scoped(self) -> None:
        repo = InMemoryAssessmentRepository()
        await repo.add(failed("a1", owner="alice"))
        self.assertIsNotNone(await repo.get("a1", "alice"))
        self.assertIsNone(await repo.get("a1", "bob"))

    async def test_pagination_walks_every_item_once_newest_first(self) -> None:
        repo = InMemoryAssessmentRepository()
        for i in range(5):
            await repo.add(failed(f"a{i}"))
        seen: list[str] = []
        cursor = None
        while True:
            page = await repo.list_for_owner("o", limit=2, cursor=cursor)
            seen += [a.assessment_id for a in page.items]
            cursor = page.next_cursor
            if cursor is None:
                break
        self.assertEqual(seen, ["a4", "a3", "a2", "a1", "a0"])

    async def test_bad_cursor_is_a_client_error(self) -> None:
        repo = InMemoryAssessmentRepository()
        for bad in ("garbage", "e30=", "eyJzIjogLTF9"):  # not b64 json / no key / negative
            with self.subTest(cursor=bad), self.assertRaises(InvalidRequestError):
                await repo.list_for_owner("o", limit=1, cursor=bad)

    async def test_duplicate_assessment_id_is_rejected(self) -> None:
        repo = InMemoryAssessmentRepository()
        await repo.add(failed("a1"))
        with self.assertRaises(PersistenceError):
            await repo.add(failed("a1"))


if __name__ == "__main__":
    unittest.main()
