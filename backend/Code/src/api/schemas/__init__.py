"""Pydantic wire-contract models for the Lovable frontend."""

from .chat import ChatRequest, ChatResponse, RetrievalSummary, SourceSnippet
from .common import APIError, APIErrorDetail, LanguageCode
from .feedback import FeedbackEntry, FeedbackResponse
from .grading import GradingRequest, GradingResult
from .health import BackendHealth, ModelStatus
from .materials import DocumentImportResponse, MaterialModel, MaterialSourceModel
from .mock_exam import MockExam, MockExamQuestion, MockExamRequest
from .quiz import Quiz, QuizQuestion, QuizRequest
from .study_plan import AvailableTimeSlot, StudyPlan, StudyPlanItem, StudyPlanRequest
from .subjects import LearningGoalModel, SubjectComponentModel, SubjectModel

__all__ = [
    "APIError",
    "APIErrorDetail",
    "BackendHealth",
    "AvailableTimeSlot",
    "ChatRequest",
    "ChatResponse",
    "FeedbackEntry",
    "FeedbackResponse",
    "GradingRequest",
    "GradingResult",
    "LanguageCode",
    "LearningGoalModel",
    "MaterialModel",
    "MaterialSourceModel",
    "DocumentImportResponse",
    "MockExam",
    "MockExamQuestion",
    "MockExamRequest",
    "ModelStatus",
    "Quiz",
    "QuizQuestion",
    "QuizRequest",
    "RetrievalSummary",
    "SourceSnippet",
    "StudyPlan",
    "StudyPlanItem",
    "StudyPlanRequest",
    "SubjectComponentModel",
    "SubjectModel",
]
