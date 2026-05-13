from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.indexer import InvertedIndex
from src.main import (
    build_command,
    compare_rankings,
    get_prompt,
    load_command,
    main,
    parse_build_depth,
    parse_find_command,
    show_help,
    show_welcome,
    success,
    warning,
    error,
)
from src.storage import save_index


def run_main_with_inputs(monkeypatch, commands: list[str]) -> None:
    inputs = iter(commands)
    monkeypatch.setattr("src.main.console.input", lambda _: next(inputs))


def make_test_index() -> InvertedIndex:
    index = InvertedIndex()
    index.add_document("doc1", "good friends love life", "Doc 1")
    return index


def test_parse_build_depth_returns_none_without_depth() -> None:
    assert parse_build_depth(["build"]) is None


def test_parse_build_depth_parses_valid_depth() -> None:
    assert parse_build_depth(["build", "--depth", "3"]) == 3


def test_parse_build_depth_rejects_unknown_option() -> None:
    with pytest.raises(ValueError, match="Unknown build option"):
        parse_build_depth(["build", "--bad"])


def test_parse_build_depth_rejects_missing_value() -> None:
    with pytest.raises(ValueError, match="Please provide a depth value"):
        parse_build_depth(["build", "--depth"])


def test_parse_build_depth_rejects_non_integer() -> None:
    with pytest.raises(ValueError, match="Depth must be an integer"):
        parse_build_depth(["build", "--depth", "abc"])


def test_parse_build_depth_rejects_negative_integer() -> None:
    with pytest.raises(ValueError, match="Depth must be 0 or greater"):
        parse_build_depth(["build", "--depth", "-1"])


def test_parse_find_command_defaults_to_tf() -> None:
    query, ranking = parse_find_command("find good friends")

    assert query == "good friends"
    assert ranking == "tf"


def test_parse_find_command_tfidf() -> None:
    query, ranking = parse_find_command("find good friends --tfidf")

    assert query == "good friends"
    assert ranking == "tfidf"


def test_parse_find_command_proximity() -> None:
    query, ranking = parse_find_command("find good friends --proximity")

    assert query == "good friends"
    assert ranking == "tf_proximity"


def test_parse_find_command_tfidf_proximity() -> None:
    query, ranking = parse_find_command("find good friends --tfidf --proximity")

    assert query == "good friends"
    assert ranking == "tfidf_proximity"


def test_parse_find_command_ignores_compare_flag() -> None:
    query, ranking = parse_find_command("find good friends --compare")

    assert query == "good friends"
    assert ranking == "tf"


def test_get_prompt_changes_when_index_loaded() -> None:
    index = InvertedIndex()

    assert "yellow" in get_prompt(None)
    assert "green" in get_prompt(index)


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


def test_load_command_handles_unexpected_exception(monkeypatch) -> None:
    def broken_load_index(_: str) -> InvertedIndex:
        raise RuntimeError("broken file")

    monkeypatch.setattr("src.main.load_index", broken_load_index)

    result = load_command()

    assert result is None


def test_show_help_without_index(capsys) -> None:
    show_help(None)
    captured = capsys.readouterr()

    assert "No index loaded" in captured.out
    assert "Available Commands" in captured.out


def test_show_help_with_index(capsys) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world", "Doc 1")

    show_help(index)
    captured = capsys.readouterr()

    assert "Index loaded" in captured.out
    assert "1 documents" in captured.out


def test_show_welcome_outputs_title(capsys) -> None:
    show_welcome()
    captured = capsys.readouterr()

    assert "Search Engine Tool" in captured.out


def test_message_helpers_output_expected_messages(capsys) -> None:
    success("done")
    warning("careful")
    error("bad")

    captured = capsys.readouterr()

    assert "done" in captured.out
    assert "careful" in captured.out
    assert "bad" in captured.out


def test_compare_rankings_outputs_all_methods(capsys) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "good friends good", "Doc 1")
    index.add_document("doc2", "good far away friends", "Doc 2")

    compare_rankings(index, "good friends")
    captured = capsys.readouterr()

    assert "Ranking comparison" in captured.out
    assert "TF" in captured.out
    assert "TF + Proximity" in captured.out
    assert "TF-IDF" in captured.out
    assert "TF-IDF + Proximity" in captured.out


def test_compare_rankings_handles_no_results(capsys) -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world", "Doc 1")

    compare_rankings(index, "missing term")
    captured = capsys.readouterr()

    assert "No results" in captured.out


def test_build_command_builds_and_saves_index(monkeypatch, tmp_path: Path) -> None:
    output_file = tmp_path / "index.json"

    fake_crawler = MagicMock()
    fake_crawler.crawl.return_value = [
        {
            "url": "doc1",
            "title": "Doc 1",
            "text": "hello world hello",
        },
        {
            "url": "doc2",
            "title": "Doc 2",
            "text": "good friends",
        },
    ]

    fake_crawler_class = MagicMock(return_value=fake_crawler)

    monkeypatch.setattr("src.main.Crawler", fake_crawler_class)
    monkeypatch.setattr("src.main.INDEX_PATH", str(output_file))

    index = build_command(max_depth=2)

    fake_crawler_class.assert_called_once()
    assert fake_crawler_class.call_args.kwargs["max_depth"] == 2

    assert output_file.exists()
    assert len(index.documents) == 2
    assert "hello" in index.index
    assert "friends" in index.index


def test_build_command_without_depth(monkeypatch, tmp_path: Path) -> None:
    output_file = tmp_path / "index.json"

    fake_crawler = MagicMock()
    fake_crawler.crawl.return_value = [
        {
            "url": "doc1",
            "title": "Doc 1",
            "text": "hello world",
        }
    ]

    fake_crawler_class = MagicMock(return_value=fake_crawler)

    monkeypatch.setattr("src.main.Crawler", fake_crawler_class)
    monkeypatch.setattr("src.main.INDEX_PATH", str(output_file))

    index = build_command()

    assert fake_crawler_class.call_args.kwargs["max_depth"] is None
    assert len(index.documents) == 1
    assert output_file.exists()


def test_main_exits_cleanly(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["exit"])

    main()

    captured = capsys.readouterr()
    assert "Goodbye" in captured.out


def test_main_quit_alias_exits(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["q"])

    main()

    captured = capsys.readouterr()
    assert "Goodbye" in captured.out


def test_main_help_then_exit(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["help", "exit"])

    main()

    captured = capsys.readouterr()
    assert "Available Commands" in captured.out
    assert "Goodbye" in captured.out


def test_main_question_mark_help_then_exit(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["?", "exit"])

    main()

    captured = capsys.readouterr()
    assert "Available Commands" in captured.out


def test_main_ignores_empty_input(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["", "exit"])

    main()

    captured = capsys.readouterr()
    assert "Goodbye" in captured.out


def test_main_clear_command(monkeypatch, capsys) -> None:
    called = {"clear": False}

    def fake_system(command: str) -> int:
        called["clear"] = command == "clear"
        return 0

    run_main_with_inputs(monkeypatch, ["clear", "exit"])
    monkeypatch.setattr("src.main.os.system", fake_system)

    main()

    assert called["clear"] is True
    captured = capsys.readouterr()
    assert "Search Engine Tool" in captured.out


def test_main_unknown_command(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["unknown", "exit"])

    main()

    captured = capsys.readouterr()
    assert "Unknown command" in captured.out


def test_main_keyboard_interrupt(monkeypatch, capsys) -> None:
    def fake_input(_: str) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr("src.main.console.input", fake_input)

    main()

    captured = capsys.readouterr()
    assert "Goodbye" in captured.out


def test_main_build_calls_build_command(monkeypatch) -> None:
    index = make_test_index()
    called = {"depth": None}

    def fake_build_command(max_depth=None):
        called["depth"] = max_depth
        return index

    run_main_with_inputs(monkeypatch, ["build", "exit"])
    monkeypatch.setattr("src.main.build_command", fake_build_command)

    main()

    assert called["depth"] is None


def test_main_build_with_depth_calls_build_command(monkeypatch) -> None:
    index = make_test_index()
    called = {"depth": None}

    def fake_build_command(max_depth=None):
        called["depth"] = max_depth
        return index

    run_main_with_inputs(monkeypatch, ["build --depth 2", "exit"])
    monkeypatch.setattr("src.main.build_command", fake_build_command)

    main()

    assert called["depth"] == 2


def test_main_build_with_bad_depth_shows_error(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["build --depth bad", "exit"])

    main()

    captured = capsys.readouterr()
    assert "Depth must be an integer" in captured.out


def test_main_load_sets_current_index(monkeypatch) -> None:
    index = make_test_index()
    called = {"loaded": False}

    def fake_load_command():
        called["loaded"] = True
        return index

    run_main_with_inputs(monkeypatch, ["load", "exit"])
    monkeypatch.setattr("src.main.load_command", fake_load_command)

    main()

    assert called["loaded"] is True


def test_main_print_without_index_shows_error(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["print life", "exit"])

    main()

    captured = capsys.readouterr()
    assert "No index loaded" in captured.out


def test_main_print_without_word_shows_error(monkeypatch, capsys) -> None:
    index = make_test_index()

    run_main_with_inputs(monkeypatch, ["load", "print", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)

    main()

    captured = capsys.readouterr()
    assert "Please provide a word" in captured.out


def test_main_print_with_index_calls_print_term(monkeypatch) -> None:
    index = make_test_index()
    called = {"term": None}

    def fake_print_term(current_index, term):
        called["term"] = term
        assert current_index is index

    run_main_with_inputs(monkeypatch, ["load", "print life", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.print_term", fake_print_term)

    main()

    assert called["term"] == "life"


def test_main_find_without_index_shows_error(monkeypatch, capsys) -> None:
    run_main_with_inputs(monkeypatch, ["find hello", "exit"])

    main()

    captured = capsys.readouterr()
    assert "No index loaded" in captured.out


def test_main_find_without_query_shows_error(monkeypatch, capsys) -> None:
    index = make_test_index()

    run_main_with_inputs(monkeypatch, ["load", "find", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)

    main()

    captured = capsys.readouterr()
    assert "Please provide a non-empty query" in captured.out


def test_main_find_calls_find_query_default(monkeypatch) -> None:
    index = make_test_index()
    called = {"query": None, "ranking": None}

    def fake_find_query(current_index, query, ranking="tf"):
        called["query"] = query
        called["ranking"] = ranking
        assert current_index is index

    run_main_with_inputs(monkeypatch, ["load", "find good friends", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.find_query", fake_find_query)

    main()

    assert called["query"] == "good friends"
    assert called["ranking"] == "tf"


def test_main_find_calls_find_query_tfidf(monkeypatch) -> None:
    index = make_test_index()
    called = {"ranking": None}

    def fake_find_query(current_index, query, ranking="tf"):
        called["ranking"] = ranking

    run_main_with_inputs(monkeypatch, ["load", "find good friends --tfidf", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.find_query", fake_find_query)

    main()

    assert called["ranking"] == "tfidf"


def test_main_find_calls_find_query_proximity(monkeypatch) -> None:
    index = make_test_index()
    called = {"ranking": None}

    def fake_find_query(current_index, query, ranking="tf"):
        called["ranking"] = ranking

    run_main_with_inputs(monkeypatch, ["load", "find good friends --proximity", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.find_query", fake_find_query)

    main()

    assert called["ranking"] == "tf_proximity"


def test_main_find_calls_find_query_tfidf_proximity(monkeypatch) -> None:
    index = make_test_index()
    called = {"ranking": None}

    def fake_find_query(current_index, query, ranking="tf"):
        called["ranking"] = ranking

    run_main_with_inputs(
        monkeypatch,
        ["load", "find good friends --tfidf --proximity", "exit"],
    )
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.find_query", fake_find_query)

    main()

    assert called["ranking"] == "tfidf_proximity"


def test_main_find_compare_calls_compare_rankings(monkeypatch) -> None:
    index = make_test_index()
    called = {"query": None}

    def fake_compare_rankings(current_index, query):
        called["query"] = query
        assert current_index is index

    run_main_with_inputs(monkeypatch, ["load", "find good friends --compare", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)
    monkeypatch.setattr("src.main.compare_rankings", fake_compare_rankings)

    main()

    assert called["query"] == "good friends"


def test_main_find_compare_without_query_shows_error(monkeypatch, capsys) -> None:
    index = make_test_index()

    run_main_with_inputs(monkeypatch, ["load", "find --compare", "exit"])
    monkeypatch.setattr("src.main.load_command", lambda: index)

    main()

    captured = capsys.readouterr()
    assert "Please provide a non-empty query" in captured.out