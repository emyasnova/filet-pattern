from __future__ import annotations

import json
from pathlib import Path

from src.config import AppConfig
from src.domain.models import ImportPipelineOptions
from src.main import run
from src.pipelines.import_pipeline import run_batch_import_pipeline, run_import_pipeline


def test_cli_exports_glyph_json(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = config.project_root / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    source_path = input_dir / "A.jpg"
    source_path.write_bytes((Path(__file__).resolve().parents[2] / "input" / "raw" / "A.jpg").read_bytes())

    monkeypatch.setattr("src.main.get_default_config", lambda: config)

    exit_code = run(["--input", "input/raw/A.jpg", "--char", "A", "--dry-run"])

    assert exit_code == 0
    exported_path = config.json_dir / "A.json"
    assert exported_path.exists()
    payload = json.loads(exported_path.read_text(encoding="utf-8"))
    assert payload["char"] == "A"
    assert payload["width"] > 0
    assert payload["height"] > 0
    assert len(payload["cells"]) == payload["height"]
    assert len(payload["cells"][0]) == payload["width"]
    preview_path = config.previews_dir / "A.png"
    assert preview_path.exists()


def test_pipeline_exports_json_and_preview(tmp_path: Path) -> None:
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

    assert result.exported_glyph.output_path.exists()
    assert result.preview_result.output_path.exists()


def test_batch_pipeline_exports_multiple_files(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = config.extracted_dir
    input_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    (input_dir / "A.jpg").write_bytes((source_root / "A.jpg").read_bytes())
    (input_dir / "B.jpg").write_bytes((source_root / "B.jpg").read_bytes())

    summary = run_batch_import_pipeline(
        config=config,
        options=ImportPipelineOptions(fill_threshold=0.35),
    )

    assert summary.success_count == 2
    assert summary.failure_count == 0
    assert (config.json_dir / "A.json").exists()
    assert (config.json_dir / "B.json").exists()
    assert (config.previews_dir / "A.png").exists()
    assert (config.previews_dir / "B.png").exists()


def test_pipeline_classifies_last_row_of_f_consistently(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = config.project_root / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    source_path = input_dir / "F.jpg"
    source_path.write_bytes((source_root / "F.jpg").read_bytes())

    result = run_import_pipeline(
        input_path=source_path,
        char="F",
        config=config,
        options=ImportPipelineOptions(fill_threshold=0.35),
    )

    assert result.classification_result.matrix[-1] == (
        0,
        0,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )


def test_pipeline_classifies_last_row_of_j_consistently(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = config.project_root / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    source_path = input_dir / "J.jpg"
    source_path.write_bytes((source_root / "J.jpg").read_bytes())

    result = run_import_pipeline(
        input_path=source_path,
        char="J",
        config=config,
        options=ImportPipelineOptions(fill_threshold=0.35),
    )

    assert result.classification_result.matrix[-1] == (
        0,
        0,
        1,
        1,
        1,
        1,
        1,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
