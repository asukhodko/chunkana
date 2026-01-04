"""
Compatibility layer for markdown_chunker v2.

Provides backward-compatible API for existing code using v1 interfaces.

**Feature: architecture-redesign**
"""

import warnings

from .chunker import MarkdownChunker
from .config import ChunkConfig
from .types import Chunk, ChunkingResult


class LegacyChunkConfig:
    """
    Legacy configuration wrapper.

    Accepts old parameter names and converts to new ChunkConfig.
    """

    @staticmethod
    def create(**kwargs: object) -> ChunkConfig:
        """Create ChunkConfig from legacy parameters."""
        return ChunkConfig.from_legacy(**kwargs)


class LegacyMarkdownChunker:
    """
    Legacy chunker wrapper.

    Provides v1-compatible interface using v2 implementation.
    """

    def __init__(self, config: ChunkConfig | None = None, **legacy_kwargs: object):
        """
        Initialize with optional legacy parameters.

        Args:
            config: ChunkConfig instance
            **legacy_kwargs: Legacy parameter names (deprecated)
        """
        if legacy_kwargs:
            warnings.warn(
                "Passing configuration as keyword arguments is deprecated. "
                "Use ChunkConfig instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            config = ChunkConfig.from_legacy(**legacy_kwargs)

        self._chunker = MarkdownChunker(config)

    def chunk(self, text: str, include_analysis: bool = False) -> list[Chunk] | ChunkingResult:
        """
        Chunk markdown text.

        Args:
            text: Markdown text to chunk
            include_analysis: If True, return ChunkingResult with analysis

        Returns:
            List[Chunk] if include_analysis=False
            ChunkingResult if include_analysis=True
        """
        if include_analysis:
            chunks, strategy, analysis = self._chunker.chunk_with_analysis(text)
            return ChunkingResult(
                chunks=chunks,
                strategy_used=strategy,
                total_chars=analysis.total_chars if analysis else 0,
                total_lines=analysis.total_lines if analysis else 0,
            )
        else:
            return self._chunker.chunk(text)

    def chunk_with_analysis(self, text: str) -> ChunkingResult:
        """
        Chunk and return full analysis.

        Args:
            text: Markdown text to chunk

        Returns:
            ChunkingResult with chunks and analysis
        """
        result = self.chunk(text, include_analysis=True)
        # Type narrowing: when include_analysis=True, result is ChunkingResult
        assert isinstance(result, ChunkingResult)
        return result


# Convenience functions for backward compatibility
def chunk_text(text: str, config: ChunkConfig | None = None) -> list[Chunk]:
    """Chunk text using v2 implementation."""
    return MarkdownChunker(config).chunk(text)


def chunk_file(path: str, config: ChunkConfig | None = None) -> list[Chunk]:
    """Chunk file using v2 implementation."""
    with open(path, encoding="utf-8") as f:
        return chunk_text(f.read(), config)
