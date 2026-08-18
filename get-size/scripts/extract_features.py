#!/usr/bin/env python3
"""Command-line interface for filet chart feature extraction."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

# Make the src-layout package importable when this file is run directly from a
# repository checkout. Installed packages and notebook imports need no workaround.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from filet_size.features import (  # noqa: E402
    extract_features_for_dataframe,
    extract_features_from_image,
)

REQUIRED_COLUMNS = {
    "image_path", "width_cells", "height_cells"
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract features from filet chart images")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--input-csv", type=Path, help="Semicolon-separated dataset CSV")
    mode.add_argument("--image-path", type=Path, help="Process one image and print JSON")
    parser.add_argument("--images-root", type=Path, help="Root for relative image paths")
    parser.add_argument("--output-csv", type=Path, help="Destination feature CSV")
    args = parser.parse_args(argv)
    if args.input_csv is not None and args.output_csv is None:
        parser.error("--output-csv is required with --input-csv")
    if args.image_path is not None and (args.images_root or args.output_csv):
        parser.error("--images-root and --output-csv are only valid with --input-csv")
    return args


def _json_value(value: object) -> object:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def run_csv(input_csv: Path, images_root: Path | None, output_csv: Path) -> int:
    if not input_csv.is_file():
        raise FileNotFoundError(f"Input CSV does not exist: {input_csv}")
    df = pd.read_csv(input_csv, sep=";")
    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {', '.join(missing)}")
    result = extract_features_for_dataframe(df, images_root)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_csv, sep=";", index=False)
    errors = int(result["feature_extraction_error"].fillna("").ne("").sum())
    print(f"Processed: {len(result)}")
    print(f"Successful: {len(result) - errors}")
    print(f"Errors: {errors}")
    print(f"Saved to: {output_csv}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.image_path is not None:
            features = extract_features_from_image(args.image_path)
            serializable = {key: _json_value(value) for key, value in features.items()}
            print(json.dumps(serializable, indent=2, ensure_ascii=False))
            return 0
        return run_csv(args.input_csv, args.images_root, args.output_csv)
    except Exception as exc:
        # CLI failures should be concise (the dataframe mode handles per-image
        # failures internally and still returns a successful batch result).
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
