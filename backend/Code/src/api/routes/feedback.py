"""Student-isolated, privacy-minimal feedback endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends

from ...config import AppConfig
from ...services.identity_service import StudentContext
from ..dependencies import ApiServices, get_api_services, get_config, get_student_context
from ..errors import ApiDomainError
from ..schemas.feedback import FeedbackEntry, FeedbackResponse

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackEntry,
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> FeedbackResponse:
    """Append feedback without copying referenced prompt or answer content."""
    try:
        row = services.feedback(**payload.model_dump(), student=student, config=config)
    except OSError as exc:
        raise ApiDomainError(
            "feedback_storage_failed",
            "Feedback could not be stored locally.",
            exc.__class__.__name__,
            True,
            503,
        ) from exc
    return FeedbackResponse(
        feedback_id=str(row["feedback_id"]),
        created_at=datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00")),
    )
