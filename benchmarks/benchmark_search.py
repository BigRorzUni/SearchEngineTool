from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Iterable

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.search import get_ranked_results
from src.storage import load_index


INDEX_PATH = "data/index.json"

QUERIES = [
    "life",
    "truth",
    "good friends",
    "love life",
    "make life",
    "life truth",
    "friend life",
    "the",
]

RANKINGS = ["tf", "tf_proximity", "tfidf", "tfidf_proximity"]

RANKING_LABELS = {
    "tf": "TF",
    "tf_proximity": "TF + Proximity",
    "tfidf": "TF-IDF",
    "tfidf_proximity": "TF-IDF + Proximity",
}

WARMUP_RUNS = 100
REPETITIONS = 1000

console = Console()


def short_doc_name(url: str) -> str:
    if url.endswith("/page/1/"):
        return "page/1"
    if "/page/" in url:
        parts = url.rstrip("/").split("/")
        return parts[-2] + "/" + parts[-1]
    return url.rstrip("/").split("/")[-1] or url


def format_score(score: int | float) -> str:
    if isinstance(score, float):
        return f"{score:.4f}"
    return str(score)


def warmup(index, queries: Iterable[str], rankings: Iterable[str], runs: int) -> None:
    for _ in range(runs):
        for query in queries:
            for ranking in rankings:
                get_ranked_results(index, query, ranking=ranking)


def benchmark_query(index, query: str, ranking: str, repetitions: int) -> dict[str, float]:
    timings_ms: list[float] = []

    for _ in range(repetitions):
        start = time.perf_counter()
        get_ranked_results(index, query, ranking=ranking)
        end = time.perf_counter()
        timings_ms.append((end - start) * 1000.0)

    return {
        "mean": statistics.mean(timings_ms),
        "median": statistics.median(timings_ms),
        "min": min(timings_ms),
        "max": max(timings_ms),
        "stdev": statistics.pstdev(timings_ms),
    }


def average_mean(results: dict[str, dict[str, dict[str, float]]], ranking: str) -> float:
    return statistics.mean(stats["mean"] for stats in results[ranking].values())


def print_header(index) -> None:
    console.print(
        Panel.fit(
            f"[bold cyan]Ranking Benchmark[/bold cyan]\n"
            f"Documents: [green]{len(index.documents)}[/green]\n"
            f"Terms: [green]{len(index.index)}[/green]\n"
            f"Queries: [green]{len(QUERIES)}[/green]\n"
            f"Repetitions: [green]{REPETITIONS}[/green]\n"
            f"Warm-up runs: [green]{WARMUP_RUNS}[/green]",
            border_style="cyan",
        )
    )


def print_timing_summary(results: dict[str, dict[str, dict[str, float]]]) -> None:
    table = Table(title="Timing Summary")
    table.add_column("Ranking Method", style="cyan", no_wrap=True)
    table.add_column("Average Mean", justify="right")
    table.add_column("Median of Medians", justify="right")
    table.add_column("Avg Std Dev", justify="right")
    table.add_column("Slowdown vs TF", justify="right")

    tf_avg = average_mean(results, "tf")

    for ranking in RANKINGS:
        query_stats = results[ranking]
        avg_mean = statistics.mean(stats["mean"] for stats in query_stats.values())
        median_of_medians = statistics.median(
            stats["median"] for stats in query_stats.values()
        )
        avg_stdev = statistics.mean(stats["stdev"] for stats in query_stats.values())
        slowdown = avg_mean / tf_avg if tf_avg > 0 else float("inf")

        slowdown_text = "baseline" if ranking == "tf" else f"{slowdown:.2f}x"

        table.add_row(
            RANKING_LABELS[ranking],
            f"{avg_mean:.4f} ms",
            f"{median_of_medians:.4f} ms",
            f"{avg_stdev:.4f} ms",
            slowdown_text,
        )

    console.print(table)


def print_timing_details(results: dict[str, dict[str, dict[str, float]]]) -> None:
    for ranking in RANKINGS:
        table = Table(title=f"Detailed Timings: {RANKING_LABELS[ranking]}")
        table.add_column("Query", style="cyan")
        table.add_column("Mean", justify="right")
        table.add_column("Median", justify="right")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
        table.add_column("Std Dev", justify="right")

        for query, stats in results[ranking].items():
            table.add_row(
                query,
                f"{stats['mean']:.4f}",
                f"{stats['median']:.4f}",
                f"{stats['min']:.4f}",
                f"{stats['max']:.4f}",
                f"{stats['stdev']:.4f}",
            )

        console.print(table)


def print_top_results(index) -> None:
    for query in QUERIES:
        table = Table(title=f"Top Results: '{query}'")
        table.add_column("Method", style="cyan", no_wrap=True)
        table.add_column("Rank", justify="right")
        table.add_column("Score", justify="right")
        table.add_column("Document")

        for method_index, ranking in enumerate(RANKINGS):
            results = get_ranked_results(index, query, ranking=ranking)[:3]

            if not results:
                table.add_row(RANKING_LABELS[ranking], "-", "-", "No results")
            else:
                for rank, (doc, score) in enumerate(results, start=1):
                    table.add_row(
                        RANKING_LABELS[ranking] if rank == 1 else "",
                        str(rank),
                        format_score(score),
                        short_doc_name(doc),
                    )

            if method_index < len(RANKINGS) - 1:
                table.add_section()

        console.print(table)


def print_difference_analysis(index) -> None:
    table = Table(title="Top-Rank Difference Analysis")
    table.add_column("Query", style="cyan")
    table.add_column("TF", justify="center")
    table.add_column("TF + Prox", justify="center")
    table.add_column("TF-IDF", justify="center")
    table.add_column("TF-IDF + Prox", justify="center")
    table.add_column("Changes", justify="center")

    for query in QUERIES:
        tops: dict[str, str] = {}

        for ranking in RANKINGS:
            results = get_ranked_results(index, query, ranking=ranking)
            tops[ranking] = short_doc_name(results[0][0]) if results else "None"

        changes = []
        if tops["tf"] != tops["tf_proximity"]:
            changes.append("TF→TF+P")
        if tops["tf"] != tops["tfidf"]:
            changes.append("TF→TF-IDF")
        if tops["tfidf"] != tops["tfidf_proximity"]:
            changes.append("TF-IDF→TF-IDF+P")

        table.add_row(
            query,
            tops["tf"],
            tops["tf_proximity"],
            tops["tfidf"],
            tops["tfidf_proximity"],
            ", ".join(changes) if changes else "None",
        )

    console.print(table)


def run_benchmarks(index) -> dict[str, dict[str, dict[str, float]]]:
    timing_results: dict[str, dict[str, dict[str, float]]] = {}

    with console.status("[bold cyan]Warming up benchmark...[/bold cyan]"):
        warmup(index, QUERIES, RANKINGS, WARMUP_RUNS)

    with console.status("[bold cyan]Running benchmark...[/bold cyan]"):
        for ranking in RANKINGS:
            timing_results[ranking] = {}
            for query in QUERIES:
                timing_results[ranking][query] = benchmark_query(
                    index=index,
                    query=query,
                    ranking=ranking,
                    repetitions=REPETITIONS,
                )

    return timing_results


def main() -> None:
    if not Path(INDEX_PATH).exists():
        raise FileNotFoundError(
            f"Index file not found at {INDEX_PATH}. Run the build command first."
        )

    index = load_index(INDEX_PATH)
    print_header(index)

    results = run_benchmarks(index)

    print_timing_summary(results)
    print_timing_details(results)
    print_difference_analysis(index)
    print_top_results(index)

    console.print(
        Panel.fit(
            "[green]Benchmark complete[/green]\n"
            "All timings are reported in milliseconds per query.",
            border_style="green",
        )
    )


if __name__ == "__main__":
    main()