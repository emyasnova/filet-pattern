"""API schemas for the persisted pattern catalog."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PatternCell = Literal[0, 1] | None


class PatternResponse(BaseModel):
    """Pattern returned to frontend clients."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    category: str
    tags: list[str]
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    cells: list[list[PatternCell]]
    created_at: datetime


class PatternPreviewResponse(BaseModel):
    """Editable matrix generated from an uploaded chart image."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(gt=0)
    height: int = Field(gt=0)
    threshold: int = Field(ge=0, le=255)
    fill_threshold: float = Field(ge=0, le=1)
    cells: list[list[PatternCell]]


class PatternCreateRequest(BaseModel):
    """Validated payload for saving an edited pattern."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=100)
    width: int = Field(gt=0, le=500)
    height: int = Field(gt=0, le=500)
    cells: list[list[PatternCell]]

    @field_validator("name", "category")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        """Reject values containing only whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        """Trim and case-insensitively deduplicate tag names."""
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            stripped = value.strip()
            if not stripped:
                continue
            if len(stripped) > 128:
                raise ValueError("tag names must not exceed 128 characters")
            normalized = stripped.casefold()
            if normalized not in seen:
                seen.add(normalized)
                result.append(stripped)
        return result

    @model_validator(mode="after")
    def validate_matrix_dimensions(self) -> "PatternCreateRequest":
        """Ensure the matrix is rectangular and matches declared dimensions."""
        if len(self.cells) != self.height:
            raise ValueError("cells row count must equal height")
        if any(len(row) != self.width for row in self.cells):
            raise ValueError("every cells row length must equal width")
        return self


class CategoryResponse(BaseModel):
    """Public category descriptor."""

    model_config = ConfigDict(extra="forbid")

    slug: str
    name: str


class TagResponse(BaseModel):
    """Public tag descriptor."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
