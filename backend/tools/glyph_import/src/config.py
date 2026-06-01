"""Configuration for the glyph import tool."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Filesystem configuration used by the CLI skeleton."""

    project_root: Path
    input_dir: Path
    prepared_dir: Path
    samples_dir: Path
    extracted_dir: Path
    input_debug_dir: Path
    previews_dir: Path
    json_dir: Path
    manifests_dir: Path
    debug_dir: Path
    log_file: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppConfig":
        """Build config paths relative to the project root."""
        resolved_root = project_root.resolve()
        return cls(
            project_root=resolved_root,
            input_dir=resolved_root / "input" / "raw",
            prepared_dir=resolved_root / "input" / "prepared",
            samples_dir=resolved_root / "input" / "samples",
            extracted_dir=resolved_root / "input" / "extracted",
            input_debug_dir=resolved_root / "input" / "debug",
            previews_dir=resolved_root / "output" / "previews",
            json_dir=resolved_root / "output" / "json",
            manifests_dir=resolved_root / "output" / "manifests",
            debug_dir=resolved_root / "output" / "debug",
            log_file=resolved_root / "output" / "debug" / "glyph_import.log",
        )


def get_default_config() -> AppConfig:
    """Return config for the current project layout."""
    return AppConfig.from_project_root(Path(__file__).resolve().parent.parent)
