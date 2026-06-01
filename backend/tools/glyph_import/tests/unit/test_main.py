from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.config import AppConfig
from src.main import build_parser, run


def test_parser_reads_basic_cli_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--input",
            "input/raw/A.jpg",
            "--char",
            "A",
            "--dry-run",
            "--fill-threshold",
            "0.4",
            "--threshold",
            "140",
            "--no-denoise",
            "--denoise-size",
            "5",
            "--min-grid-step",
            "5",
            "--max-grid-step",
            "30",
            "--expected-columns",
            "46",
            "--expected-rows",
            "37",
            "--preview-cell-size",
            "20",
            "--debug",
        ]
    )

    assert args.input.parts[-3:] == ("input", "raw", "A.jpg")
    assert args.char == "A"
    assert args.dry_run is True
    assert args.fill_threshold == 0.4
    assert args.threshold == 140
    assert args.no_denoise is True
    assert args.denoise_size == 5
    assert args.min_grid_step == 5
    assert args.max_grid_step == 30
    assert args.expected_columns == 46
    assert args.expected_rows == 37
    assert args.preview_cell_size == 20
    assert args.debug is True


def test_parser_reads_batch_argument() -> None:
    parser = build_parser()

    args = parser.parse_args(["--batch"])

    assert args.batch is True


def test_parser_reads_extraction_arguments() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "--extract",
            "--input",
            "input/raw/sheet.png",
            "--min-symbol-width",
            "10",
            "--min-symbol-height",
            "11",
            "--min-symbol-area",
            "120",
            "--crop-padding",
            "3",
        ]
    )

    assert args.extract is True
    assert args.input.parts[-3:] == ("input", "raw", "sheet.png")
    assert args.min_symbol_width == 10
    assert args.min_symbol_height == 11
    assert args.min_symbol_area == 120
    assert args.crop_padding == 3


def test_run_requires_input_argument() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--char", "A"])

    assert exc_info.value.code == 2


def test_run_requires_char_argument() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg"])

    assert exc_info.value.code == 2


def test_run_rejects_input_in_batch_mode() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--batch", "--input", "input/raw/A.jpg"])

    assert exc_info.value.code == 2


def test_run_rejects_char_in_batch_mode() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--batch", "--char", "A"])

    assert exc_info.value.code == 2


def test_run_rejects_batch_in_extraction_mode() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--extract", "--batch"])

    assert exc_info.value.code == 2


def test_run_rejects_char_in_extraction_mode() -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--extract", "--input", "input/raw/A.jpg", "--char", "A"])

    assert exc_info.value.code == 2


def test_run_prints_pipeline_status(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = run(["--input", "input/raw/A.jpg", "--char", "A", "--dry-run"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Character: A" in captured.out
    assert "Image format: jpg" in captured.out
    assert "Binary debug image:" in captured.out
    assert "Grid debug image:" in captured.out
    assert "Grid size:" in captured.out
    assert "Extracted cells:" in captured.out
    assert "First cell:" in captured.out
    assert "Fill threshold:" in captured.out
    assert "Classification matrix size:" in captured.out
    assert "First matrix row:" in captured.out
    assert "Trimmed glyph matrix size:" in captured.out
    assert "Trimmed first row:" in captured.out
    assert "Glyph char: A" in captured.out
    assert "Glyph size:" in captured.out
    assert "Exported JSON:" in captured.out
    assert "Preview image:" in captured.out
    assert "Import pipeline completed." in captured.out


def test_run_prints_debug_status_when_enabled(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = run(["--input", "input/raw/A.jpg", "--char", "A", "--debug"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Debug mode: enabled" in captured.out
    assert "Preprocess threshold:" in captured.out
    assert "Denoise enabled:" in captured.out
    assert "Denoise filter size:" in captured.out
    assert "Grid step range:" in captured.out
    assert "Preview cell size:" in captured.out


def test_run_writes_logs_to_debug_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = AppConfig.from_project_root(tmp_path)

    monkeypatch.setattr("src.main.get_default_config", lambda: config)

    exit_code = run(["--input", "input/raw/A.jpg", "--char", "A", "--dry-run"])

    assert exit_code == 0
    assert config.log_file.exists()
    contents = config.log_file.read_text(encoding="utf-8")
    assert "Import pipeline completed." in contents
    assert "Character: A" in contents
    assert "Image format: jpg" in contents
    assert (config.debug_dir / "A_grayscale.png").exists()
    assert (config.debug_dir / "A_denoised.png").exists()
    assert (config.debug_dir / "A_binary.png").exists()
    assert (config.debug_dir / "A_grid.png").exists()
    assert (config.json_dir / "A.json").exists()
    assert (config.previews_dir / "A.png").exists()
    assert "Extracted cells:" in contents
    assert "Fill threshold:" in contents
    assert "First matrix row:" in contents
    assert "Trimmed glyph matrix size:" in contents
    assert "Glyph char: A" in contents
    assert "Exported JSON:" in contents
    assert "Preview image:" in contents


def test_run_batch_processes_all_supported_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = AppConfig.from_project_root(tmp_path)
    config.extracted_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    (config.extracted_dir / "A.jpg").write_bytes((source_root / "A.jpg").read_bytes())
    (config.extracted_dir / "B.jpg").write_bytes((source_root / "B.jpg").read_bytes())
    (config.extracted_dir / "ignore.txt").write_text("skip", encoding="utf-8")
    (config.extracted_dir / "sheet1_001.png").write_bytes((source_root / "A.jpg").read_bytes())

    monkeypatch.setattr("src.main.get_default_config", lambda: config)

    exit_code = run(["--batch"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Batch input dir: {config.extracted_dir}" in captured.out
    assert "Batch processed files: 2" in captured.out
    assert "Batch successful files: 2" in captured.out
    assert "Batch failed files: 0" in captured.out
    assert "Batch item OK: char=A" in captured.out
    assert "Batch item OK: char=B" in captured.out
    assert (config.json_dir / "A.json").exists()
    assert (config.json_dir / "B.json").exists()
    assert (config.previews_dir / "A.png").exists()
    assert (config.previews_dir / "B.png").exists()


def test_run_batch_reports_item_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = AppConfig.from_project_root(tmp_path)
    config.extracted_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parents[2] / "input" / "raw"
    (config.extracted_dir / "A.jpg").write_bytes((source_root / "A.jpg").read_bytes())
    (config.extracted_dir / "Z.jpg").write_bytes(b"not-a-real-jpg")

    monkeypatch.setattr("src.main.get_default_config", lambda: config)

    exit_code = run(["--batch"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Batch processed files: 2" in captured.out
    assert "Batch successful files: 1" in captured.out
    assert "Batch failed files: 1" in captured.out
    assert "Batch item ERROR: char=Z" in captured.out


def test_run_extraction_prints_status_and_writes_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = AppConfig.from_project_root(tmp_path)
    source_path = tmp_path / "input" / "raw" / "sheet.png"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    _create_two_symbol_image(source_path)

    monkeypatch.setattr("src.main.get_default_config", lambda: config)

    exit_code = run(
        [
            "--extract",
            "--input",
            str(source_path),
            "--no-denoise",
            "--min-symbol-width",
            "8",
            "--min-symbol-height",
            "8",
            "--min-symbol-area",
            "64",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Extraction input image:" in captured.out
    assert "Extracted symbol count: 2" in captured.out
    assert "Extraction binary debug image:" in captured.out
    assert "Extraction overlay debug image:" in captured.out
    assert "Extraction manifest:" in captured.out
    assert "Extraction completed." in captured.out
    assert (config.extracted_dir / "sheet_001.png").exists()
    assert (config.extracted_dir / "sheet_002.png").exists()
    assert (config.input_debug_dir / "sheet_extraction_binary.png").exists()
    assert (config.input_debug_dir / "sheet_extraction_overlay.png").exists()
    assert (config.manifests_dir / "manifest.json").exists()


def test_run_reports_missing_input_file(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/missing.jpg", "--char", "A"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "Image file does not exist:" in captured.err


def test_run_reports_invalid_input_format(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    invalid_path = tmp_path / "glyph.bmp"
    invalid_path.write_bytes(b"BMplaceholder")

    with pytest.raises(SystemExit) as exc_info:
        run(["--input", str(invalid_path), "--char", "A"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "Only .jpg and .png files are allowed." in captured.err


def test_run_reports_invalid_fill_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg", "--char", "A", "--fill-threshold", "2"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "fill_threshold must be in the range 0..1." in captured.err


def test_run_reports_invalid_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg", "--char", "A", "--threshold", "300"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "threshold must be in the range 0..255." in captured.err


def test_run_reports_invalid_denoise_size(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg", "--char", "A", "--denoise-size", "4"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "denoise-size must be a positive odd integer." in captured.err


def test_run_reports_invalid_grid_step_range(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg", "--char", "A", "--min-grid-step", "10", "--max-grid-step", "5"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "min-grid-step must be less than or equal to max-grid-step." in captured.err


def test_run_reports_invalid_expected_grid_size(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        run(["--input", "input/raw/A.jpg", "--char", "A", "--expected-columns", "0"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "expected-columns must be positive." in captured.err


def test_module_invocation_runs_cli() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "--input",
            "input/raw/A.jpg",
            "--char",
            "A",
            "--dry-run",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Character: A" in result.stdout
    assert "Image format: jpg" in result.stdout
    assert "Binary debug image:" in result.stdout
    assert "Grid debug image:" in result.stdout
    assert "Extracted cells:" in result.stdout
    assert "Fill threshold:" in result.stdout
    assert "First matrix row:" in result.stdout
    assert "Trimmed glyph matrix size:" in result.stdout
    assert "Glyph char: A" in result.stdout
    assert "Exported JSON:" in result.stdout
    assert "Preview image:" in result.stdout
    assert "Import pipeline completed." in result.stdout


def _create_two_symbol_image(path: Path) -> None:
    image = Image.new("L", (60, 24), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 18, 18), outline=0, width=2)
    draw.line((4, 11, 18, 11), fill=0, width=2)
    draw.rectangle((34, 3, 52, 19), outline=0, width=2)
    draw.line((43, 3, 43, 19), fill=0, width=2)
    image.save(path, format="PNG")
