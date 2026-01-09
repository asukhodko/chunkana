"""
Integration tests for split chunk line numbers.

Tests that split chunks have accurate and different line numbers.
"""

import pytest

from chunkana import ChunkerConfig, chunk_markdown


class TestSplitChunkLineNumbers:
    """Integration tests for split chunk line number accuracy."""

    @pytest.fixture
    def config(self):
        return ChunkerConfig(
            max_chunk_size=500,  # Small size to force splitting
            overlap_size=50,
        )

    def test_split_chunks_have_different_line_numbers(self, config):
        """Test that split chunks have different line numbers."""
        # Document with large list that will be split
        document = """# Test Document

## Large Section

1. First item with some content to make it longer
   Additional details for the first item.

2. Second item with some content to make it longer
   Additional details for the second item.

3. Third item with some content to make it longer
   Additional details for the third item.

4. Fourth item with some content to make it longer
   Additional details for the fourth item.

5. Fifth item with some content to make it longer
   Additional details for the fifth item.

6. Sixth item with some content to make it longer
   Additional details for the sixth item.

7. Seventh item with some content to make it longer
   Additional details for the seventh item.

8. Eighth item with some content to make it longer
   Additional details for the eighth item.
"""

        chunks = chunk_markdown(document, config)

        # Find split chunks (same header_path, different split_index)
        split_groups = {}
        for chunk in chunks:
            header_path = chunk.metadata.get("header_path", "")
            if "split_index" in chunk.metadata:
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

        # Verify split chunks have different line numbers
        for _header_path, split_chunks in split_groups.items():
            if len(split_chunks) > 1:
                # Sort by split_index
                split_chunks.sort(key=lambda c: c.metadata["split_index"])

                for i in range(len(split_chunks) - 1):
                    current = split_chunks[i]
                    next_chunk = split_chunks[i + 1]

                    # Line numbers should be different
                    assert current.start_line != next_chunk.start_line, (
                        f"Split chunks have same start_line: {current.start_line}"
                    )
                    assert current.end_line != next_chunk.end_line, (
                        f"Split chunks have same end_line: {current.end_line}"
                    )

    def test_split_chunks_line_numbers_ordered(self, config):
        """Test that split chunks have ordered line numbers."""
        document = """# Test Document

## Section with Long List

1. Item one with substantial content to ensure splitting occurs
   More content for item one to make it longer.
   Even more content to reach the size threshold.

2. Item two with substantial content to ensure splitting occurs
   More content for item two to make it longer.
   Even more content to reach the size threshold.

3. Item three with substantial content to ensure splitting occurs
   More content for item three to make it longer.
   Even more content to reach the size threshold.

4. Item four with substantial content to ensure splitting occurs
   More content for item four to make it longer.
   Even more content to reach the size threshold.

5. Item five with substantial content to ensure splitting occurs
   More content for item five to make it longer.
   Even more content to reach the size threshold.
"""

        chunks = chunk_markdown(document, config)

        # Find split chunks
        split_chunks = [c for c in chunks if "split_index" in c.metadata]

        if len(split_chunks) > 1:
            # Group by header_path and sort by split_index
            split_groups = {}
            for chunk in split_chunks:
                header_path = chunk.metadata.get("header_path", "")
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

            for _header_path, group in split_groups.items():
                if len(group) > 1:
                    group.sort(key=lambda c: c.metadata["split_index"])

                    # Verify line numbers are monotonic
                    for i in range(len(group) - 1):
                        current = group[i]
                        next_chunk = group[i + 1]

                        assert current.start_line < next_chunk.start_line, (
                            f"Line numbers not ordered: {current.start_line} >= {next_chunk.start_line}"
                        )

    def test_split_chunks_cover_original_range(self, config):
        """Test that split chunks cover the original line range."""
        document = """# Document

## Section That Will Be Split

This is a long section with multiple paragraphs and list items
that should be split into multiple chunks due to size constraints.

1. First list item with detailed content
   Additional information for the first item.
   More details to make it substantial.

2. Second list item with detailed content
   Additional information for the second item.
   More details to make it substantial.

3. Third list item with detailed content
   Additional information for the third item.
   More details to make it substantial.

4. Fourth list item with detailed content
   Additional information for the fourth item.
   More details to make it substantial.

This is the conclusion of the section.
"""

        chunks = chunk_markdown(document, config)

        # Find chunks that were split
        split_groups = {}
        for chunk in chunks:
            if "split_index" in chunk.metadata:
                original_size = chunk.metadata.get("original_section_size", 0)
                header_path = chunk.metadata.get("header_path", "")

                if header_path not in split_groups:
                    split_groups[header_path] = {"chunks": [], "original_size": original_size}
                split_groups[header_path]["chunks"].append(chunk)

        # Verify coverage
        for _header_path, group in split_groups.items():
            if len(group["chunks"]) > 1:
                chunks_in_group = group["chunks"]
                chunks_in_group.sort(key=lambda c: c.metadata["split_index"])

                # First chunk should start at reasonable position
                first_chunk = chunks_in_group[0]
                last_chunk = chunks_in_group[-1]

                # Line ranges should be reasonable
                assert first_chunk.start_line <= last_chunk.start_line
                assert first_chunk.end_line <= last_chunk.end_line

    def test_non_split_chunks_unchanged(self, config):
        """Regression test: non-split chunks keep same line numbers."""
        document = """# Simple Document

## Small Section

This is a small section that won't be split.
It has just enough content to be a single chunk.

## Another Small Section

This is another small section.
Also won't be split due to size.
"""

        chunks = chunk_markdown(document, config)

        # Verify non-split chunks don't have split metadata
        for chunk in chunks:
            if "split_index" not in chunk.metadata:
                # These chunks should have normal line numbers
                assert chunk.start_line >= 0
                assert chunk.end_line >= chunk.start_line
                assert chunk.end_line > 0


class TestRealDocumentSplitting:
    """Tests with real documents that trigger splitting."""

    @pytest.fixture
    def config(self):
        return ChunkerConfig(
            max_chunk_size=800,
            overlap_size=100,
        )

    def test_sde_criteria_document_splitting(self, config):
        """Test splitting with SDE criteria document."""
        # Load the SDE criteria document
        import os

        fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sde_criteria.md")

        if os.path.exists(fixture_path):
            with open(fixture_path, encoding="utf-8") as f:
                document = f.read()

            chunks = chunk_markdown(document, config)

            # Find split chunks
            split_chunks = [c for c in chunks if "split_index" in c.metadata]

            if split_chunks:
                # Verify split chunks have accurate line numbers
                for chunk in split_chunks:
                    assert chunk.start_line >= 0
                    assert chunk.end_line >= chunk.start_line
                    assert "split_index" in chunk.metadata
                    assert chunk.metadata["split_index"] >= 0

                # Group by header_path and verify ordering
                split_groups = {}
                for chunk in split_chunks:
                    header_path = chunk.metadata.get("header_path", "")
                    if header_path not in split_groups:
                        split_groups[header_path] = []
                    split_groups[header_path].append(chunk)

                for _header_path, group in split_groups.items():
                    if len(group) > 1:
                        group.sort(key=lambda c: c.metadata["split_index"])

                        # Verify line number ordering
                        for i in range(len(group) - 1):
                            current = group[i]
                            next_chunk = group[i + 1]

                            assert current.start_line <= next_chunk.start_line, (
                                f"Split chunks not ordered: {current.start_line} > {next_chunk.start_line}"
                            )

    def test_line_numbers_match_content_position(self, config):
        """Test that line numbers match actual content position."""
        document = """Line 1
Line 2
Line 3
# Header at line 4
Line 5 content
Line 6 content
Line 7 content

## Subheader at line 9
1. List item at line 10
   Continuation at line 11
2. List item at line 12
   Continuation at line 13
3. List item at line 14
   Continuation at line 15
4. List item at line 16
   Continuation at line 17
5. List item at line 18
   Continuation at line 19
"""

        chunks = chunk_markdown(document, config)

        # Verify that line numbers correspond to actual content
        document_lines = document.split("\n")

        for chunk in chunks:
            start_line = chunk.start_line
            end_line = chunk.end_line

            # Extract actual lines from document
            if start_line < len(document_lines) and end_line < len(document_lines):
                actual_lines = document_lines[start_line : end_line + 1]
                # actual_content = "\n".join(actual_lines)  # Not used, but kept for debugging

                # Chunk content should contain some of the actual lines
                # (allowing for header repetition in split chunks)
                chunk_lines = chunk.content.split("\n")

                # At least some lines should match
                matches = 0
                for actual_line in actual_lines:
                    if actual_line.strip() and any(
                        actual_line.strip() in chunk_line for chunk_line in chunk_lines
                    ):
                        matches += 1

                # Should have some matching content
                assert matches > 0, (
                    f"No matching content found for chunk at lines {start_line}-{end_line}"
                )
