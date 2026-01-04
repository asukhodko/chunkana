"""
Unit tests for renderers.

Task 13.3: Tests for JSON format, inline metadata format.
Validates: Requirements 6.1-6.3
"""

import json

import pytest

from chunkana import Chunk
from chunkana.renderers import (
    render_dify_style,
    render_json,
    render_with_embedded_overlap,
    render_with_prev_overlap,
)


@pytest.fixture
def sample_chunks():
    """Create sample chunks for testing."""
    return [
        Chunk(
            content="First chunk content",
            start_line=1,
            end_line=5,
            metadata={
                "chunk_index": 0,
                "strategy": "structural",
                "header_path": "/Section 1",
                "content_type": "text",
            },
        ),
        Chunk(
            content="Second chunk content",
            start_line=6,
            end_line=10,
            metadata={
                "chunk_index": 1,
                "strategy": "structural",
                "header_path": "/Section 1/Subsection",
                "content_type": "text",
                "previous_content": "...from first chunk",
            },
        ),
        Chunk(
            content="Third chunk content",
            start_line=11,
            end_line=15,
            metadata={
                "chunk_index": 2,
                "strategy": "structural",
                "header_path": "/Section 2",
                "content_type": "text",
                "previous_content": "...from second chunk",
                "next_content": "preview of fourth...",
            },
        ),
    ]


class TestRenderJson:
    """Tests for render_json function."""

    def test_returns_list_of_dicts(self, sample_chunks):
        """render_json should return list of dictionaries."""
        result = render_json(sample_chunks)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(d, dict) for d in result)

    def test_dict_contains_chunk_fields(self, sample_chunks):
        """Each dict should contain chunk fields."""
        result = render_json(sample_chunks)

        for d in result:
            assert "content" in d
            assert "start_line" in d
            assert "end_line" in d
            assert "metadata" in d

    def test_empty_list_returns_empty(self):
        """Empty chunk list should return empty list."""
        result = render_json([])
        assert result == []

    def test_does_not_modify_chunks(self, sample_chunks):
        """render_json should not modify original chunks."""
        original_content = sample_chunks[0].content
        render_json(sample_chunks)
        assert sample_chunks[0].content == original_content


class TestRenderDifyStyle:
    """Tests for render_dify_style function."""

    def test_returns_list_of_strings(self, sample_chunks):
        """render_dify_style should return list of strings."""
        result = render_dify_style(sample_chunks)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    def test_contains_metadata_block(self, sample_chunks):
        """Each string should contain <metadata> block."""
        result = render_dify_style(sample_chunks)

        for s in result:
            assert "<metadata>" in s
            assert "</metadata>" in s

    def test_metadata_is_valid_json(self, sample_chunks):
        """Metadata block should contain valid JSON."""
        result = render_dify_style(sample_chunks)

        for s in result:
            # Extract JSON between tags
            start = s.index("<metadata>") + len("<metadata>")
            end = s.index("</metadata>")
            json_str = s[start:end].strip()

            # Should be valid JSON
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)

    def test_includes_start_end_line_in_metadata(self, sample_chunks):
        """Metadata should include start_line and end_line."""
        result = render_dify_style(sample_chunks)

        # Check first chunk
        start = result[0].index("<metadata>") + len("<metadata>")
        end = result[0].index("</metadata>")
        metadata = json.loads(result[0][start:end].strip())

        assert "start_line" in metadata
        assert "end_line" in metadata
        assert metadata["start_line"] == 1
        assert metadata["end_line"] == 5

    def test_content_follows_metadata(self, sample_chunks):
        """Chunk content should follow metadata block."""
        result = render_dify_style(sample_chunks)

        for i, s in enumerate(result):
            assert sample_chunks[i].content in s
            # Content should be after </metadata>
            metadata_end = s.index("</metadata>")
            content_pos = s.index(sample_chunks[i].content)
            assert content_pos > metadata_end


class TestRenderWithEmbeddedOverlap:
    """Tests for render_with_embedded_overlap function (bidirectional)."""

    def test_returns_list_of_strings(self, sample_chunks):
        """render_with_embedded_overlap should return list of strings."""
        result = render_with_embedded_overlap(sample_chunks)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    def test_first_chunk_no_previous(self, sample_chunks):
        """First chunk should not have previous content prepended."""
        result = render_with_embedded_overlap(sample_chunks)

        # First chunk has no previous_content in metadata
        assert result[0] == sample_chunks[0].content

    def test_includes_previous_content(self, sample_chunks):
        """Chunks with previous_content should have it prepended."""
        result = render_with_embedded_overlap(sample_chunks)

        # Second chunk has previous_content
        assert "...from first chunk" in result[1]
        assert "Second chunk content" in result[1]

    def test_includes_next_content(self, sample_chunks):
        """Chunks with next_content should have it appended."""
        result = render_with_embedded_overlap(sample_chunks)

        # Third chunk has both previous and next
        assert "...from second chunk" in result[2]
        assert "Third chunk content" in result[2]
        assert "preview of fourth..." in result[2]

    def test_does_not_modify_chunks(self, sample_chunks):
        """render_with_embedded_overlap should not modify original chunks."""
        original_content = sample_chunks[0].content
        render_with_embedded_overlap(sample_chunks)
        assert sample_chunks[0].content == original_content


class TestRenderWithPrevOverlap:
    """Tests for render_with_prev_overlap function (prev-only)."""

    def test_returns_list_of_strings(self, sample_chunks):
        """render_with_prev_overlap should return list of strings."""
        result = render_with_prev_overlap(sample_chunks)

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(s, str) for s in result)

    def test_first_chunk_no_previous(self, sample_chunks):
        """First chunk should not have previous content prepended."""
        result = render_with_prev_overlap(sample_chunks)

        assert result[0] == sample_chunks[0].content

    def test_includes_previous_content(self, sample_chunks):
        """Chunks with previous_content should have it prepended."""
        result = render_with_prev_overlap(sample_chunks)

        assert "...from first chunk" in result[1]
        assert "Second chunk content" in result[1]

    def test_does_not_include_next_content(self, sample_chunks):
        """render_with_prev_overlap should NOT include next_content."""
        result = render_with_prev_overlap(sample_chunks)

        # Third chunk has next_content in metadata, but it should NOT be in output
        assert "preview of fourth..." not in result[2]
        # But previous should still be there
        assert "...from second chunk" in result[2]


class TestRendererEdgeCases:
    """Edge case tests for renderers."""

    def test_empty_chunks_list(self):
        """All renderers should handle empty list."""
        assert render_json([]) == []
        assert render_dify_style([]) == []
        assert render_with_embedded_overlap([]) == []
        assert render_with_prev_overlap([]) == []

    def test_chunk_with_unicode(self):
        """Renderers should handle unicode content."""
        chunk = Chunk(
            content="Привет мир! 你好世界!",
            start_line=1,
            end_line=1,
            metadata={
                "chunk_index": 0,
                "strategy": "test",
                "header_path": "",
                "content_type": "text",
            },
        )

        result = render_dify_style([chunk])
        assert "Привет мир!" in result[0]
        assert "你好世界!" in result[0]

    def test_chunk_with_special_json_chars(self):
        """Renderers should handle special JSON characters."""
        chunk = Chunk(
            content='Content with "quotes" and \\backslash',
            start_line=1,
            end_line=1,
            metadata={
                "chunk_index": 0,
                "strategy": "test",
                "header_path": "",
                "content_type": "text",
            },
        )

        result = render_dify_style([chunk])
        # Should not raise and should contain escaped content
        assert "quotes" in result[0]

    def test_chunk_with_empty_overlap(self):
        """Renderers should handle empty overlap strings."""
        chunk = Chunk(
            content="Main content",
            start_line=1,
            end_line=1,
            metadata={
                "chunk_index": 0,
                "strategy": "test",
                "header_path": "",
                "content_type": "text",
                "previous_content": "",
                "next_content": "",
            },
        )

        result = render_with_embedded_overlap([chunk])
        assert result[0] == "Main content"
