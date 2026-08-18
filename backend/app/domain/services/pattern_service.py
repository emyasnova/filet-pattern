"""Application service for reading pattern catalog data."""

from app.api.schemas.patterns import (
    CategoryResponse,
    PatternCreateRequest,
    PatternPreviewResponse,
    PatternResponse,
    TagResponse,
)
from app.domain.services.pattern_cells import normalize_pattern_transparency
from app.infrastructure.database.pattern_repository import PatternRepository
from tools.glyph_import.src.domain.models import ImportPipelineOptions
from tools.glyph_import.src.pipelines.in_memory_import_pipeline import (
    InMemoryImportError,
    build_pattern_matrix_from_bytes,
)


def get_patterns(
    repository: PatternRepository,
    search: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
) -> list[PatternResponse]:
    """Return API patterns matching the supplied filters."""
    return [
        PatternResponse(
            id=pattern.id,
            name=pattern.name,
            category=pattern.category.slug,
            tags=[tag.name for tag in pattern.tags],
            width=pattern.width,
            height=pattern.height,
            cells=pattern.cells,
            created_at=pattern.created_at,
        )
        for pattern in repository.list_patterns(search, category, tags)
    ]


def get_categories(repository: PatternRepository) -> list[CategoryResponse]:
    """Return available pattern categories."""
    return [
        CategoryResponse(slug=category.slug, name=category.name)
        for category in repository.list_categories()
    ]


def get_tags(repository: PatternRepository) -> list[TagResponse]:
    """Return available pattern tags."""
    return [TagResponse(id=tag.id, name=tag.name) for tag in repository.list_tags()]


def generate_pattern_preview(
    *,
    image_bytes: bytes,
    filename: str,
    width: int,
    height: int,
    threshold: int,
    fill_threshold: float,
) -> PatternPreviewResponse:
    """Generate a transparent editable matrix from uploaded image bytes."""
    result = build_pattern_matrix_from_bytes(
        content=image_bytes,
        filename=filename,
        options=ImportPipelineOptions(
            threshold=threshold,
            fill_threshold=fill_threshold,
            expected_columns=width,
            expected_rows=height,
        ),
    )
    cells = normalize_pattern_transparency([list(row) for row in result.matrix])
    return PatternPreviewResponse(
        width=result.width,
        height=result.height,
        threshold=threshold,
        fill_threshold=fill_threshold,
        cells=cells,
    )


def create_pattern(
    repository: PatternRepository,
    request: PatternCreateRequest,
) -> PatternResponse:
    """Normalize and persist a user-edited pattern."""
    cells = normalize_pattern_transparency(request.cells)
    try:
        pattern = repository.create_pattern(
            name=request.name,
            category_slug=request.category,
            tag_names=request.tags,
            width=request.width,
            height=request.height,
            cells=cells,
        )
    except Exception:
        repository.rollback()
        raise
    return PatternResponse(
        id=pattern.id,
        name=pattern.name,
        category=pattern.category.slug,
        tags=[tag.name for tag in pattern.tags],
        width=pattern.width,
        height=pattern.height,
        cells=pattern.cells,
        created_at=pattern.created_at,
    )
