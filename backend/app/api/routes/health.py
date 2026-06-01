"""Health check endpoints."""

from fastapi import APIRouter

from app.api.schemas.health import HealthResponse
from app.domain.services.health_service import get_health_status

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    """Return service health status."""
    return get_health_status()
