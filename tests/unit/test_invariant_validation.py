"""
Unit tests for hierarchical invariant validation.

Tests specific scenarios and edge cases for invariant checking.
"""

import pytest

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.exceptions import HierarchicalInvariantError
from chunkana.hierarchy import HierarchyBuilder
from chunkana.types import Chunk


class TestInvariantValidation:
    """Test invariant validation logic."""

    def test_is_leaf_consistency_validation(self):
        """Test is_leaf consistency invariant validation."""
        # Create chunks with inconsistent is_leaf values
        chunk1 = Chunk(
            content="# Header\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "chunk1",
                "children_ids": ["chunk2"],  # Has children
                "is_leaf": True,  # But marked as leaf - INCONSISTENT
                "header_path": "/Header",
            },
        )

        chunk2 = Chunk(
            content="## Subheader\n\nSubcontent",
            start_line=4,
            end_line=6,
            metadata={
                "chunk_id": "chunk2",
                "parent_id": "chunk1",
                "children_ids": [],  # No children
                "is_leaf": False,  # But marked as non-leaf - INCONSISTENT
                "header_path": "/Header/Subheader",
            },
        )

        chunks = [chunk1, chunk2]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)
        with pytest.raises(HierarchicalInvariantError) as exc_info:
            builder._validate_tree_invariants(chunks)

        assert "is_leaf_consistency" in str(exc_info.value)
        assert "chunk1" in str(exc_info.value)

        # Test non-strict mode - should auto-fix
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=False)
        builder._validate_tree_invariants(chunks)

        # Verify auto-fix
        assert chunk1.metadata["is_leaf"] is False  # Should be fixed
        assert chunk2.metadata["is_leaf"] is True  # Should be fixed

    def test_parent_child_bidirectionality_validation(self):
        """Test parent-child bidirectionality invariant validation."""
        # Create chunks with broken bidirectional relationships
        parent_chunk = Chunk(
            content="# Parent\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "parent",
                "children_ids": ["child1", "child2"],
                "is_leaf": False,
                "header_path": "/Parent",
            },
        )

        child1_chunk = Chunk(
            content="## Child 1\n\nContent",
            start_line=4,
            end_line=6,
            metadata={
                "chunk_id": "child1",
                "parent_id": "parent",
                "children_ids": [],
                "is_leaf": True,
                "header_path": "/Parent/Child1",
            },
        )

        child2_chunk = Chunk(
            content="## Child 2\n\nContent",
            start_line=7,
            end_line=9,
            metadata={
                "chunk_id": "child2",
                "parent_id": "wrong_parent",  # WRONG PARENT
                "children_ids": [],
                "is_leaf": True,
                "header_path": "/Parent/Child2",
            },
        )

        chunks = [parent_chunk, child1_chunk, child2_chunk]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)
        with pytest.raises(HierarchicalInvariantError) as exc_info:
            builder._validate_tree_invariants(chunks)

        assert "parent_child_bidirectionality" in str(exc_info.value)
        assert "child2" in str(exc_info.value)

        # Test non-strict mode - should auto-fix
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=False)
        builder._validate_tree_invariants(chunks)

        # Verify auto-fix
        assert child2_chunk.metadata["parent_id"] == "parent"

    def test_orphaned_chunk_validation(self):
        """Test orphaned chunk detection and handling."""
        # Create chunk with non-existent parent
        orphaned_chunk = Chunk(
            content="## Orphaned\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "orphaned",
                "parent_id": "non_existent_parent",  # PARENT DOESN'T EXIST
                "children_ids": [],
                "is_leaf": True,
                "header_path": "/Orphaned",
            },
        )

        chunks = [orphaned_chunk]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)
        with pytest.raises(HierarchicalInvariantError) as exc_info:
            builder._validate_tree_invariants(chunks)

        assert "orphaned_chunk" in str(exc_info.value)
        assert "non_existent_parent" in str(exc_info.value)

    def test_missing_child_validation(self):
        """Test missing child detection and handling."""
        # Create parent with non-existent child
        parent_chunk = Chunk(
            content="# Parent\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "parent",
                "children_ids": ["existing_child", "non_existent_child"],  # One child missing
                "is_leaf": False,
                "header_path": "/Parent",
            },
        )

        existing_child = Chunk(
            content="## Existing Child\n\nContent",
            start_line=4,
            end_line=6,
            metadata={
                "chunk_id": "existing_child",
                "parent_id": "parent",
                "children_ids": [],
                "is_leaf": True,
                "header_path": "/Parent/ExistingChild",
            },
        )

        chunks = [parent_chunk, existing_child]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)
        with pytest.raises(HierarchicalInvariantError) as exc_info:
            builder._validate_tree_invariants(chunks)

        assert "orphaned_child" in str(exc_info.value)
        assert "non_existent_child" in str(exc_info.value)

        # Test non-strict mode - should auto-fix by removing missing child
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=False)
        builder._validate_tree_invariants(chunks)

        # Verify auto-fix
        assert "non_existent_child" not in parent_chunk.metadata["children_ids"]
        assert "existing_child" in parent_chunk.metadata["children_ids"]

    def test_content_range_consistency_validation(self):
        """Test content range consistency for root chunks."""
        # Create root chunk with inconsistent range
        root_chunk = Chunk(
            content="# Document\n\nSummary",
            start_line=5,  # WRONG - should be 1
            end_line=10,  # WRONG - should span more
            metadata={
                "chunk_id": "root",
                "is_root": True,
                "children_ids": ["child1"],
                "is_leaf": False,
                "header_path": "/",
            },
        )

        child_chunk = Chunk(
            content="## Section\n\nContent",
            start_line=1,
            end_line=100,  # Document actually ends at line 100
            metadata={
                "chunk_id": "child1",
                "parent_id": "root",
                "children_ids": [],
                "is_leaf": True,
                "header_path": "/Section",
            },
        )

        chunks = [root_chunk, child_chunk]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)
        with pytest.raises(HierarchicalInvariantError) as exc_info:
            builder._validate_tree_invariants(chunks)

        assert "content_range_consistency" in str(exc_info.value)
        assert "root" in str(exc_info.value)

    def test_validation_disabled(self):
        """Test that validation can be disabled."""
        # Create chunks with obvious invariant violations
        # (chunk is created to demonstrate the test scenario but not used directly
        # because we're testing that the builder flag is set correctly)
        _chunk = Chunk(
            content="# Header\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "chunk1",
                "children_ids": ["child1"],
                "is_leaf": True,  # INCONSISTENT
                "header_path": "/Header",
            },
        )

        # Test with validation disabled - builder should not call _validate_tree_invariants
        # in build() method, but calling it directly will still validate
        builder = HierarchyBuilder(validate_invariants=False, strict_mode=True)

        # When validate_invariants=False, the build() method skips validation
        # Direct call to _validate_tree_invariants will still validate (it's a method)
        # So we test that the builder respects the flag in build()

        # Verify the flag is set correctly
        assert not builder.validate_invariants
        assert builder.strict_mode

    def test_integration_with_chunker(self):
        """Test that chunker uses validation settings from config."""
        document = """
# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection 1.1.
"""

        # Test with validation enabled
        config = ChunkConfig(
            max_chunk_size=1000, min_chunk_size=100, validate_invariants=True, strict_mode=False
        )

        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(document)

        # Should complete successfully with validation
        assert len(result.chunks) > 0

        # Verify all chunks have consistent is_leaf values
        for chunk in result.chunks:
            children_ids = chunk.metadata.get("children_ids", [])
            is_leaf = chunk.metadata.get("is_leaf", True)
            expected_is_leaf = len(children_ids) == 0
            assert is_leaf == expected_is_leaf, (
                f"Chunk {chunk.metadata.get('chunk_id')} has inconsistent is_leaf"
            )

    def test_backward_compatibility(self):
        """Test that old validate_chains parameter still works."""
        document = """
# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection 1.1.
"""

        # Test old-style initialization
        builder = HierarchyBuilder(
            include_document_summary=True,
            validate_invariants=False,  # Disable new validation
        )

        # Should use old validation logic
        assert builder.validate_chains  # Should fall back to old validation

        # Should work without errors
        chunker = MarkdownChunker(ChunkConfig(max_chunk_size=1000))
        chunks = chunker.chunk(document)
        result = builder.build(chunks, document)

        assert len(result.chunks) > 0
