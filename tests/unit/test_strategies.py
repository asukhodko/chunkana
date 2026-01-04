"""
Unit tests for chunking strategies.

Tests strategy selection and behavior to increase coverage.
"""

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.parser import Parser
from chunkana.strategies import StrategySelector


class TestStrategySelector:
    """Tests for StrategySelector."""

    def test_code_aware_for_code_heavy(self):
        """Code-heavy documents should use code_aware strategy."""
        md_text = """# Code Example

```python
def function1():
    pass

def function2():
    pass

def function3():
    pass
```

```python
class MyClass:
    def method(self):
        pass
```
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()
        config = ChunkConfig()

        strategy = selector.select(analysis, config)
        assert strategy.name == "code_aware"

    def test_code_aware_for_tables(self):
        """Documents with tables should use code_aware strategy."""
        md_text = """# Data Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

Some text after table.
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()
        config = ChunkConfig()

        strategy = selector.select(analysis, config)
        assert strategy.name == "code_aware"

    def test_structural_for_headers(self):
        """Documents with many headers should use structural strategy."""
        md_text = """# Main Title

## Section 1

Content 1.

## Section 2

Content 2.

## Section 3

Content 3.

## Section 4

Content 4.
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()
        config = ChunkConfig()

        strategy = selector.select(analysis, config)
        assert strategy.name == "structural"

    def test_list_aware_for_lists(self):
        """List-heavy documents should use list_aware strategy."""
        md_text = """Introduction text.

- Item 1
- Item 2
- Item 3

More text.

- Item 4
- Item 5
- Item 6

Even more text.

- Item 7
- Item 8
- Item 9

Final text.

- Item 10
- Item 11
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()
        config = ChunkConfig()

        strategy = selector.select(analysis, config)
        assert strategy.name == "list_aware"

    def test_fallback_for_plain_text(self):
        """Plain text should use fallback strategy."""
        md_text = """This is just plain text without any markdown structure.
It has multiple sentences but no headers, code blocks, or lists.
Just paragraphs of text that need to be chunked somehow.
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()
        config = ChunkConfig()

        strategy = selector.select(analysis, config)
        assert strategy.name == "fallback"

    def test_strategy_override(self):
        """Strategy override should force specific strategy."""
        md_text = """# Header

Some content.
"""
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()

        # Force fallback even though document has headers
        config = ChunkConfig(strategy_override="fallback")
        strategy = selector.select(analysis, config)
        assert strategy.name == "fallback"

    def test_strategy_override_code_aware(self):
        """Strategy override to code_aware."""
        md_text = "Plain text without code."
        parser = Parser()
        analysis = parser.analyze(md_text)
        selector = StrategySelector()

        config = ChunkConfig(strategy_override="code_aware")
        strategy = selector.select(analysis, config)
        assert strategy.name == "code_aware"


class TestCodeAwareStrategy:
    """Tests for CodeAwareStrategy behavior."""

    def test_preserves_code_blocks(self):
        """Code blocks should not be split."""
        md_text = """# Example

```python
def long_function():
    # This is a long function
    x = 1
    y = 2
    z = 3
    return x + y + z
```

Text after code.
"""
        config = ChunkConfig(max_chunk_size=500)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Find chunk with code
        code_chunks = [c for c in chunks if "def long_function" in c.content]
        assert len(code_chunks) == 1

        # Code block should be complete
        code_chunk = code_chunks[0]
        assert "```python" in code_chunk.content
        assert "return x + y + z" in code_chunk.content

    def test_preserves_tables(self):
        """Tables should not be split."""
        md_text = """# Data

| Col1 | Col2 | Col3 |
|------|------|------|
| A    | B    | C    |
| D    | E    | F    |
| G    | H    | I    |

Text after table.
"""
        config = ChunkConfig(max_chunk_size=500)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Find chunk with table
        table_chunks = [c for c in chunks if "| Col1 |" in c.content]
        assert len(table_chunks) == 1

        # Table should be complete
        table_chunk = table_chunks[0]
        assert "| G    | H    | I    |" in table_chunk.content


class TestStructuralStrategy:
    """Tests for StructuralStrategy behavior."""

    def test_splits_on_headers(self):
        """Should split on header boundaries."""
        md_text = """# Section 1

Content for section 1.

# Section 2

Content for section 2.

# Section 3

Content for section 3.
"""
        config = ChunkConfig(max_chunk_size=100, overlap_size=20)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Should have multiple chunks
        assert len(chunks) >= 2

        # Each chunk should have header_path metadata
        for chunk in chunks:
            assert "header_path" in chunk.metadata

    def test_preserves_hierarchy(self):
        """Should preserve header hierarchy in metadata."""
        md_text = """# Main

## Sub 1

Content 1.

## Sub 2

Content 2.
"""
        config = ChunkConfig(max_chunk_size=1000)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Check header_path contains hierarchy
        paths = [c.metadata.get("header_path", "") for c in chunks]
        assert any("Main" in p for p in paths)


class TestListAwareStrategy:
    """Tests for ListAwareStrategy behavior."""

    def test_preserves_list_items(self):
        """List items should not be split mid-item."""
        md_text = """Introduction.

- First item with some content
- Second item with more content
- Third item with even more content

Conclusion.
"""
        config = ChunkConfig(max_chunk_size=500)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Check that list items are complete
        for chunk in chunks:
            content = chunk.content
            # If chunk has list items, they should be complete
            if "- First item" in content:
                assert "First item with some content" in content


class TestFallbackStrategy:
    """Tests for FallbackStrategy behavior."""

    def test_handles_plain_text(self):
        """Should handle plain text without structure."""
        md_text = "This is plain text. " * 50

        config = ChunkConfig(max_chunk_size=200, overlap_size=50)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Should produce chunks
        assert len(chunks) >= 1

        # All content should be preserved
        combined = "".join(c.content for c in chunks)
        assert "This is plain text" in combined

    def test_respects_size_limits(self):
        """Should respect max_chunk_size or mark as oversize."""
        md_text = "Word " * 500

        config = ChunkConfig(max_chunk_size=100, overlap_size=20)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Should produce chunks
        assert len(chunks) >= 1

        # Chunks that exceed limit should have allow_oversize flag
        for chunk in chunks:
            if len(chunk.content) > config.max_chunk_size:
                assert chunk.metadata.get("allow_oversize", False)


class TestStrategyMetadata:
    """Tests for strategy metadata in chunks."""

    def test_strategy_in_metadata(self):
        """Each chunk should have strategy in metadata."""
        md_text = """# Header

Content here.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        for chunk in chunks:
            assert "strategy" in chunk.metadata
            assert chunk.metadata["strategy"] in [
                "code_aware",
                "structural",
                "list_aware",
                "fallback",
            ]

    def test_content_type_in_metadata(self):
        """Each chunk should have content_type in metadata."""
        md_text = """Preamble text.

# Header

Section content.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        for chunk in chunks:
            assert "content_type" in chunk.metadata
