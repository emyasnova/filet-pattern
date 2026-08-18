"""Endpoints for detecting filet chart dimensions."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.schemas.image_size import ImageSizeResponse
from app.domain.services.image_size_service import (
    ImageSizeDetectionError,
    get_image_grid_size,
)
from app.core.uploads import UploadTooLargeError, read_limited_upload

router = APIRouter(prefix="/api/v1/images", tags=["images"])


@router.post("/size", response_model=ImageSizeResponse)
async def detect_image_size(file: UploadFile = File(...)) -> ImageSizeResponse:
    """Return the uploaded filet chart's dimensions in grid cells."""
    try:
        image_size = get_image_grid_size(
            await read_limited_upload(file), file.filename or ""
        )
    except UploadTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except ImageSizeDetectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    return ImageSizeResponse(width=image_size.width, height=image_size.height)
