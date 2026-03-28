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





