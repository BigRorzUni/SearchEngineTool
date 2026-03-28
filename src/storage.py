from __future__ import annotations

import json
from pathlib import Path

from indexer import InvertedIndex


def save_index(index: InvertedIndex, filepath: str) -> None:
    """
    Save an InvertedIndex to a JSON file.
    Creates parent directories if needed.
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(index.to_dict(), file, ensure_ascii=False, indent=2)


def load_index(filepath: str) -> InvertedIndex:
    """
    Load an InvertedIndex from a JSON file.
    Raises FileNotFoundError if the file is missing.
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Index file not found: {filepath}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return InvertedIndex.from_dict(data)