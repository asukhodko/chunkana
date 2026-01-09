"""
Unit tests for SectionSplitter line number calculation.

Tests the new line number calculation functionality for split chunks.
"""

import pytest

from chunkana.config import ChunkConfig
from chunkana.section_splitter import SectionSplitter, SegmentWithPosition
from chunkana.types import Chunk


class TestSegmentPositionCalculation:
    """Tests for segment position calculation."""

    @pytest.fixture
    def splitter(self):
        config = ChunkConfig(max_chunk_size=1000)
        return SectionSplitter(config)

    def test_find_body_start_line_simple_header(self, splitter):
        """Test body start line with simple header."""
        content = "## Header\n\nBody content here"
        result = splitter._find_body_start_line(content)
        assert result == 2  # Body starts at line 2 (0-indexed)

    def test_find_body_start_line_multiple_headers(self, splitter):
        """Test body start line with multiple consecutive headers."""
        content = "## Header\n\n### Subheader\n\nBody content"
        result = splitter._find_body_start_line(content)
        assert result == 4  # Body starts after both headers

    def test_find_body_start_line_no_headers(self, splitter):
        """Test body start line with no headers."""
        content = "Just body content\nMore content"
        result = splitter._find_body_start_line(content)
        assert result == 0  # Body starts immediately

    def test_find_body_start_line_header_only(self, splitter):
        """Test body start line with header only."""
        content = "## Header Only\n\n"
        result = splitter._find_body_start_line(content)
        assert result == 1  # Body starts at line 1 (after header, before empty line)

    def test_calculate_segment_positions_simple(self, splitter):
        """Test segment position calculation with simple segments."""
        segments = ["First segment", "Second segment"]
        body = "First segment\n\nSecond segment"
        original = Chunk(
            content="## Header\n\nFirst segment\n\nSecond segment",
            start_line=10,
            end_line=15,
            metadata={},
        )

        result = splitter._calculate_segment_positions(segments, body, original)

        assert len(result) == 2
        assert result[0].content == "First segment"
        assert result[0].start_line_offset == 2  # After header
        assert result[0].end_line_offset == 2  # Single line segment

        assert result[1].content == "Second segment"
        assert result[1].start_line_offset == 4  # After first segment + separator
        assert result[1].end_line_offset == 4  # Single line segment

    def test_calculate_segment_positions_multiline_segments(self, splitter):
        """Test position calculation with multiline segments."""
        segments = [
            "First segment\nLine 2 of first",
            "Second segment\nLine 2 of second\nLine 3 of second",
        ]
        body = (
            "First segment\nLine 2 of first\n\nSecond segment\nLine 2 of second\nLine 3 of second"
        )
        original = Chunk(content="## Header\n\n" + body, start_line=10, end_line=20, metadata={})

        result = splitter._calculate_segment_positions(segments, body, original)

        assert len(result) == 2
        assert result[0].end_line_offset == 3  # 2 lines in first segment (0-based)
        assert result[1].start_line_offset == 5  # Starts after first segment + separator
        assert result[1].end_line_offset == 7  # 3 lines in second segment

    def test_calculate_segment_positions_segment_not_found(self, splitter):
        """Test fallback when segment not found in body."""
        segments = ["Missing segment", "Found segment"]
        body = "Different content\n\nFound segment"
        original = Chunk(content="## Header\n\n" + body, start_line=10, end_line=15, metadata={})

        result = splitter._calculate_segment_positions(segments, body, original)

        assert len(result) == 2
        # First segment uses fallback positioning
        assert result[0].content == "Missing segment"
        assert result[0].start_line_offset == 2  # Body start

        # Second segment should be found correctly
        assert result[1].content == "Found segment"


class TestSegmentWithPositionFinding:
    """Tests for finding segments with positions."""

    @pytest.fixture
    def splitter(self):
        config = ChunkConfig(max_chunk_size=1000)
        return SectionSplitter(config)

    def test_find_segments_with_positions_list_items(self, splitter):
        """Test finding segments with list items."""
        body = "1. First item\nContent of first\n\n2. Second item\nContent of second"
        original = Chunk(content="## Header\n\n" + body, start_line=10, end_line=20, metadata={})

        result = splitter._find_segments_with_positions(body, original)

        assert len(result) == 2
        assert "1. First item" in result[0].content
        assert "2. Second item" in result[1].content
        assert result[0].start_line_offset < result[1].start_line_offset

    def test_find_segments_with_positions_empty_body(self, splitter):
        """Test with empty body (header-only chunk)."""
        body = ""
        original = Chunk(content="## Header Only\n\n", start_line=10, end_line=12, metadata={})

        result = splitter._find_segments_with_positions(body, original)
        assert result == []

    def test_find_segments_with_positions_single_segment(self, splitter):
        """Test with single segment (no split needed)."""
        body = "Single paragraph of content that cannot be split further."
        original = Chunk(content="## Header\n\n" + body, start_line=10, end_line=15, metadata={})

        result = splitter._find_segments_with_positions(body, original)
        assert result == []  # Single segment, no split


class TestChunkCreationWithLines:
    """Tests for creating chunks with accurate line numbers."""

    @pytest.fixture
    def splitter(self):
        config = ChunkConfig(max_chunk_size=1000)
        return SectionSplitter(config)

    def test_create_chunk_with_lines_first_chunk(self, splitter):
        """Test creating first chunk with accurate line numbers."""
        original = Chunk(
            content="## Header\n\nContent line 1\nContent line 2",
            start_line=10,
            end_line=15,
            metadata={},
        )
        header_stack = "## Header"
        segments = [
            SegmentWithPosition(
                content="Content line 1\nContent line 2",
                start_line_offset=2,
                end_line_offset=3,
                original_text="Content line 1\nContent line 2",
            )
        ]

        result = splitter._create_chunk_with_lines(original, header_stack, segments, index=0)

        assert result.start_line == 12  # original.start_line + start_line_offset
        assert result.end_line == 13  # original.start_line + end_line_offset
        assert result.metadata["split_index"] == 0
        assert not result.metadata["continued_from_header"]

    def test_create_chunk_with_lines_continuation_chunk(self, splitter):
        """Test creating continuation chunk with repeated header."""
        original = Chunk(
            content="## Header\n\nContent line 1\nContent line 2\nContent line 3",
            start_line=10,
            end_line=15,
            metadata={},
        )
        header_stack = "## Header"
        segments = [
            SegmentWithPosition(
                content="Content line 3",
                start_line_offset=4,
                end_line_offset=4,
                original_text="Content line 3",
            )
        ]

        result = splitter._create_chunk_with_lines(original, header_stack, segments, index=1)

        assert result.start_line == 14  # original.start_line + start_line_offset
        assert result.end_line == 14  # original.start_line + end_line_offset
        assert result.metadata["split_index"] == 1
        assert result.metadata["continued_from_header"]
        assert result.content.startswith("## Header\n\n")

    def test_create_chunk_with_lines_multiple_segments(self, splitter):
        """Test creating chunk with multiple segments."""
        original = Chunk(
            content="## Header\n\nSegment 1\n\nSegment 2\n\nSegment 3",
            start_line=10,
            end_line=18,
            metadata={},
        )
        header_stack = "## Header"
        segments = [
            SegmentWithPosition(
                content="Segment 1",
                start_line_offset=2,
                end_line_offset=2,
                original_text="Segment 1",
            ),
            SegmentWithPosition(
                content="Segment 2",
                start_line_offset=4,
                end_line_offset=4,
                original_text="Segment 2",
            ),
        ]

        result = splitter._create_chunk_with_lines(original, header_stack, segments, index=0)

        assert result.start_line == 12  # Min of segment offsets + original start
        assert result.end_line == 14  # Max of segment offsets + original start
        assert "Segment 1\n\nSegment 2" in result.content

    def test_create_chunk_with_lines_no_segments(self, splitter):
        """Test creating chunk with no segments (fallback)."""
        original = Chunk(content="## Header Only", start_line=10, end_line=12, metadata={})
        header_stack = "## Header Only"
        segments = []

        result = splitter._create_chunk_with_lines(original, header_stack, segments, index=0)

        # Should return original chunk when no segments
        assert result == original


class TestEdgeCases:
    """Tests for edge cases in line number calculation."""

    @pytest.fixture
    def splitter(self):
        config = ChunkConfig(max_chunk_size=1000)
        return SectionSplitter(config)

    def test_empty_segments_filtered(self, splitter):
        """Test that empty segments are filtered out."""
        body = "Content 1\n\n\n\nContent 2"  # Empty lines between
        original = Chunk(content="## Header\n\n" + body, start_line=10, end_line=20, metadata={})

        result = splitter._find_segments_with_positions(body, original)

        # Should handle empty segments gracefully
        for segment in result:
            assert segment.content.strip()  # No empty segments

    def test_header_only_chunk_no_split(self, splitter):
        """Test that header-only chunks are not split."""
        chunk = Chunk(content="## Header Only\n\n", start_line=10, end_line=12, metadata={})

        result = splitter._split_chunk(chunk)

        assert len(result) == 1
        assert result[0] == chunk  # Original chunk returned unchanged
