"""
Base strategy class for markdown_chunker v2.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..config import ChunkConfig
from ..types import Chunk, ContentAnalysis, LatexType

if TYPE_CHECKING:
    from ..table_grouping import TableGroup


class BaseStrategy(ABC):
    """
    Abstract base class for chunking strategies.

    All strategies must implement:
    - name: Strategy identifier
    - priority: Selection priority (1 = highest)
    - can_handle: Whether strategy can handle the document
    - apply: Apply strategy to produce chunks
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name identifier."""
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """Selection priority (1 = highest)."""
        pass

    @abstractmethod
    def can_handle(self, analysis: ContentAnalysis, config: ChunkConfig) -> bool:
        """
        Check if this strategy can handle the document.

        Args:
            analysis: Document analysis results
            config: Chunking configuration

        Returns:
            True if strategy can handle the document
        """
        pass

    @abstractmethod
    def apply(self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig) -> list[Chunk]:
        """
        Apply strategy to produce chunks.

        Args:
            md_text: Normalized markdown text
            analysis: Document analysis results
            config: Chunking configuration

        Returns:
            List of chunks
        """
        pass

    def _create_chunk(
        self, content: str, start_line: int, end_line: int, **metadata: object
    ) -> Chunk:
        """
        Create a chunk with strategy metadata.

        Args:
            content: Chunk content
            start_line: Starting line (1-indexed)
            end_line: Ending line (1-indexed)
            **metadata: Additional metadata

        Returns:
            Chunk instance
        """
        meta = {"strategy": self.name, **metadata}
        return Chunk(
            content=content,
            start_line=start_line,
            end_line=end_line,
            metadata=meta,
        )

    def _set_oversize_metadata(self, chunk: Chunk, reason: str, config: ChunkConfig) -> None:
        """
        Set metadata for oversize chunks.

        Called by strategy when creating a chunk that exceeds
        max_chunk_size for a valid reason (preserving atomic blocks).

        Args:
            chunk: Chunk to mark
            reason: Reason for oversize (code_block_integrity,
                table_integrity, section_integrity)
            config: Configuration for size check
        """
        VALID_REASONS = {
            "code_block_integrity",
            "table_integrity",
            "section_integrity",
            "latex_integrity",
            "related_code_group",
        }

        if reason not in VALID_REASONS:
            raise ValueError(f"Invalid oversize_reason: {reason}. Must be one of {VALID_REASONS}")

        if chunk.size > config.max_chunk_size:
            chunk.metadata["allow_oversize"] = True
            chunk.metadata["oversize_reason"] = reason

    def _ensure_fence_balance(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Ensure all chunks have balanced code fences.

        If a chunk has unbalanced fences, try to merge with adjacent chunk.
        If merge fails, mark with fence_balance_error.

        Args:
            chunks: List of chunks to check

        Returns:
            List of chunks with balanced fences (or error flags)
        """
        result = []
        i = 0

        while i < len(chunks):
            chunk = chunks[i]
            fence_count = chunk.content.count("```")

            if fence_count % 2 == 0:
                # Balanced - keep as is
                result.append(chunk)
                i += 1
            else:
                # Unbalanced - try to merge with next chunk
                if i + 1 < len(chunks):
                    merged_content = chunk.content + "\n" + chunks[i + 1].content
                    merged_fence_count = merged_content.count("```")

                    if merged_fence_count % 2 == 0:
                        # Merge restored balance
                        merged_chunk = self._create_chunk(
                            content=merged_content,
                            start_line=chunk.start_line,
                            end_line=chunks[i + 1].end_line,
                            merged_for_fence_balance=True,
                        )
                        result.append(merged_chunk)
                        i += 2
                        continue

                # Merge didn't help - mark error
                chunk.metadata["fence_balance_error"] = True
                chunk.metadata["fence_count"] = fence_count
                result.append(chunk)
                i += 1

        return result

    def _get_atomic_blocks_in_range(
        self, start_line: int, end_line: int, analysis: ContentAnalysis
    ) -> list[tuple[int, int, str]]:
        """
        Get atomic blocks (code, table, LaTeX) within a line range.

        Shared helper for strategies that need to preserve atomic blocks
        when splitting sections.

        Args:
            start_line: Range start (1-indexed, inclusive)
            end_line: Range end (1-indexed, inclusive)
            analysis: Document analysis with extracted blocks

        Returns:
            List of (block_start, block_end, block_type) tuples
        """
        atomic_ranges: list[tuple[int, int, str]] = []

        # Add code blocks in range
        for code_block in analysis.code_blocks:
            if start_line <= code_block.start_line <= end_line:
                atomic_ranges.append((code_block.start_line, code_block.end_line, "code"))

        # Add table blocks in range
        for table_block in analysis.tables:
            if start_line <= table_block.start_line <= end_line:
                atomic_ranges.append((table_block.start_line, table_block.end_line, "table"))

        # Add LaTeX blocks in range (only if configured)
        for latex_block in analysis.latex_blocks:
            if start_line <= latex_block.start_line <= end_line and latex_block.latex_type in (
                LatexType.DISPLAY,
                LatexType.ENVIRONMENT,
            ):
                atomic_ranges.append((latex_block.start_line, latex_block.end_line, "latex"))

        # Sort by start line
        atomic_ranges.sort(key=lambda x: x[0])

        return atomic_ranges

    def _split_text_to_size(self, text: str, start_line: int, config: ChunkConfig) -> list[Chunk]:
        """
        Split text into chunks respecting size limits.

        Splits at paragraph boundaries when possible.

        Args:
            text: Text to split
            start_line: Starting line number
            config: Configuration

        Returns:
            List of chunks
        """
        if len(text) <= config.max_chunk_size:
            if text.strip():
                end_line = start_line + text.count("\n")
                return [self._create_chunk(text, start_line, end_line)]
            return []

        chunks = []
        paragraphs = text.split("\n\n")

        current_content = ""
        current_start = start_line

        for para in paragraphs:
            para_with_sep = para + "\n\n" if para != paragraphs[-1] else para

            if len(current_content) + len(para_with_sep) <= config.max_chunk_size:
                current_content += para_with_sep
            else:
                # Save current chunk
                if current_content.strip():
                    # Calculate end_line from actual content
                    end_line = current_start + current_content.rstrip().count("\n")
                    chunks.append(
                        self._create_chunk(
                            current_content.rstrip(),
                            current_start,
                            end_line,
                        )
                    )
                    # Next chunk starts after the current chunk's last line
                    current_start = end_line + 1

                # Start new chunk
                current_content = para_with_sep

        # Save last chunk
        if current_content.strip():
            # Calculate end_line from actual content
            end_line = current_start + current_content.rstrip().count("\n")
            chunks.append(
                self._create_chunk(
                    current_content.rstrip(),
                    current_start,
                    end_line,
                )
            )

        return chunks

    def _get_table_groups(
        self,
        analysis: ContentAnalysis,
        lines: list[str],
        config: ChunkConfig,
    ) -> list["TableGroup"]:
        """
        Get table groups based on configuration.

        If table grouping is enabled, groups related tables.
        Otherwise, returns each table as a single-table group.

        Args:
            analysis: Document analysis with tables and headers
            lines: Document lines array
            config: Chunking configuration

        Returns:
            List of TableGroup objects

        Requirements: 5.1, 5.2, 5.3, 5.4
        """
        from ..table_grouping import TableGroup

        if not analysis.tables:
            return []

        grouper = config.get_table_grouper()

        if grouper is not None:
            # Table grouping enabled - use grouper
            return grouper.group_tables(analysis.tables, lines, analysis.headers)
        else:
            # Table grouping disabled - each table is its own group
            groups = []
            for table in analysis.tables:
                content = "\n".join(lines[table.start_line - 1 : table.end_line])
                group = TableGroup(
                    tables=[table],
                    start_line=table.start_line,
                    end_line=table.end_line,
                    content=content,
                )
                groups.append(group)
            return groups

    def _process_table_groups(
        self,
        table_groups: list["TableGroup"],
        config: ChunkConfig,
    ) -> list[Chunk]:
        """
        Create chunks from table groups.

        Sets appropriate metadata for grouped tables.

        Args:
            table_groups: Groups from _get_table_groups
            config: Chunking configuration

        Returns:
            List of chunks with table group metadata

        Requirements: 4.1, 4.2, 4.3
        """
        chunks = []

        for group in table_groups:
            chunk = self._create_chunk(
                content=group.content,
                start_line=group.start_line,
                end_line=group.end_line,
                content_type="table",
                is_atomic=True,
            )

            # Add table group metadata
            if group.table_count > 1:
                chunk.metadata["is_table_group"] = True
                chunk.metadata["table_group_count"] = group.table_count

            # Set oversize metadata if needed
            if chunk.size > config.max_chunk_size:
                self._set_oversize_metadata(chunk, "table_integrity", config)

            chunks.append(chunk)

        return chunks
