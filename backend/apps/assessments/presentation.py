"""Stored assessment -> the API's dictionaries. Pure apart from the URL builder passed in."""

from collections.abc import Callable
from typing import Any

from django.conf import settings

from apps.assessments.analysis import Detection, defect_dict, limitations_for, summarize
from apps.assessments.models import Assessment
from apps.assessments.taxonomy import TAXONOMY, DefectClass
from apps.common.errors import PersistenceFailed


def _defect(key: str) -> DefectClass:
    defect = TAXONOMY.get(key)
    if defect is None:
        raise PersistenceFailed(f"stored result references unknown defect class {key!r}")
    return defect


def _image_url(url_for: Callable[[str], str], key: str | None) -> str | None:
    if key is None:
        return None
    try:
        return url_for(key)
    except Exception as exc:
        # Storage URL generation can fail independently of the stored assessment. Keep the row
        # intact and return the API's storage/persistence error instead of an unclassified 500.
        raise PersistenceFailed("could not generate an image URL") from exc


def present(assessment: Assessment, url_for: Callable[[str], str]) -> dict[str, Any]:
    base = {
        "assessment_id": assessment.id,
        "created_at": assessment.created_at,
        "processing_time_ms": assessment.processing_time_ms,
    }
    if assessment.status == Assessment.Status.FAILED:
        return {**base, "status": "failed", "error_code": assessment.error_code}
    doc = assessment.result
    try:
        detections = [
            Detection(defect=_defect(d["defect_key"]), confidence=d["confidence"], box=tuple(d["box"]))
            for d in doc["detections"]
        ]
        scanned = [_defect(k) for k in doc["coverage"]["scanned"]]
        not_scanned = [_defect(k) for k in doc["coverage"]["not_scanned"]]
        original, annotated = doc["original_image_key"], doc["annotated_image_key"]
        return {
            **base,
            "status": "completed",
            "result": {
                "model_version": doc["model_version"],
                "image_check": {"is_coffee": True, **doc["image_check"]},
                "summary": summarize(detections),
                "detections": [
                    {
                        "defect": defect_dict(d.defect),
                        "confidence": d.confidence,
                        "box": dict(zip(("x1", "y1", "x2", "y2"), d.box, strict=True)),
                    }
                    for d in detections
                ],
                "coverage": {
                    "scanned": [defect_dict(c) for c in scanned],
                    "not_scanned": [defect_dict(c) for c in not_scanned],
                },
                "limitations": limitations_for(scanned, not_scanned),
                "advisory": doc["advisory"],
                "images": {
                    "original_url": _image_url(url_for, original),
                    "annotated_url": _image_url(url_for, annotated),
                    "expires_in_s": settings.IMAGE_URL_TTL_S,
                },
            },
        }
    except (KeyError, TypeError) as exc:
        raise PersistenceFailed(f"stored result of {assessment.id} is unreadable: {exc!r}") from exc


def present_list_item(assessment: Assessment) -> dict[str, Any]:
    base = {"assessment_id": assessment.id, "created_at": assessment.created_at}
    if assessment.status == Assessment.Status.FAILED:
        return {**base, "status": "failed", "error_code": assessment.error_code}
    detections = [
        Detection(defect=_defect(d["defect_key"]), confidence=d["confidence"], box=tuple(d["box"]))
        for d in assessment.result["detections"]
    ]
    summary = summarize(detections)
    return {
        **base,
        "status": "completed",
        "model_version": assessment.model_version,
        "detection_count": summary["detection_count"],
        "primary_detection_count": summary["primary_detection_count"],
        "secondary_detection_count": summary["secondary_detection_count"],
    }
