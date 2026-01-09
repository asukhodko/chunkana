"""
Regression tests for issues identified in TEST_REPORT_v2.

These tests verify that the fixes for dangling headers, section_tags consistency,
and header_moved_from tracking work correctly across all document sections.
"""

import re
from pathlib import Path

import pytest

from chunkana import ChunkConfig, MarkdownChunker


@pytest.fixture
def sde_criteria_document():
    """Load the SDE criteria test fixture."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "sde_criteria.md"
    return fixture_path.read_text(encoding="utf-8")


@pytest.fixture
def chunker():
    """Create a chunker with settings that will trigger dangling headers."""
    config = ChunkConfig(
        max_chunk_size=800,  # Small enough to create multiple chunks per section
        min_chunk_size=100,
    )
    return MarkdownChunker(config)


class TestDanglingHeadersAllSections:
    """Tests for universal dangling header fix (Issue from TEST_REPORT_v2)."""

    def test_no_dangling_headers_in_scope(self, chunker, sde_criteria_document):
        """Verify no dangling headers in Scope section."""
        chunks = chunker.chunk(sde_criteria_document)
        self._assert_no_dangling_headers(chunks, "Scope")

    def test_no_dangling_headers_in_impact(self, chunker, sde_criteria_document):
        """Verify no dangling headers in Impact section (was broken in v1)."""
        chunks = chunker.chunk(sde_criteria_document)
        self._assert_no_dangling_headers(chunks, "Impact")

    def test_no_dangling_headers_in_leadership(self, chunker, sde_criteria_document):
        """Verify no dangling headers in Leadership section (was broken in v1)."""
        chunks = chunker.chunk(sde_criteria_document)
        self._assert_no_dangling_headers(chunks, "Leadership")

    def test_no_dangling_headers_in_improvement(self, chunker, sde_criteria_document):
        """Verify no dangling headers in Improvement section (was broken in v1)."""
        chunks = chunker.chunk(sde_criteria_document)
        self._assert_no_dangling_headers(chunks, "Improvement")

    def test_no_dangling_headers_in_technical_complexity(self, chunker, sde_criteria_document):
        """Verify no dangling headers in Technical Complexity section."""
        chunks = chunker.chunk(sde_criteria_document)
        self._assert_no_dangling_headers(chunks, "Technical Complexity")

    def _assert_no_dangling_headers(self, chunks, section_name):
        """Assert that no chunk ends with a dangling header."""
        header_pattern = re.compile(r"^#{3,6}\s+.+$", re.MULTILINE)

        for i, chunk in enumerate(chunks[:-1]):  # All except last
            content = chunk.content.rstrip()
            lines = content.split("\n")

            # Find last non-empty line
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if not last_line:
                continue

            # Check if it's a header level 3+
            if header_pattern.match(last_line):
                # Check if next chunk has content for this header
                next_chunk = chunks[i + 1]
                next_first = next_chunk.content.lstrip().split("\n")[0].strip()

                # If next chunk doesn't start with a header, this is dangling
                if not header_pattern.match(next_first):
                    header_path = chunk.metadata.get("header_path", "")
                    pytest.fail(
                        f"Dangling header found in chunk {i} ({section_name}): "
                        f"'{last_line[:50]}...' at header_path={header_path}"
                    )


class TestSectionTagsConsistency:
    """Tests for section_tags matching actual content (Issue from TEST_REPORT_v2)."""

    def test_section_tags_match_content(self, chunker, sde_criteria_document):
        """Every tag in section_tags must be present as a header in content."""
        chunks = chunker.chunk(sde_criteria_document)

        for chunk in chunks:
            section_tags = chunk.metadata.get("section_tags", [])
            content = chunk.content

            for tag in section_tags:
                # Tag should appear as a header (### or ####) in content
                escaped_tag = re.escape(tag)
                pattern = r"^#{3,4}\s+" + escaped_tag + r"\s*$"
                if not re.search(pattern, content, re.MULTILINE):
                    chunk_index = chunk.metadata.get("chunk_index", "?")
                    pytest.fail(
                        f"Chunk {chunk_index}: section_tag '{tag}' not found as header in content"
                    )

    def test_headers_in_content_match_section_tags(self, chunker, sde_criteria_document):
        """Every header (level 3-4) in content should be in section_tags."""
        chunks = chunker.chunk(sde_criteria_document)
        header_pattern = re.compile(r"^#{3,4}\s+(.+)$", re.MULTILINE)

        for chunk in chunks:
            section_tags = chunk.metadata.get("section_tags", [])
            content = chunk.content

            # Find all headers in content
            headers_in_content = [
                match.group(1).strip() for match in header_pattern.finditer(content)
            ]

            for header in headers_in_content:
                if header not in section_tags:
                    chunk_index = chunk.metadata.get("chunk_index", "?")
                    pytest.fail(
                        f"Chunk {chunk_index}: header '{header}' in content "
                        f"but not in section_tags. section_tags={section_tags}"
                    )

    def test_section_tags_updated_after_dangling_fix(self, chunker, sde_criteria_document):
        """After dangling header fix, section_tags should reflect moved headers."""
        chunks = chunker.chunk(sde_criteria_document)

        for chunk in chunks:
            if chunk.metadata.get("dangling_header_fixed"):
                # This chunk received a moved header
                section_tags = chunk.metadata.get("section_tags", [])
                content = chunk.content

                # The moved header should be in section_tags
                header_pattern = re.compile(r"^#{3,4}\s+(.+)$", re.MULTILINE)
                first_header_match = header_pattern.search(content)

                if first_header_match:
                    first_header = first_header_match.group(1).strip()
                    assert first_header in section_tags, (
                        f"Moved header '{first_header}' not in section_tags "
                        f"for chunk with dangling_header_fixed=True"
                    )


class TestHeaderMovedFromTracking:
    """Tests for header_moved_from field (Issue from TEST_REPORT_v2)."""

    def test_header_moved_from_populated_when_fixed(self, chunker, sde_criteria_document):
        """header_moved_from should be populated when dangling_header_fixed=True."""
        chunks = chunker.chunk(sde_criteria_document)

        for chunk in chunks:
            if chunk.metadata.get("dangling_header_fixed"):
                header_moved_from = chunk.metadata.get("header_moved_from")
                assert header_moved_from is not None, (
                    f"Chunk {chunk.metadata.get('chunk_index')}: "
                    f"dangling_header_fixed=True but header_moved_from is None"
                )

    def test_header_moved_from_is_valid_index(self, chunker, sde_criteria_document):
        """header_moved_from should be a valid chunk index."""
        chunks = chunker.chunk(sde_criteria_document)
        num_chunks = len(chunks)

        for chunk in chunks:
            header_moved_from = chunk.metadata.get("header_moved_from")
            if header_moved_from is not None:
                if isinstance(header_moved_from, int):
                    assert 0 <= header_moved_from < num_chunks, (
                        f"Invalid header_moved_from index: {header_moved_from}"
                    )
                elif isinstance(header_moved_from, list):
                    for idx in header_moved_from:
                        assert 0 <= idx < num_chunks, (
                            f"Invalid header_moved_from index in list: {idx}"
                        )

    def test_header_moved_from_null_when_no_fix(self, chunker, sde_criteria_document):
        """header_moved_from should be absent when no header was moved."""
        chunks = chunker.chunk(sde_criteria_document)

        for chunk in chunks:
            if not chunk.metadata.get("dangling_header_fixed"):
                # Should not have header_moved_from or it should be None
                header_moved_from = chunk.metadata.get("header_moved_from")
                assert header_moved_from is None, (
                    f"Chunk {chunk.metadata.get('chunk_index')}: "
                    f"header_moved_from={header_moved_from} but dangling_header_fixed is not True"
                )


class TestLineRangeContract:
    """Tests for start_line/end_line contract documentation."""

    def test_line_ranges_are_positive(self, chunker, sde_criteria_document):
        """All line ranges should be positive integers."""
        chunks = chunker.chunk(sde_criteria_document)

        for chunk in chunks:
            assert chunk.start_line >= 1, "start_line must be >= 1"
            assert chunk.end_line >= chunk.start_line, (
                f"end_line ({chunk.end_line}) must be >= start_line ({chunk.start_line})"
            )

    def test_chunks_ordered_by_line(self, chunker, sde_criteria_document):
        """Chunks should be ordered by start_line."""
        chunks = chunker.chunk(sde_criteria_document)

        for i in range(len(chunks) - 1):
            assert chunks[i].start_line <= chunks[i + 1].start_line, (
                f"Chunks not ordered: chunk {i} starts at {chunks[i].start_line}, "
                f"chunk {i + 1} starts at {chunks[i + 1].start_line}"
            )
