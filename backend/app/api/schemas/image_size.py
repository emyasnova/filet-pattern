"""Schemas for chart image size endpoints."""

from pydantic import BaseModel, ConfigDict, PositiveInt


class ImageSizeResponse(BaseModel):
    """Detected chart dimensions measured in cells."""

    model_config = ConfigDict(extra="forbid")

    width: PositiveInt
    height: PositiveInt
