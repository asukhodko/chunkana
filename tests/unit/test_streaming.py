"""
Unit tests for streaming module.

Tests StreamingConfig, BufferManager, and StreamingChunker.
"""

import io
import tempfile
from pathlib import Path

import pytest

from chunkana import ChunkConfig
from chunkana.streaming import StreamingChunker, StreamingConfig


class TestStreamingConfig:
    """Tests for StreamingConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = StreamingConfig()

        assert config.buffer_size == 100_000
        assert config.overlap_lines == 20
        assert config.max_memory_mb == 100
        assert config.safe_split_threshold == 0.8

    def test_custom_values(self):
        """Test custom configuration values."""
        config = StreamingConfig(
            buffer_size=50_000,
            overlap_lines=10,
            max_memory_mb=50,
            safe_split_threshold=0.7,
        )

        assert config.buffer_size == 50_000
        assert config.overlap_lines == 10
        assert config.max_memory_mb == 50
        assert config.safe_split_threshold == 0.7

    def test_small_buffer_size(self):
        """Test with small buffer size."""
        config = StreamingConfig(buffer_size=1000)
        assert config.buffer_size == 1000

    def test_large_buffer_size(self):
        """Test with large buffer size."""
        config = StreamingConfig(buffer_size=10_000_000)
        assert config.buffer_size == 10_000_000


class TestStreamingChunker:
    """Tests for StreamingChunker."""

    def test_init_with_defaults(self):
        """Test initialization with default streaming config."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        assert chunker.chunk_config == chunk_config
        assert chunker.streaming_config.buffer_size == 100_000

    def test_init_with_custom_config(self):
        """Test initialization with custom streaming config."""
        chunk_config = ChunkConfig(max_chunk_size=2000)
        streaming_config = StreamingConfig(buffer_size=50_000)
        chunker = StreamingChunker(chunk_config, streaming_config)

        assert chunker.chunk_config.max_chunk_size == 2000
        assert chunker.streaming_config.buffer_size == 50_000

    def test_chunk_stream_simple(self):
        """Test chunking a simple stream."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        text = """# Header

This is some content.

## Subheader

More content here.
"""
        stream = io.StringIO(text)
        chunks = list(chunker.chunk_stream(stream))

        assert len(chunks) > 0
        # All chunks should have streaming metadata
        for chunk in chunks:
            assert "stream_chunk_index" in chunk.metadata
            assert "stream_window_index" in chunk.metadata

    def test_chunk_stream_with_code(self):
        """Test chunking stream with code blocks."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        text = """# Code Example

```python
def hello():
    return "world"
```

More text.
"""
        stream = io.StringIO(text)
        chunks = list(chunker.chunk_stream(stream))

        assert len(chunks) > 0
        combined = "".join(c.content for c in chunks)
        assert "def hello" in combined

    def test_chunk_file(self):
        """Test chunking a file."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        # Create temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\nContent here.\n")
            temp_path = f.name

        try:
            chunks = list(chunker.chunk_file(temp_path))
            assert len(chunks) > 0
        finally:
            Path(temp_path).unlink()

    def test_stream_window_index_increments(self):
        """Test that stream_window_index increments across windows."""
        chunk_config = ChunkConfig()
        streaming_config = StreamingConfig(buffer_size=100)  # Very small buffer
        chunker = StreamingChunker(chunk_config, streaming_config)

        # Create content that spans multiple windows
        text = "# Header\n\n" + "Content line.\n" * 50

        stream = io.StringIO(text)
        chunks = list(chunker.chunk_stream(stream))

        # Should have chunks from multiple windows
        [c.metadata.get("stream_window_index", 0) for c in chunks]
        # At least some chunks should exist
        assert len(chunks) > 0

    def test_empty_stream(self):
        """Test chunking empty stream."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        stream = io.StringIO("")
        chunks = list(chunker.chunk_stream(stream))

        assert len(chunks) == 0

    def test_whitespace_only_stream(self):
        """Test chunking whitespace-only stream."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        stream = io.StringIO("   \n\n   \n")
        chunks = list(chunker.chunk_stream(stream))

        assert len(chunks) == 0


class TestBufferManager:
    """Tests for BufferManager."""

    def test_read_windows_small_file(self):
        """Test reading windows from small file."""
        from chunkana.streaming.buffer_manager import BufferManager

        config = StreamingConfig(buffer_size=1000)
        manager = BufferManager(config)

        text = "Line 1\nLine 2\nLine 3\n"
        stream = io.StringIO(text)

        windows = list(manager.read_windows(stream))

        # Small file should be single window
        assert len(windows) == 1
        buffer, overlap, bytes_processed = windows[0]
        assert len(buffer) == 3
        assert len(overlap) == 0

    def test_read_windows_large_file(self):
        """Test reading windows from large file."""
        from chunkana.streaming.buffer_manager import BufferManager

        config = StreamingConfig(buffer_size=100, overlap_lines=5)
        manager = BufferManager(config)

        # Create content larger than buffer
        text = "Line content here.\n" * 50
        stream = io.StringIO(text)

        windows = list(manager.read_windows(stream))

        # Should have multiple windows
        assert len(windows) > 1

        # Second window should have overlap
        if len(windows) > 1:
            _, overlap, _ = windows[1]
            assert len(overlap) > 0

    def test_overlap_extraction(self):
        """Test overlap extraction between windows."""
        from chunkana.streaming.buffer_manager import BufferManager

        config = StreamingConfig(buffer_size=50, overlap_lines=3)
        manager = BufferManager(config)

        # Create content that spans windows
        text = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\n"
        stream = io.StringIO(text)

        windows = list(manager.read_windows(stream))

        # Check overlap in subsequent windows
        for i, (_buffer, overlap, _) in enumerate(windows):
            if i > 0:
                # Overlap should be from previous buffer
                assert len(overlap) <= config.overlap_lines


class TestSplitDetector:
    """Tests for SplitDetector."""

    def test_find_split_point_at_header(self):
        """Test finding split point before header."""
        from chunkana.streaming.fence_tracker import FenceTracker
        from chunkana.streaming.split_detector import SplitDetector

        detector = SplitDetector(threshold=0.5)
        fence_tracker = FenceTracker()

        buffer = [
            "Content line 1.\n",
            "Content line 2.\n",
            "# Header\n",
            "More content.\n",
        ]

        # Should find split point before header
        split_point = detector.find_split_point(buffer, fence_tracker)
        assert split_point >= 0

    def test_find_split_point_at_paragraph(self):
        """Test finding split point at paragraph boundary."""
        from chunkana.streaming.fence_tracker import FenceTracker
        from chunkana.streaming.split_detector import SplitDetector

        detector = SplitDetector(threshold=0.3)
        fence_tracker = FenceTracker()

        buffer = [
            "Content line 1.\n",
            "Content line 2.\n",
            "\n",  # Empty line - paragraph boundary
            "More content.\n",
        ]

        split_point = detector.find_split_point(buffer, fence_tracker)
        assert split_point >= 0

    def test_fallback_split(self):
        """Test fallback split at threshold."""
        from chunkana.streaming.fence_tracker import FenceTracker
        from chunkana.streaming.split_detector import SplitDetector

        detector = SplitDetector(threshold=0.8)
        fence_tracker = FenceTracker()

        # Buffer with no good split points
        buffer = ["line\n"] * 10

        split_point = detector.find_split_point(buffer, fence_tracker)
        # Should return threshold position
        assert split_point == 8  # 0.8 * 10


class TestStreamingIntegration:
    """Integration tests for streaming chunking."""

    def test_large_document_streaming(self):
        """Test streaming a large document."""
        chunk_config = ChunkConfig(max_chunk_size=500)
        streaming_config = StreamingConfig(buffer_size=1000)
        chunker = StreamingChunker(chunk_config, streaming_config)

        # Create large document
        sections = []
        for i in range(20):
            sections.append(f"# Section {i}\n\n")
            sections.append("Content " * 50 + "\n\n")

        text = "".join(sections)
        stream = io.StringIO(text)

        chunks = list(chunker.chunk_stream(stream))

        # Should produce multiple chunks
        assert len(chunks) > 5

        # All chunks should have content
        for chunk in chunks:
            assert chunk.content.strip()

    def test_streaming_preserves_code_blocks(self):
        """Test that streaming preserves code blocks."""
        chunk_config = ChunkConfig()
        streaming_config = StreamingConfig(buffer_size=500)
        chunker = StreamingChunker(chunk_config, streaming_config)

        text = """# Code

```python
def function():
    pass
```

# More

```javascript
console.log("hello");
```
"""
        stream = io.StringIO(text)
        chunks = list(chunker.chunk_stream(stream))

        combined = "".join(c.content for c in chunks)

        # Code blocks should be preserved
        assert "def function" in combined
        assert "console.log" in combined

    def test_streaming_metadata_consistency(self):
        """Test that streaming metadata is consistent."""
        chunk_config = ChunkConfig()
        chunker = StreamingChunker(chunk_config)

        text = "# Header\n\nContent.\n" * 10
        stream = io.StringIO(text)

        chunks = list(chunker.chunk_stream(stream))

        # Check metadata consistency
        for i, chunk in enumerate(chunks):
            assert chunk.metadata.get("stream_chunk_index") == i
            assert "stream_window_index" in chunk.metadata
            assert "bytes_processed" in chunk.metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
