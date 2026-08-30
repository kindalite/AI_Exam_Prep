"""Request-correlation middleware for the local FastAPI application."""

from __future__ import annotations

import re
import uuid

from fastapi import FastAPI, Request


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def valid_request_id(value: str | None) -> bool:
    """Return whether a caller-supplied request ID is safe to echo/log."""
    return bool(value and REQUEST_ID_PATTERN.fullmatch(value))


def register_request_id_middleware(app: FastAPI) -> None:
    """Attach a safe request ID to state and every response."""

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        incoming = request.headers.get("X-Request-Id")
        request_id = incoming if valid_request_id(incoming) else f"req_{uuid.uuid4().hex}"
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

