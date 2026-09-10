"""Public runtime configuration used by the frontend."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["config"])


class PublicConfigResponse(BaseModel):
    """Non-sensitive feature switches safe to expose publicly."""

    patternCreationEnabled: bool


@router.get("/config", response_model=PublicConfigResponse)
def public_config(settings=Depends(get_settings)) -> PublicConfigResponse:
    """Return browser-visible application settings."""
    return PublicConfigResponse(
        patternCreationEnabled=settings.pattern_creation_enabled
    )
