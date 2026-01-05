#!/usr/bin/env python3
"""
Comprehensive test for all hierarchical invariants.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.exceptions import HierarchicalInvariantError


def test_complex_document():
    """Test with a complex document that creates deep hierarchy."""
    print("Testing complex document with deep hierarchy...")

    document = """
# Introduction

This is the introduction to our document.

## Overview

This section provides an overview.

### Key Points

- Point 1
- Point 2
- Point 3

## Background

Some background information here.

# Main Content

This is the main content section.

## Section A

Content for section A.

### Subsection A.1

Content for subsection A.1.

#### Details A.1.1

Detailed information.

### Subsection A.2

Content for subsection A.2.

## Section B

Content for section B.

# Conclusion

Final thoughts and conclusions.
"""

    config = ChunkConfig(
        max_chunk_size=800, min_chunk_size=100, validate_invariants=True, strict_mode=False
    )

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} chunks")

    # Test all invariants
    errors = []

    # Build lookup map
    chunk_map = {c.metadata["chunk_id"]: c for c in result.chunks}

    for chunk in result.chunks:
        chunk_id = chunk.metadata["chunk_id"]

        # Invariant 1: is_leaf consistency
        children_ids = chunk.metadata.get("children_ids", [])
        is_leaf = chunk.metadata.get("is_leaf", True)
        expected_is_leaf = len(children_ids) == 0

        if is_leaf != expected_is_leaf:
            errors.append(
                f"Chunk {chunk_id}: is_leaf={is_leaf}, children_count={len(children_ids)}"
            )

        # Invariant 2: Parent-child bidirectionality
        parent_id = chunk.metadata.get("parent_id")
        if parent_id:
            parent_chunk = chunk_map.get(parent_id)
            if not parent_chunk:
                errors.append(f"Chunk {chunk_id}: references non-existent parent {parent_id}")
            else:
                parent_children = parent_chunk.metadata.get("children_ids", [])
                if chunk_id not in parent_children:
                    errors.append(f"Chunk {chunk_id}: not in parent's children_ids")

        # Check children exist and point back
        for child_id in children_ids:
            child_chunk = chunk_map.get(child_id)
            if not child_chunk:
                errors.append(f"Chunk {chunk_id}: references non-existent child {child_id}")
            else:
                child_parent_id = child_chunk.metadata.get("parent_id")
                if child_parent_id != chunk_id:
                    errors.append(
                        f"Child {child_id}: parent_id={child_parent_id}, expected {chunk_id}"
                    )

    if errors:
        print("✗ Invariant violations found:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ All invariants satisfied")
        return True


def test_navigation_methods():
    """Test navigation methods work correctly."""
    print("\nTesting navigation methods...")

    document = """
# Section 1

Content 1.

## Subsection 1.1

Content 1.1.

## Subsection 1.2

Content 1.2.

# Section 2

Content 2.
"""

    config = ChunkConfig(
        max_chunk_size=500, min_chunk_size=50, validate_invariants=True, strict_mode=False
    )

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    # Test navigation
    root_chunk = result.get_chunk(result.root_id)
    if not root_chunk:
        print("✗ Root chunk not found")
        return False

    print(f"✓ Root chunk found: {root_chunk.metadata.get('chunk_id')}")

    # Test get_children
    children = result.get_children(result.root_id)
    print(f"✓ Root has {len(children)} children")

    # Test get_parent for children
    for child in children:
        parent = result.get_parent(child.metadata["chunk_id"])
        if not parent or parent.metadata["chunk_id"] != result.root_id:
            print(f"✗ Child {child.metadata['chunk_id']} has wrong parent")
            return False

    print("✓ All children have correct parent")

    # Test get_flat_chunks
    flat_chunks = result.get_flat_chunks()
    print(f"✓ get_flat_chunks returned {len(flat_chunks)} leaf chunks")

    # Verify all flat chunks are leaves
    for chunk in flat_chunks:
        if not chunk.metadata.get("is_leaf", True):
            print(f"✗ Non-leaf chunk in flat results: {chunk.metadata['chunk_id']}")
            return False

    print("✓ All flat chunks are leaves")
    return True


def test_error_handling():
    """Test error handling in strict mode."""
    print("\nTesting error handling...")

    try:
        from chunkana.hierarchy import HierarchyBuilder
        from chunkana.types import Chunk

        # Create chunks with multiple invariant violations
        parent_chunk = Chunk(
            content="# Parent\n\nContent",
            start_line=1,
            end_line=3,
            metadata={
                "chunk_id": "parent",
                "children_ids": ["child1", "missing_child"],  # One child missing
                "is_leaf": True,  # WRONG - has children
                "header_path": "/Parent",
            },
        )

        child_chunk = Chunk(
            content="## Child\n\nContent",
            start_line=4,
            end_line=6,
            metadata={
                "chunk_id": "child1",
                "parent_id": "wrong_parent",  # WRONG PARENT
                "children_ids": [],
                "is_leaf": False,  # WRONG - no children
                "header_path": "/Parent/Child",
            },
        )

        chunks = [parent_chunk, child_chunk]

        # Test strict mode
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=True)

        try:
            builder._validate_tree_invariants(chunks)
            print("✗ Strict mode should have raised exception")
            return False
        except HierarchicalInvariantError as e:
            print(f"✓ Strict mode correctly raised: {e.invariant}")

        # Test non-strict mode auto-fix
        builder = HierarchyBuilder(validate_invariants=True, strict_mode=False)
        builder._validate_tree_invariants(chunks)

        # Verify fixes
        if parent_chunk.metadata["is_leaf"] is not False:
            print("✗ Parent is_leaf not fixed")
            return False

        if child_chunk.metadata["is_leaf"] is not True:
            print("✗ Child is_leaf not fixed")
            return False

        if child_chunk.metadata["parent_id"] != "parent":
            print("✗ Child parent_id not fixed")
            return False

        print("✓ Non-strict mode auto-fixed violations")
        return True

    except Exception as e:
        print(f"✗ Error in error handling test: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all comprehensive tests."""
    print("Running comprehensive hierarchical invariant tests...\n")

    success = True

    try:
        success &= test_complex_document()
        success &= test_navigation_methods()
        success &= test_error_handling()

        if success:
            print("\n✓ All comprehensive tests passed!")
            return 0
        else:
            print("\n✗ Some comprehensive tests failed!")
            return 1

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
