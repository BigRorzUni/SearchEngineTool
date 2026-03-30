from __future__ import annotations

from rich.console import Console
from rich.table import Table

from src.indexer import InvertedIndex


console = Console()


def get_ranked_results(
    index: InvertedIndex,
    query: str,
    ranking: str = "tf",
) -> list[tuple[str, int | float]]:
    """
    Return ranked results for a query without printing.
    """
    terms = InvertedIndex.tokenize(query)

    if not terms:
        return []

    matching_docs = index.find_documents_containing_all(terms)
    if not matching_docs:
        return []

    if ranking == "tfidf":
        return index.rank_documents_by_tfidf(terms, matching_docs)

    return index.rank_documents_by_term_frequency(terms, matching_docs)


def print_term(index: InvertedIndex, term: str) -> None:
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


def find_query(index: InvertedIndex, query: str, ranking: str = "tf") -> None:
    terms = InvertedIndex.tokenize(query)

    if not terms:
        console.print("[red]Please provide a non-empty query.[/red]")
        return

    ranked_docs = get_ranked_results(index, query, ranking)
    if not ranked_docs:
        console.print(
            f"[yellow]No documents contain all query terms: {' '.join(terms)}[/yellow]"
        )
        return

    if ranking == "tfidf":
        score_label = "TF-IDF Score"
        title = f"Search results for: {' '.join(terms)} (ranking: tfidf)"
    else:
        score_label = "Score"
        title = f"Search results for: {' '.join(terms)} (ranking: tf)"

    table = Table(title=title)
    table.add_column("Rank", justify="right")
    table.add_column(score_label, justify="right")
    table.add_column("Document")
    table.add_column("Title")

    for rank, (doc_url, score) in enumerate(ranked_docs, start=1):
        title_text = index.documents.get(doc_url, {}).get("title", "")
        if isinstance(score, float):
            score_text = f"{score:.4f}"
        else:
            score_text = str(score)

        table.add_row(str(rank), score_text, doc_url, title_text)

    console.print(table)