"""
Header processor for preventing dangling headers.

Detects and fixes situations where headers are separated from their content.

v2.1 Changes:
- Universal dangling header detection (not tied to specific header_path)
- Works for header levels 2-6 (## and deeper) - expanded from 3-6
- Reduced threshold from 50 to 30 characters
- Uses chunk_id instead of chunk_index for stable tracking
"""

import re
from dataclasses import dataclass

from .config import ChunkConfig
from .types import Chunk


@dataclass
class DanglingHeaderInfo:
    """Information about a detected dangling header."""

    chunk_index: int
    chunk_id: str | None  # Stable chunk_id for tracking
    header_text: str
    header_level: int
    header_line_in_chunk: int  # Line index within the chunk (0-based)


class DanglingHeaderDetector:
    """
    Detects dangling headers in chunk sequences.

    A dangling header is a header that appears at the end of a chunk
    while its content is in the next chunk.

    v2.1 Changes:
    - Detects levels 2-6 (expanded from 3-6)
    - Reduced threshold from 50 to 30 characters
    """

    # v2.1: Reduced from 50 to 30
    MIN_CONTENT_THRESHOLD = 30

    def __init__(self) -> None:
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

    def detect_dangling_headers_detailed(self, chunks: list[Chunk]) -> list[DanglingHeaderInfo]:
        """
        Detect dangling headers with detailed information.

        Args:
            chunks: List of chunks to analyze

        Returns:
            List of DanglingHeaderInfo for each detected dangling header
        """
        results = []

        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]

            info = self._get_dangling_header_info(current_chunk, next_chunk, i)
            if info:
                results.append(info)

        return results

    def _has_dangling_header(self, current_chunk: Chunk, next_chunk: Chunk) -> bool:
        """
        Check if current chunk has a dangling header.

        v2.1: Universal detection algorithm:
        1. Find the last non-empty line in current chunk
        2. Check if it's a header (level 2-6) - expanded from 3-6
        3. Check if next chunk starts with content (not a header of same/higher level)
        4. If next chunk has content for this header, it's dangling

        Args:
            current_chunk: Current chunk to check
            next_chunk: Next chunk in sequence

        Returns:
            True if current chunk has dangling header
        """
        # Find last non-empty line
        content = current_chunk.content.rstrip()
        lines = content.split("\n")

        last_line = None
        for line in reversed(lines):
            stripped = line.strip()
            if stripped:
                last_line = stripped
                break

        if not last_line:
            return False

        # Check if it's a header
        header_match = self.header_pattern.match(last_line)
        if not header_match:
            return False

        header_level = len(header_match.group(1))

        # v2.1: Consider levels 2-6 as potentially dangling (expanded from 3-6)
        # Level 1 is document title, usually not dangling
        if header_level < 2:
            return False

        # Check if there's minimal content after the header in current chunk
        # v2.1: Reduced threshold from 50 to 30
        content_after = self._get_content_after_last_header(lines)
        if len(content_after.strip()) > self.MIN_CONTENT_THRESHOLD:
            return False  # Has substantial content, not dangling

        # Check next chunk
        next_content = next_chunk.content.lstrip()
        if not next_content:
            return False

        next_first_line = next_content.split("\n")[0].strip()

        # If next chunk starts with a header of same or higher level, not dangling
        next_header_match = self.header_pattern.match(next_first_line)
        if next_header_match:
            next_level = len(next_header_match.group(1))
            if next_level <= header_level:
                return False  # Next chunk starts with same/higher level header

        # Next chunk has content that belongs to this header
        return len(next_content.strip()) >= 20

    def _get_dangling_header_info(
        self, current_chunk: Chunk, next_chunk: Chunk, chunk_index: int
    ) -> DanglingHeaderInfo | None:
        """
        Get detailed info about a dangling header if present.

        Args:
            current_chunk: Current chunk to check
            next_chunk: Next chunk in sequence
            chunk_index: Index of current chunk

        Returns:
            DanglingHeaderInfo if dangling header found, None otherwise
        """
        content = current_chunk.content.rstrip()
        lines = content.split("\n")

        # Find last non-empty line and its index
        last_line = None
        last_line_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped:
                last_line = stripped
                last_line_idx = i
                break

        if not last_line:
            return None

        header_match = self.header_pattern.match(last_line)
        if not header_match:
            return None

        header_level = len(header_match.group(1))
        header_text = header_match.group(2).strip()

        # v2.1: Detect levels 2-6 (expanded from 3-6)
        if header_level < 2:
            return None

        # Check content after header (v2.1: threshold 30)
        content_after = self._get_content_after_last_header(lines)
        if len(content_after.strip()) > self.MIN_CONTENT_THRESHOLD:
            return None

        # Check next chunk
        next_content = next_chunk.content.lstrip()
        if not next_content or len(next_content.strip()) < 20:
            return None

        next_first_line = next_content.split("\n")[0].strip()
        next_header_match = self.header_pattern.match(next_first_line)
        if next_header_match:
            next_level = len(next_header_match.group(1))
            if next_level <= header_level:
                return None

        return DanglingHeaderInfo(
            chunk_index=chunk_index,
            chunk_id=current_chunk.metadata.get("chunk_id"),  # v2.1: Stable ID
            header_text=header_text,
            header_level=header_level,
            header_line_in_chunk=last_line_idx,
        )

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

    v2.1 Changes:
    - Uses chunk_id instead of chunk_index for stable tracking
    - header_moved_from_id field instead of header_moved_from
    """

    def __init__(self, config: ChunkConfig):
        self.config = config

    def fix_dangling_header(
        self,
        chunks: list[Chunk],
        dangling_index: int,
        header_info: DanglingHeaderInfo | None = None,
    ) -> list[Chunk]:
        """
        Fix a dangling header by moving it or merging chunks.

        Strategy:
        1. Try to move header to the beginning of next chunk
        2. If that would exceed size limits, try to merge chunks
        3. If merging would exceed limits, leave as is but log warning

        Args:
            chunks: List of chunks
            dangling_index: Index of chunk with dangling header
            header_info: Optional detailed info about the dangling header

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

        # Handle edge case: if removing header leaves empty content
        if not new_current_content.strip():
            # Merge entire current chunk into next
            new_next_content = current_chunk.content.strip() + "\n\n" + next_chunk.content
            if len(new_next_content) <= self.config.max_chunk_size:
                new_next_chunk = Chunk(
                    content=new_next_content,
                    start_line=current_chunk.start_line,
                    end_line=next_chunk.end_line,
                    metadata=next_chunk.metadata.copy(),
                )
                new_next_chunk.metadata["dangling_header_fixed"] = True
                new_next_chunk.metadata["merge_reason"] = "dangling_header_prevention"
                # v2.1: Track with chunk_id (stable)
                self._track_header_moved_from(new_next_chunk, header_info)

                result = chunks.copy()
                result[dangling_index : dangling_index + 2] = [new_next_chunk]
                return result

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

            # v2.1: Update metadata with chunk_id tracking
            new_next_chunk.metadata["dangling_header_fixed"] = True
            self._track_header_moved_from(new_next_chunk, header_info)

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

                # v2.1: Update metadata with chunk_id tracking
                merged_chunk.metadata["dangling_header_fixed"] = True
                merged_chunk.metadata["merge_reason"] = "dangling_header_prevention"
                self._track_header_moved_from(merged_chunk, header_info)

                # Replace two chunks with one
                result = chunks.copy()
                result[dangling_index : dangling_index + 2] = [merged_chunk]

                return result

            else:
                # Cannot fix without exceeding size limits
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Cannot fix dangling header in chunk {dangling_index} "
                    f"without exceeding size limits. Header: {header_line[:50]}..."
                )
                return chunks

    def _track_header_moved_from(
        self, target_chunk: Chunk, header_info: DanglingHeaderInfo | None
    ) -> None:
        """
        Track the source chunk when a header is moved.

        v2.1: Uses chunk_id (stable) instead of chunk_index.
        Supports multiple moves by storing as list when needed.

        Args:
            target_chunk: The chunk receiving the moved header
            header_info: Info about the dangling header (contains chunk_id)
        """
        # v2.1: Use chunk_id for stable tracking
        source_id = header_info.chunk_id if header_info else None

        if source_id is None:
            # Fallback to index if no chunk_id available
            if header_info:
                source_id = str(header_info.chunk_index)
            else:
                return

        existing = target_chunk.metadata.get("header_moved_from_id")

        if existing is None:
            target_chunk.metadata["header_moved_from_id"] = source_id
        elif isinstance(existing, str):
            target_chunk.metadata["header_moved_from_id"] = [existing, source_id]
        elif isinstance(existing, list):
            target_chunk.metadata["header_moved_from_id"].append(source_id)


class HeaderProcessor:
    """
    Main component for preventing dangling headers.

    v2.1 Changes:
    - Universal detection for all sections
    - Levels 2-6 (expanded from 3-6)
    - Threshold 30 chars (reduced from 50)
    - chunk_id tracking (stable)
    """

    def __init__(self, config: ChunkConfig):
        self.config = config
        self.detector = DanglingHeaderDetector()
        self.mover = HeaderMover(config)

    def prevent_dangling_headers(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Prevent headers from being separated from their content.

        IMPORTANT: This is called BEFORE SectionSplitter, so headers
        are "attached" to their content before any splitting occurs.

        v2.1: Works for ALL sections (Scope, Impact, Leadership, etc.)
        Detects levels 2-6 with threshold 30 chars.

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
        max_iterations = 20  # Increased for complex documents
        iteration = 0

        while iteration < max_iterations:
            # Use detailed detection for better tracking
            dangling_infos = self.detector.detect_dangling_headers_detailed(result)

            if not dangling_infos:
                break  # No more dangling headers

            # Fix the first dangling header found
            # We fix one at a time because indices change after modifications
            info = dangling_infos[0]
            result = self.mover.fix_dangling_header(result, info.chunk_index, info)

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
