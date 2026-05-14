# SearchEngineTool

A Python-based command-line search engine that crawls a website, builds a positional inverted index, and supports query-based retrieval with multiple ranking strategies.

## Features

- Polite web crawler with optional depth-limited traversal
- URL canonicalisation to avoid duplicate homepage/page-one indexing
- Positional inverted index storing term frequency and token positions
- Search using TF, TF-IDF, proximity ranking, and combined TF-IDF + proximity
- JSON-based index persistence
- Benchmarking script for ranking algorithm comparison
- Automated test suite using `pytest` and `pytest-cov`

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Tool

Run the application from the project root:

```bash
python -m src.main
```

Once running, type:

```bash
> help
```

to view available commands.

## Commands

### `build`

Crawls the target website, builds the inverted index, and saves it to `data/index.json`.

```bash
> build
```

Optionally, a maximum traversal depth can be specified:

```bash
> build --depth 0
> build --depth 3
```

- `build` crawls all allowed pages
- `build --depth 0` indexes only the start page
- `build --depth N` follows links up to depth `N`
- extracts quote text, authors, and tags
- builds an inverted index with term frequencies and token positions
- saves the compiled index to `data/index.json`

### `load`

Loads a previously saved index from disk.

```bash
> load
```

Use this to avoid re-crawling the website every time.

### `print <word>`

Displays the inverted index entry for a specific word.

```bash
> print life
```

Output includes:

- documents containing the word
- term frequency per document
- token positions of the word
- document frequency

### `find <query>`

Searches for documents containing all query terms.

```bash
> find good friends
```

Supported ranking modes:

```bash
> find <query>
> find <query> --tfidf
> find <query> --proximity
> find <query> --tfidf --proximity
> find <query> --compare
```

- `find <query>` uses Term Frequency (TF)
- `find <query> --tfidf` uses TF-IDF ranking
- `find <query> --proximity` uses TF + proximity ranking
- `find <query> --tfidf --proximity` uses TF-IDF + proximity ranking
- `find <query> --compare` compares all ranking strategies for the query

### `clear`

Clears the terminal.

```bash
> clear
```

### `exit`

Exits the program.

```bash
> exit
```

Aliases:

```bash
> quit
> q
```

## Example Workflow

```bash
> build
> print life
> find good friends
> find love life --compare
> exit
```

## Testing

This project uses `pytest` for unit testing and `pytest-cov` for coverage analysis.

Run all tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src --cov-report=term-missing
```

The tests cover:

- tokenisation and inverted index construction
- term frequencies and positional indexing
- save/load behaviour
- search and ranking behaviour
- crawler behaviour using mocked HTTP requests
- command parsing and error handling

## Benchmarking

This project includes a benchmark script for comparing:

- Term Frequency (TF)
- TF + Proximity
- TF-IDF
- TF-IDF + Proximity

Before running benchmarks, ensure an index exists:

```bash
python -m src.main
```

Then inside the tool:

```bash
> build
> exit
```

Run the benchmark script:

```bash
python -m benchmarks.benchmark_search
```

The benchmark outputs:

- mean query time
- median query time
- minimum and maximum timings
- standard deviation
- relative slowdown versus TF
- top-3 search results for each ranking method
- ranking difference analysis

## Troubleshooting

Run the tool as a module:

```bash
python -m src.main
```

Running this may not work correctly due to package imports:

```bash
python src/main.py
```

# Evaluation of Ranking Algorithms

This project evaluates four ranking strategies:

- TF — baseline ranking using summed term frequency
- TF + Proximity — TF ranking enhanced using positional scoring
- TF-IDF — ranking using inverse document frequency
- TF-IDF + Proximity — ranking combining rarity weighting and positional scoring

The goal was to compare computational performance, retrieval quality, and algorithmic trade-offs.

## Methodology

Benchmarks were conducted using representative query types:

- single-term queries: `life`, `truth`
- multi-term queries: `good friends`, `love life`, `make life`, `life truth`, `friend life`
- common-term queries: `the`, `the life, `the end`

Each query was executed 1000 times with 100 warm-up runs to reduce interpreter and caching effects.

Benchmark configuration:

- Documents indexed: 10
- Indexed terms: 849
- Queries benchmarked: 9

## Computational Performance

| Ranking Method | Average Mean | Median of Medians | Avg Std Dev | Slowdown vs TF |
|---|---:|---:|---:|---:|
| TF | 0.0039 ms | 0.0038 ms | 0.0008 ms | baseline |
| TF + Proximity | 0.0087 ms | 0.0067 ms | 0.0018 ms | 2.26× |
| TF-IDF | 0.0067 ms | 0.0067 ms | 0.0013 ms | 1.72× |
| TF-IDF + Proximity | 0.0116 ms | 0.0087 ms | 0.0018 ms | 2.99× |

All query times remained below 0.02 milliseconds per query, so runtime overhead remained negligible for this dataset.

Observed complexity trend:

```text
TF < TF-IDF ≈ TF + Proximity < TF-IDF + Proximity
```

TF is computationally simplest because it only sums term frequencies.

TF-IDF introduces inverse document frequency calculations, while proximity ranking requires positional comparisons between query terms.

Combining TF-IDF and proximity produced the highest computational cost because both rarity weighting and positional scoring are applied.

## Retrieval Quality Analysis

The benchmark also evaluated how ranking strategies affected retrieval quality.

For the query `the life`:

- TF selected `page/2`
- TF-IDF selected `page/10`

This demonstrates how TF-IDF changes rankings by reducing the influence of the extremely common term the and placing greater emphasis on the more informative term life.

For the query `good friends`:

- TF selected `page/2`
- TF + Proximity also selected `page/2`
- however, the proximity score bonus increased because the terms appeared close together within the document

This demonstrates how positional scoring can strengthen phrase-like matches even when ranking order remains unchanged.

For the query `love life`:

- TF selected `page/2`
- TF-IDF selected `page/5`

For the query `make life`:

- TF-IDF selected `page/5`
- TF-IDF + Proximity selected `page/2`

This demonstrates how proximity scoring can change rankings by rewarding documents where query terms appear closer together.

For common-term queries such as `the`:

- TF selected `page/9`
- TF-IDF selected `page/4`

TF strongly favours repetition frequency, while TF-IDF reduces the influence of extremely common terms that appear across many documents.

The query `the life` demonstrated the combined impact of rarity weighting and proximity scoring:

- TF selected `page/2`
- TF-IDF selected `page/10`
- TF-IDF + Proximity still selected `page/10`, but significantly increased the score separation from other pages

This demonstrates how TF-IDF prioritises informative terms while proximity scoring strengthens phrase-like matches.

## Trade-Off Analysis

| Aspect | TF | TF + Proximity | TF-IDF | TF-IDF + Proximity |
|---|---|---|---|---|
| Computational cost | Very low | Higher | Slightly higher | Highest |
| Implementation complexity | Simple | Moderate | Moderate | Most complex |
| Handling common terms | Poor | Poor | Strong | Strong |
| Multi-term query quality | Basic | Improved | Improved | Strongest |
| Positional awareness | None | Yes | None | Yes |

## Conclusion

TF provides a fast and simple baseline ranking strategy but suffers from frequency bias.

TF + Proximity improves phrase-like query handling by incorporating positional information into ranking decisions.

TF-IDF improves semantic relevance by incorporating term rarity into ranking decisions.

TF-IDF + Proximity produced the most context-aware retrieval behaviour while remaining computationally inexpensive for the dataset used in this project.

## Limitations

Current limitations include:

- relatively small dataset size
- benchmark timings affected by Python interpreter noise
- TF-IDF remaining a bag-of-words model without semantic understanding
- proximity scoring only considering adjacent query terms
- no support for exact phrase search or synonym expansion

## Future Work

Potential future improvements include:

- exact phrase matching
- more advanced proximity scoring
- stemming and stop-word removal
- synonym expansion and query suggestion
- evaluation on larger datasets
- semantic retrieval using embeddings or vector search