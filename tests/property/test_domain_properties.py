"""
Property-based tests for domain properties PROP-1 through PROP-9.

Ported from dify-markdown-chunker to increase test coverage.
These tests validate the core correctness properties.
"""

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from chunkana import ChunkConfig, MarkdownChunker

# =============================================================================
# Generators
# =============================================================================


@st.composite
def markdown_text(draw, min_size: int = 1, max_size: int = 5000):
    """Generate arbitrary markdown text."""
    text = draw(
        st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "Z"), blacklist_characters="\x00\r"
            ),
            min_size=min_size,
            max_size=max_size,
        )
    )
    assume(text.strip())
    return text


@st.composite
def markdown_with_headers(draw):
    """Generate markdown with headers."""
    sections = []
    num_sections = draw(st.integers(min_value=2, max_value=5))

    for i in range(num_sections):
        level = draw(st.integers(min_value=1, max_value=3))
        header = "#" * level + f" Section {i + 1}"
        content = draw(
            st.text(
                alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
                min_size=20,
                max_size=200,
            ).filter(lambda x: x.strip() and "#" not in x)
        )
        sections.append(f"{header}\n\n{content}")

    return "\n\n".join(sections)


@st.composite
def markdown_with_code(draw):
    """Generate markdown with code blocks."""
    parts = []
    num_blocks = draw(st.integers(min_value=1, max_value=3))

    for _i in range(num_blocks):
        text = draw(
            st.text(min_size=10, max_size=100).filter(lambda x: "```" not in x and x.strip())
        )
        parts.append(text)

        lang = draw(st.sampled_from(["python", "javascript", "bash", ""]))
        code = draw(st.text(min_size=5, max_size=150).filter(lambda x: "```" not in x))
        parts.append(f"```{lang}\n{code}\n```")

    final = draw(st.text(min_size=10, max_size=100).filter(lambda x: "```" not in x and x.strip()))
    parts.append(final)

    return "\n\n".join(parts)


@st.composite
def markdown_with_tables(draw):
    """Generate markdown with tables."""
    header = "# Document with Table\n\n"

    # Generate table
    cols = draw(st.integers(min_value=2, max_value=4))
    rows = draw(st.integers(min_value=2, max_value=5))

    header_row = "| " + " | ".join([f"Col{i}" for i in range(cols)]) + " |"
    sep_row = "| " + " | ".join(["---"] * cols) + " |"

    data_rows = []
    for _r in range(rows):
        cells = [
            draw(st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnop")) for _ in range(cols)
        ]
        data_rows.append("| " + " | ".join(cells) + " |")

    table = "\n".join([header_row, sep_row] + data_rows)

    after = "\n\nText after table."

    return header + table + after


# =============================================================================
# PROP-1: No Content Loss
# =============================================================================


class TestProp1NoContentLoss:
    """PROP-1: No Content Loss - content should be preserved."""

    @given(doc=markdown_text(min_size=50, max_size=2000))
    @settings(max_examples=100, deadline=None)
    def test_content_preserved(self, doc: str):
        """All non-whitespace chars should be present in chunks."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(doc)

        # Reconstruct content
        reconstructed = "".join(c.content for c in chunks)

        # All non-whitespace chars should be present
        original_chars = {c for c in doc if not c.isspace()}
        reconstructed_chars = {c for c in reconstructed if not c.isspace()}

        missing = original_chars - reconstructed_chars
        assert not missing, f"Characters lost: {missing}"


# =============================================================================
# PROP-2: Size Bounds
# =============================================================================


class TestProp2SizeBounds:
    """PROP-2: Size Bounds - chunks should respect max_chunk_size."""

    @given(doc=markdown_text(min_size=100, max_size=3000))
    @settings(max_examples=100, deadline=None)
    def test_size_bounds_respected(self, doc: str):
        """Chunks should not exceed max_chunk_size unless allow_oversize."""
        config = ChunkConfig(max_chunk_size=500)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(doc)

        for i, chunk in enumerate(chunks):
            if len(chunk.content) > config.max_chunk_size:
                assert chunk.metadata.get("allow_oversize", False), (
                    f"Chunk {i} exceeds max_chunk_size ({len(chunk.content)}) "
                    f"without allow_oversize flag"
                )


# =============================================================================
# PROP-3: Monotonic Ordering
# =============================================================================


class TestProp3MonotonicOrdering:
    """PROP-3: Monotonic Ordering - chunk start_lines should be non-decreasing."""

    @given(doc=markdown_text(min_size=100, max_size=2000))
    @settings(max_examples=100, deadline=None)
    def test_monotonic_ordering(self, doc: str):
        """Chunk start_lines should be monotonically non-decreasing."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(doc)

        for i in range(len(chunks) - 1):
            assert chunks[i].start_line <= chunks[i + 1].start_line, (
                f"Chunks out of order: chunk {i} starts at line {chunks[i].start_line}, "
                f"chunk {i + 1} starts at line {chunks[i + 1].start_line}"
            )


# =============================================================================
# PROP-4: No Empty Chunks
# =============================================================================


class TestProp4NoEmptyChunks:
    """PROP-4: No Empty Chunks - all chunks should have content."""

    @given(doc=markdown_text(min_size=50, max_size=2000))
    @settings(max_examples=100, deadline=None)
    def test_no_empty_chunks(self, doc: str):
        """No chunk should have empty or whitespace-only content."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(doc)

        for i, chunk in enumerate(chunks):
            assert chunk.content.strip(), f"Chunk {i} is empty or whitespace-only"


# =============================================================================
# PROP-5: Valid Line Numbers
# =============================================================================


class TestProp5ValidLineNumbers:
    """PROP-5: Valid Line Numbers - start_line >= 1 and end_line >= start_line."""

    @given(doc=markdown_text(min_size=50, max_size=2000))
    @settings(max_examples=100, deadline=None)
    def test_valid_line_numbers(self, doc: str):
        """Each chunk should have valid line numbers."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(doc)

        for i, chunk in enumerate(chunks):
            assert chunk.start_line >= 1, f"Chunk {i} has invalid start_line: {chunk.start_line}"
            assert chunk.end_line >= chunk.start_line, (
                f"Chunk {i} has end_line ({chunk.end_line}) < start_line ({chunk.start_line})"
            )


# =============================================================================
# PROP-6: Code Block Integrity
# =============================================================================


class TestProp6CodeBlockIntegrity:
    """PROP-6: Code Block Integrity - code blocks should not be split."""

    @given(doc=markdown_with_code())
    @settings(max_examples=100, deadline=None)
    def test_code_blocks_not_split(self, doc: str):
        """Each code block should be in exactly one chunk."""
        chunker = MarkdownChunker(ChunkConfig(max_chunk_size=2000))
        chunks = chunker.chunk(doc)

        for i, chunk in enumerate(chunks):
            fence_count = chunk.content.count("```")
            has_error = chunk.metadata.get("fence_balance_error", False)

            # Either balanced fences or error flag
            assert fence_count % 2 == 0 or has_error, (
                f"Chunk {i} has unbalanced fences ({fence_count}) without error flag"
            )


# =============================================================================
# PROP-7: Table Integrity
# =============================================================================


class TestProp7TableIntegrity:
    """PROP-7: Table Integrity - tables should not be split."""

    @given(doc=markdown_with_tables())
    @settings(max_examples=50, deadline=None)
    def test_tables_not_split(self, doc: str):
        """Each table should be in at most one chunk."""
        chunker = MarkdownChunker(ChunkConfig(max_chunk_size=2000))
        chunks = chunker.chunk(doc)

        # Find table header in chunks
        table_header = "| Col0 |"
        containing = [i for i, c in enumerate(chunks) if table_header in c.content]

        # Table should be in at most one chunk
        assert len(containing) <= 1, f"Table found in multiple chunks: {containing}"


# =============================================================================
# PROP-9: Idempotence
# =============================================================================


class TestProp9Idempotence:
    """PROP-9: Idempotence - chunking should be deterministic."""

    @given(doc=markdown_text(min_size=50, max_size=2000))
    @settings(max_examples=100, deadline=None)
    def test_idempotence(self, doc: str):
        """Chunking multiple times should produce identical results."""
        chunker = MarkdownChunker()

        chunks1 = chunker.chunk(doc)
        chunks2 = chunker.chunk(doc)

        assert len(chunks1) == len(chunks2), (
            f"Different chunk counts: {len(chunks1)} vs {len(chunks2)}"
        )

        for i, (c1, c2) in enumerate(zip(chunks1, chunks2, strict=False)):
            assert c1.content == c2.content, f"Chunk {i} content differs"
            assert c1.start_line == c2.start_line, f"Chunk {i} start_line differs"
            assert c1.end_line == c2.end_line, f"Chunk {i} end_line differs"


# =============================================================================
# Additional Core Properties
# =============================================================================


class TestDataPreservation:
    """Test content is preserved in various scenarios."""

    def test_content_preserved_simple(self):
        """Test content is preserved in simple case."""
        chunker = MarkdownChunker()
        text = "Hello world. This is a test."
        chunks = chunker.chunk(text)

        combined = "".join(c.content for c in chunks)

        for word in ["Hello", "world", "This", "test"]:
            assert word in combined

    def test_content_preserved_with_code(self):
        """Test content is preserved with code blocks."""
        chunker = MarkdownChunker()
        text = """# Header

Some text.

```python
def hello():
    return "world"
```

More text.
"""
        chunks = chunker.chunk(text)
        combined = "".join(c.content for c in chunks)

        assert "Header" in combined
        assert "def hello" in combined
        assert "More text" in combined

    @given(
        st.text(min_size=1, max_size=500).filter(
            lambda x: x.strip() and any(c.isalnum() for c in x)
        )
    )
    @settings(
        max_examples=50,
        deadline=5000,
        suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.too_slow],
    )
    def test_alphanumeric_content_preserved(self, text: str):
        """Property: Alphanumeric content is preserved."""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(text)

        if not chunks:
            return

        combined = "".join(c.content for c in chunks)

        import re

        original_words = set(re.findall(r"\w+", text))
        combined_words = set(re.findall(r"\w+", combined))

        preserved = len(original_words & combined_words)
        total = len(original_words)
        if total > 0:
            assert preserved / total >= 0.8, f"Only {preserved}/{total} words preserved"


class TestIdempotenceDetailed:
    """Detailed idempotence tests."""

    def test_chunking_deterministic(self):
        """Test chunking produces same result on repeated calls."""
        chunker = MarkdownChunker()
        text = """# Header

Some content here.

## Subheader

More content.
"""
        chunks1 = chunker.chunk(text)
        chunks2 = chunker.chunk(text)

        assert len(chunks1) == len(chunks2)

        for c1, c2 in zip(chunks1, chunks2, strict=False):
            assert c1.content == c2.content
            assert c1.start_line == c2.start_line
            assert c1.end_line == c2.end_line

    def test_different_chunker_instances_same_result(self):
        """Test different chunker instances produce same result."""
        config = ChunkConfig(max_chunk_size=500)

        chunker1 = MarkdownChunker(config)
        chunker2 = MarkdownChunker(config)

        text = "Test content. " * 20

        chunks1 = chunker1.chunk(text)
        chunks2 = chunker2.chunk(text)

        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2, strict=False):
            assert c1.content == c2.content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
