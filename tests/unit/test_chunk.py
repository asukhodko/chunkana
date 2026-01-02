"""
Unit tests for Chunk dataclass validation.

Task 13.1: Tests for invalid start_line, end_line, empty content.
Validates: Requirements 1.4
"""

import pytest

from chunkana import Chunk


class TestChunkValidation:
    """Tests for Chunk validation on creation."""

    def test_valid_chunk_creation(self):
        """Valid chunk should be created without errors."""
        chunk = Chunk(
            content="Hello, world!",
            start_line=1,
            end_line=1,
            metadata={"chunk_index": 0},
        )
        assert chunk.content == "Hello, world!"
        assert chunk.start_line == 1
        assert chunk.end_line == 1
        assert chunk.size == 13

    def test_invalid_start_line_zero(self):
        """start_line=0 should raise ValueError (1-indexed)."""
        with pytest.raises(ValueError, match="start_line must be >= 1"):
            Chunk(content="test", start_line=0, end_line=1)

    def test_invalid_start_line_negative(self):
        """Negative start_line should raise ValueError."""
        with pytest.raises(ValueError, match="start_line must be >= 1"):
            Chunk(content="test", start_line=-1, end_line=1)

    def test_invalid_end_line_less_than_start(self):
        """end_line < start_line should raise ValueError."""
        with pytest.raises(ValueError, match="end_line.*must be >= start_line"):
            Chunk(content="test", start_line=5, end_line=3)

    def test_empty_content_raises_error(self):
        """Empty content should raise ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            Chunk(content="", start_line=1, end_line=1)

    def test_whitespace_only_content_raises_error(self):
        """Whitespace-only content should raise ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            Chunk(content="   \n\t  ", start_line=1, end_line=1)

    def test_single_line_chunk(self):
        """Single line chunk (start_line == end_line) is valid."""
        chunk = Chunk(content="Single line", start_line=5, end_line=5)
        assert chunk.start_line == chunk.end_line == 5

    def test_multiline_chunk(self):
        """Multiline chunk should work correctly."""
        content = "Line 1\nLine 2\nLine 3"
        chunk = Chunk(content=content, start_line=10, end_line=12)
        assert chunk.start_line == 10
        assert chunk.end_line == 12
        assert chunk.size == len(content)


class TestChunkSerialization:
    """Tests for Chunk serialization methods."""

    def test_to_dict_contains_required_fields(self):
        """to_dict should contain all required fields."""
        chunk = Chunk(
            content="Test content",
            start_line=1,
            end_line=2,
            metadata={"key": "value"},
        )
        d = chunk.to_dict()

        assert "content" in d
        assert "start_line" in d
        assert "end_line" in d
        assert "size" in d
        assert "line_count" in d
        assert "metadata" in d

        assert d["content"] == "Test content"
        assert d["start_line"] == 1
        assert d["end_line"] == 2
        assert d["size"] == 12
        assert d["line_count"] == 2
        assert d["metadata"] == {"key": "value"}

    def test_from_dict_creates_valid_chunk(self):
        """from_dict should create valid Chunk."""
        data = {
            "content": "Restored content",
            "start_line": 5,
            "end_line": 10,
            "metadata": {"restored": True},
        }
        chunk = Chunk.from_dict(data)

        assert chunk.content == "Restored content"
        assert chunk.start_line == 5
        assert chunk.end_line == 10
        assert chunk.metadata == {"restored": True}

    def test_to_json_returns_valid_json(self):
        """to_json should return valid JSON string."""
        import json

        chunk = Chunk(content="JSON test", start_line=1, end_line=1)
        json_str = chunk.to_json()

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["content"] == "JSON test"

    def test_from_json_creates_valid_chunk(self):
        """from_json should create valid Chunk from JSON string."""
        import json

        data = {
            "content": "From JSON",
            "start_line": 1,
            "end_line": 1,
            "metadata": {},
        }
        json_str = json.dumps(data)
        chunk = Chunk.from_json(json_str)

        assert chunk.content == "From JSON"

    def test_roundtrip_preserves_unicode(self):
        """Serialization should preserve unicode content."""
        content = "Привет мир! 你好世界! 🎉"
        chunk = Chunk(content=content, start_line=1, end_line=1)

        restored = Chunk.from_dict(chunk.to_dict())
        assert restored.content == content

        restored_json = Chunk.from_json(chunk.to_json())
        assert restored_json.content == content


class TestChunkProperties:
    """Tests for Chunk computed properties."""

    def test_size_property(self):
        """size property should return content length."""
        chunk = Chunk(content="12345", start_line=1, end_line=1)
        assert chunk.size == 5

    def test_size_with_unicode(self):
        """size should count unicode characters correctly."""
        chunk = Chunk(content="Привет", start_line=1, end_line=1)
        assert chunk.size == 6  # 6 Cyrillic characters

    def test_line_count_in_dict(self):
        """line_count in to_dict should be end_line - start_line + 1."""
        chunk = Chunk(content="test", start_line=5, end_line=10)
        d = chunk.to_dict()
        assert d["line_count"] == 6
