"""
Performance regression tests for chunkana.

These tests ensure that quality improvements don't significantly impact performance.
Target: No more than 20% degradation from baseline.
"""

import statistics
import time
from collections.abc import Callable

import pytest

from chunkana import ChunkConfig, MarkdownChunker

# Test documents of varying sizes
SMALL_DOC = """
# Small Document

This is a small test document with minimal content.

## Section 1

Some content here.

## Section 2

More content here.
"""

MEDIUM_DOC = (
    """
# Medium Document

This is a medium-sized test document with more content.

## Introduction

This section provides an introduction to the topic at hand.
It contains multiple paragraphs of text to simulate real-world usage.

The content here is designed to test chunking performance with
a reasonable amount of text that might be found in typical documentation.

## Main Content

### Subsection 1

Here we have detailed information about the first topic.
This includes multiple lines of text and various formatting elements.

- List item 1
- List item 2
- List item 3

### Subsection 2

More detailed content follows here. This section contains
additional paragraphs to increase the document size.

```python
def example_code():
    '''Example code block'''
    return "Hello, World!"
```

### Subsection 3

Final subsection with concluding remarks and additional content
to round out the medium-sized document.

## Conclusion

This concludes our medium-sized test document.
"""
    * 5
)  # Repeat 5 times for medium size


LARGE_DOC = (
    """
# Large Document

This is a large test document designed to stress-test chunking performance.

## Chapter 1: Introduction

### 1.1 Background

This section provides extensive background information on the topic.
The content is designed to be substantial enough to test performance
with larger documents that might be encountered in production.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo.

### 1.2 Objectives

The objectives of this document are:

1. To test chunking performance
2. To verify quality improvements don't impact speed
3. To establish baseline metrics

### 1.3 Scope

This document covers various aspects of performance testing including:

- Timing measurements
- Memory usage patterns
- Algorithmic complexity

## Chapter 2: Technical Details

### 2.1 Architecture

The architecture consists of multiple components working together:

```python
class Component:
    def __init__(self):
        self.data = []

    def process(self, input_data):
        # Process the input
        result = self._transform(input_data)
        return result

    def _transform(self, data):
        return data.upper()
```

### 2.2 Implementation

Implementation details follow standard patterns:

| Feature | Status | Notes |
|---------|--------|-------|
| Chunking | Complete | Optimized |
| Validation | Complete | With invariants |
| Headers | Complete | Dangling prevention |

### 2.3 Testing

Testing is performed at multiple levels:

- Unit tests for individual components
- Integration tests for workflows
- Performance tests for regression detection

## Chapter 3: Results

### 3.1 Performance Metrics

Performance metrics show consistent results across test runs.
The system maintains acceptable performance even with large documents.

### 3.2 Quality Metrics

Quality metrics demonstrate improved output:

- No invariant violations
- No dangling headers
- Minimal micro-chunks

## Conclusion

This large document serves as a comprehensive test case for
performance regression testing in the chunkana library.
"""
    * 10
)  # Repeat 10 times for large size


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self):
        self.elapsed = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start


def measure_operation(func: Callable, iterations: int = 5) -> dict:
    """
    Measure operation performance over multiple iterations.

    Returns dict with min, max, mean, median, stdev times.
    """
    times = []

    for _ in range(iterations):
        with PerformanceTimer() as timer:
            func()
        times.append(timer.elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "iterations": iterations,
    }


@pytest.mark.performance
class TestChunkingPerformance:
    """Test chunking performance with various document sizes."""

    @pytest.fixture
    def default_config(self):
        return ChunkConfig(
            max_chunk_size=1000,
            min_chunk_size=100,
            overlap_size=100,
            validate_invariants=True,
            strict_mode=False,
        )

    @pytest.fixture
    def no_validation_config(self):
        return ChunkConfig(
            max_chunk_size=1000,
            min_chunk_size=100,
            overlap_size=100,
            validate_invariants=False,
        )

    def test_small_document_performance(self, default_config):
        """Small documents should chunk in < 50ms."""
        chunker = MarkdownChunker(default_config)

        metrics = measure_operation(lambda: chunker.chunk(SMALL_DOC), iterations=10)

        assert metrics["mean"] < 0.05, f"Small doc chunking too slow: {metrics['mean']:.3f}s"
        print(
            f"\nSmall doc: mean={metrics['mean'] * 1000:.2f}ms, stdev={metrics['stdev'] * 1000:.2f}ms"
        )

    def test_medium_document_performance(self, default_config):
        """Medium documents should chunk in < 200ms."""
        chunker = MarkdownChunker(default_config)

        metrics = measure_operation(lambda: chunker.chunk(MEDIUM_DOC), iterations=5)

        assert metrics["mean"] < 0.2, f"Medium doc chunking too slow: {metrics['mean']:.3f}s"
        print(
            f"\nMedium doc: mean={metrics['mean'] * 1000:.2f}ms, stdev={metrics['stdev'] * 1000:.2f}ms"
        )

    def test_large_document_performance(self, default_config):
        """Large documents should chunk in < 1s."""
        chunker = MarkdownChunker(default_config)

        metrics = measure_operation(lambda: chunker.chunk(LARGE_DOC), iterations=3)

        assert metrics["mean"] < 1.0, f"Large doc chunking too slow: {metrics['mean']:.3f}s"
        print(
            f"\nLarge doc: mean={metrics['mean'] * 1000:.2f}ms, stdev={metrics['stdev'] * 1000:.2f}ms"
        )

    def test_validation_overhead(self, default_config, no_validation_config):
        """Validation overhead should be < 20% of total time."""
        chunker_with_validation = MarkdownChunker(default_config)
        chunker_without_validation = MarkdownChunker(no_validation_config)

        # Measure with validation
        with_validation = measure_operation(
            lambda: chunker_with_validation.chunk(MEDIUM_DOC), iterations=5
        )

        # Measure without validation
        without_validation = measure_operation(
            lambda: chunker_without_validation.chunk(MEDIUM_DOC), iterations=5
        )

        # Calculate overhead
        overhead = (with_validation["mean"] - without_validation["mean"]) / without_validation[
            "mean"
        ]

        assert overhead < 0.2, f"Validation overhead too high: {overhead * 100:.1f}%"
        print(f"\nValidation overhead: {overhead * 100:.1f}%")


@pytest.mark.performance
class TestHierarchicalPerformance:
    """Test hierarchical chunking performance."""

    @pytest.fixture
    def config(self):
        return ChunkConfig(
            max_chunk_size=1000,
            min_chunk_size=100,
            overlap_size=100,
            validate_invariants=True,
            strict_mode=False,
        )

    def test_hierarchical_small_document(self, config):
        """Hierarchical chunking of small docs should be < 100ms."""
        chunker = MarkdownChunker(config)

        metrics = measure_operation(lambda: chunker.chunk_hierarchical(SMALL_DOC), iterations=10)

        assert metrics["mean"] < 0.1, f"Hierarchical small doc too slow: {metrics['mean']:.3f}s"
        print(f"\nHierarchical small: mean={metrics['mean'] * 1000:.2f}ms")

    def test_hierarchical_medium_document(self, config):
        """Hierarchical chunking of medium docs should be < 300ms."""
        chunker = MarkdownChunker(config)

        metrics = measure_operation(lambda: chunker.chunk_hierarchical(MEDIUM_DOC), iterations=5)

        assert metrics["mean"] < 0.3, f"Hierarchical medium doc too slow: {metrics['mean']:.3f}s"
        print(f"\nHierarchical medium: mean={metrics['mean'] * 1000:.2f}ms")

    def test_hierarchical_large_document(self, config):
        """Hierarchical chunking of large docs should be < 2s."""
        chunker = MarkdownChunker(config)

        metrics = measure_operation(lambda: chunker.chunk_hierarchical(LARGE_DOC), iterations=3)

        assert metrics["mean"] < 2.0, f"Hierarchical large doc too slow: {metrics['mean']:.3f}s"
        print(f"\nHierarchical large: mean={metrics['mean'] * 1000:.2f}ms")

    def test_navigation_performance(self, config):
        """Navigation methods should be O(1) - < 1ms per operation."""
        chunker = MarkdownChunker(config)
        result = chunker.chunk_hierarchical(MEDIUM_DOC)

        # Measure get_chunk
        get_chunk_metrics = measure_operation(
            lambda: result.get_chunk(result.root_id), iterations=100
        )

        # Measure get_children
        get_children_metrics = measure_operation(
            lambda: result.get_children(result.root_id), iterations=100
        )

        # Measure get_flat_chunks
        get_flat_metrics = measure_operation(lambda: result.get_flat_chunks(), iterations=100)

        assert get_chunk_metrics["mean"] < 0.001, "get_chunk too slow"
        assert get_children_metrics["mean"] < 0.001, "get_children too slow"
        assert get_flat_metrics["mean"] < 0.01, "get_flat_chunks too slow"

        print(
            f"\nNavigation: get_chunk={get_chunk_metrics['mean'] * 1000:.3f}ms, "
            f"get_children={get_children_metrics['mean'] * 1000:.3f}ms, "
            f"get_flat={get_flat_metrics['mean'] * 1000:.3f}ms"
        )


@pytest.mark.performance
@pytest.mark.slow
class TestScalability:
    """Test that performance scales linearly with document size."""

    @pytest.fixture
    def config(self):
        return ChunkConfig(
            max_chunk_size=1000,
            min_chunk_size=100,
            overlap_size=100,
            validate_invariants=True,
        )

    def test_linear_scaling(self, config):
        """Chunking time should scale roughly linearly with document size."""
        chunker = MarkdownChunker(config)

        # Create documents of increasing size
        sizes = [1, 2, 4, 8]
        times = []

        for multiplier in sizes:
            doc = MEDIUM_DOC * multiplier

            metrics = measure_operation(lambda d=doc: chunker.chunk(d), iterations=3)
            times.append(metrics["mean"])

        # Check that time doesn't grow faster than O(n log n)
        # For linear scaling, time[i] / time[0] should be roughly sizes[i]
        # Allow 150% margin for O(n log n) behavior and additional processing
        # (SectionSplitter adds overhead for large documents)
        for i in range(1, len(sizes)):
            expected_ratio = sizes[i] * 2.5  # Allow 150% margin
            actual_ratio = times[i] / times[0]

            assert actual_ratio < expected_ratio, (
                f"Non-linear scaling detected: {actual_ratio:.1f}x for {sizes[i]}x size"
            )

        print(f"\nScaling ratios: {[f'{t / times[0]:.1f}x' for t in times]}")


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns."""

    @pytest.fixture
    def config(self):
        return ChunkConfig(
            max_chunk_size=1000,
            min_chunk_size=100,
            validate_invariants=True,
        )

    def test_chunk_count_reasonable(self, config):
        """Number of chunks should be reasonable for document size."""
        chunker = MarkdownChunker(config)

        # Small doc
        small_chunks = chunker.chunk(SMALL_DOC)
        assert len(small_chunks) < 20, f"Too many chunks for small doc: {len(small_chunks)}"

        # Medium doc
        medium_chunks = chunker.chunk(MEDIUM_DOC)
        assert len(medium_chunks) < 100, f"Too many chunks for medium doc: {len(medium_chunks)}"

        # Large doc
        large_chunks = chunker.chunk(LARGE_DOC)
        assert len(large_chunks) < 500, f"Too many chunks for large doc: {len(large_chunks)}"

        print(
            f"\nChunk counts: small={len(small_chunks)}, "
            f"medium={len(medium_chunks)}, large={len(large_chunks)}"
        )

    def test_hierarchical_chunk_count(self, config):
        """Hierarchical mode should not create excessive chunks."""
        chunker = MarkdownChunker(config)

        result = chunker.chunk_hierarchical(MEDIUM_DOC)
        flat_chunks = result.get_flat_chunks()

        # Hierarchical should have more total chunks (includes parents)
        # but flat chunks should be similar to non-hierarchical
        assert len(result.chunks) < 200, f"Too many hierarchical chunks: {len(result.chunks)}"
        assert len(flat_chunks) < 100, f"Too many flat chunks: {len(flat_chunks)}"

        print(f"\nHierarchical: total={len(result.chunks)}, flat={len(flat_chunks)}")


# Benchmark runner for manual testing
def run_benchmarks():
    """Run all benchmarks and print results."""
    print("=" * 60)
    print("CHUNKANA PERFORMANCE BENCHMARKS")
    print("=" * 60)

    config = ChunkConfig(
        max_chunk_size=1000,
        min_chunk_size=100,
        overlap_size=100,
        validate_invariants=True,
    )
    chunker = MarkdownChunker(config)

    # Standard chunking
    print("\n--- Standard Chunking ---")
    for name, doc in [("Small", SMALL_DOC), ("Medium", MEDIUM_DOC), ("Large", LARGE_DOC)]:
        metrics = measure_operation(lambda d=doc: chunker.chunk(d), iterations=5)
        print(f"{name}: {metrics['mean'] * 1000:.2f}ms (±{metrics['stdev'] * 1000:.2f}ms)")

    # Hierarchical chunking
    print("\n--- Hierarchical Chunking ---")
    for name, doc in [("Small", SMALL_DOC), ("Medium", MEDIUM_DOC), ("Large", LARGE_DOC)]:
        metrics = measure_operation(lambda d=doc: chunker.chunk_hierarchical(d), iterations=5)
        print(f"{name}: {metrics['mean'] * 1000:.2f}ms (±{metrics['stdev'] * 1000:.2f}ms)")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    run_benchmarks()
