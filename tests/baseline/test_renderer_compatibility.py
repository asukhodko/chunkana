"""
Renderer compatibility tests for Chunkana.

These tests ensure Chunkana renderers produce output matching v2 golden outputs.
Based on BASELINE.md:
- include_metadata=True → render_dify_style()
- include_metadata=False → render_with_embedded_overlap() (v2 uses bidirectional)
"""

import json
from pathlib import Path

import pytest

from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_with_embedded_overlap

TESTS_DIR = Path(__file__).parent.parent
BASELINE_DIR = TESTS_DIR / "baseline"
FIXTURES_DIR = BASELINE_DIR / "fixtures"
GOLDEN_DIFY_STYLE_DIR = BASELINE_DIR / "golden_dify_style"
GOLDEN_NO_METADATA_DIR = BASELINE_DIR / "golden_no_metadata"


def get_fixtures():
    """Get list of fixture files."""
    if not FIXTURES_DIR.exists():
        return []
    return list(FIXTURES_DIR.glob("*.md"))


def load_golden_jsonl(path: Path) -> list[str]:
    """Load golden outputs from JSONL file."""
    outputs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                # Golden files use "text" key (from plugin output)
                outputs.append(data["text"])
    return outputs


@pytest.mark.parametrize("fixture_path", get_fixtures(), ids=lambda p: p.stem)
def test_render_dify_style_compatibility(fixture_path: Path):
    """
    Ensure render_dify_style() matches v2 include_metadata=True output.

    Validates: Requirements 6.3, 19.3
    """
    golden_path = GOLDEN_DIFY_STYLE_DIR / f"{fixture_path.stem}.jsonl"

    if not golden_path.exists():
        pytest.skip(f"Golden output not found: {golden_path}")

    # Load fixture and golden output
    markdown = fixture_path.read_text(encoding="utf-8")
    expected_outputs = load_golden_jsonl(golden_path)

    # Chunk with chunkana and render
    chunks = chunk_markdown(markdown)
    actual_outputs = render_dify_style(chunks)

    # Compare count
    assert len(actual_outputs) == len(expected_outputs), (
        f"Output count mismatch: expected {len(expected_outputs)}, got {len(actual_outputs)}"
    )

    # Compare each output
    for i, (actual, expected) in enumerate(zip(actual_outputs, expected_outputs, strict=False)):
        # Normalize line endings
        actual_norm = actual.replace("\r\n", "\n")
        expected_norm = expected.replace("\r\n", "\n")

        # Compare (allowing for minor JSON formatting differences)
        # Extract metadata and content separately for better error messages
        if actual_norm != expected_norm:
            # Try to provide helpful diff
            actual_lines = actual_norm.split("\n")
            expected_lines = expected_norm.split("\n")

            # Find first difference
            for j, (a_line, e_line) in enumerate(zip(actual_lines, expected_lines, strict=False)):
                if a_line != e_line:
                    pytest.fail(
                        f"Chunk {i}, line {j} mismatch:\n"
                        f"Expected: {repr(e_line)}\n"
                        f"Actual: {repr(a_line)}"
                    )

            # Length difference
            if len(actual_lines) != len(expected_lines):
                pytest.fail(
                    f"Chunk {i}: line count mismatch: "
                    f"expected {len(expected_lines)}, got {len(actual_lines)}"
                )


@pytest.mark.parametrize("fixture_path", get_fixtures(), ids=lambda p: p.stem)
def test_render_no_metadata_compatibility(fixture_path: Path):
    """
    Ensure render_with_embedded_overlap() matches v2 include_metadata=False output.

    Per BASELINE.md: v2 uses bidirectional overlap (prev + content + next)
    when include_metadata=False.

    Validates: Requirements 6.4, 6.5, 19.3
    """
    golden_path = GOLDEN_NO_METADATA_DIR / f"{fixture_path.stem}.jsonl"

    if not golden_path.exists():
        pytest.skip(f"Golden output not found: {golden_path}")

    # Load fixture and golden output
    markdown = fixture_path.read_text(encoding="utf-8")
    expected_outputs = load_golden_jsonl(golden_path)

    # Chunk with chunkana and render with bidirectional overlap
    chunks = chunk_markdown(markdown)
    actual_outputs = render_with_embedded_overlap(chunks)

    # Compare count
    assert len(actual_outputs) == len(expected_outputs), (
        f"Output count mismatch: expected {len(expected_outputs)}, got {len(actual_outputs)}"
    )

    # Compare each output
    for i, (actual, expected) in enumerate(zip(actual_outputs, expected_outputs, strict=False)):
        # Normalize line endings
        actual_norm = actual.replace("\r\n", "\n")
        expected_norm = expected.replace("\r\n", "\n")

        assert actual_norm == expected_norm, (
            f"Chunk {i}: content mismatch:\n"
            f"Expected ({len(expected_norm)} chars): {repr(expected_norm[:200])}\n"
            f"Actual ({len(actual_norm)} chars): {repr(actual_norm[:200])}"
        )


def test_golden_dify_style_outputs_exist():
    """Verify golden dify_style outputs are present."""
    assert GOLDEN_DIFY_STYLE_DIR.exists(), (
        f"Golden dify_style directory not found: {GOLDEN_DIFY_STYLE_DIR}"
    )
    golden_files = list(GOLDEN_DIFY_STYLE_DIR.glob("*.jsonl"))
    assert len(golden_files) > 0, "No golden dify_style output files found"


def test_golden_no_metadata_outputs_exist():
    """Verify golden no_metadata outputs are present."""
    assert GOLDEN_NO_METADATA_DIR.exists(), (
        f"Golden no_metadata directory not found: {GOLDEN_NO_METADATA_DIR}"
    )
    golden_files = list(GOLDEN_NO_METADATA_DIR.glob("*.jsonl"))
    assert len(golden_files) > 0, "No golden no_metadata output files found"
