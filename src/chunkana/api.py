"""
Public API convenience functions for Chunkana.

This module provides simple functions for common chunking operations.
All functions return consistent types (no union returns).
"""

from typing import Iterator

from .chunker import MarkdownChunker
from .config import ChunkerConfig
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
    chunker = MarkdownChunker(config or ChunkerConfig.default())
    return chunker.analyze(text)


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
    return chunker.chunk_with_analysis(text)


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
    metrics = ChunkingMetrics.from_chunks(
        chunks, cfg.min_chunk_size, cfg.max_chunk_size
    )
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
