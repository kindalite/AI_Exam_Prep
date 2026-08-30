"""Safe user-scoped document import and indexing route."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from ...config import AppConfig
from ...services.identity_service import StudentContext
from ...services.upload_service import (
    DocumentParseError,
    FileTooLargeError,
    IndexBusyError,
    IndexingFailedError,
    UnsupportedMediaTypeError,
)
from ..dependencies import ApiServices, get_api_services, get_config, get_student_context
from ..errors import ApiDomainError
from ..schemas.adapters import document_import_to_response
from ..schemas.materials import DocumentImportResponse

router = APIRouter(prefix="/api", tags=["materials"])


@router.post("/import/document", response_model=DocumentImportResponse)
def import_document(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    component_subject_id: str | None = Form(default=None),
    section: str = Form(...),
    language: str = Form(...),
    student: StudentContext = Depends(get_student_context),
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
) -> DocumentImportResponse:
    """Stream, parse, and rebuild only the identified student's corpus."""
    try:
        result = services.import_document(
            stream=file.file,
            original_name=file.filename or "material",
            content_type=file.content_type,
            subject_id=subject_id,
            component_subject_id=component_subject_id,
            section=section,
            language=language,
            student=student,
            config=config,
        )
        return document_import_to_response(result)
    except FileTooLargeError as exc:
        raise ApiDomainError("file_too_large", "The uploaded file is too large.", str(exc), False, 413) from exc
    except UnsupportedMediaTypeError as exc:
        raise ApiDomainError("unsupported_media_type", "This file type is not supported.", str(exc), False, 415) from exc
    except DocumentParseError as exc:
        raise ApiDomainError("parse_failed", "The document could not be parsed.", str(exc), False, 422) from exc
    except IndexBusyError as exc:
        raise ApiDomainError("index_busy", "This subject index is already being rebuilt.", str(exc), True, 409) from exc
    except IndexingFailedError as exc:
        raise ApiDomainError("vector_unavailable", "The user-scoped index rebuild failed.", str(exc), True, 503) from exc
    except ValueError as exc:
        raise ApiDomainError("validation_error", "The upload fields are invalid.", str(exc), False, 422) from exc
