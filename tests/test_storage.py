from pathlib import Path

import pytest

from src.indexer import InvertedIndex
from src.storage import load_index, save_index


def test_save_index_creates_file(tmp_path: Path) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world hello", "Doc 1")

    output_file = tmp_path / "index.json"
    save_index(index, str(output_file))

    assert output_file.exists()


def test_load_index_restores_saved_data(tmp_path: Path) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world hello", "Doc 1")
    index.add_document("doc2", "good friends", "Doc 2")

    output_file = tmp_path / "index.json"
    save_index(index, str(output_file))

    loaded = load_index(str(output_file))

    assert loaded.index == index.index
    assert loaded.documents == index.documents


def test_save_index_creates_parent_directories(tmp_path: Path) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world", "Doc 1")

    output_file = tmp_path / "nested" / "data" / "index.json"
    save_index(index, str(output_file))

    assert output_file.exists()


def test_load_index_raises_for_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="Index file not found"):
        load_index(str(missing_file))


def test_save_and_load_empty_index(tmp_path: Path) -> None:
    index = InvertedIndex()

    output_file = tmp_path / "empty_index.json"
    save_index(index, str(output_file))

    loaded = load_index(str(output_file))

    assert loaded.index == {}
    assert loaded.documents == {}