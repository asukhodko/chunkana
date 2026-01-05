"""
Header processor for preventing dangling headers.

Detects and fixes situations where headers are separated from their content.
"""

import re

from .config import ChunkConfig
from .types import Chunk


class DanglingHeaderDetector:
    """
    Detects dangling headers in chunk sequences.

    A dangling header is a header that appears at the end of a chunk
    while its content is in the next chunk.
    """

    def __init__(self):
        # Regex for detecting headers (ATX style)
        self.header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

    def detect_dangling_headers(self, chunks: list[Chunk]) -> list[int]:
        """
        Detect chunks with dangling headers.

        Args:
            chunks: List of chunks to analyze

        Returns:
            List of chunk indices that have dangling headers
        """
        dangling_indices = []

        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]

            if self._has_dangling_header(current_chunk, next_chunk):
                dangling_indices.append(i)

        return dangling_indices

    def _has_dangling_header(self, current_chunk: Chunk, next_chunk: Chunk) -> bool:
        """
        Check if current chunk has a dangling header.

        A header is dangling if:
        1. Current chunk ends with a header (level 4+ typically)
        2. Next chunk starts with content that belongs to that header
        3. The header has minimal or no content after it in current chunk

        Args:
            current_chunk: Current chunk to check
            next_chunk: Next chunk in sequence

        Returns:
            True if current chunk has dangling header
        """
        current_lines = current_chunk.content.strip().split("\n")
        next_lines = next_chunk.content.strip().split("\n")

        if not current_lines or not next_lines:
            return False

        # Check if current chunk ends with a header
        last_line = current_lines[-1].strip()
        header_match = self.header_pattern.match(last_line)

        if not header_match:
            return False

        header_level = len(header_match.group(1))  # Count # characters

        # Only consider level 4+ headers as potentially dangling
        # Level 1-3 headers are usually section boundaries
        if header_level < 4:
            return False

        # Check if there's minimal content after the header
        content_after_header = self._get_content_after_last_header(current_lines)

        # If there's substantial content after the header, it's not dangling
        if len(content_after_header.strip()) > 50:
            return False

        # Check if next chunk starts with content (not another header)
        first_next_line = next_lines[0].strip()
        if self.header_pattern.match(first_next_line):
            return False  # Next chunk starts with header, not content

        # Check if next chunk has content that could belong to the header
        next_content = next_chunk.content.strip()
        return len(next_content) >= 20

    def _get_content_after_last_header(self, lines: list[str]) -> str:
        """
        Get content after the last header in the lines.

        Args:
            lines: Lines of text

        Returns:
            Content after the last header
        """
        # Find the last header
        last_header_index = -1
        for i in range(len(lines) - 1, -1, -1):
            if self.header_pattern.match(lines[i].strip()):
                last_header_index = i
                break

        if last_header_index == -1:
            return "\n".join(lines)

        # Return content after the last header
        content_lines = lines[last_header_index + 1 :]
        return "\n".join(content_lines)


class HeaderMover:
    """
    Moves headers between chunks to fix dangling situations.
    """

    def __init__(self, config: ChunkConfig):
        self.config = config

    def fix_dangling_header(self, chunks: list[Chunk], dangling_index: int) -> list[Chunk]:
        """
        Fix a dangling header by moving it or merging chunks.

        Strategy:
        1. Try to move header to the beginning of next chunk
        2. If that would exceed size limits, try to merge chunks
        3. If merging would exceed limits, leave as is but log warning

        Args:
            chunks: List of chunks
            dangling_index: Index of chunk with dangling header

        Returns:
            Modified list of chunks
        """
        if dangling_index >= len(chunks) - 1:
            return chunks

        current_chunk = chunks[dangling_index]
        next_chunk = chunks[dangling_index + 1]

        # Extract the dangling header
        current_lines = current_chunk.content.strip().split("\n")
        header_line = current_lines[-1]

        # Remove header from current chunk
        new_current_content = "\n".join(current_lines[:-1]).strip()

        # Add header to beginning of next chunk
        new_next_content = header_line + "\n\n" + next_chunk.content

        # Check if next chunk would exceed size limit
        if len(new_next_content) <= self.config.max_chunk_size:
            # Move header to next chunk
            new_current_chunk = Chunk(
                content=new_current_content,
                start_line=current_chunk.start_line,
                end_line=current_chunk.end_line - 1,  # One less line
                metadata=current_chunk.metadata.copy(),
            )

            new_next_chunk = Chunk(
                content=new_next_content,
                start_line=next_chunk.start_line - 1,  # Include header line
                end_line=next_chunk.end_line,
                metadata=next_chunk.metadata.copy(),
            )

            # Update metadata
            new_next_chunk.metadata["dangling_header_fixed"] = True
            new_next_chunk.metadata["header_moved_from"] = current_chunk.metadata.get("chunk_id")

            # Replace chunks
            result = chunks.copy()
            result[dangling_index] = new_current_chunk
            result[dangling_index + 1] = new_next_chunk

            return result

        else:
            # Try merging chunks
            merged_content = current_chunk.content + "\n\n" + next_chunk.content

            if len(merged_content) <= self.config.max_chunk_size:
                # Merge chunks
                merged_chunk = Chunk(
                    content=merged_content,
                    start_line=current_chunk.start_line,
                    end_line=next_chunk.end_line,
                    metadata=current_chunk.metadata.copy(),
                )

                # Update metadata
                merged_chunk.metadata["dangling_header_fixed"] = True
                merged_chunk.metadata["merge_reason"] = "dangling_header_prevention"

                # Replace two chunks with one
                result = chunks.copy()
                result[dangling_index : dangling_index + 2] = [merged_chunk]

                return result

            else:
                # Cannot fix without exceeding size limits
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Cannot fix dangling header in chunk {current_chunk.metadata.get('chunk_id', 'unknown')} "
                    f"without exceeding size limits. Header: {header_line[:50]}..."
                )
                return chunks


class HeaderProcessor:
    """
    Main component for preventing dangling headers.
    """

    def __init__(self, config: ChunkConfig):
        self.config = config
        self.detector = DanglingHeaderDetector()
        self.mover = HeaderMover(config)

    def prevent_dangling_headers(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Prevent headers from being separated from their content.

        Args:
            chunks: List of chunks to process

        Returns:
            List of chunks with dangling headers fixed
        """
        if len(chunks) <= 1:
            return chunks

        result = chunks.copy()

        # Iteratively fix dangling headers
        # We need to iterate because fixing one dangling header might create another
        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            dangling_indices = self.detector.detect_dangling_headers(result)

            if not dangling_indices:
                break  # No more dangling headers

            # Fix the first dangling header found
            # We fix one at a time because indices change after modifications
            dangling_index = dangling_indices[0]
            result = self.mover.fix_dangling_header(result, dangling_index)

            iteration += 1

        if iteration >= max_iterations:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Reached maximum iterations ({max_iterations}) for dangling header fixes. "
                f"Some dangling headers may remain."
            )

        return result

    def update_header_paths(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Update header_path metadata after header movements.

        This ensures that header_path remains accurate after headers
        have been moved between chunks.

        Args:
            chunks: List of chunks to update

        Returns:
            List of chunks with updated header_path metadata
        """
        # This is a simplified implementation
        # In a full implementation, we would re-parse headers and rebuild paths

        for chunk in chunks:
            if chunk.metadata.get("dangling_header_fixed"):
                # Mark that header_path might need recalculation
                chunk.metadata["header_path_needs_update"] = True

        return chunks
