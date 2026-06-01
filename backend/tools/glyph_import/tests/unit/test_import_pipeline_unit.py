from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config import AppConfig
from src.domain.models import ImportPipelineOptions
from src.pipelines.import_pipeline import (
    ImportPipelineError,
    run_batch_import_pipeline,
    run_import_pipeline,
)


def test_run_import_pipeline_returns_full_result(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = config.project_root / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    source_path = input_dir / "A.jpg"
    source_path.write_bytes((Path(__file__).resolve().parents[2] / "input" / "raw" / "A.jpg").read_bytes())

    result = run_import_pipeline(
        input_path=source_path,
        char="A",
        config=config,
        options=ImportPipelineOptions(fill_threshold=0.35),
    )

    assert result.options.fill_threshold == 0.35
    assert result.loaded_image.path == source_path.resolve()
    assert result.grid_result.column_count > 0
    assert result.grid_result.row_count > 0
    assert result.exported_glyph.output_path == config.json_dir / "A.json"
    assert result.preview_result.output_path == config.previews_dir / "A.png"
    payload = json.loads(result.exported_glyph.output_path.read_text(encoding="utf-8"))
    assert payload["char"] == "A"


def test_run_import_pipeline_wraps_stage_errors(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)

    with pytest.raises(ImportPipelineError, match="Image file does not exist"):
        run_import_pipeline(
            input_path=config.project_root / "input" / "raw" / "missing.jpg",
            char="A",
            config=config,
            options=ImportPipelineOptions(fill_threshold=0.35),
        )


def test_run_batch_import_pipeline_collects_successes_and_failures(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    config.extracted_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    (config.extracted_dir / "A.jpg").write_bytes((source_root / "A.jpg").read_bytes())
    (config.extracted_dir / "Z.jpg").write_bytes(b"not-a-real-jpg")

    summary = run_batch_import_pipeline(
        config=config,
        options=ImportPipelineOptions(fill_threshold=0.35),
    )

    assert summary.processed_count == 2
    assert summary.input_dir == config.extracted_dir
    assert summary.success_count == 1
    assert summary.failure_count == 1
    assert summary.items[0].char == "A"
    assert summary.items[0].success is True
    assert summary.items[1].char == "Z"
    assert summary.items[1].success is False
    assert summary.items[1].error_message is not None
