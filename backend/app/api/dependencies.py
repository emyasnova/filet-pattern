"""Shared API authorization dependencies."""

from fastapi import Depends, HTTPException, status

from app.core.config import get_settings


def require_pattern_creation(settings=Depends(get_settings)) -> None:
    """Reject expensive import work before request files are consumed."""
    if not settings.pattern_creation_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pattern creation is currently unavailable",
        )
