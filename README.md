# SearchEngineTool
A Python-based command-line search engine that crawls a website, builds an inverted index, and supports query-based retrieval with ranking.

## Setup

python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt


## Testing

This project uses `pytest` for unit testing and `pytest-cov` for coverage analysis.

### Running tests

To run all tests:

```bash
pytest
```

To run tests with coverage
```bash
pytest --cov=src --cov-report=term-missing
```

## Run

```bash
python -m src.main
```

Once running, you will see:

```bash
Search Engine Tool
Commands: build, load, print <word>, find <query>, exit
```

### build
Crawls the target website, builds the inverted index, and saves it to disk.
```bash
> build
```
-   Fetches all pages
-   Extracts text content
-   Builds an inverted index
-   Saves it to data/index.json

⸻

### load
Loads a previously saved index from disk.
```bash
> load
```
Use this to avoid re-crawling the website every time.


### print <word>
Displays the inverted index entry for a specific word.
```bash
> print life
```
Output includes:
-   Documents containing the word
-   Term frequency per document
-   Positions of the word
-   Document frequency

### find <query>
Searches for documents containing all query terms.
```bash
> find good friends
```
Returns:
-   Matching documents
-   Ranked by relevance (based on term frequency)
-   Document titles

### exit
Exits the program.
```bash
> exit
```

### Example Workflow
```bash
> build
> print life
> find good friends
> exit
```

## Troubleshooting

If you encounter import issues, ensure you are running the tool as a module:
```bash
python -m src.main
```
Running ```bash python src/main.py``` may not work correctly due to package imports.



## Evaluation of Ranking Algorithms

This project evaluates two ranking strategies for information retrieval:

- **Term Frequency (TF)** — baseline approach using summed term frequency
- **TF-IDF** — enhanced ranking incorporating inverse document frequency

The goal is to compare both **computational performance** and **retrieval quality**.

---

### Methodology

A benchmark was conducted using a fixed set of representative queries:

- Single-term queries: `life`, `friends`, `truth`, `books`
- Multi-term queries: `love life`, `good friends`
- Common-word query: `the`

Each query was executed **1000 times** to obtain stable timing measurements.

Performance was measured using `time.perf_counter()` and averaged across runs.

---

### Computational Performance

| Ranking Method | Average Time per Query |
|---------------|----------------------|
| TF            | 0.0069 ms            |
| TF-IDF        | 0.0158 ms            |

TF-IDF is approximately **2.3× slower** than the baseline TF approach.  
This overhead arises from:

- logarithmic IDF computation
- floating-point arithmetic
- length normalisation

However, absolute query times remain **extremely low (<0.02 ms)**, making the performance difference negligible for this dataset.

---

### Retrieval Quality Analysis

#### 1. Handling Frequent Terms

For the query `the`:

- TF ranks documents purely by frequency
- TF-IDF reduces the influence of this common term

This demonstrates TF-IDF’s ability to **down-weight high-frequency, low-information terms**, improving result relevance.

---

#### 2. Multi-Term Query Behaviour

For the query `love life`:

- TF prioritises documents with the highest raw counts
- TF-IDF produces a different ranking that better reflects meaningful term combinations

TF-IDF therefore provides improved **semantic relevance** for compound queries.

---

#### 3. Relevance vs Frequency

For queries such as `life`:

- TF favours documents with many occurrences
- TF-IDF balances frequency with term distinctiveness across the corpus

This results in a more **informative ranking**, rather than simply rewarding repetition.

---

#### 4. Discovery of Relevant Documents

TF-IDF occasionally promotes documents that are not top-ranked under TF, indicating improved sensitivity to **informative term usage** rather than raw counts alone.

---

### Trade-Off Analysis

| Aspect              | TF (Baseline)        | TF-IDF                     |
|--------------------|---------------------|----------------------------|
| Computational cost | Very low            | Slightly higher            |
| Implementation     | Simple              | Moderate complexity        |
| Ranking quality    | Frequency-biased    | More semantically meaningful |
| Handling common terms | Poor            | Strong                     |
| Multi-term queries | Basic               | Improved                   |

---

### Conclusion

While TF provides a fast and simple baseline, TF-IDF offers **significantly improved ranking quality** with only a negligible increase in computational cost.

Therefore, TF-IDF represents a better overall trade-off for search relevance in this system.

---

### Limitations

- The dataset is small (10 pages), so performance differences are minimal
- TF-IDF remains a **bag-of-words model**, ignoring word order and proximity
- Further improvements could include:
  - proximity-based ranking
  - phrase search
  - query expansion techniques

These enhancements are explored as potential future work.