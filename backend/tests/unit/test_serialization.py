import unittest

from app.adapters.db.postgres.serialization import RESULT_SCHEMA_VERSION, result_from_json, result_to_json
from app.adapters.db.memory_repository import InMemoryAssessmentRepository
from app.adapters.storage.memory import InMemoryImageStore
from app.domain.errors import PersistenceError
from app.domain.taxonomy import ECX_TAXONOMY
from app.services.assessment_service import AssessmentService
from app.services.image_validation import ImageLimits
from tests.unit.fakes import CountingIds, FakeAdvisor, FakeVision, FixedClock, make_image, raw


class SerializationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        service = AssessmentService(
            vision=FakeVision((raw("Full Black", 0.91), raw("Partial Black", 0.6), raw("Partial Black", 0.8))),
            advisor=FakeAdvisor(), images=InMemoryImageStore(),
            repository=InMemoryAssessmentRepository(), taxonomy=ECX_TAXONOMY,
            limits=ImageLimits(10 * 1024 * 1024, 50_000_000, 320), clock=FixedClock(),
            new_id=CountingIds(), image_url_ttl_s=900, retain_original_image=True,
            max_assessments_per_hour=100, max_concurrent_assessments=2,
        )
        outcome = await service.create_assessment(data=make_image(), owner_id="o")
        assert outcome.view.assessment.result is not None
        self.result = outcome.view.assessment.result

    def test_round_trips_exactly(self) -> None:
        stored = result_to_json(self.result)
        self.assertEqual(result_from_json(stored, ECX_TAXONOMY), self.result)

    def test_document_is_plain_json_types(self) -> None:
        import json

        self.assertEqual(json.loads(json.dumps(result_to_json(self.result))), result_to_json(self.result))

    def test_summary_is_recomputed_not_stored(self) -> None:
        stored = result_to_json(self.result)
        self.assertNotIn("summary", stored)
        self.assertEqual(result_from_json(stored, ECX_TAXONOMY).summary.detection_count, 3)

    def test_unknown_defect_key_fails_loudly(self) -> None:
        stored = result_to_json(self.result)
        stored["detections"][0]["defect_key"] = "removed_class"
        with self.assertRaises(PersistenceError):
            result_from_json(stored, ECX_TAXONOMY)

    def test_unsupported_schema_version_and_missing_fields_fail_loudly(self) -> None:
        newer = {**result_to_json(self.result), "schema": RESULT_SCHEMA_VERSION + 1}
        with self.assertRaises(PersistenceError):
            result_from_json(newer, ECX_TAXONOMY)
        broken = result_to_json(self.result)
        del broken["advisory"]
        with self.assertRaises(PersistenceError):
            result_from_json(broken, ECX_TAXONOMY)


if __name__ == "__main__":
    unittest.main()
