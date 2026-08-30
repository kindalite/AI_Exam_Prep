"""FastAPI application factory and local backend entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from time import monotonic

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .errors import register_exception_handlers
from .middleware import register_request_id_middleware
from .routes import chat, feedback, health, materials, study_tools, subjects


API_VERSION = "0.1.0"
LOCAL_FRONTEND_ORIGINS = ("http://localhost:8080", "http://127.0.0.1:8080")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Record process start metadata without probing optional dependencies."""
    app.state.started_monotonic = monotonic()
    app.state.started_at = datetime.now(timezone.utc).isoformat()
    yield


def create_app() -> FastAPI:
    """Build the local API with middleware, errors, and route modules."""
    api = FastAPI(
        title="Alim Study Assistant API",
        version=API_VERSION,
        description="Local Python AI/RAG backend for the Lovable frontend.",
        lifespan=lifespan,
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_FRONTEND_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Student-Id", "X-Request-Id"],
        expose_headers=["X-Request-Id"],
    )
    register_request_id_middleware(api)
    register_exception_handlers(api)
    api.include_router(health.router)
    api.include_router(subjects.router)
    api.include_router(materials.router)
    api.include_router(chat.router)
    api.include_router(study_tools.router)
    api.include_router(feedback.router)
    return api


app = create_app()
