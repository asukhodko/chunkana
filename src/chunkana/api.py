"""
Public API convenience functions for Chunkana.

This module provides simple functions for common chunking operations.
All functions return consistent types (no union returns).
"""

from collections.abc import Iterator
from pathlib import Path

from .chunker import MarkdownChunker
from .config import ChunkerConfig
from .hierarchy import HierarchicalChunkingResult, HierarchyBuilder
from .streaming import StreamingChunker, StreamingConfig
from .types import Chunk, ChunkingMetrics, ChunkingResult, ContentAnalysis


def chunk_markdown(
    text: str,
    config: ChunkerConfig | None = None,
) -> list[Chunk]:
    """
    Chunk markdown text into semantic segments.

    This is the primary entry point for basic chunking.
    Always returns List[Chunk], never a union type.

    Args:
        text: Markdown text to chunk
        config: Optional configuration (uses defaults if None)

    Returns:
        List of Chunk objects with content and metadata

    Example:
        >>> chunks = chunk_markdown("# Hello\\n\\nWorld")
        >>> print(chunks[0].content)
    """
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    return chunker.chunk(text)


def analyze_markdown(
    text: str,
    config: ChunkerConfig | None = None,
) -> ContentAnalysis:
    """
    Analyze markdown document without chunking.

    Returns content analysis with metrics about the document:
    code ratio, header count, table count, list blocks, etc.

    Args:
        text: Markdown text to analyze
        config: Optional configuration

    Returns:
        ContentAnalysis with document metrics

    Example:
        >>> analysis = analyze_markdown(text)
        >>> print(f"Code ratio: {analysis.code_ratio}")
    """
    from .parser import get_parser

    parser = get_parser()
    return parser.analyze(text)


def chunk_with_analysis(
    text: str,
    config: ChunkerConfig | None = None,
) -> ChunkingResult:
    """
    Chunk text and return structured result with analysis.

    Returns ChunkingResult containing:
    - chunks: List[Chunk]
    - strategy_used: str
    - processing_time: float
    - total_chars: int
    - total_lines: int

    Args:
        text: Markdown text to chunk
        config: Optional configuration

    Returns:
        ChunkingResult with chunks and metadata

    Example:
        >>> result = chunk_with_analysis(text)
        >>> print(f"Strategy: {result.strategy_used}")
        >>> print(f"Chunks: {len(result.chunks)}")
    """
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    chunks, strategy, analysis = chunker.chunk_with_analysis(text)
    return ChunkingResult(
        chunks=chunks,
        strategy_used=strategy,
        total_chars=analysis.total_chars if analysis else 0,
        total_lines=analysis.total_lines if analysis else 0,
    )


def chunk_with_metrics(
    text: str,
    config: ChunkerConfig | None = None,
) -> tuple[list[Chunk], ChunkingMetrics]:
    """
    Chunk text and return quality metrics.

    Returns tuple of (chunks, metrics) where metrics contains:
    - total_chunks
    - avg_chunk_size
    - std_dev_size
    - min_size, max_size
    - undersize_count, oversize_count

    Args:
        text: Markdown text to chunk
        config: Optional configuration

    Returns:
        Tuple of (List[Chunk], ChunkingMetrics)

    Example:
        >>> chunks, metrics = chunk_with_metrics(text)
        >>> print(f"Avg size: {metrics.avg_chunk_size}")
    """
    cfg = config or ChunkerConfig.default()
    chunker = MarkdownChunker(cfg)
    chunks = chunker.chunk(text)
    metrics = ChunkingMetrics.from_chunks(chunks, cfg.min_chunk_size, cfg.max_chunk_size)
    return chunks, metrics


def iter_chunks(
    text: str,
    config: ChunkerConfig | None = None,
) -> Iterator[Chunk]:
    """
    Yield chunks one at a time for memory efficiency.

    Use this for large documents where you want to process
    chunks incrementally without loading all into memory.

    Args:
        text: Markdown text to chunk
        config: Optional configuration

    Yields:
        Chunk objects one at a time

    Example:
        >>> for chunk in iter_chunks(large_text):
        ...     process(chunk)
    """
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    # For now, just iterate over the list
    # TODO: Implement true streaming in chunker
    yield from chunker.chunk(text)


# =============================================================================
# Plugin Parity API Functions (Task 6)
# =============================================================================


def chunk_text(
    text: str,
    config: ChunkerConfig | None = None,
) -> list[Chunk]:
    """
    Chunk markdown text into semantic segments.

    This is an alias for chunk_markdown() for plugin compatibility.

    Args:
        text: Markdown text to chunk
        config: Optional configuration (uses defaults if None)

    Returns:
        List of Chunk objects with content and metadata

    Example:
        >>> chunks = chunk_text("# Hello\\n\\nWorld")
        >>> print(chunks[0].content)
    """
    return chunk_markdown(text, config)


def chunk_file(
    file_path: str | Path,
    config: ChunkerConfig | None = None,
    encoding: str = "utf-8",
) -> list[Chunk]:
    """
    Chunk markdown file into semantic segments.

    Reads file and chunks its content. Raises appropriate errors
    for file not found or encoding issues.

    Args:
        file_path: Path to markdown file
        config: Optional configuration (uses defaults if None)
        encoding: File encoding (default: utf-8)

    Returns:
        List of Chunk objects with content and metadata

    Raises:
        FileNotFoundError: If file does not exist
        UnicodeDecodeError: If file cannot be decoded with given encoding

    Example:
        >>> chunks = chunk_file("README.md")
        >>> print(f"Found {len(chunks)} chunks")
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    text = path.read_text(encoding=encoding)
    return chunk_markdown(text, config)


def chunk_file_streaming(
    file_path: str | Path,
    chunk_config: ChunkerConfig | None = None,
    streaming_config: StreamingConfig | None = None,
    encoding: str = "utf-8",
) -> Iterator[Chunk]:
    """
    Chunk large markdown file in streaming mode.

    Memory-efficient chunking for large files (>10MB).
    Yields chunks incrementally without loading entire file.

    Invariants maintained:
    - Line coverage: all source lines appear in output
    - Atomic blocks: code blocks and tables not split
    - Monotonic start_line: chunks ordered by position

    Args:
        file_path: Path to markdown file
        chunk_config: Chunking configuration (uses defaults if None)
        streaming_config: Streaming configuration (uses defaults if None)
        encoding: File encoding (default: utf-8)

    Yields:
        Chunk objects with streaming metadata

    Raises:
        FileNotFoundError: If file does not exist
        UnicodeDecodeError: If file cannot be decoded

    Example:
        >>> for chunk in chunk_file_streaming("large_doc.md"):
        ...     process(chunk)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    cfg = chunk_config or ChunkerConfig.default()
    streamer = StreamingChunker(cfg, streaming_config)

    # Use streaming chunker's file method
    yield from streamer.chunk_file(str(path))


def chunk_hierarchical(
    text: str,
    config: ChunkerConfig | None = None,
    include_document_summary: bool = True,
) -> HierarchicalChunkingResult:
    """
    Chunk text and return hierarchical result with navigation.

    Creates parent-child relationships between chunks based on
    header structure. Enables tree-based navigation and retrieval.

    Args:
        text: Markdown text to chunk
        config: Optional configuration (uses defaults if None)
        include_document_summary: Whether to create root document chunk

    Returns:
        HierarchicalChunkingResult with navigation methods:
        - get_chunk(id): Get chunk by ID
        - get_children(id): Get child chunks
        - get_parent(id): Get parent chunk
        - get_ancestors(id): Get path to root
        - get_flat_chunks(): Get leaf chunks only

    Example:
        >>> result = chunk_hierarchical(text)
        >>> root = result.get_chunk(result.root_id)
        >>> children = result.get_children(result.root_id)
    """
    chunks = chunk_markdown(text, config)
    builder = HierarchyBuilder(include_document_summary=include_document_summary)
    return builder.build(chunks, text)
