"""
Property-based tests for hierarchical chunking invariants.

Tests that hierarchical tree invariants hold for all valid markdown documents.
"""

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import integers, text

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.exceptions import HierarchicalInvariantError


# Hypothesis strategies for generating test data
@st.composite
def markdown_document(draw):
    """Generate valid markdown documents for testing."""
    # Generate headers at different levels
    headers = []
    for level in range(1, 4):  # H1, H2, H3
        count = draw(integers(min_value=0, max_value=3))
        for _ in range(count):
            header_text = draw(
                text(
                    min_size=5,
                    max_size=50,
                    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
                )
            )
            headers.append(f"{'#' * level} {header_text}")

    # Generate content paragraphs
    paragraphs = []
    paragraph_count = draw(integers(min_value=1, max_value=5))
    for _ in range(paragraph_count):
        paragraph = draw(
            text(
                min_size=20,
                max_size=200,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs", "Po")),
            )
        )
        paragraphs.append(paragraph)

    # Combine headers and paragraphs
    content_parts = headers + paragraphs
    draw(st.randoms()).shuffle(content_parts)

    # Join with double newlines
    document = "\n\n".join(content_parts)

    # Ensure document is not empty
    assume(len(document.strip()) > 10)

    return document


@st.composite
def chunk_config(draw):
    """Generate valid chunk configurations."""
    max_size = draw(integers(min_value=500, max_value=8192))
    min_size = draw(integers(min_value=100, max_value=max_size // 2))
    overlap = draw(integers(min_value=0, max_value=min(200, max_size // 4)))

    return ChunkConfig(
        max_chunk_size=max_size,
        min_chunk_size=min_size,
        overlap_size=overlap,
        validate_invariants=True,
        strict_mode=False,  # Use non-strict mode for property tests
    )


class TestHierarchicalInvariants:
    """Test hierarchical tree invariants using property-based testing."""

    @given(markdown_document(), chunk_config())
    @settings(max_examples=50, deadline=5000)  # Limit examples for performance
    def test_is_leaf_consistency_property(self, document, config):
        """
        Property 1: is_leaf Consistency

        For any hierarchical chunking result, all chunks must have is_leaf
        that equals (children_ids is empty).

        **Validates: Requirements 1.1, 1.2**
        """
        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        for chunk in result.chunks:
            children_ids = chunk.metadata.get("children_ids", [])
            is_leaf = chunk.metadata.get("is_leaf", True)

            # Core invariant: is_leaf must equal (children_ids is empty)
            expected_is_leaf = len(children_ids) == 0
            assert is_leaf == expected_is_leaf, (
                f"Chunk {chunk.metadata.get('chunk_id')} has is_leaf={is_leaf} "
                f"but children_ids has {len(children_ids)} elements. "
                f"Expected is_leaf={expected_is_leaf}"
            )

    @given(markdown_document(), chunk_config())
    @settings(max_examples=50, deadline=5000)
    def test_parent_child_bidirectionality_property(self, document, config):
        """
        Property 2: Parent-Child Bidirectionality

        For any hierarchical chunking result, parent-child relationships
        must be bidirectional and consistent.

        **Validates: Requirements 1.3**
        """
        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        # Build lookup map
        chunk_map = {c.metadata["chunk_id"]: c for c in result.chunks}

        for chunk in result.chunks:
            chunk_id = chunk.metadata["chunk_id"]

            # Test parent -> child direction
            parent_id = chunk.metadata.get("parent_id")
            if parent_id:
                parent_chunk = chunk_map.get(parent_id)
                assert parent_chunk is not None, (
                    f"Chunk {chunk_id} references non-existent parent {parent_id}"
                )

                parent_children = parent_chunk.metadata.get("children_ids", [])
                assert chunk_id in parent_children, (
                    f"Chunk {chunk_id} has parent_id={parent_id} but parent's children_ids "
                    f"{parent_children} does not include {chunk_id}"
                )

            # Test child -> parent direction
            children_ids = chunk.metadata.get("children_ids", [])
            for child_id in children_ids:
                child_chunk = chunk_map.get(child_id)
                assert child_chunk is not None, (
                    f"Chunk {chunk_id} references non-existent child {child_id}"
                )

                child_parent_id = child_chunk.metadata.get("parent_id")
                assert child_parent_id == chunk_id, (
                    f"Chunk {chunk_id} has child {child_id} but child's parent_id is {child_parent_id}"
                )

    @given(markdown_document(), chunk_config())
    @settings(max_examples=30, deadline=5000)
    def test_content_range_consistency_property(self, document, config):
        """
        Property 3: Content Range Consistency

        For any hierarchical chunking result with root chunk, the root chunk
        content should be consistent with its start_line and end_line range.

        **Validates: Requirements 1.4**
        """
        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        # Find root chunk
        root_chunk = result.get_chunk(result.root_id)
        if root_chunk and root_chunk.metadata.get("is_root"):
            # Root should start at line 1
            assert root_chunk.start_line == 1, (
                f"Root chunk should start at line 1, got {root_chunk.start_line}"
            )

            # Root should span most of the document
            non_root_chunks = [c for c in result.chunks if not c.metadata.get("is_root")]
            if non_root_chunks:
                max_end_line = max(c.end_line for c in non_root_chunks)
                # Allow some tolerance for summary content
                assert root_chunk.end_line >= max_end_line * 0.8, (
                    f"Root chunk end_line {root_chunk.end_line} should be close to "
                    f"document end {max_end_line}"
                )

    @given(markdown_document(), chunk_config())
    @settings(max_examples=30, deadline=5000)
    def test_no_orphaned_chunks_property(self, document, config):
        """
        Property 4: No Orphaned Chunks

        For any hierarchical chunking result, all chunks should be properly
        connected in the tree (no orphaned chunks except root).

        **Validates: Requirements 1.3, 1.5**
        """
        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        # Build lookup map
        chunk_map = {c.metadata["chunk_id"]: c for c in result.chunks}

        for chunk in result.chunks:
            chunk_id = chunk.metadata["chunk_id"]
            is_root = chunk.metadata.get("is_root", False)
            parent_id = chunk.metadata.get("parent_id")

            if is_root:
                # Root should have no parent
                assert parent_id is None, f"Root chunk {chunk_id} should not have parent_id"
            else:
                # Non-root chunks must have a parent
                assert parent_id is not None, f"Non-root chunk {chunk_id} must have parent_id"
                assert parent_id in chunk_map, (
                    f"Chunk {chunk_id} references non-existent parent {parent_id}"
                )

    def test_strict_mode_raises_exceptions(self):
        """Test that strict mode raises exceptions for invariant violations."""
        # Create a document that will likely create hierarchy
        document = """
# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection 1.1.

# Section 2

Content for section 2.
"""

        config = ChunkConfig(
            max_chunk_size=1000, min_chunk_size=100, validate_invariants=True, strict_mode=True
        )

        chunker = MarkdownChunker(config)

        # This should work normally
        result = chunker.chunk_hierarchical(document)
        assert len(result.chunks) > 0

        # Manually corrupt a chunk to test strict mode
        if result.chunks:
            # Corrupt is_leaf to create invariant violation
            chunk = result.chunks[0]
            original_is_leaf = chunk.metadata.get("is_leaf")
            chunk.metadata["is_leaf"] = not original_is_leaf

            # Create new hierarchy builder in strict mode
            from chunkana.hierarchy import HierarchyBuilder

            strict_builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)

            # This should raise an exception
            with pytest.raises(HierarchicalInvariantError) as exc_info:
                strict_builder._validate_tree_invariants(result.chunks)

            assert "is_leaf_consistency" in str(exc_info.value)

    def test_non_strict_mode_auto_fixes(self):
        """Test that non-strict mode auto-fixes invariant violations."""
        document = """
# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection 1.1.
"""

        config = ChunkConfig(
            max_chunk_size=1000, min_chunk_size=100, validate_invariants=True, strict_mode=False
        )

        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        # Manually corrupt a chunk to test auto-fix
        if result.chunks:
            chunk = result.chunks[0]
            children_ids = chunk.metadata.get("children_ids", [])

            # Corrupt is_leaf to create invariant violation
            chunk.metadata["is_leaf"] = len(children_ids) > 0  # Opposite of correct value

            # Create new hierarchy builder in non-strict mode
            from chunkana.hierarchy import HierarchyBuilder

            non_strict_builder = HierarchyBuilder(validate_invariants=True, strict_mode=False)

            # This should auto-fix without raising exception
            non_strict_builder._validate_tree_invariants(result.chunks)

            # Verify the fix
            expected_is_leaf = len(children_ids) == 0
            assert chunk.metadata["is_leaf"] == expected_is_leaf
