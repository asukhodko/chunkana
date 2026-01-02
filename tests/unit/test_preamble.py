"""
Tests for preamble handling and structural strategy selection.

Ported from dify-markdown-chunker to increase test coverage.
"""

import pytest

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.parser import Parser
from chunkana.strategies import StrategySelector


class TestPreambleScenario:
    """Tests for preamble scenario using structured document with preamble."""

    @pytest.fixture
    def test_document(self):
        """Create a test document with preamble."""
        return """Preamble text introducing the document.

This is additional preamble content before the first header.
It provides context and introduction.

More preamble content here.
Multiple paragraphs of preamble.

# Main Title

## Section 1

Content of section 1.

### Subsection 1.1

- Item 1
- Item 2
- Item 3

### Subsection 1.2

More content here.

## Section 2

Content of section 2.

### Subsection 2.1

- Item A
- Item B
- Item C

### Subsection 2.2

Final content.
"""

    @pytest.fixture
    def config(self):
        """Configuration matching manual test parameters."""
        return ChunkConfig(
            max_chunk_size=1000,
            overlap_size=200,
        )

    def test_strategy_selection_is_structural(self, test_document, config):
        """Test that structural strategy is selected (not list_aware)."""
        parser = Parser()
        analysis = parser.analyze(test_document)
        selector = StrategySelector()
        strategy = selector.select(analysis, config)

        assert strategy.name == "structural", (
            f"Expected structural strategy, got {strategy.name}. "
            f"Document has {analysis.header_count} headers, "
            f"{analysis.list_count} list blocks (ratio {analysis.list_ratio:.2%}). "
        )

    def test_first_chunk_is_preamble(self, test_document, config):
        """Test that first chunk has correct preamble metadata."""
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(test_document)

        assert len(chunks) > 0, "Document should produce at least one chunk"

        first_chunk = chunks[0]

        assert first_chunk.metadata["content_type"] == "preamble", (
            "First chunk should have content_type='preamble'"
        )
        assert first_chunk.metadata["header_path"] == "/__preamble__", (
            "Preamble should have header_path='/__preamble__'"
        )
        assert first_chunk.metadata["header_level"] == 0, "Preamble should have header_level=0"
        assert first_chunk.metadata["chunk_index"] == 0, "First chunk should have chunk_index=0"

        assert first_chunk.start_line == 1, "Preamble should start at line 1"

    def test_preamble_content_accuracy(self, test_document, config):
        """Test that preamble content matches expected text."""
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(test_document)

        first_chunk = chunks[0]

        assert first_chunk.metadata["content_type"] == "preamble"
        assert "Preamble text" in first_chunk.content
        assert "introducing the document" in first_chunk.content
        assert "# Main Title" not in first_chunk.content

    def test_preamble_next_content_present(self, test_document, config):
        """Test that next_content field is present and contains next section."""
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(test_document)

        first_chunk = chunks[0]

        if len(chunks) > 1:
            assert "next_content" in first_chunk.metadata, (
                "First chunk metadata should contain next_content field"
            )

            next_content = first_chunk.metadata["next_content"]
            assert next_content and next_content.strip(), "next_content should not be empty"

    def test_strategy_field_in_metadata(self, test_document, config):
        """Test that strategy field is present in metadata."""
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(test_document)

        for chunk in chunks:
            assert "strategy" in chunk.metadata, (
                f"Chunk {chunk.metadata.get('chunk_index')} missing strategy field"
            )
            assert chunk.metadata["strategy"] == "structural"


class TestDocumentWithoutPreamble:
    """Tests for documents that start directly with a header."""

    def test_no_preamble_when_starts_with_header(self):
        """Test document starting with # has no preamble chunk."""
        md_text = """# First Header

This is the first section content.

## Subsection

More content here.
"""

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        assert len(chunks) > 0, "Document should produce chunks"

        first_chunk = chunks[0]
        assert first_chunk.metadata["content_type"] != "preamble", (
            "Document starting with header should not have preamble chunk"
        )
        assert first_chunk.metadata["header_path"] != "/__preamble__", (
            "First chunk should not have preamble header_path"
        )

    def test_no_preamble_with_only_whitespace_before_header(self):
        """Test that whitespace-only content before header doesn't create preamble."""
        md_text = """


# First Header

Content here.
"""

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        preamble_chunks = [c for c in chunks if c.metadata.get("content_type") == "preamble"]
        assert len(preamble_chunks) == 0, "Whitespace-only content should not create preamble chunk"


class TestLongPreamble:
    """Tests for documents with long preamble close to max_chunk_size."""

    def test_long_preamble_near_limit(self):
        """Test preamble close to max_chunk_size is handled correctly."""
        preamble_lines = [
            f"Preamble line {i} with some additional text content." for i in range(15)
        ]
        preamble = "\n".join(preamble_lines)

        md_text = f"""{preamble}

# Main Title

## Section 1

Section content.

## Section 2

More content.

## Section 3

Final content.
"""

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        assert len(chunks) > 0

        first_chunk = chunks[0]
        assert first_chunk.metadata["content_type"] == "preamble"
        assert first_chunk.start_line == 1


class TestMultipleChunks:
    """Tests for documents requiring multiple chunks."""

    def test_multiple_chunks_with_preamble(self):
        """Test document with preamble that produces multiple chunks."""
        preamble = "Preamble content before headers.\nMore preamble."

        sections = []
        for i in range(10):
            section = f"""## Section {i}

This is section {i} with substantial content that will help fill up the chunks.
It needs to be long enough to trigger multiple chunks.
More text here to increase size.
Additional paragraphs to make it realistic.
Even more content.
"""
            sections.append(section)

        md_text = f"""{preamble}

# Main Title

{"".join(sections)}
"""

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        assert len(chunks) > 2, f"Expected multiple chunks, got {len(chunks)}"

        indices = [c.metadata["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks))), (
            "chunk_index should be sequential starting from 0"
        )

        assert chunks[0].metadata["content_type"] == "preamble"


class TestStrategySelectionLogic:
    """Tests for strategy selection logic."""

    def test_structural_preferred_over_list_aware_for_hierarchical_docs(self):
        """Test that structural strategy is preferred for hierarchical documents."""
        md_text = """# Main Title

## Section 1

Content here.

### Subsection 1.1

- List item 1
- List item 2

### Subsection 1.2

More content.

## Section 2

### Subsection 2.1

- Item A
- Item B

### Subsection 2.2

Final content.
"""

        parser = Parser()
        analysis = parser.analyze(md_text)
        config = ChunkConfig()
        selector = StrategySelector()
        strategy = selector.select(analysis, config)

        assert strategy.name == "structural", (
            f"Expected structural strategy for hierarchical document, got {strategy.name}. "
            f"Headers: {analysis.header_count}, Lists: {analysis.list_count}"
        )

    def test_list_aware_for_list_heavy_without_structure(self):
        """Test that list_aware is selected for list-heavy documents without structure."""
        md_text = """Some introduction text.

- Item 1
- Item 2
- Item 3

Another paragraph.

- Item 4
- Item 5
- Item 6

More text.

- Item 7
- Item 8

Yet more text.

- Item 9
- Item 10

Final paragraph.

- Item 11
- Item 12
- Item 13
"""

        parser = Parser()
        analysis = parser.analyze(md_text)
        config = ChunkConfig()
        selector = StrategySelector()
        strategy = selector.select(analysis, config)

        assert strategy.name == "list_aware", (
            f"Expected list_aware for list-heavy document, got {strategy.name}. "
            f"Lists: {analysis.list_count}, List ratio: {analysis.list_ratio:.2%}"
        )
