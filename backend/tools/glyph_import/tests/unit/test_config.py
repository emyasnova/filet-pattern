from __future__ import annotations

from pathlib import Path

from src.config import AppConfig


def test_config_builds_expected_paths(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)

    assert config.project_root == tmp_path.resolve()
    assert config.input_dir == tmp_path / "input" / "raw"
    assert config.prepared_dir == tmp_path / "input" / "prepared"
    assert config.samples_dir == tmp_path / "input" / "samples"
    assert config.extracted_dir == tmp_path / "input" / "extracted"
    assert config.input_debug_dir == tmp_path / "input" / "debug"
    assert config.previews_dir == tmp_path / "output" / "previews"
    assert config.json_dir == tmp_path / "output" / "json"
    assert config.manifests_dir == tmp_path / "output" / "manifests"
    assert config.debug_dir == tmp_path / "output" / "debug"
    assert config.log_file == tmp_path / "output" / "debug" / "glyph_import.log"
