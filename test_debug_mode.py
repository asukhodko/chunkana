#!/usr/bin/env python3
"""
Test script for debug mode behavior.

Note: The current ChunkConfig doesn't have a 'debug' parameter.
These tests verify metadata consistency and hierarchical behavior.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chunkana import ChunkConfig, MarkdownChunker


def test_basic_metadata():
    """Test that basic metadata is present."""
    print("Testing basic metadata...")

    document = """
# Section 1

Content for section 1.

## Subsection 1.1

More content here.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Check that basic metadata is present
    for chunk in chunks:
        if "content_type" not in chunk.metadata:
            print("✗ Missing content_type")
            return False
        if "chunk_index" not in chunk.metadata:
            print("✗ Missing chunk_index")
            return False

    print("✓ Basic metadata present")
    return True


def test_hierarchical_metadata():
    """Test that hierarchical metadata is present."""
    print("\nTesting hierarchical metadata...")

    document = """
# Section 1

Content for section 1.

## Subsection 1.1

More content here.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} chunks")

    # Check that hierarchical metadata IS present
    for chunk in result.chunks:
        if "chunk_id" not in chunk.metadata:
            print("✗ Missing chunk_id in hierarchical mode")
            return False

    print("✓ Hierarchical metadata present")
    return True


def test_hierarchical_navigation():
    """Test hierarchical navigation methods."""
    print("\nTesting hierarchical navigation...")

    document = """
# Document Title

Introduction.

## Section 1

Content 1.

## Section 2

Content 2.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} hierarchical chunks")

    # Navigation should work
    root = result.get_chunk(result.root_id)
    if not root:
        print("✗ Could not get root chunk")
        return False

    children = result.get_children(result.root_id)
    print(f"✓ Root has {len(children)} children")

    # get_flat_chunks should work
    flat = result.get_flat_chunks()
    print(f"✓ get_flat_chunks returned {len(flat)} chunks")

    print("✓ Hierarchical navigation works")
    return True


def test_hierarchical_relationships():
    """Test hierarchical parent-child relationships."""
    print("\nTesting hierarchical relationships...")

    document = """
# Document Title

Introduction.

## Section 1

Content 1.

## Section 2

Content 2.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} hierarchical chunks")

    # Check for hierarchical metadata
    for chunk in result.chunks:
        if "chunk_id" not in chunk.metadata:
            print("✗ Missing chunk_id in hierarchical mode")
            return False

    # Navigation should work
    root = result.get_chunk(result.root_id)
    if not root:
        print("✗ Could not get root chunk")
        return False

    if not root.metadata.get("is_root"):
        print("✗ Root chunk missing is_root flag")
        return False

    children = result.get_children(result.root_id)
    print(f"✓ Root has {len(children)} children")

    # Check parent-child relationships
    for child in children:
        if child.metadata.get("parent_id") != result.root_id:
            print("✗ Child has incorrect parent_id")
            return False

    print("✓ Hierarchical relationships correct")
    return True


def test_get_flat_chunks_consistency():
    """Test that get_flat_chunks returns consistent results."""
    print("\nTesting get_flat_chunks consistency...")

    document = """
# Main Title

Introduction paragraph with some content.

## Section 1

Section 1 content here.

### Subsection 1.1

Subsection content.

## Section 2

Section 2 content.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)
    flat = result.get_flat_chunks()

    print(f"✓ get_flat_chunks returned {len(flat)} chunks")

    # All flat chunks should be leaves or have significant content
    for chunk in flat:
        is_root = chunk.metadata.get("is_root", False)

        if is_root:
            print("✗ Root chunk should not be in flat chunks")
            return False

    print("✓ Flat chunks are consistent")
    return True


def test_metadata_fields_documented():
    """Test that documented metadata fields are present."""
    print("\nTesting documented metadata fields...")

    document = """
# Test Document

Some content here.

## Section

More content.
"""

    config = ChunkConfig(max_chunk_size=500, min_chunk_size=50, validate_invariants=True)

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    # Check root chunk has documented fields
    root = result.get_chunk(result.root_id)

    documented_fields = [
        "chunk_id",
        "content_type",
        "header_path",
        "header_level",
        "parent_id",
        "children_ids",
        "is_leaf",
        "is_root",
        "hierarchy_level",
    ]

    missing = []
    for field in documented_fields:
        if field not in root.metadata:
            missing.append(field)

    if missing:
        print(f"✗ Missing documented fields in root: {missing}")
        return False

    print("✓ All documented metadata fields present")
    return True


def test_invariant_validation():
    """Test that invariant validation works correctly."""
    print("\nTesting invariant validation...")

    document = """
# Document

Content here.

## Section 1

Section content.

## Section 2

More content.
"""

    # Test with validation enabled
    config = ChunkConfig(
        max_chunk_size=500, min_chunk_size=50, validate_invariants=True, strict_mode=False
    )

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} chunks with validation")

    # Verify is_leaf consistency
    for chunk in result.chunks:
        children_ids = chunk.metadata.get("children_ids", [])
        is_leaf = chunk.metadata.get("is_leaf", True)
        expected_is_leaf = len(children_ids) == 0

        if is_leaf != expected_is_leaf:
            print(f"✗ is_leaf inconsistency in chunk {chunk.metadata.get('chunk_id')}")
            return False

    print("✓ All invariants satisfied")
    return True


def main():
    """Run all debug mode tests."""
    print("Running metadata and hierarchical behavior tests...\n")

    success = True

    try:
        success &= test_basic_metadata()
        success &= test_hierarchical_metadata()
        success &= test_hierarchical_navigation()
        success &= test_hierarchical_relationships()
        success &= test_get_flat_chunks_consistency()
        success &= test_metadata_fields_documented()
        success &= test_invariant_validation()

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
