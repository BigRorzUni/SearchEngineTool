from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Iterable

from src.search import get_ranked_results
from src.storage import load_index


INDEX_PATH = "data/index.json"

# Include both single-term and multi-term queries.
# Proximity only affects multi-term queries, so those should dominate the analysis.
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

RANKINGS = ["tf", "tfidf", "tfidf_proximity"]

# Warm up the interpreter and caches a little before measuring.
WARMUP_RUNS = 100

# Number of timed repetitions per query/ranking pair.
REPETITIONS = 1000


def short_doc_name(url: str) -> str:
    """
    Convert a quotes.toscrape URL into a short page label for readable output.
    """
    if url.endswith("/page/1/"):
        return "page/1"
    if "/page/" in url:
        return url.rstrip("/").split("/")[-2] + "/" + url.rstrip("/").split("/")[-1]
    return url.rstrip("/").split("/")[-1] or url


def format_score(score: int | float) -> str:
    if isinstance(score, float):
        return f"{score:.4f}"
    return str(score)


def warmup(index, queries: Iterable[str], rankings: Iterable[str], runs: int) -> None:
    """
    Warm up the code paths before measuring timings.
    """
    for _ in range(runs):
        for query in queries:
            for ranking in rankings:
                get_ranked_results(index, query, ranking=ranking)


def benchmark_query(index, query: str, ranking: str, repetitions: int) -> dict[str, float]:
    """
    Benchmark one query/ranking pair and return timing statistics in milliseconds.
    """
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


def print_timing_table(results: dict[str, dict[str, dict[str, float]]]) -> None:
    """
    Print a readable timing summary for each ranking algorithm.
    """
    print("=== Timing Results (ms/query) ===\n")

    for ranking, query_stats in results.items():
        print(f"--- {ranking.upper()} ---")
        print(
            f"{'Query':<18} {'Mean':>10} {'Median':>10} {'Min':>10} {'Max':>10} {'Std Dev':>10}"
        )

        means: list[float] = []

        for query, stats in query_stats.items():
            means.append(stats["mean"])
            print(
                f"{query:<18} "
                f"{stats['mean']:>10.4f} "
                f"{stats['median']:>10.4f} "
                f"{stats['min']:>10.4f} "
                f"{stats['max']:>10.4f} "
                f"{stats['stdev']:>10.4f}"
            )

        avg_mean = statistics.mean(means)
        print(f"\n{'Average mean':<18} {avg_mean:>10.4f}\n")


def print_relative_speed_summary(results: dict[str, dict[str, dict[str, float]]]) -> None:
    """
    Compare average mean query times across ranking strategies.
    """
    avg_means = {
        ranking: statistics.mean(stats["mean"] for stats in query_stats.values())
        for ranking, query_stats in results.items()
    }

    print("=== Relative Speed Summary ===\n")
    for ranking, avg in avg_means.items():
        print(f"{ranking:<18} {avg:.4f} ms/query")

    baseline = avg_means["tf"]
    print()
    for ranking, avg in avg_means.items():
        if ranking == "tf":
            continue
        slowdown = avg / baseline if baseline > 0 else float("inf")
        print(f"{ranking:<18} is {slowdown:.2f}x slower than tf")
    print()


def print_top_results(index) -> None:
    """
    Print top-3 results per query for each ranking method.
    """
    print("=== Example Top Results (Top 3) ===\n")

    for query in QUERIES:
        print(f"Query: '{query}'")
        for ranking in RANKINGS:
            results = get_ranked_results(index, query, ranking=ranking)[:3]
            formatted = [
                (short_doc_name(doc), format_score(score))
                for doc, score in results
            ]
            print(f"  {ranking:<18} {formatted}")
        print()


def print_difference_analysis(index) -> None:
    """
    Highlight where TF-IDF and proximity change the top-ranked result.
    """
    print("=== Ranking Difference Analysis ===\n")

    for query in QUERIES:
        tf_results = get_ranked_results(index, query, ranking="tf")
        tfidf_results = get_ranked_results(index, query, ranking="tfidf")
        prox_results = get_ranked_results(index, query, ranking="tfidf_proximity")

        tf_top = short_doc_name(tf_results[0][0]) if tf_results else "None"
        tfidf_top = short_doc_name(tfidf_results[0][0]) if tfidf_results else "None"
        prox_top = short_doc_name(prox_results[0][0]) if prox_results else "None"

        changed_tfidf = tf_top != tfidf_top
        changed_prox = tfidf_top != prox_top

        print(f"Query: '{query}'")
        print(f"  Top tf result:               {tf_top}")
        print(f"  Top tfidf result:            {tfidf_top}")
        print(f"  Top tfidf_proximity result:  {prox_top}")
        print(f"  tf -> tfidf changed top rank:            {'yes' if changed_tfidf else 'no'}")
        print(f"  tfidf -> tfidf_proximity changed top rank: {'yes' if changed_prox else 'no'}")
        print()


def main() -> None:
    if not Path(INDEX_PATH).exists():
        raise FileNotFoundError(
            f"Index file not found at {INDEX_PATH}. Run the build command first."
        )

    index = load_index(INDEX_PATH)

    print(f"Loaded index with {len(index.documents)} documents and {len(index.index)} terms.")
    print(f"Benchmarking {len(QUERIES)} queries over {REPETITIONS} repetitions each.")
    print(f"Warm-up runs: {WARMUP_RUNS}\n")

    warmup(index, QUERIES, RANKINGS, WARMUP_RUNS)

    timing_results: dict[str, dict[str, dict[str, float]]] = {}

    for ranking in RANKINGS:
        timing_results[ranking] = {}
        for query in QUERIES:
            timing_results[ranking][query] = benchmark_query(
                index=index,
                query=query,
                ranking=ranking,
                repetitions=REPETITIONS,
            )

    print_timing_table(timing_results)
    print_relative_speed_summary(timing_results)
    print_top_results(index)
    print_difference_analysis(index)


if __name__ == "__main__":
    main()