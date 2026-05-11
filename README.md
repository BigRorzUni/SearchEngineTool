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
python3 -m venv venv
source venv/bin/activate
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

## Evaluation of Ranking Algorithms

This project evaluates four ranking strategies:

- **Term Frequency (TF)** — baseline ranking using summed term frequency
- **TF + Proximity** — TF ranking enhanced with positional proximity
- **TF-IDF** — ranking using inverse document frequency
- **TF-IDF + Proximity** — ranking combining rarity and positional proximity

The goal is to compare computational performance, retrieval quality, and algorithmic trade-offs.

### Methodology

A benchmark was conducted using representative queries:

- single-term queries: `life`, `truth`
- multi-term queries: `good friends`, `love life`, `make life`, `life truth`, `friend life`
- common-word query: `the`

Each query was executed **1000 times**, with warm-up runs to reduce caching and interpreter effects.

### Computational Performance

| Ranking Method | Average Time per Query |
|---|---:|
| TF | 0.0086 ms |
| TF + Proximity | 0.0148 ms |
| TF-IDF | 0.0120 ms |
| TF-IDF + Proximity | 0.0165 ms |

Compared to TF:

- TF + Proximity is approximately **1.71× slower**
- TF-IDF is approximately **1.39× slower**
- TF-IDF + Proximity is approximately **1.91× slower**

All query times remain below **0.02 ms per query**, so the runtime overhead is negligible for this dataset.

Expected complexity trend:

```text
TF < TF-IDF ≈ TF + Proximity < TF-IDF + Proximity
```

### Retrieval Quality Analysis

For the query `the`, TF ranks documents by raw frequency, while TF-IDF down-weights this common low-information term.

For multi-term queries, proximity scoring rewards documents where query terms occur close together. This improves phrase-like queries such as `good friends` and `love life`.

Observed ranking changes include:

- `life`: TF selects `page/2`, while TF-IDF selects `page/10`
- `love life`: TF selects `page/2`, while TF-IDF selects `page/5`
- `make life`: TF-IDF selects `page/5`, while TF-IDF + Proximity selects `page/2`

### Trade-Off Analysis

| Aspect | TF | TF + Proximity | TF-IDF | TF-IDF + Proximity |
|---|---|---|---|---|
| Computational cost | Very low | Higher | Slightly higher | Highest |
| Implementation complexity | Simple | Moderate | Moderate | Most complex |
| Handling common terms | Poor | Poor | Strong | Strong |
| Multi-term query quality | Basic | Improved | Improved | Strongest |
| Positional awareness | None | Yes | None | Yes |

### Conclusion

TF provides a fast baseline but suffers from frequency bias.

TF-IDF improves ranking by incorporating term rarity.

Proximity scoring improves multi-term queries by using positional information.

TF-IDF + Proximity provides the most context-aware ranking while remaining fast enough for this dataset.

### Limitations

- small dataset size
- benchmark timings are affected by interpreter noise
- TF-IDF remains a bag-of-words model
- proximity scoring only considers adjacent query terms

### Future Work

Potential improvements include:

- exact phrase search
- more advanced proximity scoring
- query expansion and synonym handling
- evaluation on larger datasets
- learning-based ranking approaches