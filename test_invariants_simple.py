#!/usr/bin/env python3
"""
Simple test script to verify invariant validation works.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.exceptions import HierarchicalInvariantError


def test_basic_functionality():
    """Test basic functionality works."""
    print("Testing basic functionality...")

    document = """
# Section 1

Content for section 1.

## Subsection 1.1

Content for subsection 1.1.

# Section 2

Content for section 2.
"""

    config = ChunkConfig(
        max_chunk_size=1000, min_chunk_size=100, validate_invariants=True, strict_mode=False
    )

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} chunks")

    # Verify all chunks have consistent is_leaf values
    for chunk in result.chunks:
        children_ids = chunk.metadata.get("children_ids", [])
        is_leaf = chunk.metadata.get("is_leaf", True)
        expected_is_leaf = len(children_ids) == 0

        if is_leaf != expected_is_leaf:
            print(f"✗ Chunk {chunk.metadata.get('chunk_id')} has inconsistent is_leaf")
            return False

    print("✓ All chunks have consistent is_leaf values")
    return True


def test_strict_mode():
    """Test strict mode validation."""
    print("\nTesting strict mode...")

    try:
        from chunkana.hierarchy import HierarchyBuilder
        from chunkana.types import Chunk

        # Create chunk with inconsistent is_leaf
        chunk = Chunk(
            content="# Header\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "test_chunk",
                "children_ids": ["child1"],  # Has children
                "is_leaf": True,  # But marked as leaf - INCONSISTENT
                "header_path": "/Header",
            },
        )

        chunks = [chunk]

        # Test strict mode - should raise exception
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)

        try:
            builder._validate_tree_invariants(chunks)
            print("✗ Strict mode should have raised exception")
            return False
        except HierarchicalInvariantError as e:
            print(f"✓ Strict mode correctly raised exception: {e}")
            return True

    except Exception as e:
        print(f"✗ Error in strict mode test: {e}")
        return False


def main():
    """Run all tests."""
    print("Running invariant validation tests...\n")

    success = True

    try:
        success &= test_basic_functionality()
        success &= test_strict_mode()

        if success:
            print("\n✓ All tests passed!")
            return 0
        else:
            print("\n✗ Some tests failed!")
            return 1

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
