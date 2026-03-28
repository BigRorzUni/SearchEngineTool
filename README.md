# SearchEngineTool

## Setup

python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

## Run
python src/main.py

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