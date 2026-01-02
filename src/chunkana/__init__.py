"""
Chunkana - Intelligent Markdown chunking library for RAG systems.

This library provides structure-aware chunking of Markdown documents,
preserving code blocks, tables, lists, and LaTeX formulas.

Basic usage:
    from chunkana import chunk_markdown

    chunks = chunk_markdown("# Hello\\n\\nWorld")
    for chunk in chunks:
        print(chunk.content)

Advanced usage:
    from chunkana import MarkdownChunker, ChunkerConfig

    config = ChunkerConfig(max_chunk_size=4096, overlap_size=200)
    chunker = MarkdownChunker(config)
    chunks = chunker.chunk(text)
"""

__version__ = "0.1.0"

# Core API
from .api import (
    analyze_markdown,
    chunk_markdown,
    chunk_with_analysis,
    chunk_with_metrics,
    iter_chunks,
)

# Classes
from .chunker import MarkdownChunker
from .config import ChunkConfig, ChunkerConfig
from .hierarchy import HierarchicalChunkingResult, HierarchyBuilder
from .types import (
    Chunk,
    ChunkingMetrics,
    ChunkingResult,
    ContentAnalysis,
    FencedBlock,
)

# Validation
from .validator import ValidationResult, Validator, validate_chunks

__all__ = [
    # Version
    "__version__",
    # Functions
    "chunk_markdown",
    "analyze_markdown",
    "chunk_with_analysis",
    "chunk_with_metrics",
    "iter_chunks",
    # Classes
    "MarkdownChunker",
    "ChunkConfig",
    "ChunkerConfig",
    "Chunk",
    "ContentAnalysis",
    "FencedBlock",
    "ChunkingResult",
    "ChunkingMetrics",
    "HierarchicalChunkingResult",
    "HierarchyBuilder",
    "Validator",
    "ValidationResult",
    "validate_chunks",
]
