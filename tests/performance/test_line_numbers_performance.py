"""
Performance tests for line number calculation.

Measures the performance impact of the new line number calculation.
"""

import time
from pathlib import Path

import pytest

from chunkana import ChunkConfig, chunk_markdown


class TestLineNumbersPerformance:
    """Performance tests for line number calculation."""

    @pytest.fixture
    def large_document(self):
        """Generate a large document for performance testing."""
        sections = []
        for i in range(20):  # 20 sections
            sections.append(f"## Section {i + 1}")
            sections.append("")

            # Add list items that will trigger splitting
            for j in range(15):  # 15 items per section
                sections.append(
                    f"{j + 1}. Item {j + 1} with substantial content to ensure splitting occurs when the chunk size limit is reached."
                )
                sections.append(
                    f"   Additional details for item {j + 1} to make it longer and more realistic for testing purposes."
                )
                sections.append(
                    "   Even more content to reach the size threshold for splitting and validate line number calculation."
                )
                sections.append(
                    "   This ensures we have enough content to trigger the section splitter functionality."
                )
                sections.append("")

        return "\n".join(sections)

    @pytest.fixture
    def sde_criteria_document(self):
        """Load the SDE criteria document for realistic testing."""
        fixture_path = Path(__file__).parent.parent / "fixtures" / "sde_criteria.md"
        if fixture_path.exists():
            return fixture_path.read_text(encoding="utf-8")
        return None

    def test_performance_with_splitting(self):
        """Test performance when splitting occurs."""
        # Use SDE document which is known to trigger splitting
        sde_path = Path(__file__).parent.parent / "fixtures" / "sde_criteria.md"
        if not sde_path.exists():
            pytest.skip("SDE criteria document not available")

        split_document = sde_path.read_text(encoding="utf-8")
        config = ChunkConfig(max_chunk_size=800, overlap_size=100)

        # Measure time
        start_time = time.time()
        chunks = chunk_markdown(split_document, config)
        end_time = time.time()

        processing_time = end_time - start_time

        # Performance assertions
        assert processing_time < 10.0, f"Processing took too long: {processing_time:.2f}s"

        # Verify we got chunks with splits
        split_chunks = [c for c in chunks if "split_index" in c.metadata]
        if len(split_chunks) == 0:
            # If no splits with SDE doc, create a simple test that forces splitting
            split_document = self._create_forced_split_document()
            chunks = chunk_markdown(split_document, config)
            split_chunks = [c for c in chunks if "split_index" in c.metadata]

        assert len(split_chunks) > 0, (
            f"No split chunks found. Total chunks: {len(chunks)}, sizes: {[len(c.content) for c in chunks[:5]]}"
        )

        # Calculate throughput
        doc_size = len(split_document)
        throughput = doc_size / processing_time

        print("Performance metrics:")
        print(f"  Document size: {doc_size:,} chars")
        print(f"  Processing time: {processing_time:.3f}s")
        print(f"  Throughput: {throughput:,.0f} chars/sec")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Split chunks: {len(split_chunks)}")

    def _create_forced_split_document(self):
        """Create a document that definitely forces splitting."""
        # Create a single section with content that exceeds chunk size
        content = "## Large Section\n\n"
        content += "This section will definitely exceed the chunk size limit.\n\n"

        # Add enough content to exceed 800 chars in a single chunk
        for i in range(50):
            content += (
                f"Sentence {i + 1} with substantial content that makes this section very long. "
            )

        return content

    def _create_split_document(self):
        """Create a document that will trigger splitting."""
        sections = []

        # Create sections that will be chunked as single units, then split
        for i in range(3):
            sections.append(f"## Section {i + 1}")
            sections.append("")
            sections.append(
                f"This is section {i + 1} with content that will be chunked as a single unit initially, then split by the section splitter."
            )
            sections.append("")

            # Create large paragraphs without natural break points
            paragraph1 = f"This is a very long paragraph for section {i + 1} that contains substantial content but no list items or other natural break points that the initial chunker would use. This paragraph goes on and on with detailed explanations and comprehensive information that makes it quite lengthy. We continue adding more and more content to ensure this becomes a substantial block of text that exceeds the chunk size limit when combined with the header. Additional sentences with more detailed information and explanations continue to expand this paragraph. Even more content is added here to ensure we reach the target size for triggering the section splitter functionality."

            paragraph2 = f"Another substantial paragraph for section {i + 1} follows with even more detailed content and comprehensive explanations. This paragraph also contains extensive information and detailed descriptions that contribute to the overall size of this section. We continue to add more and more content to ensure the total section size exceeds the chunk size limit. Additional comprehensive details and thorough explanations are included throughout this paragraph."

            paragraph3 = f"A third major paragraph for section {i + 1} with extensive content and detailed information continues to build up the size of this section. This paragraph contains comprehensive explanations and detailed descriptions that make it quite substantial. We deliberately add more and more content to ensure the section becomes large enough to require splitting."

            sections.extend([paragraph1, "", paragraph2, "", paragraph3, ""])

        return "\n".join(sections)

    def test_performance_comparison_with_sde_document(self, sde_criteria_document):
        """Compare performance with realistic document."""
        if not sde_criteria_document:
            pytest.skip("SDE criteria document not available")

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)

        # Run multiple times for more accurate measurement
        times = []
        for _ in range(5):
            start_time = time.time()
            chunks = chunk_markdown(sde_criteria_document, config)
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        # Performance assertions
        assert avg_time < 2.0, f"Average processing time too long: {avg_time:.3f}s"

        # Verify functionality
        split_chunks = [c for c in chunks if "split_index" in c.metadata]

        print("SDE document performance:")
        print(f"  Document size: {len(sde_criteria_document):,} chars")
        print(f"  Average time: {avg_time:.3f}s")
        print(f"  Min time: {min_time:.3f}s")
        print(f"  Max time: {max_time:.3f}s")
        print(f"  Total chunks: {len(chunks)}")
        print(f"  Split chunks: {len(split_chunks)}")

    def test_memory_usage_reasonable(self, large_document):
        """Test that memory usage is reasonable."""
        try:
            import os

            import psutil

            process = psutil.Process(os.getpid())

            # Measure memory before
            memory_before = process.memory_info().rss

            config = ChunkConfig(max_chunk_size=400, overlap_size=50)
            chunks = chunk_markdown(large_document, config)

            # Measure memory after
            memory_after = process.memory_info().rss
            memory_increase = memory_after - memory_before

            # Memory increase should be reasonable
            doc_size = len(large_document)
            memory_ratio = memory_increase / doc_size if doc_size > 0 else 0

            print("Memory usage:")
            print(f"  Document size: {doc_size:,} chars")
            print(f"  Memory increase: {memory_increase:,} bytes")
            print(f"  Memory ratio: {memory_ratio:.2f}x")
            print(f"  Total chunks: {len(chunks)}")

            # Memory should not increase by more than 5x document size
            assert memory_ratio < 5.0, f"Memory usage too high: {memory_ratio:.2f}x"

        except ImportError:
            pytest.skip("psutil not available for memory testing")

    def test_scalability_with_document_size(self):
        """Test scalability with increasing document size."""
        sizes = [1000, 5000, 10000, 20000]  # Character counts
        times = []

        config = ChunkConfig(max_chunk_size=600, overlap_size=100)

        for size in sizes:
            # Generate document of specific size
            sections = []
            current_size = 0
            section_num = 1

            while current_size < size:
                section = f"## Section {section_num}\n\n"
                for i in range(10):
                    item = f"{i + 1}. Item with content to reach target size. "
                    item += "Additional content to make it substantial. "
                    section += item + "\n"

                sections.append(section)
                current_size += len(section)
                section_num += 1

            document = "\n".join(sections)[:size]  # Trim to exact size

            # Measure processing time
            start_time = time.time()
            chunks = chunk_markdown(document, config)
            end_time = time.time()

            processing_time = end_time - start_time
            times.append(processing_time)

            print(f"Size {size:,}: {processing_time:.3f}s ({len(chunks)} chunks)")

        # Check that time scales reasonably (should be roughly linear)
        # Allow for some variation due to document structure differences
        for i in range(1, len(times)):
            size_ratio = sizes[i] / sizes[i - 1]
            time_ratio = times[i] / times[i - 1]

            # Time ratio should not be much larger than size ratio
            assert time_ratio < size_ratio * 2.0, (
                f"Poor scalability: {size_ratio:.1f}x size → {time_ratio:.1f}x time"
            )

    def test_overhead_measurement(self, sde_criteria_document):
        """Measure overhead of line number calculation."""
        if not sde_criteria_document:
            pytest.skip("SDE criteria document not available")

        config = ChunkConfig(max_chunk_size=1000, overlap_size=200)

        # Run chunking multiple times to get stable measurements
        times = []
        for _ in range(10):
            start_time = time.time()
            chunks = chunk_markdown(sde_criteria_document, config)
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)

        # Check if we have split chunks (where line number calculation matters)
        split_chunks = [c for c in chunks if "split_index" in c.metadata]

        if split_chunks:
            # Calculate overhead per split chunk
            overhead_per_split = avg_time / len(split_chunks)

            print("Overhead analysis:")
            print(f"  Total processing time: {avg_time:.3f}s")
            print(f"  Split chunks: {len(split_chunks)}")
            print(f"  Overhead per split: {overhead_per_split * 1000:.1f}ms")

            # Overhead should be reasonable
            assert overhead_per_split < 0.1, (
                f"Overhead per split chunk too high: {overhead_per_split:.3f}s"
            )
