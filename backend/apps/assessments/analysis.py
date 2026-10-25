"""Pure analysis rules. Counts are numbers of detections (bounding boxes), never beans."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import fmean
from typing import Any

from apps.assessments.taxonomy import DefectCategory, DefectClass


@dataclass(frozen=True, slots=True)
class Detection:
    defect: DefectClass
    confidence: float  # model confidence in [0, 1]; not a probability of being correct
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels of the uploaded image


def defect_dict(defect: DefectClass) -> dict[str, str]:
    return {"key": defect.key, "name": defect.name, "category": defect.category.value}


def summarize(detections: Sequence[Detection]) -> dict[str, Any]:
    grouped: dict[str, list[Detection]] = defaultdict(list)
    for detection in detections:
        grouped[detection.defect.key].append(detection)
    by_class = sorted(
        (
            {
                "defect": defect_dict(items[0].defect),
                "count": len(items),
                "mean_confidence": round(fmean(i.confidence for i in items), 3),
            }
            for items in grouped.values()
        ),
        key=lambda tally: (-tally["count"], tally["defect"]["name"]),
    )

    def total(category: DefectCategory) -> int:
        return sum(t["count"] for t in by_class if t["defect"]["category"] == category.value)

    return {
        "detection_count": len(detections),
        "primary_detection_count": total(DefectCategory.PRIMARY),
        "secondary_detection_count": total(DefectCategory.SECONDARY),
        "by_class": by_class,
    }


def limitations_for(
    scanned: Sequence[DefectClass], not_scanned: Sequence[DefectClass]
) -> list[dict[str, str]]:
    """Transparency statements required on every report; numbers come from the coverage."""
    limitations = [
        {
            "code": "PRELIMINARY_AI_ASSESSMENT",
            "message": "Preliminary AI screening of a photograph. This is not an official ECX or SCA grade.",
        }
    ]
    if not_scanned:
        total = len(scanned) + len(not_scanned)
        limitations.append(
            {
                "code": "PARTIAL_CLASS_COVERAGE",
                "message": (
                    f"Only {len(scanned)} of {total} ECX defect classes are scanned "
                    f"({', '.join(c.name for c in scanned)}). Defects in the other "
                    f"{len(not_scanned)} classes are not detected, so real defect counts may be higher."
                ),
            }
        )
    limitations.append(
        {
            "code": "HIDDEN_DEFECTS_NOT_DETECTABLE",
            "message": "Defects hidden from the camera, or inside the bean, cannot be detected from a photograph.",
        }
    )
    limitations.append(
        {
            "code": "MANUAL_VERIFICATION_REQUIRED",
            "message": "Counts are model predictions. Verify them manually before any commercial or export decision.",
        }
    )
    return limitations
