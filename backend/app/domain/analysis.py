"""Pure analysis rules. No I/O. Every number is derived, never typed in twice."""

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from statistics import fmean

from app.domain.models import ClassTally, Coverage, Detection, DetectionSummary
from app.domain.taxonomy import DefectCategory, DefectTaxonomy


def summarize(detections: Sequence[Detection]) -> DetectionSummary:
    """Group detections by class. Counts are of defect instances, not of beans."""
    grouped: dict[str, list[Detection]] = defaultdict(list)
    for detection in detections:
        grouped[detection.defect.key].append(detection)

    tallies = sorted(
        (
            ClassTally(
                defect=items[0].defect,
                count=len(items),
                mean_confidence=round(fmean(item.confidence for item in items), 3),
            )
            for items in grouped.values()
        ),
        key=lambda tally: (-tally.count, tally.defect.name),
    )
    return DetectionSummary(
        detection_count=len(detections),
        primary_count=sum(t.count for t in tallies if t.defect.category is DefectCategory.PRIMARY),
        secondary_count=sum(
            t.count for t in tallies if t.defect.category is DefectCategory.SECONDARY
        ),
        by_class=tuple(tallies),
    )


def build_coverage(taxonomy: DefectTaxonomy) -> Coverage:
    return Coverage(scanned=taxonomy.scanned, not_scanned=taxonomy.not_scanned)


class LimitationCode(StrEnum):
    """Stable codes so the frontend can localize the message."""

    PRELIMINARY_AI_ASSESSMENT = "PRELIMINARY_AI_ASSESSMENT"
    PARTIAL_CLASS_COVERAGE = "PARTIAL_CLASS_COVERAGE"
    HIDDEN_DEFECTS_NOT_DETECTABLE = "HIDDEN_DEFECTS_NOT_DETECTABLE"
    MANUAL_VERIFICATION_REQUIRED = "MANUAL_VERIFICATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class Limitation:
    code: LimitationCode
    message: str


def limitations_for(coverage: Coverage) -> tuple[Limitation, ...]:
    """Transparency statements required on every report. Numbers come from `coverage`."""
    limitations = [
        Limitation(
            LimitationCode.PRELIMINARY_AI_ASSESSMENT,
            "Preliminary AI screening of a photograph. This is not an official ECX or SCA grade.",
        )
    ]
    if coverage.not_scanned:
        total = len(coverage.scanned) + len(coverage.not_scanned)
        names = ", ".join(c.name for c in coverage.scanned)
        limitations.append(
            Limitation(
                LimitationCode.PARTIAL_CLASS_COVERAGE,
                f"Only {len(coverage.scanned)} of {total} ECX defect classes are scanned "
                f"({names}). Defects in the other {len(coverage.not_scanned)} classes are not "
                "detected, so real defect counts may be higher.",
            )
        )
    limitations.append(
        Limitation(
            LimitationCode.HIDDEN_DEFECTS_NOT_DETECTABLE,
            "Defects hidden from the camera, or inside the bean, cannot be detected "
            "from a photograph.",
        )
    )
    limitations.append(
        Limitation(
            LimitationCode.MANUAL_VERIFICATION_REQUIRED,
            "Counts are model predictions. Verify them manually before any commercial "
            "or export decision.",
        )
    )
    return tuple(limitations)
