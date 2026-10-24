"""Domain objects -> public API models. The only place the two vocabularies meet."""

from app.domain.analysis import limitations_for
from app.domain.errors import InvariantViolationError
from app.domain.models import Assessment, AssessmentPage, AssessmentResult
from app.domain.operations import (
    ModelReloadResult,
    ModelVersionUsage,
    OperationalLimits,
    OutcomeOverview,
)
from app.domain.taxonomy import DefectClass
from app.domain.users import User
from app.schemas.admin import (
    AdminAssessmentListOut,
    AdminAssessmentOut,
    LimitsOut,
    ModelReloadOut,
    ModelVersionsOut,
    ModelVersionUsageOut,
    OutcomeCountOut,
    OverviewOut,
)
from app.schemas.assessments import (
    AdvisoryOut,
    AssessmentListItemOut,
    AssessmentListOut,
    AssessmentOut,
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
    ImageCheckOut,
    ImagesOut,
    LimitationOut,
    SummaryOut,
)
from app.schemas.auth import TokenOut, UserOut
from app.services.assessment_service import AssessmentView
from app.services.ports import IssuedToken


def _defect(defect: DefectClass) -> DefectClassOut:
    return DefectClassOut(key=defect.key, name=defect.name, category=defect.category)


def _result(view: AssessmentView, result: AssessmentResult) -> AssessmentResultOut:
    summary = result.summary
    advisory = result.advisory
    return AssessmentResultOut(
        model_version=result.model_version,
        image_check=ImageCheckOut(
            coffee_confidence=result.image_check.coffee_confidence,
            validator_version=result.image_check.validator_version,
        ),
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
        advisory=AdvisoryOut(
            generator_model=advisory.generator_model,
            summary=BilingualTextOut(en=advisory.summary.en, am=advisory.summary.am),
            recommendations=[
                BilingualTextOut(en=item.en, am=item.am) for item in advisory.recommendations
            ],
        ),
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
    raise InvariantViolationError(f"assessment {assessment.assessment_id} has neither result nor error")


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
    raise InvariantViolationError(f"assessment {assessment.assessment_id} has neither result nor error")


def to_list_out(page: AssessmentPage) -> AssessmentListOut:
    items: list[AssessmentListItemOut] = [_list_item(a) for a in page.items]
    return AssessmentListOut(items=items, next_cursor=page.next_cursor)


def to_user_out(user: User) -> UserOut:
    return UserOut(
        user_id=user.user_id, email=user.email, role=user.role, created_at=user.created_at
    )


def to_token_out(token: IssuedToken) -> TokenOut:
    return TokenOut(access_token=token.access_token, expires_in_s=token.expires_in_s)


def _admin_item(assessment: Assessment) -> AdminAssessmentOut:
    result = assessment.result
    return AdminAssessmentOut(
        assessment_id=assessment.assessment_id,
        owner_id=assessment.owner_id,
        status=assessment.status,
        created_at=assessment.created_at,
        processing_time_ms=assessment.processing_time_ms,
        error_code=assessment.error_code,
        model_version=None if result is None else result.model_version,
        validator_version=None if result is None else result.image_check.validator_version,
        detection_count=None if result is None else result.summary.detection_count,
    )


def to_admin_assessment_out(assessment: Assessment) -> AdminAssessmentOut:
    return _admin_item(assessment)


def to_admin_list_out(page: AssessmentPage) -> AdminAssessmentListOut:
    return AdminAssessmentListOut(
        items=[_admin_item(a) for a in page.items], next_cursor=page.next_cursor
    )


def to_model_versions_out(usage: tuple[ModelVersionUsage, ...]) -> ModelVersionsOut:
    return ModelVersionsOut(
        versions=[
            ModelVersionUsageOut(
                model_version=u.model_version,
                validator_version=u.validator_version,
                assessments=u.assessments,
                first_seen=u.first_seen,
                last_seen=u.last_seen,
            )
            for u in usage
        ]
    )


def to_overview_out(overview: OutcomeOverview) -> OverviewOut:
    return OverviewOut(
        since=overview.since,
        window_hours=overview.window_hours,
        outcomes=[
            OutcomeCountOut(status=o.status, error_code=o.error_code, count=o.count)
            for o in overview.outcomes
        ],
    )


def to_limits_out(limits: OperationalLimits) -> LimitsOut:
    return LimitsOut(
        max_image_bytes=limits.max_image_bytes,
        max_image_pixels=limits.max_image_pixels,
        min_image_side_px=limits.min_image_side_px,
        max_assessments_per_user_per_hour=limits.max_assessments_per_user_per_hour,
        max_concurrent_assessments=limits.max_concurrent_assessments,
        vision_timeout_s=limits.vision_timeout_s,
        gemini_timeout_s=limits.gemini_timeout_s,
        image_url_ttl_s=limits.image_url_ttl_s,
        retain_original_image=limits.retain_original_image,
    )


def to_model_reload_out(result: ModelReloadResult) -> ModelReloadOut:
    return ModelReloadOut(reloaded=result.reloaded, engine=result.engine)


__all__ = [
    "AssessmentOut",
    "to_admin_assessment_out",
    "to_admin_list_out",
    "to_assessment_out",
    "to_completed_out",
    "to_limits_out",
    "to_list_out",
    "to_model_reload_out",
    "to_model_versions_out",
    "to_overview_out",
    "to_token_out",
    "to_user_out",
]
