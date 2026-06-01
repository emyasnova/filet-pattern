"""Helpers for reading and writing JSON artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json_file(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON using UTF-8 and stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(f"{text}\n", encoding="utf-8")
