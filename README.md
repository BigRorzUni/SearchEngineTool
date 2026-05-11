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
Optionally a max traversal depth can be specified
```bash
> build --depth 0
> build --depth 3
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

This project evaluates four ranking strategies for information retrieval:

- **Term Frequency (TF)** — baseline approach using summed term frequency  
- **TF + Proximity** — frequency-based ranking enhanced with positional proximity  
- **TF-IDF** — ranking incorporating inverse document frequency  
- **TF-IDF + Proximity** — ranking combining term rarity with positional proximity  

The goal is to compare both **computational performance** and **retrieval quality**, and to analyse the trade-offs between algorithmic complexity and ranking effectiveness.

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

| Ranking Method      | Average Time per Query |
|--------------------|------------------------|
| TF                 | 0.0086 ms              |
| TF + Proximity     | 0.0148 ms              |
| TF-IDF             | 0.0120 ms              |
| TF-IDF + Proximity | 0.0165 ms              |

Compared to the TF baseline:

- **TF + Proximity** is approximately **1.71× slower**
- **TF-IDF** is approximately **1.39× slower**
- **TF-IDF + Proximity** is approximately **1.91× slower**

This overhead arises from:

- logarithmic IDF computation  
- floating-point arithmetic  
- positional distance calculations for proximity scoring  

However, all query times remain extremely small (**<0.02 ms per query**), meaning:

- differences are negligible in practice  
- interpreter overhead and system noise influence measurements  
- all approaches are effectively instantaneous at this scale  

From a theoretical perspective, the expected complexity relationship is:

`TF < TF-IDF ≈ TF + Proximity < TF-IDF + Proximity`

which broadly aligns with the observed timing trend.

---

### Retrieval Quality Analysis

#### 1. Handling Frequent Terms

For the query `the`:

- TF ranks documents purely by raw frequency  
- TF + Proximity behaves identically to TF, because proximity has no effect for single-term queries  
- TF-IDF significantly reduces the influence of this common term  
- TF-IDF + Proximity behaves identically to TF-IDF for the same reason  

This demonstrates TF-IDF’s ability to **down-weight high-frequency, low-information terms**, producing more meaningful rankings.

---

#### 2. Effect of Proximity Alone

Introducing proximity without IDF allows the effect of positional information to be isolated.

For example:

- In `good friends`, TF ranks `page/2` above `page/6`
- TF + Proximity preserves the same top-ranked document, but increases the score gap because `page/2` contains the terms closer together

This shows that proximity can strengthen ranking confidence even when it does not change the final ordering.

---

#### 3. Multi-Term Query Behaviour

For multi-term queries such as `love life` and `make life`:

- TF prioritises documents with the highest raw counts  
- TF + Proximity rewards documents where terms occur nearer each other  
- TF-IDF produces rankings that better reflect meaningful combinations of terms by accounting for rarity  
- TF-IDF + Proximity combines both effects, rewarding documents that are both informative and locally coherent  

This improves **phrase-like query interpretation**.

---

#### 4. Proximity Effects

The proximity-based ranking introduces a bonus based on the distance between query terms.

- Documents where terms are closer together receive a higher score  
- Documents with dispersed terms receive a smaller bonus  
- For single-term queries, proximity has **no effect**, as no inter-term distance exists  

For example:

- In `make life`, TF-IDF ranks `page/5` highest  
- With TF-IDF + Proximity, `page/2` becomes the top result  

This demonstrates that proximity ranking can **change top-ranked documents** when term closeness is significant.

---

#### 5. Relevance vs Frequency

For queries such as `life`:

- TF strongly favours documents with repeated occurrences  
- TF + Proximity does not change the ranking, because the query contains only one term  
- TF-IDF balances frequency with term rarity, changing the top result from `page/2` to `page/10`  
- TF-IDF + Proximity again matches TF-IDF for the same reason  

This highlights that TF-IDF contributes most strongly when rarity matters, whereas proximity contributes most strongly on multi-term queries.

---

#### 6. Ranking Differences

Changes in top-ranked documents were observed:

- **TF → TF + Proximity** did not change the top result for any benchmark query, but often increased score separation for multi-term queries  
- **TF → TF-IDF** changed the top result for `life`, `love life`, `make life`, and `the`  
- **TF-IDF → TF-IDF + Proximity** changed the top result for `make life`  

Notably:

- `life`: TF selects `page/2`, while TF-IDF selects `page/10`
- `love life`: TF selects `page/2`, while TF-IDF selects `page/5`
- `make life`: TF-IDF selects `page/5`, while TF-IDF + Proximity selects `page/2`

This confirms that each method captures **different aspects of relevance**:

- TF captures repetition  
- Proximity captures local term relationships  
- TF-IDF captures rarity  
- TF-IDF + Proximity combines all three

---

### Trade-Off Analysis

| Aspect               | TF (Baseline)     | TF + Proximity        | TF-IDF                     | TF-IDF + Proximity        |
|----------------------|-------------------|-----------------------|----------------------------|---------------------------|
| Computational cost   | Very low          | Higher                | Slightly higher            | Highest                   |
| Implementation       | Simple            | Moderate              | Moderate                   | Most complex              |
| Ranking quality      | Frequency-biased  | Better for multi-term queries | More semantically meaningful | Most context-aware     |
| Handling common terms| Poor              | Poor                  | Strong                     | Strong                    |
| Multi-term queries   | Basic             | Improved              | Improved                   | Strongest                 |
| Use of positional data | None            | Full utilisation      | None                       | Full utilisation          |

---

### Conclusion

The baseline TF approach provides a fast and simple ranking method but suffers from strong frequency bias and poor handling of common terms.

Adding proximity to TF improves sensitivity to local term relationships, but on this dataset it mainly affects score separation rather than final top-ranked documents.

TF-IDF significantly improves ranking quality by incorporating term rarity, producing more meaningful results with minimal computational overhead.

TF-IDF + Proximity further enhances retrieval performance by leveraging positional information to capture relationships between terms, improving multi-word query relevance and, in some cases, altering top-ranked results.

Although the more advanced methods introduce additional computational complexity, benchmarking shows that their runtime cost remains negligible for this dataset. Therefore, the improved ranking quality justifies their use.

---

### Limitations

- The dataset is small (10 documents), limiting observable performance differences  
- Benchmark timings are influenced by measurement noise due to extremely small execution times  
- TF-IDF remains a **bag-of-words model**, ignoring full phrase structure  
- Proximity scoring considers only adjacent query terms  
- On this dataset, TF + Proximity often strengthens score differences without changing final rankings  

---

### Future Work

Potential improvements include:

- exact phrase search  
- more advanced proximity scoring models  
- query expansion and synonym handling  
- evaluation on larger datasets  
- learning-based ranking approaches  

These extensions would further improve retrieval quality and bring the system closer to real-world search engine behaviour.