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
- `find <query>` – search using term frequency (TF)
- `find <query> --tfidf` – use TF-IDF ranking
- `find <query> --proximity` – use TF + proximity
- `find <query> --tfidf --proximity` – use TF-IDF + proximity

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

This project evaluates three ranking strategies for information retrieval:

- **Term Frequency (TF)** — baseline approach using summed term frequency  
- **TF-IDF** — enhanced ranking incorporating inverse document frequency  
- **TF-IDF + Proximity** — extended ranking incorporating positional information to reward term closeness  

The goal is to compare both **computational performance** and **retrieval quality**, and analyse the trade-offs between algorithmic complexity and ranking effectiveness.

---

### Methodology

A benchmark was conducted using a fixed set of representative queries:

- Single-term queries: `life`, `truth`  
- Multi-term queries: `good friends`, `love life`, `make life`, `life truth`, `friend life`  
- Common-word query: `the`  

Each query was executed **1000 times**, with additional warm-up runs to reduce caching and interpreter effects.

Performance was measured using `time.perf_counter()` and averaged across runs.

---

### Computational Performance

| Ranking Method         | Average Time per Query |
|-----------------------|----------------------|
| TF                    | 0.0086 ms            |
| TF-IDF                | 0.0108 ms            |
| TF-IDF + Proximity    | 0.0162 ms            |

TF-IDF is approximately **1.26× slower** than TF, while TF-IDF with proximity is approximately **1.88× slower**.

This overhead arises from:

- logarithmic IDF computation  
- floating-point arithmetic  
- additional positional distance calculations for proximity scoring  

However, all query times remain extremely small (**<0.02 ms per query**), meaning:

- differences are negligible in practice  
- interpreter overhead and system noise influence measurements  
- all approaches are effectively instantaneous at this scale  

From a theoretical perspective, the expected complexity relationship is: `TF < TF-IDF < TF-IDF + Proximity`
which aligns with the observed trend in average timings.

---

### Retrieval Quality Analysis

#### 1. Handling Frequent Terms

For the query `the`:

- TF ranks documents purely by frequency  
- TF-IDF significantly reduces the influence of this common term  

This demonstrates TF-IDF’s ability to **down-weight high-frequency, low-information terms**, producing more meaningful rankings.

---

#### 2. Multi-Term Query Behaviour

For queries such as `love life` and `good friends`:

- TF prioritises documents with the highest raw counts  
- TF-IDF produces rankings that better reflect meaningful combinations of terms  
- TF-IDF + Proximity further refines results by rewarding documents where terms appear close together  

This improves **phrase-like query interpretation**.

---

#### 3. Proximity Effects

The proximity-based ranking introduces a bonus based on the distance between query terms.

- Documents where terms are closer together receive a higher score  
- Documents with dispersed terms receive a smaller or negligible bonus  

For example:

- In `make life`, TF-IDF ranks `page/5` highest  
- With proximity, `page/2` becomes the top result  

This demonstrates that proximity ranking can **change top-ranked documents** when term closeness is significant.

For single-term queries, proximity has **no effect**, as no inter-term distance exists. This behaviour is expected and confirms the correctness of the implementation.

---

#### 4. Relevance vs Frequency

For queries such as `life`:

- TF favours documents with repeated occurrences  
- TF-IDF balances frequency with term rarity  
- TF-IDF + Proximity adds contextual relevance through term positioning  

This progression shows increasingly **informative and context-aware ranking behaviour**.

---

#### 5. Ranking Differences

Changes in top-ranked documents were observed:

- **TF → TF-IDF** changes ranking by reducing common-term bias  
- **TF-IDF → TF-IDF + Proximity** occasionally changes rankings based on term closeness  

Notably:

- `life`: TF selects `page/2`, while TF-IDF selects `page/10`  
- `love life`: TF selects `page/2`, while TF-IDF selects `page/5`  
- `make life`: proximity ranking changes the top result from `page/5` (TF-IDF) to `page/2`  

This confirms that each method captures **different aspects of relevance**.

---

### Trade-Off Analysis

| Aspect                  | TF (Baseline)        | TF-IDF                     | TF-IDF + Proximity          |
|-------------------------|---------------------|----------------------------|-----------------------------|
| Computational cost      | Very low            | Slightly higher            | Higher                      |
| Implementation          | Simple              | Moderate complexity        | More complex                |
| Ranking quality         | Frequency-biased    | More semantically meaningful | Most context-aware         |
| Handling common terms   | Poor                | Strong                     | Strong                      |
| Multi-term queries      | Basic               | Improved                   | Strong                      |
| Use of positional data  | None                | None                       | Full utilisation            |

---

### Conclusion

The baseline TF approach provides a fast and simple ranking method but suffers from strong frequency bias and poor handling of common terms.

TF-IDF significantly improves ranking quality by incorporating term rarity, producing more meaningful results with minimal computational overhead.

TF-IDF with proximity further enhances retrieval performance by leveraging positional information to capture relationships between terms, improving multi-word query relevance and occasionally altering top-ranked results.

Although these methods introduce additional computational complexity, benchmarking shows that their runtime cost is negligible for this dataset. Therefore, the improved ranking quality justifies their use.

---

### Limitations

- The dataset is small (10 documents), limiting observable performance differences  
- Benchmark timings are influenced by measurement noise due to extremely small execution times  
- TF-IDF remains a **bag-of-words model**, ignoring full phrase structure  
- Proximity scoring considers only adjacent query terms  

---

### Future Work

Potential improvements include:

- exact phrase search  
- more advanced proximity scoring models  
- query expansion and synonym handling  
- evaluation on larger datasets  
- learning-based ranking approaches  

These extensions would further improve retrieval quality and bring the system closer to real-world search engine behaviour.