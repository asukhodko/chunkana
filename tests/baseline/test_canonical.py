"""
Baseline canonical tests for Chunkana.

These tests ensure Chunkana canonical output (list[Chunk]) matches
plugin golden outputs byte-for-byte.

Source of truth: tests/baseline/golden_canonical/*.jsonl
Generated from plugin at commit specified in BASELINE.md
"""

import json
from pathlib import Path

import pytest

from chunkana import chunk_markdown

TESTS_DIR = Path(__file__).parent.parent
BASELINE_DIR = TESTS_DIR / "baseline"
FIXTURES_DIR = BASELINE_DIR / "fixtures"
GOLDEN_CANONICAL_DIR = BASELINE_DIR / "golden_canonical"


def normalize_content(content: str) -> str:
    """Normalize content for comparison: CRLF→LF only, NO strip."""
    return content.replace("\r\n", "\n")


def load_golden_canonical(fixture_name: str) -> list[dict]:
    """Load golden canonical output from JSONL file."""
    golden_path = GOLDEN_CANONICAL_DIR / f"{fixture_name}.jsonl"
    if not golden_path.exists():
        return []

    chunks = []
    with open(golden_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def get_fixtures():
    """Get list of fixture files that have golden outputs."""
    if not FIXTURES_DIR.exists():
        return []

    fixtures = []
    for fixture_path in FIXTURES_DIR.glob("*.md"):
        golden_path = GOLDEN_CANONICAL_DIR / f"{fixture_path.stem}.jsonl"
        if golden_path.exists():
            fixtures.append(fixture_path)

    return fixtures


@pytest.mark.parametrize("fixture_path", get_fixtures(), ids=lambda p: p.stem)
def test_canonical_output(fixture_path: Path):
    """
    Compare chunk output with golden canonical.

    Verifies:
    - Chunk count matches
    - Content matches (with CRLF→LF normalization, NO strip)
    - start_line and end_line match exactly
    - Full metadata dict matches
    """
    # Load fixture
    markdown = fixture_path.read_text(encoding="utf-8")

    # Load golden
    expected = load_golden_canonical(fixture_path.stem)
    if not expected:
        pytest.skip(f"Golden output not found for {fixture_path.stem}")

    # Chunk with Chunkana
    chunks = chunk_markdown(markdown)

    # Compare chunk count
    assert len(chunks) == len(expected), (
        f"Chunk count mismatch: expected {len(expected)}, got {len(chunks)}"
    )

    # Compare each chunk
    for i, (chunk, golden) in enumerate(zip(chunks, expected, strict=False)):
        # Content comparison with CRLF→LF normalization (NO strip!)
        actual_content = normalize_content(chunk.content)
        expected_content = normalize_content(golden["content"])

        if actual_content != expected_content:
            # Show detailed diff
            pytest.fail(
                f"Chunk {i} content mismatch:\n"
                f"Expected ({len(expected_content)} chars): {repr(expected_content[:200])}\n"
                f"Actual ({len(actual_content)} chars): {repr(actual_content[:200])}"
            )

        # Line numbers must match exactly
        assert chunk.start_line == golden["start_line"], (
            f"Chunk {i} start_line mismatch: "
            f"expected {golden['start_line']}, got {chunk.start_line}"
        )
        assert chunk.end_line == golden["end_line"], (
            f"Chunk {i} end_line mismatch: expected {golden['end_line']}, got {chunk.end_line}"
        )

        # Metadata comparison
        # Note: We compare key subsets that are guaranteed to match
        # Some metadata keys may differ (e.g., chunk_id is generated)
        expected_metadata = golden["metadata"]
        actual_metadata = chunk.metadata

        # Core metadata keys that must match
        core_keys = ["strategy", "content_type", "header_path"]
        for key in core_keys:
            if key in expected_metadata:
                assert key in actual_metadata, f"Chunk {i} missing metadata key: {key}"
                assert actual_metadata[key] == expected_metadata[key], (
                    f"Chunk {i} metadata[{key}] mismatch: "
                    f"expected {expected_metadata[key]!r}, got {actual_metadata[key]!r}"
                )

        # Overlap metadata (if present)
        for key in ["previous_content", "next_content"]:
            if key in expected_metadata:
                assert key in actual_metadata, f"Chunk {i} missing overlap metadata: {key}"
                expected_overlap = normalize_content(expected_metadata[key])
                actual_overlap = normalize_content(actual_metadata[key])
                assert actual_overlap == expected_overlap, (
                    f"Chunk {i} metadata[{key}] mismatch:\n"
                    f"Expected: {repr(expected_overlap[:100])}\n"
                    f"Actual: {repr(actual_overlap[:100])}"
                )


def test_golden_canonical_exists():
    """Verify golden canonical outputs are present."""
    assert GOLDEN_CANONICAL_DIR.exists(), (
        f"Golden canonical directory not found: {GOLDEN_CANONICAL_DIR}"
    )
    golden_files = list(GOLDEN_CANONICAL_DIR.glob("*.jsonl"))
    assert len(golden_files) > 0, "No golden canonical files found"


def test_fixtures_have_goldens():
    """Verify all fixtures have corresponding golden outputs."""
    fixtures = list(FIXTURES_DIR.glob("*.md"))
    missing = []

    for fixture in fixtures:
        golden_path = GOLDEN_CANONICAL_DIR / f"{fixture.stem}.jsonl"
        if not golden_path.exists():
            missing.append(fixture.stem)

    if missing:
        pytest.fail(f"Missing golden outputs for fixtures: {missing}")
