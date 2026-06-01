"""Schemas for health endpoints."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    """Response model for the health check endpoint."""

    model_config = ConfigDict(extra="forbid")

    status: str
