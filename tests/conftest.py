"""
Pytest configuration and fixtures for Chunkana tests.
"""

import json
from pathlib import Path

import pytest

# Paths
TESTS_DIR = Path(__file__).parent
BASELINE_DIR = TESTS_DIR / "baseline"
FIXTURES_DIR = BASELINE_DIR / "fixtures"
GOLDEN_DIR = BASELINE_DIR / "golden"
GOLDEN_DIFY_STYLE_DIR = BASELINE_DIR / "golden_dify_style"
GOLDEN_NO_METADATA_DIR = BASELINE_DIR / "golden_no_metadata"


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to baseline fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def golden_dir() -> Path:
    """Path to golden outputs directory."""
    return GOLDEN_DIR


@pytest.fixture
def sample_markdown() -> str:
    """Simple markdown document for testing."""
    return """# Test Document

This is a test document.

## Section One

Some content in section one.

## Section Two

More content in section two.

```python
def hello():
    print("Hello!")
```
"""


@pytest.fixture
def code_heavy_markdown() -> str:
    """Code-heavy markdown for testing."""
    return """# Code Examples

## Python

```python
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```

## JavaScript

```javascript
function factorial(n) {
    return n <= 1 ? 1 : n * factorial(n - 1);
}
```
"""


@pytest.fixture
def list_heavy_markdown() -> str:
    """List-heavy markdown for testing."""
    return """# Shopping List

- Fruits
  - Apples
  - Bananas
- Vegetables
  - Carrots
  - Broccoli

## Tasks

1. First task
2. Second task
   1. Subtask A
   2. Subtask B
3. Third task
"""


def load_golden_output(fixture_name: str) -> dict:
    """Load golden output for a fixture."""
    golden_path = GOLDEN_DIR / f"{fixture_name}.json"
    if not golden_path.exists():
        pytest.skip(f"Golden output not found: {golden_path}")
    return json.loads(golden_path.read_text(encoding="utf-8"))


def load_fixture(fixture_name: str) -> str:
    """Load a fixture markdown file."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.md"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")
