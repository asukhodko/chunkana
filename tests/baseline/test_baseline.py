"""
Baseline compatibility tests for Chunkana.

These tests ensure Chunkana output matches dify-markdown-chunker v2 golden outputs.
"""

import json
from pathlib import Path

import pytest

from chunkana import chunk_markdown

TESTS_DIR = Path(__file__).parent.parent
BASELINE_DIR = TESTS_DIR / "baseline"
FIXTURES_DIR = BASELINE_DIR / "fixtures"
GOLDEN_DIR = BASELINE_DIR / "golden"


def get_fixtures():
    """Get list of fixture files."""
    if not FIXTURES_DIR.exists():
        return []
    return list(FIXTURES_DIR.glob("*.md"))


@pytest.mark.parametrize("fixture_path", get_fixtures(), ids=lambda p: p.stem)
def test_baseline_compatibility(fixture_path: Path):
    """Ensure chunkana output matches v2 golden outputs."""
    golden_path = GOLDEN_DIR / f"{fixture_path.stem}.json"
    
    if not golden_path.exists():
        pytest.skip(f"Golden output not found: {golden_path}")
    
    # Load fixture and golden output
    markdown = fixture_path.read_text(encoding="utf-8")
    expected = json.loads(golden_path.read_text(encoding="utf-8"))
    
    # Chunk with chunkana
    chunks = chunk_markdown(markdown)
    actual = [c.to_dict() for c in chunks]
    
    # Compare chunk count
    assert len(actual) == len(expected["chunks"]), (
        f"Chunk count mismatch: expected {len(expected['chunks'])}, got {len(actual)}"
    )
    
    # Compare each chunk
    for i, (a, e) in enumerate(zip(actual, expected["chunks"])):
        # Line numbers must match exactly
        assert a["start_line"] == e["start_line"], (
            f"Chunk {i}: start_line mismatch: expected {e['start_line']}, got {a['start_line']}"
        )
        assert a["end_line"] == e["end_line"], (
            f"Chunk {i}: end_line mismatch: expected {e['end_line']}, got {a['end_line']}"
        )
        
        # Strategy must match
        assert a["metadata"]["strategy"] == e["metadata"]["strategy"], (
            f"Chunk {i}: strategy mismatch: "
            f"expected {e['metadata']['strategy']}, got {a['metadata']['strategy']}"
        )
        
        # Content comparison: normalize line endings only, NO .strip()
        # Using .strip() hides whitespace bugs - don't do it
        actual_content = a["content"].replace("\r\n", "\n")
        expected_content = e["content"].replace("\r\n", "\n")
        assert actual_content == expected_content, (
            f"Chunk {i}: content mismatch:\n"
            f"Expected: {repr(expected_content[:100])}\n"
            f"Actual: {repr(actual_content[:100])}"
        )


def test_baseline_fixtures_exist():
    """Verify baseline fixtures are present."""
    assert FIXTURES_DIR.exists(), f"Fixtures directory not found: {FIXTURES_DIR}"
    fixtures = list(FIXTURES_DIR.glob("*.md"))
    assert len(fixtures) > 0, "No fixture files found"


def test_golden_outputs_exist():
    """Verify golden outputs are present."""
    assert GOLDEN_DIR.exists(), f"Golden directory not found: {GOLDEN_DIR}"
    golden_files = list(GOLDEN_DIR.glob("*.json"))
    assert len(golden_files) > 0, "No golden output files found"
