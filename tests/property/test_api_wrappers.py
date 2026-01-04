"""
Property tests for API wrapper functions (Task 6.5-6.8).

Tests:
- chunk_text equivalence to chunk_markdown
- chunk_file equivalence to chunk_markdown
- chunk_file_streaming invariants
- chunk_hierarchical leaf coverage
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from chunkana import (
    ChunkerConfig,
    chunk_file,
    chunk_file_streaming,
    chunk_hierarchical,
    chunk_markdown,
    chunk_text,
)

# =============================================================================
# Strategies
# =============================================================================

markdown_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S", "Zs"),
        whitelist_characters="\n#*-_`[]()>",
    ),
    min_size=1,
    max_size=2000,
).filter(lambda x: x.strip())


simple_markdown = st.sampled_from(
    [
        "# Hello\n\nWorld",
        "## Section\n\nContent here.\n\n## Another\n\nMore content.",
        "# Doc\n\n```python\ncode\n```\n\nText after.",
        "Plain text without headers.",
        "# H1\n\n## H2\n\n### H3\n\nDeep nesting.",
    ]
)


# =============================================================================
# Task 6.5: chunk_text Equivalence
# =============================================================================


class TestChunkTextEquivalence:
    """Property 5: chunk_text produces identical output to chunk_markdown."""

    @given(text=markdown_text)
    @settings(max_examples=50)
    def test_chunk_text_equals_chunk_markdown(self, text: str):
        """chunk_text(text) == chunk_markdown(text) for all inputs."""
        result_text = chunk_text(text)
        result_markdown = chunk_markdown(text)

        assert len(result_text) == len(result_markdown)
        for ct, cm in zip(result_text, result_markdown, strict=False):
            assert ct.content == cm.content
            assert ct.start_line == cm.start_line
            assert ct.end_line == cm.end_line

    @given(text=simple_markdown)
    def test_chunk_text_with_config(self, text: str):
        """chunk_text respects config same as chunk_markdown."""
        config = ChunkerConfig(max_chunk_size=1000, overlap_size=50)

        result_text = chunk_text(text, config)
        result_markdown = chunk_markdown(text, config)

        assert len(result_text) == len(result_markdown)


# =============================================================================
# Task 6.6: chunk_file Equivalence
# =============================================================================


class TestChunkFileEquivalence:
    """Property 6: chunk_file produces identical output to chunk_markdown."""

    @given(text=simple_markdown)
    def test_chunk_file_equals_chunk_markdown(self, text: str):
        """chunk_file(path) == chunk_markdown(read(path))."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            f.flush()
            temp_path = f.name

        try:
            result_file = chunk_file(temp_path)
            result_markdown = chunk_markdown(text)

            assert len(result_file) == len(result_markdown)
            for cf, cm in zip(result_file, result_markdown, strict=False):
                assert cf.content == cm.content
                assert cf.start_line == cm.start_line
                assert cf.end_line == cm.end_line
        finally:
            Path(temp_path).unlink()

    def test_chunk_file_not_found(self):
        """chunk_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            chunk_file("/nonexistent/path/file.md")

    def test_chunk_file_path_object(self):
        """chunk_file accepts Path objects."""
        text = "# Test\n\nContent"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            f.flush()
            temp_path = Path(f.name)

        try:
            result = chunk_file(temp_path)
            assert len(result) > 0
        finally:
            temp_path.unlink()


# =============================================================================
# Task 6.7: chunk_file_streaming Invariants
# =============================================================================


class TestChunkFileStreamingInvariants:
    """Property 7: chunk_file_streaming maintains chunking invariants."""

    @given(text=simple_markdown)
    def test_streaming_yields_chunks(self, text: str):
        """Streaming yields at least one chunk for non-empty input."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            f.flush()
            temp_path = f.name

        try:
            chunks = list(chunk_file_streaming(temp_path))
            assert len(chunks) > 0
        finally:
            Path(temp_path).unlink()

    @given(text=simple_markdown)
    def test_streaming_monotonic_start_line(self, text: str):
        """Streaming chunks have monotonically increasing start_line."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            f.flush()
            temp_path = f.name

        try:
            chunks = list(chunk_file_streaming(temp_path))
            for i in range(1, len(chunks)):
                assert chunks[i].start_line >= chunks[i - 1].start_line, (
                    f"Chunk {i} start_line {chunks[i].start_line} < "
                    f"chunk {i - 1} start_line {chunks[i - 1].start_line}"
                )
        finally:
            Path(temp_path).unlink()

    @given(text=simple_markdown)
    def test_streaming_no_empty_chunks(self, text: str):
        """Streaming produces no empty chunks."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(text)
            f.flush()
            temp_path = f.name

        try:
            chunks = list(chunk_file_streaming(temp_path))
            for i, chunk in enumerate(chunks):
                assert chunk.content.strip(), f"Chunk {i} is empty"
        finally:
            Path(temp_path).unlink()

    def test_streaming_file_not_found(self):
        """chunk_file_streaming raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            list(chunk_file_streaming("/nonexistent/path/file.md"))


# =============================================================================
# Task 6.8: chunk_hierarchical Leaf Coverage
# =============================================================================


class TestChunkHierarchicalLeafCoverage:
    """Property 8: chunk_hierarchical leaf chunks cover all content."""

    @given(text=simple_markdown)
    def test_hierarchical_returns_result(self, text: str):
        """chunk_hierarchical returns HierarchicalChunkingResult."""
        result = chunk_hierarchical(text)
        assert result is not None
        assert hasattr(result, "chunks")
        assert hasattr(result, "root_id")
        assert hasattr(result, "get_flat_chunks")

    @given(text=simple_markdown)
    def test_leaf_chunks_cover_content(self, text: str):
        """Leaf chunks from get_flat_chunks() cover source content."""
        result = chunk_hierarchical(text)
        leaves = result.get_flat_chunks()

        # All leaves should have content
        for leaf in leaves:
            assert leaf.content.strip(), "Leaf chunk has no content"

        # Concatenated leaf content should cover source
        # (allowing for overlap and formatting differences)
        leaf_content = "".join(c.content for c in leaves)

        # Check that significant words from source appear in leaves
        source_words = set(text.split())
        leaf_words = set(leaf_content.split())

        # At least 80% of source words should appear in leaves
        if source_words:
            coverage = len(source_words & leaf_words) / len(source_words)
            assert coverage >= 0.8, f"Leaf coverage {coverage:.1%} < 80%"

    @given(text=simple_markdown)
    def test_hierarchical_root_exists(self, text: str):
        """Hierarchical result has valid root chunk."""
        result = chunk_hierarchical(text)
        root = result.get_chunk(result.root_id)
        assert root is not None, "Root chunk not found"

    @given(text=simple_markdown)
    def test_hierarchical_navigation_works(self, text: str):
        """Navigation methods work correctly."""
        result = chunk_hierarchical(text)

        # Get children of root
        children = result.get_children(result.root_id)
        assert isinstance(children, list)

        # Each child should have root as parent
        for child in children:
            parent = result.get_parent(child.metadata["chunk_id"])
            if parent:
                assert parent.metadata["chunk_id"] == result.root_id

    def test_hierarchical_without_summary(self):
        """chunk_hierarchical works without document summary."""
        text = "# Test\n\nContent"
        result = chunk_hierarchical(text, include_document_summary=False)
        assert result is not None
        assert len(result.chunks) > 0
