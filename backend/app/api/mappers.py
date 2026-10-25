"""Domain objects -> public API models. The only place the two vocabularies meet."""

from app.domain.analysis import limitations_for
from app.domain.errors import InvariantViolationError
from app.domain.models import Assessment, AssessmentPage, AssessmentResult
from app.domain.taxonomy import DefectClass
from app.schemas.assessments import (
    AdvisoryOut,
    AssessmentListItemOut,
    AssessmentListOut,
    AssessmentResultOut,
    BilingualTextOut,
    BoundingBoxOut,
    ClassTallyOut,
    CompletedAssessmentOut,
    CompletedListItemOut,
    CoverageOut,
    DefectClassOut,
    DetectionOut,
    FailedAssessmentOut,
    FailedListItemOut,
    ImagesOut,
    LimitationOut,
    SummaryOut,
)
from app.services.assessment_service import AssessmentView


def _defect(defect: DefectClass) -> DefectClassOut:
    return DefectClassOut(key=defect.key, name=defect.name, category=defect.category)


def _result(view: AssessmentView, result: AssessmentResult) -> AssessmentResultOut:
    summary = result.summary
    # advisory = result.advisory
    return AssessmentResultOut(
        model_version=result.model_version,
        summary=SummaryOut(
            detection_count=summary.detection_count,
            primary_detection_count=summary.primary_count,
            secondary_detection_count=summary.secondary_count,
            by_class=[
                ClassTallyOut(
                    defect=_defect(tally.defect),
                    count=tally.count,
                    mean_confidence=tally.mean_confidence,
                )
                for tally in summary.by_class
            ],
        ),
        detections=[
            DetectionOut(
                defect=_defect(item.defect),
                confidence=item.confidence,
                box=BoundingBoxOut(x1=item.box.x1, y1=item.box.y1, x2=item.box.x2, y2=item.box.y2),
            )
            for item in result.detections
        ],
        coverage=CoverageOut(
            scanned=[_defect(c) for c in result.coverage.scanned],
            not_scanned=[_defect(c) for c in result.coverage.not_scanned],
        ),
        limitations=[
            LimitationOut(code=item.code, message=item.message)
            for item in limitations_for(result.coverage)
        ],
        # advisory=AdvisoryOut(
        #     generator_model=advisory.generator_model,
        #     summary=BilingualTextOut(en=advisory.summary.en, am=advisory.summary.am),
        #     recommendations=[
        #         BilingualTextOut(en=item.en, am=item.am) for item in advisory.recommendations
        #     ],
        # ),
        images=ImagesOut(
            original_url=view.original_image_url,
            annotated_url=view.annotated_image_url,
            expires_in_s=view.image_url_ttl_s,
        ),
    )


def to_assessment_out(view: AssessmentView) -> CompletedAssessmentOut | FailedAssessmentOut:
    assessment = view.assessment
    if assessment.result is not None:
        return CompletedAssessmentOut(
            assessment_id=assessment.assessment_id,
            created_at=assessment.created_at,
            processing_time_ms=assessment.processing_time_ms,
            result=_result(view, assessment.result),
        )
    if assessment.error_code is not None:
        return FailedAssessmentOut(
            assessment_id=assessment.assessment_id,
            created_at=assessment.created_at,
            processing_time_ms=assessment.processing_time_ms,
            error_code=assessment.error_code,
        )
    raise InvariantViolationError(
        f"assessment {assessment.assessment_id} has neither result nor error"
    )


def to_completed_out(view: AssessmentView) -> CompletedAssessmentOut:
    out = to_assessment_out(view)
    if not isinstance(out, CompletedAssessmentOut):
        raise InvariantViolationError(
            f"assessment {view.assessment.assessment_id} was expected to be completed"
        )
    return out


def _list_item(assessment: Assessment) -> CompletedListItemOut | FailedListItemOut:
    if assessment.result is not None:
        summary = assessment.result.summary
        return CompletedListItemOut(
            assessment_id=assessment.assessment_id,
            created_at=assessment.created_at,
            model_version=assessment.result.model_version,
            detection_count=summary.detection_count,
            primary_detection_count=summary.primary_count,
            secondary_detection_count=summary.secondary_count,
        )
    if assessment.error_code is not None:
        return FailedListItemOut(
            assessment_id=assessment.assessment_id,
            created_at=assessment.created_at,
            error_code=assessment.error_code,
        )
    raise InvariantViolationError(
        f"assessment {assessment.assessment_id} has neither result nor error"
    )


def to_list_out(page: AssessmentPage) -> AssessmentListOut:
    items: list[AssessmentListItemOut] = [_list_item(a) for a in page.items]
    return AssessmentListOut(items=items, next_cursor=page.next_cursor)
