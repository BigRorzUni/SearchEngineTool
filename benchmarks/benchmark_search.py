from __future__ import annotations

import statistics
import time
from pathlib import Path

from src.search import get_ranked_results
from src.storage import load_index


INDEX_PATH = "data/index.json"

QUERIES = [
    "life",
    "friends",
    "truth",
    "books",
    "love life",
    "good friends",
    "the",
]

RANKINGS = ["tf", "tfidf"]
REPETITIONS = 1000


def benchmark_query(index, query: str, ranking: str, repetitions: int) -> float:
    timings = []

    for _ in range(repetitions):
        start = time.perf_counter()
        get_ranked_results(index, query, ranking=ranking)
        end = time.perf_counter()
        timings.append(end - start)

    return statistics.mean(timings)


def main() -> None:
    if not Path(INDEX_PATH).exists():
        raise FileNotFoundError(
            f"Index file not found at {INDEX_PATH}. Run the build command first."
        )

    index = load_index(INDEX_PATH)

    print(f"Loaded index with {len(index.documents)} documents and {len(index.index)} terms.\n")
    print(f"Benchmarking {len(QUERIES)} queries over {REPETITIONS} repetitions each.\n")

    for ranking in RANKINGS:
        print(f"=== Ranking: {ranking} ===")
        overall = []

        for query in QUERIES:
            avg_time = benchmark_query(index, query, ranking, REPETITIONS)
            overall.append(avg_time)
            print(f"{query:<15} {avg_time * 1000:.4f} ms/query")

        print(f"Average across queries: {statistics.mean(overall) * 1000:.4f} ms/query\n")

    print("=== Example top results ===")
    for query in QUERIES:
        print(f"\nQuery: {query}")
        for ranking in RANKINGS:
            results = get_ranked_results(index, query, ranking=ranking)[:3]
            print(f"  {ranking}: {results}")


if __name__ == "__main__":
    main()