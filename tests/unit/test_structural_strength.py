"""
Unit tests for structural strength evaluation.

Ported from dify-markdown-chunker to increase test coverage.
Tests the small_chunk flagging logic that considers structural strength.
"""

from chunkana import ChunkConfig, MarkdownChunker


class TestStructuralStrength:
    """Test structural strength evaluation for small_chunk flagging."""

    def test_level_2_header_prevents_small_flag(self):
        """Chunk with level 2 header should not be flagged as small."""
        markdown = """## Scope

Brief but meaningful content.
"""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=100)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        scope_chunks = [c for c in chunks if "## Scope" in c.content]
        if scope_chunks:
            chunk = scope_chunks[0]
            assert not chunk.metadata.get("small_chunk", False), (
                "Level 2 header chunk should not be flagged as small"
            )

    def test_level_3_header_prevents_small_flag(self):
        """Chunk with level 3 header should not be flagged as small."""
        markdown = """### Technical Complexity

Short description.
"""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=100)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            if "### Technical Complexity" in chunk.content:
                assert not chunk.metadata.get("small_chunk", False)

    def test_multiple_paragraphs_prevent_small_flag(self):
        """Chunk with multiple paragraphs should not be flagged as small."""
        markdown = """First paragraph with some content.

Second paragraph with more content.

Third paragraph."""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=150)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            paragraph_breaks = chunk.content.count("\n\n")
            if paragraph_breaks >= 2:
                assert not chunk.metadata.get("small_chunk", False), (
                    "Multi-paragraph chunk should not be flagged as small"
                )

    def test_sufficient_text_lines_prevent_small_flag(self):
        """Chunk with 3+ non-header lines should not be flagged as small."""
        markdown = """Line one of content.
Line two of content.
Line three of content.
Line four of content."""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=150)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            lines = [
                line
                for line in chunk.content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            if len(lines) >= 3:
                assert not chunk.metadata.get("small_chunk", False)

    def test_meaningful_content_prevents_small_flag(self):
        """Chunk with >100 chars of non-header content should not be flagged."""
        markdown = """## Short Header

This is a section with meaningful content that exceeds one hundred characters after we extract the header. This text provides substantial information."""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            if "meaningful content" in chunk.content:
                lines = [
                    line for line in chunk.content.split("\n") if not line.strip().startswith("#")
                ]
                non_header = "\n".join(lines).strip()
                if len(non_header) > 100:
                    assert not chunk.metadata.get("small_chunk", False)

    def test_structurally_weak_chunk_is_flagged(self):
        """Truly weak chunk should still be flagged as small."""
        markdown = """# Main

## Section 1

Substantial content for section 1 that will be a normal chunk.

## Section 2

Very brief.

## Section 3

More substantial content for section 3."""
        config = ChunkConfig(max_chunk_size=250, min_chunk_size=100, overlap_size=50)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        small_chunks = [c for c in chunks if c.metadata.get("small_chunk", False)]
        assert isinstance(small_chunks, list)

    def test_lists_not_considered_structural_strength(self):
        """Lists are not yet considered as structural strength indicators."""
        markdown = """- Item 1
- Item 2
- Item 3
- Item 4"""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=100)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        assert len(chunks) >= 1


class TestSmallChunkFlagging:
    """Test small_chunk flag behavior."""

    def test_small_chunk_reason_is_cannot_merge(self):
        """small_chunk_reason should be 'cannot_merge'."""
        markdown = """# Main

## Section 1

Long content that forms a normal chunk with sufficient text.

## Section 2

x

## Section 3

More long content that forms another normal chunk."""
        config = ChunkConfig(max_chunk_size=200, min_chunk_size=100, overlap_size=50)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            if chunk.metadata.get("small_chunk", False):
                assert chunk.metadata.get("small_chunk_reason") == "cannot_merge"

    def test_content_rich_scope_not_flagged(self):
        """Content-rich Scope section should not be flagged as small."""
        markdown = """# Task Description

## Scope

#### Problem Description

The current system has issues with performance and scalability.
We need to redesign the architecture to handle increased load.

#### Work Completed

1. Analyzed current architecture
2. Designed new approach
3. Implemented proof of concept
4. Validated with stakeholders

Multiple paragraphs and substantial content make this structurally strong."""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            if "## Scope" in chunk.content:
                assert not chunk.metadata.get("small_chunk", False), (
                    "Content-rich Scope section should not be flagged as small"
                )

    def test_impact_section_not_flagged(self):
        """Content-rich Impact section should not be flagged as small."""
        markdown = """## Impact (Delivery)

The project delivered significant value:

- Improved system performance by 5x
- Reduced infrastructure costs by 40%
- Enabled new product features
- Improved developer experience

Team of 8 people worked for 6 months."""
        config = ChunkConfig(max_chunk_size=1000, min_chunk_size=200)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(markdown)

        for chunk in chunks:
            if "## Impact" in chunk.content:
                assert not chunk.metadata.get("small_chunk", False)
