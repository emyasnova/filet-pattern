"""Health check endpoints."""

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.schemas.health import HealthResponse
from app.domain.services.health_service import get_health_status
from app.infrastructure.database.session import get_database_session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    """Return service health status."""
    return get_health_status()


@router.get("/ready", response_model=HealthResponse)
def readiness(
    response: Response, session: Session = Depends(get_database_session)
) -> HealthResponse:
    """Report readiness only after a database round trip succeeds."""
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable")
    return HealthResponse(status="ok")
