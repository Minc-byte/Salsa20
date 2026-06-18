"""Shared utilities for reproducible experiments and result output."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any


def set_experiment_seed(seed: int) -> None:
    """Initialize deterministic randomness for reproducible experiments."""
    random.seed(seed)


def write_json(path: str | Path, payload: object) -> None:
    """Write JSON experiment output."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    """Write CSV experiment output."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
