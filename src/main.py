from __future__ import annotations

from rich.console import Console

from src.crawler import Crawler
from src.indexer import InvertedIndex
from src.search import find_query, print_term
from src.storage import load_index, save_index


BASE_URL = "https://quotes.toscrape.com/"
INDEX_PATH = "data/index.json"

console = Console()


def build_command() -> InvertedIndex:
    """
    Crawl the target site, build the index, save it to disk,
    and return the built index.
    """
    console.print("[bold cyan]Building index...[/bold cyan]")

    crawler = Crawler(base_url=BASE_URL, politeness_delay=6.0)
    documents = crawler.crawl()

    index = InvertedIndex()
    for document in documents:
        index.add_document(
            url=document["url"],
            text=document["text"],
            title=document["title"],
        )

    save_index(index, INDEX_PATH)

    console.print(f"[green]Index built and saved to {INDEX_PATH}[/green]")
    console.print(
        f"[green]Indexed {len(index.documents)} documents and {len(index.index)} unique terms.[/green]"
    )

    return index


def load_command() -> InvertedIndex | None:
    """
    Load an index from disk and return it.
    """
    try:
        index = load_index(INDEX_PATH)
        console.print(f"[green]Loaded index from {INDEX_PATH}[/green]")
        console.print(
            f"[green]Loaded {len(index.documents)} documents and {len(index.index)} unique terms.[/green]"
        )
        return index
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/red]")
        return None
    except Exception as exc:
        console.print(f"[red]Failed to load index: {exc}[/red]")
        return None


def main() -> None:
    """
    Run the command-line interface for the search tool.
    """
    console.print("[bold]Search Engine Tool[/bold]")
    console.print("Commands: build, load, print <word>, find <query> [--tfidf], exit")

    current_index: InvertedIndex | None = None

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            console.print("[cyan]Goodbye.[/cyan]")
            break

        if not raw:
            continue

        if raw == "exit":
            console.print("[cyan]Goodbye.[/cyan]")
            break

        if raw == "build":
            current_index = build_command()
            continue

        if raw == "load":
            current_index = load_command()
            continue

        if raw == "print":
            if current_index is None:
                console.print("[red]No index loaded. Use 'build' or 'load' first.[/red]")
            else:
                console.print("[red]Please provide a word to print.[/red]")
            continue

        if raw == "find":
            if current_index is None:
                console.print("[red]No index loaded. Use 'build' or 'load' first.[/red]")
            else:
                console.print("[red]Please provide a non-empty query.[/red]")
            continue

        if raw.startswith("print "):
            if current_index is None:
                console.print("[red]No index loaded. Use 'build' or 'load' first.[/red]")
                continue

            term = raw[len("print "):].strip()
            print_term(current_index, term)
            continue

        if raw.startswith("find "):
            if current_index is None:
                console.print("[red]No index loaded. Use 'build' or 'load' first.[/red]")
                continue

            parts = raw.split()

            # Default ranking
            ranking = "tf"

            # Check for optional flag
            if "--tfidf" in parts:
                ranking = "tfidf"
                parts.remove("--tfidf")

            # Reconstruct query
            query = " ".join(parts[1:]).strip()

            find_query(current_index, query, ranking=ranking)
            continue

        console.print(
            "[yellow]Unknown command. Use: build, load, print <word>, find <query>, exit[/yellow]"
        )


if __name__ == "__main__":
    main()