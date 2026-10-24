import unittest
from datetime import UTC, datetime

from app.domain.analysis import LimitationCode, build_coverage, limitations_for, summarize
from app.domain.errors import ErrorCode, UnknownDefectClassError
from app.domain.models import Assessment, AssessmentStatus, BoundingBox, Detection
from app.domain.taxonomy import (
    ECX_TAXONOMY,
    DefectCategory,
    DefectClass,
    DefectTaxonomy,
)

BOX = BoundingBox(0, 0, 1, 1)


def detection(label: str, confidence: float) -> Detection:
    return Detection(defect=ECX_TAXONOMY.from_vision_label(label), confidence=confidence, box=BOX)


class TaxonomyTests(unittest.TestCase):
    def test_inventory_matches_the_ecx_rubric(self) -> None:
        categories = [c.category for c in ECX_TAXONOMY.all]
        self.assertEqual(len(categories), 13)
        self.assertEqual(categories.count(DefectCategory.PRIMARY), 6)
        self.assertEqual(categories.count(DefectCategory.SECONDARY), 7)

    def test_only_three_classes_are_scanned_today(self) -> None:
        self.assertEqual(
            {c.vision_label for c in ECX_TAXONOMY.scanned},
            {"Full Black", "Partial Black", "Coffee Husk / Parchment"},
        )
        self.assertEqual(len(ECX_TAXONOMY.not_scanned), 10)

    def test_category_comes_from_the_taxonomy_not_the_caller(self) -> None:
        self.assertIs(ECX_TAXONOMY.from_vision_label("Full Black").category, DefectCategory.PRIMARY)
        self.assertIs(
            ECX_TAXONOMY.from_vision_label("Coffee Husk / Parchment").category,
            DefectCategory.SECONDARY,
        )

    def test_unknown_label_fails_instead_of_guessing(self) -> None:
        with self.assertRaises(UnknownDefectClassError) as caught:
            ECX_TAXONOMY.from_vision_label("Mystery Spot")
        self.assertIs(caught.exception.code, ErrorCode.INFERENCE_FAILED)

    def test_duplicate_keys_and_labels_are_rejected(self) -> None:
        a = DefectClass("a", "A", DefectCategory.PRIMARY, vision_label="x")
        with self.assertRaises(ValueError):
            DefectTaxonomy([a, DefectClass("a", "B", DefectCategory.PRIMARY)])
        with self.assertRaises(ValueError):
            DefectTaxonomy([a, DefectClass("b", "B", DefectCategory.PRIMARY, vision_label="x")])


class SummaryTests(unittest.TestCase):
    def test_zero_detections_is_a_valid_summary(self) -> None:
        summary = summarize([])
        self.assertEqual(
            (summary.detection_count, summary.primary_count, summary.secondary_count), (0, 0, 0)
        )
        self.assertEqual(summary.by_class, ())

    def test_counts_are_detection_counts_grouped_by_class(self) -> None:
        summary = summarize(
            [
                detection("Full Black", 0.9),
                detection("Partial Black", 0.9),
                detection("Partial Black", 0.5),
            ]
        )
        self.assertEqual(summary.detection_count, 3)
        self.assertEqual(summary.primary_count, 1)
        self.assertEqual(summary.secondary_count, 2)
        first = summary.by_class[0]
        self.assertEqual((first.defect.name, first.count, first.mean_confidence), ("Partial Black", 2, 0.7))


class LimitationTests(unittest.TestCase):
    def test_coverage_numbers_are_derived_from_the_taxonomy(self) -> None:
        by_code = {lim.code: lim for lim in limitations_for(build_coverage(ECX_TAXONOMY))}
        message = by_code[LimitationCode.PARTIAL_CLASS_COVERAGE].message
        self.assertIn("Only 3 of 13", message)
        self.assertIn("other 10", message)

    def test_no_partial_coverage_note_when_everything_is_scanned(self) -> None:
        full = DefectTaxonomy([DefectClass("a", "A", DefectCategory.PRIMARY, vision_label="A")])
        codes = {lim.code for lim in limitations_for(build_coverage(full))}
        self.assertNotIn(LimitationCode.PARTIAL_CLASS_COVERAGE, codes)
        self.assertIn(LimitationCode.PRELIMINARY_AI_ASSESSMENT, codes)


class AssessmentInvariantTests(unittest.TestCase):
    def test_failed_assessment_must_carry_an_error_code(self) -> None:
        with self.assertRaises(ValueError):
            Assessment(
                assessment_id="a", owner_id="o", status=AssessmentStatus.FAILED,
                created_at=datetime.now(UTC), processing_time_ms=0, image_sha256="x",
                result=None, error_code=None, idempotency_key=None,
            )

    def test_completed_assessment_must_carry_a_result(self) -> None:
        with self.assertRaises(ValueError):
            Assessment(
                assessment_id="a", owner_id="o", status=AssessmentStatus.COMPLETED,
                created_at=datetime.now(UTC), processing_time_ms=0, image_sha256="x",
                result=None, error_code=None, idempotency_key=None,
            )

    def test_failed_factory_drops_the_idempotency_key(self) -> None:
        failed = Assessment.failed(
            assessment_id="a", owner_id="o", created_at=datetime.now(UTC),
            processing_time_ms=1, image_sha256="x", error_code=ErrorCode.INFERENCE_FAILED,
        )
        self.assertIsNone(failed.idempotency_key)
        self.assertIsNone(failed.result)


if __name__ == "__main__":
    unittest.main()
