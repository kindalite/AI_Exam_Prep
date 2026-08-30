"""API-safe domain errors and standard FastAPI exception handlers."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


@dataclass
class ApiDomainError(Exception):
    """Known domain failure that can be returned without leaking internals."""

    code: str
    message: str
    detail: str = ""
    retryable: bool = False
    status_code: int = 400


class ModelUnavailableError(ApiDomainError):
    """Model provider is temporarily unavailable."""


class VectorUnavailableError(ApiDomainError):
    """Vector storage is temporarily unavailable."""


class FileMediaError(ApiDomainError):
    """Uploaded file or optional media processing failed."""


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "req_unknown"))


def error_response(
    request: Request,
    *,
    code: str,
    message: str,
    detail: str,
    retryable: bool,
    status_code: int,
) -> JSONResponse:
    """Return the standard error envelope for every API failure."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "detail": detail,
                "retryable": retryable,
                "request_id": _request_id(request),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register safe handlers for validation, domain, file, HTTP, and unknown errors."""

    @app.exception_handler(ApiDomainError)
    async def handle_domain_error(request: Request, exc: ApiDomainError) -> JSONResponse:
        return error_response(
            request,
            code=exc.code,
            message=exc.message,
            detail=exc.detail,
            retryable=exc.retryable,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return error_response(
            request,
            code="validation_error",
            message="The request did not match the API contract.",
            detail=str(exc),
            retryable=False,
            status_code=422,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return error_response(
            request,
            code=code,
            message=str(exc.detail),
            detail="",
            retryable=False,
            status_code=exc.status_code,
        )

    @app.exception_handler(OSError)
    async def handle_file_error(request: Request, exc: OSError) -> JSONResponse:
        return error_response(
            request,
            code="file_media_error",
            message="A local file or media operation failed.",
            detail=exc.__class__.__name__,
            retryable=False,
            status_code=400,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(
            request,
            code="internal_error",
            message="The backend could not complete the request.",
            detail="Unexpected internal error.",
            retryable=True,
            status_code=500,
        )

