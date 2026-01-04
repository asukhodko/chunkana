"""
Fallback strategy for markdown_chunker v2.

Universal strategy that works for any document.
Splits by paragraphs and groups to max_chunk_size.
"""

from ..config import ChunkConfig
from ..types import Chunk, ContentAnalysis
from .base import BaseStrategy


class FallbackStrategy(BaseStrategy):
    """
    Universal fallback strategy.

    Works for any document by splitting on paragraph boundaries
    and grouping paragraphs to fit within max_chunk_size.

    Priority: 4 (lowest - used when no other strategy applies)
    """

    @property
    def name(self) -> str:
        return "fallback"

    @property
    def priority(self) -> int:
        return 4

    def can_handle(self, analysis: ContentAnalysis, config: ChunkConfig) -> bool:
        """Always returns True - fallback handles everything."""
        return True

    def apply(self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig) -> list[Chunk]:
        """
        Apply fallback strategy.

        Splits document by paragraphs and groups them to fit max_chunk_size.
        Preserves atomic blocks (code, tables, LaTeX) if present.
        """
        if not md_text.strip():
            return []

        # O1: Use cached lines from analysis (fallback for backward compatibility)
        lines = analysis.get_lines()
        if lines is None:
            lines = md_text.split("\n")

        # Check for atomic blocks
        atomic_ranges = self._get_atomic_blocks_in_range(1, len(lines), analysis)

        if atomic_ranges:
            # Document has atomic blocks - preserve them
            return self._apply_with_atomic_blocks(md_text, atomic_ranges, config)
        else:
            # No atomic blocks - simple paragraph splitting
            return self._apply_simple_paragraph_split(md_text, config)

    def _apply_simple_paragraph_split(self, md_text: str, config: ChunkConfig) -> list[Chunk]:
        """Simple paragraph splitting without atomic blocks."""
        # Split by double newlines (paragraphs)
        paragraphs = md_text.split("\n\n")

        chunks = []
        current_content = ""
        current_start_line = 1
        current_line = 1

        for para in paragraphs:
            if not para.strip():
                current_line += para.count("\n") + 2
                continue

            para_with_sep = para + "\n\n"
            para_lines = para.count("\n") + 2

            # Check if adding this paragraph exceeds limit
            if (
                current_content
                and len(current_content) + len(para_with_sep) > config.max_chunk_size
            ):
                # Save current chunk
                if current_content.strip():
                    end_line = current_line - 1
                    chunks.append(
                        self._create_chunk(
                            current_content.rstrip(),
                            current_start_line,
                            end_line,
                            content_type="text",  # O2: Explicit content type
                        )
                    )

                # Start new chunk
                current_content = para_with_sep
                current_start_line = current_line
                current_line += para_lines
            else:
                current_content += para_with_sep
                current_line += para_lines

        # Save last chunk
        if current_content.strip():
            end_line = current_line - 1
            chunks.append(
                self._create_chunk(
                    current_content.rstrip(),
                    current_start_line,
                    max(end_line, current_start_line),
                    content_type="text",  # O2: Explicit content type
                )
            )

        return chunks

    def _apply_with_atomic_blocks(
        self,
        md_text: str,
        atomic_ranges: list[tuple[int, int, str]],
        config: ChunkConfig,
    ) -> list[Chunk]:
        """Apply fallback strategy preserving atomic blocks.

        Args:
            md_text: Full markdown text
            atomic_ranges: List of (start, end, type) for atomic blocks
            config: Chunking configuration

        Returns:
            List of chunks with atomic blocks preserved
        """
        lines = md_text.split("\n")
        chunks = []
        current_line = 1

        for block_start, block_end, block_type in atomic_ranges:
            # Handle text before atomic block
            if current_line < block_start:
                text_lines = lines[current_line - 1 : block_start - 1]
                text_content = "\n".join(text_lines)
                if text_content.strip():
                    # Split text by paragraphs
                    text_chunks = self._apply_simple_paragraph_split(text_content, config)
                    # Adjust line numbers
                    for chunk in text_chunks:
                        chunk.start_line += current_line - 1
                        chunk.end_line += current_line - 1
                    chunks.extend(text_chunks)

            # Handle atomic block
            block_lines = lines[block_start - 1 : block_end]
            block_content = "\n".join(block_lines)
            if block_content.strip():
                chunk = self._create_chunk(
                    block_content,
                    block_start,
                    block_end,
                    content_type=block_type,
                    is_atomic=True,
                )
                # Set oversize metadata if needed
                if chunk.size > config.max_chunk_size:
                    reason = (
                        "code_block_integrity"
                        if block_type == "code"
                        else ("table_integrity" if block_type == "table" else "latex_integrity")
                    )
                    self._set_oversize_metadata(chunk, reason, config)
                chunks.append(chunk)

            current_line = block_end + 1

        # Handle text after last atomic block
        if current_line <= len(lines):
            text_lines = lines[current_line - 1 :]
            text_content = "\n".join(text_lines)
            if text_content.strip():
                text_chunks = self._apply_simple_paragraph_split(text_content, config)
                # Adjust line numbers
                for chunk in text_chunks:
                    chunk.start_line += current_line - 1
                    chunk.end_line += current_line - 1
                chunks.extend(text_chunks)

        return chunks
