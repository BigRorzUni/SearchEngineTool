from __future__ import annotations

import os

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.crawler import Crawler
from src.indexer import InvertedIndex
from src.search import find_query, print_term
from src.storage import load_index, save_index


BASE_URL = "https://quotes.toscrape.com/"
INDEX_PATH = "data/index.json"

console = Console()


def success(message: str) -> None:
    console.print(f"[green]✓[/green] {message}")


def warning(message: str) -> None:
    console.print(f"[yellow]![/yellow] {message}")


def error(message: str) -> None:
    console.print(f"[red]✗[/red] {message}")


def show_welcome() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Search Engine Tool[/bold cyan]\n"
            "Type [bold]help[/bold] or [bold]?[/bold] to view available commands.",
            border_style="cyan",
        )
    )


def show_help(current_index: InvertedIndex | None = None) -> None:
    if current_index is None:
        status = "[yellow]No index loaded[/yellow]"
    else:
        status = (
            f"[green]Index loaded[/green] | "
            f"{len(current_index.documents)} documents | "
            f"{len(current_index.index)} terms"
        )

    console.print(
        Panel.fit(
            status,
            title="Status",
            border_style="green" if current_index is not None else "yellow",
        )
    )

    commands = Table(title="Available Commands")
    commands.add_column("Command", style="cyan", no_wrap=True)
    commands.add_column("Description")

    commands.add_row("build", "Crawl all allowed pages, build the index, and save it.")
    commands.add_row(
        "build --depth N",
        "Crawl with a maximum traversal depth. Depth 0 indexes only the start page.",
    )
    commands.add_row("load", f"Load the saved index from {INDEX_PATH}.")
    commands.add_row("print <word>", "Print the inverted index entry for a word.")
    commands.add_row("find <query>", "Search using baseline term-frequency ranking.")
    commands.add_row("find <query> --tfidf", "Search using TF-IDF ranking.")
    commands.add_row("find <query> --proximity", "Search using TF + proximity ranking.")
    commands.add_row(
        "find <query> --tfidf --proximity",
        "Search using TF-IDF + proximity ranking.",
    )
    commands.add_row("help or ?", "Show this help menu.")
    commands.add_row("clear", "Clear the terminal.")
    commands.add_row("exit, quit, or q", "Exit the program.")

    console.print(commands)

    examples = Table(title="Examples")
    examples.add_column("Example", style="green", no_wrap=True)
    examples.add_column("What it does")

    examples.add_row("build", "Build the full index.")
    examples.add_row("build --depth 0", "Index only the start page.")
    examples.add_row("load", "Load the saved index.")
    examples.add_row("print truth", "Show postings for the word 'truth'.")
    examples.add_row("find love life", "Search using TF ranking.")
    examples.add_row("find love life --tfidf", "Search using TF-IDF ranking.")
    examples.add_row("find love life --proximity", "Search using TF + proximity.")
    examples.add_row(
        "find love life --tfidf --proximity",
        "Search using TF-IDF + proximity.",
    )

    console.print(examples)


def build_command(max_depth: int | None = None) -> InvertedIndex:
    """
    Crawl the target site, build the index, save it to disk,
    and return the built index.
    """
    console.print("[bold cyan]Building index...[/bold cyan]")

    if max_depth is None:
        console.print("[cyan]Depth limit: unlimited[/cyan]")
    else:
        console.print(f"[cyan]Depth limit: {max_depth}[/cyan]")

    crawler = Crawler(base_url=BASE_URL, politeness_delay=6.0, max_depth=max_depth)
    documents = crawler.crawl()

    index = InvertedIndex()

    with console.status("[bold cyan]Indexing documents...[/bold cyan]"):
        for document in documents:
            index.add_document(
                url=document["url"],
                text=document["text"],
                title=document["title"],
            )

    with console.status("[bold cyan]Saving index...[/bold cyan]"):
        save_index(index, INDEX_PATH)

    console.print(
        Panel.fit(
            f"[green]Index built successfully[/green]\n"
            f"Documents: {len(index.documents)}\n"
            f"Unique terms: {len(index.index)}\n"
            f"Saved to: {INDEX_PATH}",
            title="Build Summary",
            border_style="green",
        )
    )

    return index


def load_command() -> InvertedIndex | None:
    """
    Load an index from disk and return it.
    """
    try:
        with console.status("[bold cyan]Loading index...[/bold cyan]"):
            index = load_index(INDEX_PATH)

        console.print(
            Panel.fit(
                f"[green]Index loaded successfully[/green]\n"
                f"Documents: {len(index.documents)}\n"
                f"Unique terms: {len(index.index)}\n"
                f"Source: {INDEX_PATH}",
                title="Load Summary",
                border_style="green",
            )
        )

        return index

    except FileNotFoundError as exc:
        error(str(exc))
        return None

    except Exception as exc:
        error(f"Failed to load index: {exc}")
        return None


def parse_build_depth(parts: list[str]) -> int | None:
    """
    Parse optional build depth from command parts.
    """
    if len(parts) == 1:
        return None

    if "--depth" not in parts:
        raise ValueError("Unknown build option. Use: build [--depth N]")

    depth_index = parts.index("--depth")

    if depth_index + 1 >= len(parts):
        raise ValueError("Please provide a depth value after --depth.")

    try:
        max_depth = int(parts[depth_index + 1])
    except ValueError as exc:
        raise ValueError("Depth must be an integer.") from exc

    if max_depth < 0:
        raise ValueError("Depth must be 0 or greater.")

    return max_depth


def parse_find_command(raw: str) -> tuple[str, str]:
    """
    Parse a find command into query text and ranking mode.

    Supported forms:
    - find <query>
    - find <query> --tfidf
    - find <query> --proximity
    - find <query> --tfidf --proximity
    """
    parts = raw.split()

    use_tfidf = "--tfidf" in parts
    use_proximity = "--proximity" in parts

    query_parts = [p for p in parts[1:] if p not in ("--tfidf", "--proximity")]
    query = " ".join(query_parts).strip()

    if use_tfidf and use_proximity:
        ranking = "tfidf_proximity"
    elif use_tfidf:
        ranking = "tfidf"
    elif use_proximity:
        ranking = "tf_proximity"
    else:
        ranking = "tf"

    return query, ranking


def get_prompt(current_index: InvertedIndex | None) -> str:
    """
    Return a status-aware prompt while keeping the '>' symbol.
    """
    if current_index is None:
        return "[bold yellow]>[/bold yellow] "
    return "[bold green]>[/bold green] "


def main() -> None:
    """
    Run the command-line interface for the search tool.
    """
    show_welcome()

    current_index: InvertedIndex | None = None

    while True:
        try:
            raw = console.input(get_prompt(current_index)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            success("Goodbye.")
            break

        if not raw:
            continue

        if raw in {"help", "?"}:
            show_help(current_index)
            continue

        if raw == "clear":
            os.system("clear")
            show_welcome()
            continue

        if raw in {"exit", "quit", "q"}:
            success("Goodbye.")
            break

        if raw.startswith("build"):
            parts = raw.split()

            try:
                max_depth = parse_build_depth(parts)
            except ValueError as exc:
                error(str(exc))
                continue

            current_index = build_command(max_depth=max_depth)
            continue

        if raw == "load":
            current_index = load_command()
            continue

        if raw == "print":
            if current_index is None:
                error("No index loaded. Use 'build' or 'load' first.")
            else:
                error("Please provide a word to print.")
            continue

        if raw == "find":
            if current_index is None:
                error("No index loaded. Use 'build' or 'load' first.")
            else:
                error("Please provide a non-empty query.")
            continue

        if raw.startswith("print "):
            if current_index is None:
                error("No index loaded. Use 'build' or 'load' first.")
                continue

            term = raw[len("print ") :].strip()
            print_term(current_index, term)
            continue

        if raw.startswith("find "):
            if current_index is None:
                error("No index loaded. Use 'build' or 'load' first.")
                continue

            query, ranking = parse_find_command(raw)

            if not query:
                error("Please provide a non-empty query.")
                continue

            find_query(current_index, query, ranking=ranking)
            continue

        warning("Unknown command. Type 'help' to view available commands.")


if __name__ == "__main__":
    main()