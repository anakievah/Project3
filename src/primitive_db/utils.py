from __future__ import annotations

import json
import os
from typing import Any

from src.constants import DATA_DIR


def load_metadata(filepath: str) -> dict[str, Any]:
    """Load metadata from JSON file, return empty dict if file is missing."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:  # noqa: TRY003
        raise ValueError(f"Файл метаданных поврежден: {exc}") from exc


def save_metadata(filepath: str, data: dict[str, Any]) -> None:
    """Save metadata dict to JSON file."""
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _table_path(table_name: str) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name: str) -> list[dict[str, Any]]:
    """Load table data from data/<table>.json, return empty list if missing."""
    path = _table_path(table_name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:  # noqa: TRY003
        raise ValueError(f"Файл данных таблицы поврежден: {exc}") from exc


def save_table_data(table_name: str, data: list[dict[str, Any]]) -> None:
    """Save list of records to data/<table>.json."""
    path = _table_path(table_name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
