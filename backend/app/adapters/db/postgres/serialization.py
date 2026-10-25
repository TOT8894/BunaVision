"""Domain result <-> the JSON document stored in `assessments.result`.

Pure functions, no database. Rehydration goes through the taxonomy by stable defect key, so a
stored result whose class has since been removed fails loudly instead of being mislabeled.
The document carries a schema version so the format can evolve without guessing.
"""

from typing import Any

from app.domain.analysis import summarize
from app.domain.errors import PersistenceError
from app.domain.models import (
    Advisory,
    AssessmentResult,
    BilingualText,
    BoundingBox,
    Coverage,
    Detection,
    ImageCheck,
)
from app.domain.taxonomy import DefectClass, DefectTaxonomy

RESULT_SCHEMA_VERSION = 1


def result_to_json(result: AssessmentResult) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA_VERSION,
        "model_version": result.model_version,
        "image_check": {
            "coffee_confidence": result.image_check.coffee_confidence,
            "validator_version": result.image_check.validator_version,
        },
        "detections": [
            {
                "defect_key": d.defect.key,
                "confidence": d.confidence,
                "box": [d.box.x1, d.box.y1, d.box.x2, d.box.y2],
            }
            for d in result.detections
        ],
        "coverage": {
            "scanned": [c.key for c in result.coverage.scanned],
            "not_scanned": [c.key for c in result.coverage.not_scanned],
        },
        "advisory": {
            "generator_model": result.advisory.generator_model,
            "summary": _text_to_json(result.advisory.summary),
            "recommendations": [_text_to_json(r) for r in result.advisory.recommendations],
        },
        "original_image_key": result.original_image_key,
        "annotated_image_key": result.annotated_image_key,
    }


def result_from_json(data: dict[str, Any], taxonomy: DefectTaxonomy) -> AssessmentResult:
    try:
        if data["schema"] != RESULT_SCHEMA_VERSION:
            raise PersistenceError(f"unsupported stored result schema {data['schema']!r}")
        detections = tuple(
            Detection(
                defect=_defect(taxonomy, item["defect_key"]),
                confidence=float(item["confidence"]),
                box=BoundingBox(*(float(v) for v in item["box"])),
            )
            for item in data["detections"]
        )
        advisory = data["advisory"]
        return AssessmentResult(
            model_version=data["model_version"],
            image_check=ImageCheck(
                coffee_confidence=float(data["image_check"]["coffee_confidence"]),
                validator_version=data["image_check"]["validator_version"],
            ),
            detections=detections,
            summary=summarize(detections),
            coverage=Coverage(
                scanned=tuple(_defect(taxonomy, k) for k in data["coverage"]["scanned"]),
                not_scanned=tuple(_defect(taxonomy, k) for k in data["coverage"]["not_scanned"]),
            ),
            advisory=Advisory(
                generator_model=advisory["generator_model"],
                summary=_text_from_json(advisory["summary"]),
                recommendations=tuple(_text_from_json(r) for r in advisory["recommendations"]),
            ),
            original_image_key=data["original_image_key"],
            annotated_image_key=data["annotated_image_key"],
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PersistenceError(f"stored assessment result is unreadable: {exc!r}") from exc


def _defect(taxonomy: DefectTaxonomy, key: str) -> DefectClass:
    defect = taxonomy.get(key)
    if defect is None:
        raise PersistenceError(f"stored result references unknown defect class {key!r}")
    return defect


def _text_to_json(text: BilingualText) -> dict[str, str]:
    return {"en": text.en, "am": text.am}


def _text_from_json(data: dict[str, str]) -> BilingualText:
    return BilingualText(en=data["en"], am=data["am"])
