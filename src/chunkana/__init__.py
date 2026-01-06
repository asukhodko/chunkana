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

__version__ = "0.1.2"

# Core API
from .api import (
    analyze_markdown,
    chunk_file,
    chunk_file_streaming,
    chunk_hierarchical,
    chunk_markdown,
    chunk_text,
    chunk_with_analysis,
    chunk_with_metrics,
    iter_chunks,
)

# Classes
from .chunker import MarkdownChunker
from .config import ChunkConfig, ChunkerConfig
from .exceptions import (
    ChunkanaError,
    ConfigurationError,
    HierarchicalInvariantError,
    TreeConstructionError,
    ValidationError,
)
from .hierarchy import HierarchicalChunkingResult, HierarchyBuilder
from .invariant_validator import InvariantValidator
from .invariant_validator import ValidationResult as InvariantValidationResult

# Renderers
from .renderers import (
    render_dify_style,
    render_inline_metadata,
    render_json,
    render_with_embedded_overlap,
    render_with_prev_overlap,
)
from .section_splitter import SectionSplitter

# Streaming
from .streaming import StreamingChunker, StreamingConfig
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
    # Functions - Core
    "chunk_markdown",
    "chunk_text",
    "chunk_file",
    "chunk_file_streaming",
    "chunk_hierarchical",
    "analyze_markdown",
    "chunk_with_analysis",
    "chunk_with_metrics",
    "iter_chunks",
    # Functions - Renderers
    "render_dify_style",
    "render_with_embedded_overlap",
    "render_with_prev_overlap",
    "render_json",
    "render_inline_metadata",
    # Classes - Core
    "MarkdownChunker",
    "ChunkConfig",
    "ChunkerConfig",
    "Chunk",
    "ContentAnalysis",
    "FencedBlock",
    "ChunkingResult",
    "ChunkingMetrics",
    # Classes - Exceptions
    "ChunkanaError",
    "HierarchicalInvariantError",
    "ValidationError",
    "ConfigurationError",
    "TreeConstructionError",
    # Classes - Hierarchy
    "HierarchicalChunkingResult",
    "HierarchyBuilder",
    # Classes - Section Splitting
    "SectionSplitter",
    # Classes - Invariant Validation
    "InvariantValidator",
    "InvariantValidationResult",
    # Classes - Streaming
    "StreamingChunker",
    "StreamingConfig",
    # Classes - Validation
    "Validator",
    "ValidationResult",
    "validate_chunks",
]
