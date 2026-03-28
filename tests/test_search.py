from src.indexer import InvertedIndex
from src.search import find_query, print_term


def build_test_index() -> InvertedIndex:
    index = InvertedIndex()
    index.add_document("doc1", "good friends good books", "Doc 1")
    index.add_document("doc2", "good friends", "Doc 2")
    index.add_document("doc3", "books only here", "Doc 3")
    return index


def test_print_term_shows_term_information(capsys) -> None:
    index = build_test_index()

    print_term(index, "good")
    captured = capsys.readouterr()

    assert "Inverted index for 'good'" in captured.out
    assert "doc1" in captured.out
    assert "doc2" in captured.out
    assert "Document frequency:" in captured.out


def test_print_term_handles_missing_word(capsys) -> None:
    index = build_test_index()

    print_term(index, "missing")
    captured = capsys.readouterr()

    assert "'missing' was not found in the index." in captured.out


def test_print_term_handles_empty_input(capsys) -> None:
    index = build_test_index()

    print_term(index, "   ")
    captured = capsys.readouterr()

    assert "Please provide a word to print." in captured.out


def test_find_query_shows_ranked_results(capsys) -> None:
    index = build_test_index()

    find_query(index, "good friends")
    captured = capsys.readouterr()

    assert "Search results for: good friends" in captured.out
    assert "doc1" in captured.out
    assert "doc2" in captured.out
    assert "Doc 1" in captured.out
    assert "Doc 2" in captured.out


def test_find_query_handles_missing_terms(capsys) -> None:
    index = build_test_index()

    find_query(index, "good missing")
    captured = capsys.readouterr()

    assert "No documents contain all query terms: good missing" in captured.out


def test_find_query_handles_empty_query(capsys) -> None:
    index = build_test_index()

    find_query(index, "")
    captured = capsys.readouterr()

    assert "Please provide a non-empty query." in captured.out