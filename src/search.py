from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.indexer import InvertedIndex


console = Console()


def print_term(index: InvertedIndex, term: str) -> None:
    """
    Print the inverted index entry for a single term.
    """
    term = term.strip().lower()

    if not term:
        console.print("[red]Please provide a word to print.[/red]")
        return

    term_data = index.get_postings(term)

    if term_data is None:
        console.print(f"[yellow]'{term}' was not found in the index.[/yellow]")
        return

    table = Table(title=f"Inverted index for '{term}'")
    table.add_column("Document")
    table.add_column("Term Frequency", justify="right")
    table.add_column("Positions")

    for doc_url, posting in sorted(term_data["postings"].items()):
        positions = ", ".join(str(pos) for pos in posting["positions"])
        table.add_row(doc_url, str(posting["term_freq"]), positions)

    console.print(table)
    console.print(f"[cyan]Document frequency:[/cyan] {term_data['doc_freq']}")


def find_query(index: InvertedIndex, query: str) -> None:
    """
    Find documents containing all terms in the query and print ranked results.
    """
    terms = InvertedIndex.tokenize(query)

    if not terms:
        console.print("[red]Please provide a non-empty query.[/red]")
        return

    matching_docs = index.find_documents_containing_all(terms)

    if not matching_docs:
        console.print(
            f"[yellow]No documents contain all query terms: {' '.join(terms)}[/yellow]"
        )
        return

    ranked_docs = index.rank_documents_by_term_frequency(terms, matching_docs)

    table = Table(title=f"Search results for: {' '.join(terms)}")
    table.add_column("Rank", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Document")
    table.add_column("Title")

    for rank, (doc_url, score) in enumerate(ranked_docs, start=1):
        title = index.documents.get(doc_url, {}).get("title", "")
        table.add_row(str(rank), str(score), doc_url, title)

    console.print(table)