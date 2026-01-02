"""
List-aware strategy for markdown_chunker v2.

For documents with high list content (changelogs, feature lists, task lists).
Preserves list hierarchies and binds context paragraphs.
"""

import re
from typing import List, Optional, Tuple

from ..config import ChunkConfig
from ..types import Chunk, ContentAnalysis, ListBlock, ListItem, ListType
from .base import BaseStrategy


class ListAwareStrategy(BaseStrategy):
    """
    Strategy for list-heavy documents.

    Activation criteria:
    - For documents WITHOUT strong structure:
      list_ratio > list_ratio_threshold (default 0.4)
      OR list_count >= list_count_threshold (default 5)

    - For documents WITH strong structure (many headers, deep hierarchy):
      list_ratio > list_ratio_threshold (default 0.4)
      AND list_count >= list_count_threshold (default 5)

    This prevents list_aware from interfering with structural strategy
    for hierarchical documents that happen to contain some lists.

    Core features:
    - Preserves nested list hierarchies
    - Binds introduction paragraphs to lists
    - Groups related list items
    - Respects size limits while maintaining structure

    Priority: 2 (after CodeAware, before Structural)
    """

    @property
    def name(self) -> str:
        return "list_aware"

    @property
    def priority(self) -> int:
        return 2

    def can_handle(self, analysis: ContentAnalysis, config: ChunkConfig) -> bool:
        """
        Can handle if document is list-heavy.

        Strategy:
        - For documents with strong structural hierarchy (many headers),
          require BOTH list_ratio and list_count thresholds to avoid
          interfering with structural strategy
        - For documents without strong structure, use OR logic

        Args:
            analysis: Document analysis results
            config: Chunking configuration

        Returns:
            True if document is list-heavy enough for this strategy
        """
        # Check if document has strong structural hierarchy
        # A document is considered "strongly structural" if it has:
        # - Sufficient headers (>= structure_threshold)
        # - Deep hierarchy (max_header_depth > 1)
        # - Headers significantly outnumber lists (header_count / list_count > 5)
        has_strong_structure = (
            analysis.header_count >= config.structure_threshold
            and analysis.max_header_depth > 1
            and analysis.list_count > 0
            and (analysis.header_count / analysis.list_count) > 5
        )

        if has_strong_structure:
            # For structural documents, require BOTH conditions
            # Lists must be both numerous AND dominant
            return (
                analysis.list_ratio > config.list_ratio_threshold
                and analysis.list_count >= config.list_count_threshold
            )
        else:
            # For non-structural documents, use OR logic (original behavior)
            return (
                analysis.list_ratio > config.list_ratio_threshold
                or analysis.list_count >= config.list_count_threshold
            )

    def apply(
        self, md_text: str, analysis: ContentAnalysis, config: ChunkConfig
    ) -> List[Chunk]:
        """Apply list-aware chunking strategy."""
        if not md_text.strip():
            return []

        # O1: Use cached lines from analysis (fallback for backward compatibility)
        lines = analysis.get_lines()
        if lines is None:
            lines = md_text.split("\n")

        list_blocks = analysis.list_blocks
        headers = analysis.headers

        if not list_blocks:
            return self._split_text_to_size(md_text, 1, config)

        chunks = self._process_all_list_blocks(lines, list_blocks, headers, config)
        chunks = self._process_remaining_text(
            chunks, lines, list_blocks, headers, config
        )
        return chunks

    def _process_all_list_blocks(
        self,
        lines: List[str],
        list_blocks: List,
        headers: List,
        config: ChunkConfig,
    ) -> List[Chunk]:
        """Process all list blocks and text between them."""
        chunks: List[Chunk] = []
        current_line = 1
        processed_blocks = set()  # Track processed blocks to prevent duplication

        for block in list_blocks:
            # Skip if this block was already processed (e.g., with introduction)
            if id(block) in processed_blocks:
                continue

            # Handle content before list block
            if current_line < block.start_line:
                block_processed, chunks, current_line = self._process_text_before_list(
                    chunks, lines, current_line, block, config, headers
                )
                if block_processed:
                    processed_blocks.add(id(block))
                    continue

            # Handle list block
            chunks, current_line = self._process_list_block(
                chunks, lines, block, config, headers
            )
            processed_blocks.add(id(block))

        return chunks

    def _process_remaining_text(
        self,
        chunks: List[Chunk],
        lines: List[str],
        list_blocks: List,
        headers: List,
        config: ChunkConfig,
    ) -> List[Chunk]:
        """Process any remaining text after the last list block."""
        if not list_blocks:
            return chunks

        last_block = list_blocks[-1]
        current_line = last_block.end_line + 1

        # Handle content after last list
        if current_line <= len(lines):
            text_after = "\n".join(lines[current_line - 1 :])
            if text_after.strip():
                text_chunks = self._split_text_to_size(text_after, current_line, config)
                # Add header_path to text chunks after lists
                for chunk in text_chunks:
                    self._add_header_path_to_chunk(chunk, headers, chunk.start_line)
                chunks.extend(text_chunks)

        return chunks

    def _process_text_before_list(
        self,
        chunks: List[Chunk],
        lines: List[str],
        current_line: int,
        block: ListBlock,
        config: ChunkConfig,
        headers: List,
    ) -> Tuple[bool, List[Chunk], int]:
        """Process text before a list block.

        Returns:
            Tuple of (block_was_processed, chunks, next_line)
            - block_was_processed: True if the list block was included with introduction
            - chunks: Updated chunks list
            - next_line: Next line to process
        """
        text_before = "\n".join(lines[current_line - 1 : block.start_line - 1])
        if not text_before.strip():
            return False, chunks, current_line

        intro_context = self._extract_introduction_context(text_before, block, config)
        if intro_context:
            # Try to bind introduction with list
            list_content = self._reconstruct_list_block(block, lines)
            combined = intro_context + "\n\n" + list_content

            if len(combined) <= config.max_chunk_size:
                chunk = self._create_list_chunk(
                    combined,
                    current_line,
                    block.end_line,
                    block,
                    has_context_binding=True,
                )
                # Add header_path to chunk
                self._add_header_path_to_chunk(chunk, headers, current_line)
                chunks.append(chunk)
                # Return True to indicate block was processed
                return True, chunks, block.end_line + 1

        # Process text separately
        text_chunks = self._split_text_to_size(text_before, current_line, config)
        # Add header_path to text chunks
        for chunk in text_chunks:
            self._add_header_path_to_chunk(chunk, headers, chunk.start_line)
        chunks.extend(text_chunks)
        # Return False to indicate block needs separate processing
        return False, chunks, block.start_line

    def _process_list_block(
        self,
        chunks: List[Chunk],
        lines: List[str],
        block: ListBlock,
        config: ChunkConfig,
        headers: List,
    ) -> Tuple[List[Chunk], int]:
        """Process a list block."""
        list_content = self._reconstruct_list_block(block, lines)

        if len(list_content) <= config.max_chunk_size:
            chunk = self._create_list_chunk(
                list_content,
                block.start_line,
                block.end_line,
                block,
                has_context_binding=False,
            )
            # Add header_path to chunk
            self._add_header_path_to_chunk(chunk, headers, block.start_line)
            chunks.append(chunk)
        else:
            list_chunks = self._split_list_preserving_hierarchy(block, lines, config)
            # Add header_path to all split chunks
            for chunk in list_chunks:
                self._add_header_path_to_chunk(chunk, headers, chunk.start_line)
            chunks.extend(list_chunks)

        return chunks, block.end_line + 1

    def _extract_introduction_context(
        self, text_before: str, list_block: ListBlock, config: ChunkConfig
    ) -> Optional[str]:
        """
        Extract introduction paragraph if present.

        Introduction patterns:
        - Ends with colon
        - Contains phrases: "following", "include", "such as"
        - Short enough (< 200 chars)
        - Within 2 lines of list start

        Note: LaTeX formulas in introduction paragraphs are naturally
        preserved as part of the paragraph text (no special handling needed).

        Args:
            text_before: Text preceding the list
            list_block: The list block to check
            config: Configuration

        Returns:
            Introduction text or None
        """
        paragraphs = text_before.split("\n\n")
        if not paragraphs:
            return None

        last_para = paragraphs[-1].strip()

        # Check if too long
        if len(last_para) > 200:
            return None

        # Check introduction patterns
        intro_patterns = [
            r":\s*$",  # Ends with colon
            r"(?i)\b(the following|includes?|such as|these)\b",
        ]

        for pattern in intro_patterns:
            if re.search(pattern, last_para):
                return last_para

        return None

    def _reconstruct_list_block(self, block: ListBlock, lines: List[str]) -> str:
        """
        Reconstruct markdown list from ListBlock.

        Args:
            block: ListBlock to reconstruct
            lines: All document lines

        Returns:
            Markdown text of the list
        """
        # Use original lines for reconstruction to preserve formatting
        list_lines = lines[block.start_line - 1 : block.end_line]
        return "\n".join(list_lines)

    def _split_list_preserving_hierarchy(
        self, block: ListBlock, lines: List[str], config: ChunkConfig
    ) -> List[Chunk]:
        """
        Split large list block while preserving hierarchy.

        Strategy:
        - Split at top-level items (depth 0)
        - Keep parent with all children
        - If single top-level item is too large, mark as oversize

        Args:
            block: ListBlock to split
            lines: All document lines
            config: Configuration

        Returns:
            List of chunks
        """
        chunks: List[Chunk] = []
        current_items: List[ListItem] = []
        current_start_line = None

        for i, item in enumerate(block.items):
            # Start new group at top-level items
            if item.depth == 0 and current_items:
                # Check if current group fits
                group_text, actual_end_line = self._reconstruct_item_group(
                    current_items, lines, block
                )

                if len(group_text) <= config.max_chunk_size:
                    chunk = self._create_list_chunk(
                        group_text,
                        current_start_line,
                        actual_end_line,
                        block,
                        has_context_binding=False,
                    )
                    chunks.append(chunk)
                else:
                    # Single top-level item group exceeds limit - mark oversize
                    chunk = self._create_list_chunk(
                        group_text,
                        current_start_line,
                        actual_end_line,
                        block,
                        has_context_binding=False,
                    )
                    self._set_oversize_metadata(
                        chunk, "list_hierarchy_integrity", config
                    )
                    chunks.append(chunk)

                # Start new group
                current_items = [item]
                current_start_line = item.line_number
            else:
                # Add to current group
                if not current_items:
                    current_start_line = item.line_number
                current_items.append(item)

        # Handle last group
        if current_items:
            group_text, actual_end_line = self._reconstruct_item_group(
                current_items, lines, block
            )

            if len(group_text) <= config.max_chunk_size:
                chunk = self._create_list_chunk(
                    group_text,
                    current_start_line,
                    actual_end_line,
                    block,
                    has_context_binding=False,
                )
                chunks.append(chunk)
            else:
                chunk = self._create_list_chunk(
                    group_text,
                    current_start_line,
                    actual_end_line,
                    block,
                    has_context_binding=False,
                )
                self._set_oversize_metadata(chunk, "list_hierarchy_integrity", config)
                chunks.append(chunk)

        return chunks

    def _reconstruct_item_group(
        self, items: List[ListItem], lines: List[str], block: ListBlock
    ) -> Tuple[str, int]:
        """
        Reconstruct markdown for a group of list items.

        Args:
            items: Items to reconstruct
            lines: All document lines
            block: Parent list block (used to determine end boundary)

        Returns:
            Tuple of (markdown_text, actual_end_line)
        """
        if not items:
            return "", 0

        start_line = items[0].line_number

        # Find the actual end line including continuation lines
        # If this is the last item in the block, use block's end_line
        # Otherwise, use the line before the next item starts
        last_item_line = items[-1].line_number

        # Find where this group actually ends
        if last_item_line == block.items[-1].line_number:
            # This is the last item in the block, use block's end line
            end_line = block.end_line
        else:
            # Find the next item after our last item
            last_item_idx = block.items.index(items[-1])
            if last_item_idx + 1 < len(block.items):
                next_item = block.items[last_item_idx + 1]
                # End just before the next item starts
                end_line = next_item.line_number - 1
            else:
                # Shouldn't happen, but fallback to block end
                end_line = block.end_line

        group_lines = lines[start_line - 1 : end_line]
        return "\n".join(group_lines), end_line

    def _create_list_chunk(
        self,
        content: str,
        start_line: int,
        end_line: int,
        list_block: ListBlock,
        has_context_binding: bool,
    ) -> Chunk:
        """
        Create chunk with list-specific metadata.

        Args:
            content: Chunk content
            start_line: Starting line
            end_line: Ending line
            list_block: Source list block
            has_context_binding: Whether introduction is included

        Returns:
            Chunk with metadata
        """
        # Collect list types
        list_types = set(item.list_type.value for item in list_block.items)

        # Checkbox stats if applicable
        checkbox_stats = None
        if list_block.list_type == ListType.CHECKBOX:
            checkbox_items = [
                item for item in list_block.items if item.list_type == ListType.CHECKBOX
            ]
            if checkbox_items:
                total = len(checkbox_items)
                checked = sum(1 for item in checkbox_items if item.is_checked)
                unchecked = total - checked
                checkbox_stats = {
                    "total": total,
                    "checked": checked,
                    "unchecked": unchecked,
                }

        return self._create_chunk(
            content,
            start_line,
            end_line,
            content_type="list",
            has_nested_lists=list_block.has_nested,
            max_list_depth=list_block.max_depth,
            list_item_count=list_block.item_count,
            has_context_binding=has_context_binding,
            context_type="introduction" if has_context_binding else None,
            list_types=list(list_types),
            checkbox_stats=checkbox_stats,
            hierarchy_preserved=True,
            header_path="",  # Will be filled by _add_header_path_to_chunk
        )

    def _add_header_path_to_chunk(
        self, chunk: Chunk, headers: List, start_line: int
    ) -> None:
        """Add header_path metadata to a chunk.

        Builds header hierarchy path similar to structural strategy.
        Format: "/Level1/Level2/Level3" (string, not list)

        Args:
            chunk: Chunk to add header_path to
            headers: All headers from document analysis
            start_line: Starting line of the chunk
        """
        # Build header stack from headers BEFORE chunk start
        header_stack: List = []

        for header in headers:
            # Only consider headers BEFORE chunk start
            if header.line >= start_line:
                break

            # Build hierarchy: new header replaces same/higher levels
            while header_stack and header_stack[-1].level >= header.level:
                header_stack.pop()
            header_stack.append(header)

        # Build header_path as string (path-like format)
        if header_stack:
            chunk.metadata["header_path"] = "/" + "/".join(h.text for h in header_stack)
        else:
            chunk.metadata["header_path"] = ""

        # Set header_level (deepest level in path)
        chunk.metadata["header_level"] = header_stack[-1].level if header_stack else 0
