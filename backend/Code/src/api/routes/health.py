"""Process, vector, and model health routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from ...config import AppConfig
from ..dependencies import ApiServices, get_api_services, get_config
from ..schemas.health import BackendHealth, ModelStatus


router = APIRouter(tags=["health"])


@router.get("/health", response_model=BackendHealth)
def health(
    request: Request,
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
):
    """Return process liveness plus safe dependency status."""
    return services.health(
        config,
        request.app.state.started_monotonic,
        api_version=request.app.version,
    )


@router.get("/api/model/status", response_model=ModelStatus)
def model_status(
    config: AppConfig = Depends(get_config),
    services: ApiServices = Depends(get_api_services),
):
    """Return safe model/provider status without requiring student identity."""
    return services.model_status(config)
