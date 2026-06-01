"""Schemas for scheme generation API contract."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RangeSchema(BaseModel):
    """Inclusive min/max range constraints."""

    model_config = ConfigDict(extra="forbid")

    min: int = Field(..., ge=1)
    max: int = Field(..., ge=1)


class SchemeConstraintsSchema(BaseModel):
    """Scheme size constraints."""

    model_config = ConfigDict(extra="forbid")

    width: RangeSchema
    height: RangeSchema


class SymbolConstraintsSchema(BaseModel):
    """Symbol size constraints."""

    model_config = ConfigDict(extra="forbid")

    width: RangeSchema
    height: RangeSchema


class GenerateSchemeRequest(BaseModel):
    """Request model for scheme generation."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    scheme: SchemeConstraintsSchema
    symbol: SymbolConstraintsSchema


CellValue = Literal[0, 1] | None


class GenerateSchemeResponse(BaseModel):
    """Response model for scheme generation."""

    model_config = ConfigDict(extra="forbid")

    width: int = Field(..., ge=1)
    height: int = Field(..., ge=1)
    cells: list[list[CellValue]]
    meta: dict[str, Any]


class ErrorBodySchema(BaseModel):
    """Error details returned by the API."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Wrapper for API errors."""

    model_config = ConfigDict(extra="forbid")

    error: ErrorBodySchema
