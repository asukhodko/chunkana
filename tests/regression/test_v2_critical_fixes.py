"""
Regression tests for v2 critical fixes.

Tests the fixes for:
- CHNK-CRIT-01: Dangling headers
- CHNK-CRIT-02: Max chunk size violations
- Header stack repetition in split chunks
- Recall-based coverage metric

Uses the sde_criteria.md fixture from the original test report.
"""

import re
from pathlib import Path

import pytest

from chunkana import ChunkConfig, InvariantValidator, MarkdownChunker, SectionSplitter

# Fixture path
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sde_criteria_document() -> str:
    """Load the SDE criteria document fixture."""
    fixture_path = FIXTURES_DIR / "sde_criteria.md"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def chunker_1000() -> MarkdownChunker:
    """Chunker with max_chunk_size=1000."""
    return MarkdownChunker(ChunkConfig(max_chunk_size=1000))


@pytest.fixture
def chunker_2000() -> MarkdownChunker:
    """Chunker with max_chunk_size=2000."""
    return MarkdownChunker(ChunkConfig(max_chunk_size=2000))


@pytest.fixture
def validator_1000() -> InvariantValidator:
    """Validator with max_chunk_size=1000."""
    return InvariantValidator(ChunkConfig(max_chunk_size=1000), strict=True)


@pytest.fixture
def validator_2000() -> InvariantValidator:
    """Validator with max_chunk_size=2000."""
    return InvariantValidator(ChunkConfig(max_chunk_size=2000), strict=True)


class TestNoDanglingHeaders:
    """Tests for dangling header prevention."""

    def test_no_dangling_headers_basic(self, sde_criteria_document, chunker_1000, validator_1000):
        """No chunk should end with a header without content."""
        chunks = chunker_1000.chunk(sde_criteria_document)
        result = validator_1000.validate(chunks, sde_criteria_document)

        assert len(result.dangling_header_indices) == 0, (
            f"Found dangling headers at chunks: {result.dangling_header_indices}"
        )

    def test_no_dangling_in_scope_section(self, sde_criteria_document, chunker_1000):
        """Scope section should not have dangling headers."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Find chunks in Scope section
        scope_chunks = [c for c in chunks if "Scope" in c.metadata.get("header_path", "")]

        header_pattern = re.compile(r"^#{1,6}\s+")
        for chunk in scope_chunks:
            lines = chunk.content.rstrip().split("\n")
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if last_line:
                assert not header_pattern.match(last_line), (
                    f"Dangling header in Scope section: {last_line[:50]}"
                )

    def test_no_dangling_in_impact_section(self, sde_criteria_document, chunker_1000):
        """Impact section should not have dangling headers."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        impact_chunks = [c for c in chunks if "Impact" in c.metadata.get("header_path", "")]

        header_pattern = re.compile(r"^#{1,6}\s+")
        for chunk in impact_chunks:
            lines = chunk.content.rstrip().split("\n")
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if last_line:
                assert not header_pattern.match(last_line), (
                    f"Dangling header in Impact section: {last_line[:50]}"
                )

    @pytest.mark.parametrize(
        "section", ["Scope", "Impact", "Leadership", "Improvement", "Technical Complexity"]
    )
    def test_no_dangling_in_any_section(self, sde_criteria_document, chunker_2000, section):
        """No section should have dangling headers."""
        chunks = chunker_2000.chunk(sde_criteria_document)

        section_chunks = [c for c in chunks if section in str(c.metadata.get("header_path", ""))]

        header_pattern = re.compile(r"^#{1,6}\s+")
        for chunk in section_chunks:
            lines = chunk.content.rstrip().split("\n")
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if last_line:
                assert not header_pattern.match(last_line), (
                    f"Dangling header in {section} section: {last_line[:50]}"
                )


class TestMaxChunkSize:
    """Tests for max chunk size compliance."""

    def test_no_invalid_oversize(self, sde_criteria_document, chunker_1000, validator_1000):
        """No chunk should exceed max_size without valid reason."""
        chunks = chunker_1000.chunk(sde_criteria_document)
        result = validator_1000.validate(chunks, sde_criteria_document)

        assert len(result.invalid_oversize_indices) == 0, (
            f"Found invalid oversize chunks: {result.invalid_oversize_indices}"
        )

    def test_all_chunks_within_size_or_valid_reason(self, sde_criteria_document, chunker_1000):
        """All chunks should be within size limit or have valid oversize reason."""
        config = ChunkConfig(max_chunk_size=1000)
        chunks = chunker_1000.chunk(sde_criteria_document)

        valid_reasons = {"code_block_integrity", "table_integrity", "list_item_integrity"}

        for i, chunk in enumerate(chunks):
            if len(chunk.content) > config.max_chunk_size:
                reason = chunk.metadata.get("oversize_reason", "")
                assert reason in valid_reasons, (
                    f"Chunk {i} exceeds max_size ({len(chunk.content)} > {config.max_chunk_size}) "
                    f"with invalid reason: '{reason}'"
                )

    def test_no_section_integrity_oversize(self, sde_criteria_document, chunker_1000):
        """No chunk should have section_integrity as oversize reason."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        for i, chunk in enumerate(chunks):
            reason = chunk.metadata.get("oversize_reason", "")
            assert reason != "section_integrity", (
                f"Chunk {i} has deprecated section_integrity oversize reason"
            )


class TestHeaderStackRepetition:
    """Tests for header stack repetition in split chunks."""

    def test_continued_chunks_have_header_stack(self, sde_criteria_document, chunker_1000):
        """Continued chunks should start with header."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        for chunk in chunks:
            if chunk.metadata.get("continued_from_header"):
                first_line = chunk.content.strip().split("\n")[0]
                assert first_line.startswith("#"), (
                    f"Continued chunk should start with header: {first_line[:50]}"
                )

    def test_split_index_is_sequential(self, sde_criteria_document, chunker_1000):
        """Split indices should be sequential within a section."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Group chunks by header_path and original_section_size (better grouping)
        split_groups: dict[tuple[str, int], list[int]] = {}
        for chunk in chunks:
            if "split_index" in chunk.metadata:
                header_path = chunk.metadata.get("header_path", "")
                original_size = chunk.metadata.get("original_section_size", 0)
                key = (header_path, original_size)
                if key not in split_groups:
                    split_groups[key] = []
                split_groups[key].append(chunk.metadata["split_index"])

        for (header_path, original_size), indices in split_groups.items():
            sorted_indices = sorted(indices)
            expected = list(range(len(sorted_indices)))
            assert sorted_indices == expected, (
                f"Split indices not sequential for section {header_path} "
                f"(size {original_size}): {sorted_indices}"
            )


class TestCoverage:
    """Tests for content coverage (recall metric)."""

    def test_content_coverage_at_least_95_percent(
        self, sde_criteria_document, chunker_1000, validator_1000
    ):
        """Content coverage should be at least 95%."""
        chunks = chunker_1000.chunk(sde_criteria_document)
        result = validator_1000.validate(chunks, sde_criteria_document)

        assert result.coverage >= 0.95, f"Content coverage {result.coverage:.1%} < 95%"

    def test_coverage_not_inflated_by_repetition(self, sde_criteria_document, chunker_1000):
        """Coverage should not be inflated by header repetition."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Calculate coverage manually
        def normalize(s: str) -> str:
            return " ".join(s.split())

        original_lines = []
        for line in sde_criteria_document.split("\n"):
            normalized = normalize(line)
            if len(normalized) >= 20:
                original_lines.append(normalized)

        chunks_text = normalize(" ".join(c.content for c in chunks))

        found = sum(1 for line in original_lines if line in chunks_text)
        coverage = found / len(original_lines) if original_lines else 1.0

        # Coverage should be high but not > 1.0 (which would indicate inflation)
        assert 0.95 <= coverage <= 1.0, (
            f"Coverage {coverage:.1%} is outside expected range [95%, 100%]"
        )


class TestTracking:
    """Tests for header movement tracking."""

    def test_header_moved_from_id_is_stable(self, sde_criteria_document, chunker_1000):
        """header_moved_from_id should use chunk_id (stable), not index."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        for chunk in chunks:
            if chunk.metadata.get("dangling_header_fixed"):
                # Should have header_moved_from_id, not header_moved_from
                moved_from = chunk.metadata.get("header_moved_from_id")
                # It's OK if it's None (fallback case), but should not be an int
                if moved_from is not None:
                    if isinstance(moved_from, list):
                        for item in moved_from:
                            assert isinstance(item, str), (
                                f"header_moved_from_id should be string, got {type(item)}"
                            )
                    else:
                        assert isinstance(moved_from, str), (
                            f"header_moved_from_id should be string, got {type(moved_from)}"
                        )


class TestSplitChunkLineNumbers:
    """Tests for split chunk line number accuracy."""

    def test_split_chunks_have_different_line_numbers(self, sde_criteria_document, chunker_1000):
        """Split chunks should have different line numbers."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Find split chunks (same header_path, different split_index)
        split_groups = {}
        for chunk in chunks:
            header_path = chunk.metadata.get("header_path", "")
            if "split_index" in chunk.metadata:
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

        # Verify split chunks have different line numbers
        for _header_path, split_chunks in split_groups.items():
            if len(split_chunks) > 1:
                # Sort by split_index
                split_chunks.sort(key=lambda c: c.metadata["split_index"])

                for i in range(len(split_chunks) - 1):
                    current = split_chunks[i]
                    next_chunk = split_chunks[i + 1]

                    # Line numbers should be different
                    assert current.start_line != next_chunk.start_line, (
                        f"Split chunks have same start_line: {current.start_line}"
                    )
                    assert current.end_line != next_chunk.end_line, (
                        f"Split chunks have same end_line: {current.end_line}"
                    )

    def test_split_chunks_line_numbers_ordered(self, sde_criteria_document, chunker_1000):
        """Split chunks should have ordered line numbers."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Find split chunks
        split_chunks = [c for c in chunks if "split_index" in c.metadata]

        if len(split_chunks) > 1:
            # Group by header_path and sort by split_index
            split_groups = {}
            for chunk in split_chunks:
                header_path = chunk.metadata.get("header_path", "")
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

            for _header_path, group in split_groups.items():
                if len(group) > 1:
                    group.sort(key=lambda c: c.metadata["split_index"])

                    # Verify line numbers are monotonic
                    for i in range(len(group) - 1):
                        current = group[i]
                        next_chunk = group[i + 1]

                        assert current.start_line <= next_chunk.start_line, (
                            f"Line numbers not ordered: {current.start_line} > {next_chunk.start_line}"
                        )

    def test_non_split_chunks_line_numbers_unchanged(self, sde_criteria_document, chunker_1000):
        """Non-split chunks should maintain normal line numbers."""
        chunks = chunker_1000.chunk(sde_criteria_document)

        # Verify non-split chunks don't have split metadata
        for chunk in chunks:
            if "split_index" not in chunk.metadata:
                # These chunks should have normal line numbers
                assert chunk.start_line >= 0
                assert chunk.end_line >= chunk.start_line
                assert chunk.end_line > 0


class TestSectionSplitter:
    """Unit tests for SectionSplitter."""

    def test_extract_header_stack_single_header(self):
        """Should extract single header."""
        splitter = SectionSplitter(ChunkConfig(max_chunk_size=1000))

        content = "## Section\n\nSome content here."
        header_stack, body = splitter._extract_header_stack_and_body(content)

        assert header_stack == "## Section"
        assert body == "Some content here."

    def test_extract_header_stack_multiple_headers(self):
        """Should extract multiple consecutive headers."""
        splitter = SectionSplitter(ChunkConfig(max_chunk_size=1000))

        content = "## Impact\n\n#### Итоги работы\n\n1. First item"
        header_stack, body = splitter._extract_header_stack_and_body(content)

        assert "## Impact" in header_stack
        assert "#### Итоги работы" in header_stack
        assert body == "1. First item"

    def test_split_by_list_items(self):
        """Should split by list items."""
        splitter = SectionSplitter(ChunkConfig(max_chunk_size=1000))

        body = "1. First item\n2. Second item\n3. Third item"
        segments = splitter._split_by_list_items(body)

        assert len(segments) == 3
        assert "First item" in segments[0]
        assert "Second item" in segments[1]
        assert "Third item" in segments[2]

    def test_split_by_paragraphs(self):
        """Should split by paragraphs."""
        splitter = SectionSplitter(ChunkConfig(max_chunk_size=1000))

        body = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        segments = splitter._split_by_paragraphs(body)

        assert len(segments) == 3


class TestPipelineOrder:
    """Tests for correct pipeline order (dangling fix → split)."""

    def test_dangling_fix_before_split(self):
        """Dangling headers should be fixed before splitting."""
        # Create a document where order matters
        doc = """## Section

#### Subsection

1. Item one with some content that makes it longer
2. Item two with some content that makes it longer
3. Item three with some content that makes it longer
4. Item four with some content that makes it longer
5. Item five with some content that makes it longer
"""

        # Use small chunk size to force splitting (with smaller overlap)
        chunker = MarkdownChunker(ChunkConfig(max_chunk_size=300, overlap_size=50))
        chunks = chunker.chunk(doc)

        # All chunks should have headers (no dangling)
        header_pattern = re.compile(r"^#{1,6}\s+")
        for i, chunk in enumerate(chunks):
            lines = chunk.content.rstrip().split("\n")
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if last_line and i < len(chunks) - 1:  # Not last chunk
                assert not header_pattern.match(last_line), (
                    f"Chunk {i} ends with dangling header: {last_line}"
                )
