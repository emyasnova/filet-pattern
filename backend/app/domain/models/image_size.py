"""Domain models for chart image size detection."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ImageGridSize:
    """Detected chart dimensions measured in grid cells."""

    width: int
    height: int
