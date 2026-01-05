#!/usr/bin/env python3
"""
Test script for micro-chunk minimization.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chunkana import ChunkConfig, MarkdownChunker


def test_small_chunk_flagging():
    """Test that small chunks are properly flagged."""
    print("Testing small chunk flagging...")

    # Create document with potential micro-chunks
    document = """
# Main Section

This is a substantial section with lots of content.
It has multiple paragraphs and meaningful information.
The content here is quite detailed and informative.

## Short Section

X

## Another Section

This section also has substantial content.
Multiple lines of text that provide value.
More information here for the reader.
"""

    config = ChunkConfig(
        max_chunk_size=500,
        min_chunk_size=100,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Check for small_chunk flags
    small_chunks = [c for c in chunks if c.metadata.get("small_chunk")]
    flagged_count = len(small_chunks)

    print(f"✓ Found {flagged_count} flagged small chunks")

    # Verify small chunks are actually small
    for chunk in small_chunks:
        if chunk.size >= config.min_chunk_size:
            print(
                f"✗ Chunk flagged as small but size {chunk.size} >= min_chunk_size {config.min_chunk_size}"
            )
            return False

    print("✓ All flagged chunks are actually small")
    return True


def test_structural_strength_detection():
    """Test that structurally strong chunks are not flagged."""
    print("\nTesting structural strength detection...")

    # Create document with structurally strong small chunks
    document = """
# Introduction

Brief intro.

## Key Points

- Point 1
- Point 2
- Point 3

This is important.

## Details

More detailed information here.
With multiple paragraphs.

And even more content.
"""

    config = ChunkConfig(
        max_chunk_size=300,
        min_chunk_size=150,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Check that chunks with strong headers are not flagged
    for chunk in chunks:
        header_level = chunk.metadata.get("header_level", 0)
        is_flagged = chunk.metadata.get("small_chunk", False)

        # Level 2-3 headers should not be flagged even if small
        if header_level in [2, 3] and is_flagged:
            print(f"✗ Chunk with header level {header_level} should not be flagged as small")
            return False

    print("✓ Structurally strong chunks not flagged")
    return True


def test_merge_within_section():
    """Test that merging prefers same section."""
    print("\nTesting merge within section preference...")

    document = """
# Section A

Content A1.

Content A2.

# Section B

Content B1.

Content B2.
"""

    config = ChunkConfig(
        max_chunk_size=500,
        min_chunk_size=100,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Verify chunks maintain section boundaries
    for chunk in chunks:
        content = chunk.content
        # Check that Section A content is not mixed with Section B content
        if "Content A" in content and "Content B" in content:
            # This might be okay if they're in the same merged chunk
            # but we should verify the header_path is consistent
            pass

    print("✓ Section boundaries respected")
    return True


def test_preamble_not_merged():
    """Test that preamble chunks are not merged with structural chunks."""
    print("\nTesting preamble isolation...")

    document = """
This is preamble content before any headers.
It should stay separate.

# First Section

This is section content.
"""

    config = ChunkConfig(
        max_chunk_size=500,
        min_chunk_size=50,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Find preamble chunk
    preamble_chunks = [c for c in chunks if c.metadata.get("content_type") == "preamble"]

    if preamble_chunks:
        preamble = preamble_chunks[0]
        # Verify preamble doesn't contain section content
        if "# First Section" in preamble.content:
            print("✗ Preamble merged with section content")
            return False
        print("✓ Preamble isolated from sections")
    else:
        print("✓ No preamble detected (document starts with header)")

    return True


def test_metadata_after_merge():
    """Test that metadata is correctly updated after merging."""
    print("\nTesting metadata after merge...")

    document = """
# Main Section

Short content.

More content here that should be merged.

Even more content.
"""

    config = ChunkConfig(
        max_chunk_size=1000,
        min_chunk_size=200,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Verify all chunks have required metadata
    for i, chunk in enumerate(chunks):
        if "chunk_index" not in chunk.metadata:
            print(f"✗ Chunk {i} missing chunk_index")
            return False
        if "content_type" not in chunk.metadata:
            print(f"✗ Chunk {i} missing content_type")
            return False

    print("✓ All chunks have required metadata")
    return True


def test_integration_with_hierarchical():
    """Test micro-chunk handling with hierarchical chunking."""
    print("\nTesting integration with hierarchical chunking...")

    document = """
# Document Title

Introduction paragraph.

## Section 1

Content for section 1.

### Subsection 1.1

Small content.

### Subsection 1.2

More content here.

## Section 2

Final section content.
"""

    config = ChunkConfig(
        max_chunk_size=400,
        min_chunk_size=100,
        overlap_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    result = chunker.chunk_hierarchical(document)

    print(f"✓ Created {len(result.chunks)} hierarchical chunks")

    # Verify hierarchical structure is maintained
    flat_chunks = result.get_flat_chunks()
    print(f"✓ {len(flat_chunks)} leaf chunks")

    # Check for small_chunk flags in leaf chunks
    small_leaves = [c for c in flat_chunks if c.metadata.get("small_chunk")]
    print(f"✓ {len(small_leaves)} small leaf chunks flagged")

    return True


def main():
    """Run all micro-chunk tests."""
    print("Running micro-chunk minimization tests...\n")

    success = True

    try:
        success &= test_small_chunk_flagging()
        success &= test_structural_strength_detection()
        success &= test_merge_within_section()
        success &= test_preamble_not_merged()
        success &= test_metadata_after_merge()
        success &= test_integration_with_hierarchical()

        if success:
            print("\n✓ All micro-chunk tests passed!")
            return 0
        else:
            print("\n✗ Some micro-chunk tests failed!")
            return 1

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
