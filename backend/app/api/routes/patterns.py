"""Endpoints for browsing, previewing, and creating persisted patterns."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.schemas.patterns import (
    CategoryResponse,
    PatternCreateRequest,
    PatternPreviewResponse,
    PatternResponse,
    TagResponse,
)
from app.core.uploads import UploadTooLargeError, read_limited_upload
from app.domain.services.pattern_service import (
    create_pattern,
    generate_pattern_preview,
    get_categories,
    get_patterns,
    get_tags,
)
from app.infrastructure.database.pattern_repository import PatternRepository
from app.infrastructure.database.session import get_database_session
from tools.glyph_import.src.pipelines.in_memory_import_pipeline import InMemoryImportError

router = APIRouter(prefix="/api/v1", tags=["patterns"])
DatabaseSession = Annotated[Session, Depends(get_database_session)]


@router.get("/patterns", response_model=list[PatternResponse])
def list_patterns(
    session: DatabaseSession,
    search: str | None = None,
    category: str | None = None,
    tags: Annotated[list[str] | None, Query()] = None,
) -> list[PatternResponse]:
    """Return newest patterns matching optional search filters."""
    return get_patterns(PatternRepository(session), search, category, tags)


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(session: DatabaseSession) -> list[CategoryResponse]:
    """Return all available pattern categories."""
    return get_categories(PatternRepository(session))


@router.get("/tags", response_model=list[TagResponse])
def list_tags(session: DatabaseSession) -> list[TagResponse]:
    """Return all available pattern tags."""
    return get_tags(PatternRepository(session))


@router.post("/patterns/preview", response_model=PatternPreviewResponse)
async def preview_pattern(
    file: UploadFile = File(...),
    width: int = Form(..., ge=1, le=500),
    height: int = Form(..., ge=1, le=500),
    threshold: int = Form(128, ge=0, le=255),
    fill_threshold: float = Form(0.35, ge=0, le=1),
) -> PatternPreviewResponse:
    """Build an editable matrix from an uploaded chart image."""
    try:
        return generate_pattern_preview(
            image_bytes=await read_limited_upload(file),
            filename=file.filename or "",
            width=width,
            height=height,
            threshold=threshold,
            fill_threshold=fill_threshold,
        )
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=str(exc)) from exc
    except InMemoryImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.post(
    "/patterns",
    response_model=PatternResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_pattern(
    request: PatternCreateRequest,
    session: DatabaseSession,
) -> PatternResponse:
    """Persist an edited pattern and create any missing tags."""
    try:
        return create_pattern(PatternRepository(session), request)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
