#!/usr/bin/env python3
"""
Test script for dangling header prevention.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from chunkana import ChunkConfig, MarkdownChunker
from chunkana.header_processor import DanglingHeaderDetector, HeaderProcessor
from chunkana.types import Chunk


def test_dangling_header_detection():
    """Test detection of dangling headers."""
    print("Testing dangling header detection...")

    detector = DanglingHeaderDetector()

    # Create chunks with dangling header
    chunk1 = Chunk(
        content="# Section 1\n\nSome content here.\n\n#### Subsection Details",
        start_line=1,
        end_line=5,
        metadata={"chunk_id": "chunk1"},
    )

    chunk2 = Chunk(
        content="This is the detailed content for the subsection.\nIt has multiple lines of information.",
        start_line=6,
        end_line=8,
        metadata={"chunk_id": "chunk2"},
    )

    chunks = [chunk1, chunk2]
    dangling_indices = detector.detect_dangling_headers(chunks)

    if len(dangling_indices) == 1 and dangling_indices[0] == 0:
        print("✓ Correctly detected dangling header in chunk1")
        return True
    else:
        print(f"✗ Expected dangling header in chunk1, got indices: {dangling_indices}")
        return False


def test_no_false_positives():
    """Test that normal headers are not flagged as dangling."""
    print("Testing no false positives...")

    detector = DanglingHeaderDetector()

    # Create chunks without dangling headers
    chunk1 = Chunk(
        content="# Section 1\n\nThis section has substantial content.\nMultiple paragraphs of text.\n\nMore content here.",
        start_line=1,
        end_line=6,
        metadata={"chunk_id": "chunk1"},
    )

    chunk2 = Chunk(
        content="# Section 2\n\nThis is a new section with its own content.",
        start_line=7,
        end_line=9,
        metadata={"chunk_id": "chunk2"},
    )

    chunks = [chunk1, chunk2]
    dangling_indices = detector.detect_dangling_headers(chunks)

    if len(dangling_indices) == 0:
        print("✓ No false positives detected")
        return True
    else:
        print(f"✗ False positives detected: {dangling_indices}")
        return False


def test_header_moving():
    """Test moving headers to fix dangling situations."""
    print("Testing header moving...")

    config = ChunkConfig(max_chunk_size=1000, min_chunk_size=100)
    processor = HeaderProcessor(config)

    # Create chunks with dangling header
    chunk1 = Chunk(
        content="# Section 1\n\nSome content.\n\n#### Details",
        start_line=1,
        end_line=5,
        metadata={"chunk_id": "chunk1"},
    )

    chunk2 = Chunk(
        content="Content for the details section.",
        start_line=6,
        end_line=7,
        metadata={"chunk_id": "chunk2"},
    )

    chunks = [chunk1, chunk2]
    fixed_chunks = processor.prevent_dangling_headers(chunks)

    # Check that header was moved
    if len(fixed_chunks) == 2:
        # Header should be moved to chunk2
        if (
            "#### Details" in fixed_chunks[1].content
            and "#### Details" not in fixed_chunks[0].content
        ):
            print("✓ Header successfully moved to next chunk")

            # Check metadata
            if fixed_chunks[1].metadata.get("dangling_header_fixed"):
                print("✓ Metadata correctly updated")
                return True
            else:
                print("✗ Metadata not updated")
                return False
        else:
            print("✗ Header not moved correctly")
            print(f"Chunk 0: {fixed_chunks[0].content}")
            print(f"Chunk 1: {fixed_chunks[1].content}")
            return False
    else:
        print(f"✗ Expected 2 chunks, got {len(fixed_chunks)}")
        return False


def test_chunk_merging():
    """Test merging chunks when header moving would exceed size limits."""
    print("Testing chunk merging for large chunks...")

    # Use small max_chunk_size to force merging
    config = ChunkConfig(max_chunk_size=200, min_chunk_size=50, overlap_size=50)
    processor = HeaderProcessor(config)

    # Create chunks where moving header would exceed size limit
    chunk1 = Chunk(
        content="# Section 1\n\nSome content here.\n\n#### Long Header Name That Takes Space",
        start_line=1,
        end_line=5,
        metadata={"chunk_id": "chunk1"},
    )

    chunk2 = Chunk(
        content="This is a very long content section that would exceed the size limit if we added the header to it. "
        + "It has lots of text to make it large.",
        start_line=6,
        end_line=8,
        metadata={"chunk_id": "chunk2"},
    )

    chunks = [chunk1, chunk2]
    fixed_chunks = processor.prevent_dangling_headers(chunks)

    # Should merge into single chunk if total size allows
    total_size = len(chunk1.content) + len(chunk2.content) + 4  # +4 for \n\n separator

    if total_size <= config.max_chunk_size:
        if len(fixed_chunks) == 1:
            print("✓ Chunks successfully merged")

            # Check metadata
            if fixed_chunks[0].metadata.get("dangling_header_fixed"):
                print("✓ Merge metadata correctly set")
                return True
            else:
                print("✗ Merge metadata not set")
                return False
        else:
            print(f"✗ Expected 1 merged chunk, got {len(fixed_chunks)}")
            return False
    else:
        # If total size exceeds limit, should leave unchanged with warning
        if len(fixed_chunks) == 2:
            print("✓ Chunks left unchanged due to size constraints")
            return True
        else:
            print(f"✗ Unexpected result: {len(fixed_chunks)} chunks")
            return False


def test_integration_with_chunker():
    """Test integration with MarkdownChunker."""
    print("Testing integration with MarkdownChunker...")

    document = """
# Introduction

This is the introduction section with some content.

## Background

Some background information here.

#### Important Note

This note should stay with its content.

The content for the important note goes here.
It has multiple lines.

## Conclusion

Final thoughts.
"""

    config = ChunkConfig(
        max_chunk_size=300,  # Small size to create potential dangling headers
        min_chunk_size=50,
        validate_invariants=True,
        strict_mode=False,
    )

    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(document)

    print(f"✓ Created {len(chunks)} chunks")

    # Check for dangling headers
    has_dangling = False
    for i in range(len(chunks) - 1):
        current_content = chunks[i].content.strip()
        if current_content.endswith("#### Important Note"):
            next_content = chunks[i + 1].content.strip()
            if "The content for the important note" in next_content:
                has_dangling = True
                break

    if not has_dangling:
        print("✓ No dangling headers found")
        return True
    else:
        print("✗ Dangling header detected")
        return False


def main():
    """Run all dangling header tests."""
    print("Running dangling header prevention tests...\n")

    success = True

    try:
        success &= test_dangling_header_detection()
        success &= test_no_false_positives()
        success &= test_header_moving()
        success &= test_chunk_merging()
        success &= test_integration_with_chunker()

        if success:
            print("\n✓ All dangling header tests passed!")
            return 0
        else:
            print("\n✗ Some dangling header tests failed!")
            return 1

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
