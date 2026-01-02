# Contributing to Chunkana

Thank you for your interest in contributing to Chunkana!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/asukhodko/chunkana.git
cd chunkana
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Code Style

We use:
- **ruff** for linting and formatting
- **mypy** for type checking

Run checks:
```bash
ruff check src/chunkana
mypy src/chunkana
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=chunkana

# Specific test file
pytest tests/unit/test_chunk.py
```

### Test Categories

- `tests/unit/` - Unit tests for individual components
- `tests/property/` - Property-based tests using hypothesis
- `tests/baseline/` - Compatibility tests with dify-markdown-chunker v2
- `tests/examples/` - Documentation example tests

### Baseline Tests

Baseline tests ensure compatibility with dify-markdown-chunker v2:

```bash
# Regenerate golden outputs (requires dify-markdown-chunker)
python scripts/generate_baseline.py

# Run baseline tests
pytest tests/baseline/
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Reporting Issues

Please include:
- Python version
- Chunkana version
- Minimal reproducible example
- Expected vs actual behavior
