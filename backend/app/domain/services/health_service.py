"""Health-related application services."""

from app.api.schemas.health import HealthResponse


def get_health_status() -> HealthResponse:
    """Return the current backend health status."""
    return HealthResponse(status="ok")
