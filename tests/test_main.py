from pathlib import Path

from src.indexer import InvertedIndex
from src.main import load_command
from src.storage import save_index


def test_load_command_returns_none_when_index_missing(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.main.INDEX_PATH", str(tmp_path / "missing.json"))

    result = load_command()

    assert result is None


def test_load_command_returns_index_when_file_exists(monkeypatch, tmp_path: Path) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world", "Doc 1")

    output_file = tmp_path / "index.json"
    save_index(index, str(output_file))

    monkeypatch.setattr("src.main.INDEX_PATH", str(output_file))

    loaded = load_command()

    assert loaded is not None
    assert loaded.index == index.index
    assert loaded.documents == index.documents