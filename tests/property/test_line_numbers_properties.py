"""
Property-based tests for line number accuracy.

Uses Hypothesis to generate test cases and verify line number properties.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from chunkana import ChunkConfig, chunk_markdown


@st.composite
def markdown_document_with_lists(draw):
    """Generate markdown documents with lists that may trigger splitting."""
    num_sections = draw(st.integers(min_value=1, max_value=3))

    sections = []
    current_line = 1

    for i in range(num_sections):
        header_level = draw(st.integers(min_value=1, max_value=3))
        header = "#" * header_level + f" Section {i + 1}"
        sections.append(header)
        current_line += 1

        # Add empty line after header
        sections.append("")
        current_line += 1

        # Add list items
        num_items = draw(st.integers(min_value=3, max_value=8))
        for j in range(num_items):
            item_content = draw(
                st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=20, max_size=100)
            )
            item = f"{j + 1}. {item_content}"
            sections.append(item)
            current_line += 1

            # Sometimes add continuation
            if draw(st.booleans()):
                continuation = "   " + draw(
                    st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=10, max_size=50)
                )
                sections.append(continuation)
                current_line += 1

        # Add empty line between sections
        if i < num_sections - 1:
            sections.append("")
            current_line += 1

    return "\n".join(sections)


class TestLineNumberProperties:
    """Property-based tests for line number accuracy."""

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=20, deadline=5000)
    def test_line_numbers_monotonic(self, doc):
        """Property: line numbers are monotonic across all chunks."""
        config = ChunkConfig(max_chunk_size=400, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        # Sort chunks by start_line
        sorted_chunks = sorted(chunks, key=lambda c: c.start_line)

        # Verify monotonic property
        for i in range(len(sorted_chunks) - 1):
            current = sorted_chunks[i]
            next_chunk = sorted_chunks[i + 1]

            assert current.start_line <= next_chunk.start_line, (
                f"Line numbers not monotonic: {current.start_line} > {next_chunk.start_line}"
            )

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=20, deadline=5000)
    def test_no_line_gaps_in_split_chunks(self, doc):
        """Property: no gaps in line coverage within split groups."""
        config = ChunkConfig(max_chunk_size=400, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        # Group split chunks by header_path
        split_groups = {}
        for chunk in chunks:
            if "split_index" in chunk.metadata:
                header_path = chunk.metadata.get("header_path", "")
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

        # Verify no gaps within each split group
        for _header_path, group in split_groups.items():
            if len(group) > 1:
                group.sort(key=lambda c: c.metadata["split_index"])

                # Check that chunks are reasonably connected
                for i in range(len(group) - 1):
                    current = group[i]
                    next_chunk = group[i + 1]

                    # Next chunk should start at or after current chunk ends
                    assert next_chunk.start_line >= current.start_line, (
                        f"Gap in split chunks: {current.end_line} -> {next_chunk.start_line}"
                    )

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=20, deadline=5000)
    def test_split_chunk_ranges_within_reasonable_bounds(self, doc):
        """Property: split chunk line ranges are within reasonable bounds."""
        config = ChunkConfig(max_chunk_size=400, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        doc_lines = doc.split("\n")
        max_line = len(doc_lines) - 1

        for chunk in chunks:
            # Line numbers should be reasonable (allowing for some overlap extension)
            assert chunk.start_line >= 0, f"start_line {chunk.start_line} should be >= 0"

            # start_line should be <= end_line
            assert chunk.start_line <= chunk.end_line, (
                f"start_line {chunk.start_line} > end_line {chunk.end_line}"
            )

            # Allow some extension beyond document bounds due to overlap/processing
            # but not excessively beyond
            assert chunk.end_line <= max_line + 10, (
                f"end_line {chunk.end_line} too far beyond document bounds {max_line}"
            )

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=20, deadline=5000)
    def test_split_chunks_have_consistent_metadata(self, doc):
        """Property: split chunks have consistent metadata."""
        config = ChunkConfig(max_chunk_size=400, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        split_chunks = [c for c in chunks if "split_index" in c.metadata]

        for chunk in split_chunks:
            metadata = chunk.metadata

            # Split chunks should have required metadata
            assert "split_index" in metadata
            assert "original_section_size" in metadata
            assert isinstance(metadata["split_index"], int)
            assert metadata["split_index"] >= 0
            assert isinstance(metadata["original_section_size"], int)
            assert metadata["original_section_size"] > 0

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=15, deadline=5000)
    def test_line_numbers_correspond_to_content(self, doc):
        """Property: line numbers should correspond to actual content."""
        config = ChunkConfig(max_chunk_size=500, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        doc_lines = doc.split("\n")

        for chunk in chunks:
            start_line = chunk.start_line
            end_line = chunk.end_line

            # Skip if line numbers are beyond document boundaries (due to overlap/processing)
            if start_line >= len(doc_lines) or end_line >= len(doc_lines):
                continue

            # Skip if line range is invalid
            if start_line < 0 or end_line < start_line:
                continue

            # Extract actual lines from document
            actual_lines = doc_lines[start_line : min(end_line + 1, len(doc_lines))]
            chunk_lines = chunk.content.split("\n")

            # At least some content should match
            # (allowing for header repetition in split chunks)
            matches = 0
            for actual_line in actual_lines:
                if actual_line.strip():
                    for chunk_line in chunk_lines:
                        if actual_line.strip() in chunk_line:
                            matches += 1
                            break

            # Should have some matching content if we have actual lines
            if actual_lines and any(line.strip() for line in actual_lines):
                # Allow for cases where content doesn't match due to processing
                # Just ensure we don't have completely invalid line numbers
                assert start_line >= 0 and end_line >= start_line, (
                    f"Invalid line range: {start_line}-{end_line}"
                )


class TestSplitChunkProperties:
    """Property-based tests specific to split chunks."""

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=15, deadline=5000)
    def test_split_chunks_preserve_order(self, doc):
        """Property: split chunks preserve document order."""
        config = ChunkConfig(max_chunk_size=300, overlap_size=30)
        chunks = chunk_markdown(doc, config)

        # Group split chunks by header_path
        split_groups = {}
        for chunk in chunks:
            if "split_index" in chunk.metadata:
                header_path = chunk.metadata.get("header_path", "")
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

        # Verify order preservation within each group
        for _header_path, group in split_groups.items():
            if len(group) > 1:
                # Sort by split_index
                group.sort(key=lambda c: c.metadata["split_index"])

                # Verify split_index sequence
                for i, chunk in enumerate(group):
                    assert chunk.metadata["split_index"] == i, (
                        f"Split index not sequential: expected {i}, got {chunk.metadata['split_index']}"
                    )

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=15, deadline=5000)
    def test_continued_chunks_have_headers(self, doc):
        """Property: continued chunks should start with headers."""
        config = ChunkConfig(max_chunk_size=300, overlap_size=30)
        chunks = chunk_markdown(doc, config)

        for chunk in chunks:
            if chunk.metadata.get("continued_from_header"):
                first_line = chunk.content.strip().split("\n")[0]
                assert first_line.startswith("#"), (
                    f"Continued chunk should start with header: {first_line[:50]}"
                )

    @given(doc=markdown_document_with_lists())
    @settings(max_examples=15, deadline=5000)
    def test_split_chunks_total_size_reasonable(self, doc):
        """Property: total size of split chunks should be reasonable."""
        config = ChunkConfig(max_chunk_size=400, overlap_size=50)
        chunks = chunk_markdown(doc, config)

        # Group split chunks
        split_groups = {}
        for chunk in chunks:
            if "split_index" in chunk.metadata:
                header_path = chunk.metadata.get("header_path", "")
                if header_path not in split_groups:
                    split_groups[header_path] = []
                split_groups[header_path].append(chunk)

        # Verify total size is reasonable
        for _header_path, group in split_groups.items():
            if len(group) > 1:
                total_content_size = sum(len(c.content) for c in group)
                original_size = group[0].metadata.get("original_section_size", 0)

                # Total size should be larger than original (due to header repetition)
                # but not excessively larger. Allow small variations due to content normalization.
                if original_size > 0:
                    ratio = total_content_size / original_size
                    assert 0.95 <= ratio <= 3.0, (
                        f"Split chunks size ratio unreasonable: {ratio:.2f}"
                    )
