"""
Section splitter for handling oversize chunks.

Splits chunks that exceed max_chunk_size while preserving header context.

CRITICAL: This module is called AFTER HeaderProcessor.prevent_dangling_headers(),
so chunks already contain their headers when splitting occurs.

v2.1 Changes:
- Header stack extraction (all consecutive headers at chunk start)
- Pack-until-full algorithm with header repetition
- Proper metadata for continued chunks

v2.2 Changes (Line Numbers Fix):
- SegmentWithPosition dataclass for tracking segment positions
- Accurate line number calculation for split chunks
- _find_segments_with_positions() for position-aware segment finding
- _create_chunk_with_lines() for accurate line number assignment
- Line numbers reflect content-only (not including overlap)

Line Number Semantics:
- start_line: First line of chunk.content in original document
- end_line: Last line of chunk.content in original document
- Split chunks have different, ordered line numbers
- Non-split chunks maintain original line numbers unchanged
"""

import re
from dataclasses import dataclass

from .config import ChunkConfig
from .types import Chunk


@dataclass
class SegmentWithPosition:
    """Segment with its position in the original document."""

    content: str
    start_line_offset: int  # Offset from original chunk start
    end_line_offset: int  # Offset from original chunk start
    original_text: str  # For debugging/validation


@dataclass
class SplitResult:
    """Result of splitting a chunk."""

    chunks: list[Chunk]
    was_split: bool
    original_size: int
    num_parts: int


class SectionSplitter:
    """
    Splits oversize sections while preserving header context.

    IMPORTANT: Called AFTER HeaderProcessor.prevent_dangling_headers(),
    so chunks already contain their headers.

    Split strategy priority:
    1. By list items (numbered or bulleted)
    2. By paragraphs (\\n\\n)
    3. By sentences (fallback)

    Each continuation chunk repeats the header_stack from the original.
    """

    def __init__(self, config: ChunkConfig):
        self.config = config
        self.min_content_after_header = 100

        # Patterns for splitting
        self.header_pattern = re.compile(r"^#{1,6}\s+", re.MULTILINE)
        self.list_item_pattern = re.compile(r"^(\d+\.|[-*+])\s+", re.MULTILINE)

    def split_oversize_sections(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Split chunks that exceed max_chunk_size.

        Args:
            chunks: List of chunks (already processed by HeaderProcessor)

        Returns:
            List of chunks with oversize sections split
        """
        result = []

        for chunk in chunks:
            if self._needs_splitting(chunk):
                split_chunks = self._split_chunk(chunk)
                result.extend(split_chunks)
            else:
                result.append(chunk)

        return result

    def _needs_splitting(self, chunk: Chunk) -> bool:
        """Check if chunk needs to be split."""
        if len(chunk.content) <= self.config.max_chunk_size:
            return False

        # Don't split atomic blocks (code, tables)
        if self._is_atomic_block(chunk):
            return False

        # Don't split if already marked as valid oversize
        if chunk.metadata.get("allow_oversize"):
            reason = chunk.metadata.get("oversize_reason", "")
            if reason in ("code_block_integrity", "table_integrity"):
                return False

        return True

    def _find_segments_with_positions(
        self, body: str, original: Chunk
    ) -> list[SegmentWithPosition]:
        """
        Find segments with their line positions in the original document.

        Strategy:
        1. Split body into segments (existing logic)
        2. For each segment, find its position in original content
        3. Calculate line offsets from original.start_line

        Args:
            body: Body text (without header_stack)
            original: Original chunk being split

        Returns:
            List of segments with position information
        """
        # Handle empty body (header-only chunks)
        if not body.strip():
            return []

        # Use existing segment finding logic
        segments = self._find_segments(body)

        # Filter out empty segments
        segments = [s for s in segments if s.strip()]

        if len(segments) <= 1:
            return []

        # Calculate positions for segments
        return self._calculate_segment_positions(segments, body, original)

    def _calculate_segment_positions(
        self, segments: list[str], body: str, original: Chunk
    ) -> list[SegmentWithPosition]:
        """
        Calculate line positions for segments.

        Algorithm:
        1. Find body start line in original content
        2. For each segment:
           a. Find segment start position in body
           b. Count lines from body start to segment start
           c. Count lines in segment
           d. Calculate absolute line numbers

        Args:
            segments: List of segment strings
            body: Body text (without header_stack)
            original: Original chunk being split

        Returns:
            List of segments with position information
        """
        result = []
        body_start_line = self._find_body_start_line(original.content)

        current_pos = 0
        for i, segment in enumerate(segments):
            # Find segment in body
            segment_start = body.find(segment, current_pos)
            if segment_start == -1:
                # Fallback: use sequential positioning
                if i == 0:
                    segment_start = 0
                else:
                    # Estimate position based on previous segments
                    prev_segments_length = sum(
                        len(s) + 2 for s in segments[:i]
                    )  # +2 for separators
                    segment_start = min(prev_segments_length, len(body))

            # Count lines from body start to segment start
            lines_before = body[:segment_start].count("\n")
            lines_in_segment = segment.count("\n")

            # Calculate line offsets from original chunk start
            start_line_offset = body_start_line + lines_before
            end_line_offset = start_line_offset + lines_in_segment

            result.append(
                SegmentWithPosition(
                    content=segment,
                    start_line_offset=start_line_offset,
                    end_line_offset=end_line_offset,
                    original_text=segment,
                )
            )

            current_pos = segment_start + len(segment)

        return result

    def _find_body_start_line(self, content: str) -> int:
        """
        Find the line offset where body starts in original content.

        Body starts after all consecutive headers at the beginning.

        Args:
            content: Original chunk content

        Returns:
            Line offset from content start where body begins
        """
        lines = content.split("\n")
        body_start_idx = 0
        in_header_section = True

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                # Empty line - continue if we're still in header section
                continue

            if stripped.startswith("#") and in_header_section:
                body_start_idx = i + 1
            else:
                # First non-header, non-empty line - end of header section
                in_header_section = False
                body_start_idx = i
                break

        return body_start_idx

    def _is_atomic_block(self, chunk: Chunk) -> bool:
        """Check if chunk is an atomic block (code or table)."""
        content_type = chunk.metadata.get("content_type", "")
        if content_type in ("code", "table"):
            return True

        # Also check content directly
        content = chunk.content.strip()

        # Code block detection
        if content.startswith("```") and content.endswith("```"):
            return True

        # Table detection (has | and ---)
        if "|" in content and "---" in content:
            lines = content.split("\n")
            table_lines = [line for line in lines if "|" in line]
            if len(table_lines) >= 2:
                return True

        return False

    def _split_chunk(self, chunk: Chunk) -> list[Chunk]:
        """
        Split a chunk with header_stack repetition and accurate line numbers.

        Args:
            chunk: Chunk to split

        Returns:
            List of split chunks with accurate line numbers
        """
        header_stack, body = self._extract_header_stack_and_body(chunk.content)

        if not body.strip():
            # No body to split, return original
            return [chunk]

        segments_with_positions = self._find_segments_with_positions(body, chunk)

        if len(segments_with_positions) <= 1:
            # Cannot split further, mark as oversize
            chunk.metadata["allow_oversize"] = True
            chunk.metadata["oversize_reason"] = "list_item_integrity"
            return [chunk]

        return self._pack_segments_into_chunks_with_lines(
            chunk, header_stack, segments_with_positions
        )

    def _extract_header_stack_and_body(self, content: str) -> tuple[str, str]:
        """
        Extract header_stack (all consecutive headers at start) and body.

        Header_stack is the sequence of consecutive header lines at the
        beginning of content (skipping empty lines between headers).

        Example:
            "## Impact\\n\\n#### Итоги работы\\n\\n1. First item..."
            → header_stack = "## Impact\\n\\n#### Итоги работы"
            → body = "1. First item..."

        Args:
            content: Chunk content

        Returns:
            Tuple of (header_stack, body)
        """
        lines = content.split("\n")
        header_lines: list[str] = []
        body_start_idx = 0
        in_header_section = True

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                # Empty line - continue if we're still in header section
                if in_header_section and header_lines:
                    header_lines.append("")  # Preserve empty line between headers
                continue

            if stripped.startswith("#") and in_header_section:
                header_lines.append(line)
                body_start_idx = i + 1
            else:
                # First non-header, non-empty line - end of header section
                in_header_section = False
                body_start_idx = i
                break

        # Remove trailing empty lines from header_stack
        while header_lines and not header_lines[-1].strip():
            header_lines.pop()

        header_stack = "\n".join(header_lines) if header_lines else ""
        body = "\n".join(lines[body_start_idx:]).strip()

        return header_stack, body

    def _find_segments(self, body: str) -> list[str]:
        """
        Find segments for splitting.

        Priority:
        1. List items (numbered or bulleted)
        2. Paragraphs (separated by \\n\\n)
        3. Sentences (fallback)

        Args:
            body: Body text to segment

        Returns:
            List of segments
        """
        # Try list items first
        list_segments = self._split_by_list_items(body)
        if len(list_segments) > 1:
            return list_segments

        # Try paragraphs
        para_segments = self._split_by_paragraphs(body)
        if len(para_segments) > 1:
            return para_segments

        # Fallback to sentences
        return self._split_by_sentences(body)

    def _split_by_list_items(self, body: str) -> list[str]:
        """
        Split by list items (numbered or bulleted).

        Args:
            body: Body text

        Returns:
            List of segments (each starting with a list marker)
        """
        matches = list(self.list_item_pattern.finditer(body))

        if len(matches) <= 1:
            return [body]

        segments = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            segment = body[start:end].strip()
            if segment:
                segments.append(segment)

        return segments if segments else [body]

    def _split_by_paragraphs(self, body: str) -> list[str]:
        """
        Split by paragraphs (double newline).

        Args:
            body: Body text

        Returns:
            List of paragraph segments
        """
        paragraphs = re.split(r"\n\n+", body)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_by_sentences(self, body: str) -> list[str]:
        """
        Split by sentences (fallback).

        Args:
            body: Body text

        Returns:
            List of sentence segments
        """
        # Simple sentence splitting on . ! ?
        sentences = re.split(r"(?<=[.!?])\s+", body)
        return [s.strip() for s in sentences if s.strip()]

    def _pack_segments_into_chunks_with_lines(
        self, original: Chunk, header_stack: str, segments: list[SegmentWithPosition]
    ) -> list[Chunk]:
        """
        Pack segments into chunks with header_stack repetition and accurate line numbers.

        Algorithm "pack until full":
        1. Accumulate segments while they fit
        2. When next segment doesn't fit, create chunk and start new one
        3. Each chunk (except first) starts with header_stack

        Args:
            original: Original chunk being split
            header_stack: Headers to repeat in continuation chunks
            segments: List of segments with positions to pack

        Returns:
            List of packed chunks with accurate line numbers
        """
        # Calculate available space for body
        header_size = len(header_stack) + 2 if header_stack else 0  # +2 for \n\n
        max_body_size = self.config.max_chunk_size - header_size

        # Ensure we have reasonable space for body
        if max_body_size < 100:
            max_body_size = self.config.max_chunk_size // 2

        chunks: list[Chunk] = []
        current_segments: list[SegmentWithPosition] = []
        current_size = 0
        chunk_index = 0

        for segment in segments:
            segment_size = len(segment.content) + 2  # +2 for separator

            # Check if segment fits in current chunk
            if current_size + segment_size <= max_body_size:
                current_segments.append(segment)
                current_size += segment_size
            else:
                # Create chunk from accumulated segments
                if current_segments:
                    chunks.append(
                        self._create_chunk_with_lines(
                            original, header_stack, current_segments, chunk_index
                        )
                    )
                    chunk_index += 1

                # Start new chunk with this segment
                if segment_size <= max_body_size:
                    current_segments = [segment]
                    current_size = segment_size
                else:
                    # Segment too large - create oversize chunk
                    chunks.append(
                        self._create_chunk_with_lines(
                            original,
                            header_stack,
                            [segment],
                            chunk_index,
                            allow_oversize=True,
                            oversize_reason="list_item_integrity",
                        )
                    )
                    chunk_index += 1
                    current_segments = []
                    current_size = 0

        # Create final chunk from remaining segments
        if current_segments:
            chunks.append(
                self._create_chunk_with_lines(original, header_stack, current_segments, chunk_index)
            )

        return chunks if chunks else [original]

    def _pack_segments_into_chunks(
        self, original: Chunk, header_stack: str, segments: list[str]
    ) -> list[Chunk]:
        """
        Pack segments into chunks with header_stack repetition.

        Algorithm "pack until full":
        1. Accumulate segments while they fit
        2. When next segment doesn't fit, create chunk and start new one
        3. Each chunk (except first) starts with header_stack

        Args:
            original: Original chunk being split
            header_stack: Headers to repeat in continuation chunks
            segments: List of segments to pack

        Returns:
            List of packed chunks
        """
        # Calculate available space for body
        header_size = len(header_stack) + 2 if header_stack else 0  # +2 for \n\n
        max_body_size = self.config.max_chunk_size - header_size

        # Ensure we have reasonable space for body
        if max_body_size < 100:
            max_body_size = self.config.max_chunk_size // 2

        chunks: list[Chunk] = []
        current_segments: list[str] = []
        current_size = 0
        chunk_index = 0

        for segment in segments:
            segment_size = len(segment) + 2  # +2 for separator

            # Check if segment fits in current chunk
            if current_size + segment_size <= max_body_size:
                current_segments.append(segment)
                current_size += segment_size
            else:
                # Create chunk from accumulated segments
                if current_segments:
                    chunks.append(
                        self._create_chunk(original, header_stack, current_segments, chunk_index)
                    )
                    chunk_index += 1

                # Start new chunk with this segment
                if segment_size <= max_body_size:
                    current_segments = [segment]
                    current_size = segment_size
                else:
                    # Segment too large - create oversize chunk
                    chunks.append(
                        self._create_chunk(
                            original,
                            header_stack,
                            [segment],
                            chunk_index,
                            allow_oversize=True,
                            oversize_reason="list_item_integrity",
                        )
                    )
                    chunk_index += 1
                    current_segments = []
                    current_size = 0

        # Create final chunk from remaining segments
        if current_segments:
            chunks.append(self._create_chunk(original, header_stack, current_segments, chunk_index))

        return chunks if chunks else [original]

    def _create_chunk_with_lines(
        self,
        original: Chunk,
        header_stack: str,
        segments: list[SegmentWithPosition],
        index: int,
        allow_oversize: bool = False,
        oversize_reason: str = "",
    ) -> Chunk:
        """
        Create chunk with accurate line numbers.

        Line number calculation:
        - start_line: First segment's start_line
        - end_line: Last segment's end_line
        - Accounts for header_stack repetition in continuation chunks

        Args:
            original: Original chunk being split
            header_stack: Headers to prepend (for continuation chunks)
            segments: Body segments with position info for this chunk
            index: Split index (0 = first chunk)
            allow_oversize: Whether to mark as oversize
            oversize_reason: Reason for oversize

        Returns:
            New Chunk with accurate line numbers
        """
        if not segments:
            return original

        # Calculate content line range
        start_line_offset = min(seg.start_line_offset for seg in segments)
        end_line_offset = max(seg.end_line_offset for seg in segments)

        # Calculate absolute line numbers
        start_line = original.start_line + start_line_offset
        end_line = original.start_line + end_line_offset

        # Build content
        body = "\n\n".join(seg.content for seg in segments)
        if header_stack and index > 0:
            # Continuation chunk - repeat header_stack
            content = f"{header_stack}\n\n{body}"
            continued = True
        elif header_stack:
            # First chunk - header_stack already present
            content = f"{header_stack}\n\n{body}"
            continued = False
        else:
            content = body
            continued = False  # No header_stack means no continuation

        # Copy and update metadata
        metadata = original.metadata.copy()
        metadata["continued_from_header"] = continued
        metadata["split_index"] = index
        metadata["original_section_size"] = len(original.content)

        if allow_oversize:
            metadata["allow_oversize"] = True
            metadata["oversize_reason"] = oversize_reason

        return Chunk(
            content=content,
            start_line=start_line,
            end_line=end_line,
            metadata=metadata,
        )

    def _create_chunk(
        self,
        original: Chunk,
        header_stack: str,
        segments: list[str],
        index: int,
        allow_oversize: bool = False,
        oversize_reason: str = "",
    ) -> Chunk:
        """
        Create a chunk with header_stack.

        Args:
            original: Original chunk being split
            header_stack: Headers to prepend (for continuation chunks)
            segments: Body segments for this chunk
            index: Split index (0 = first chunk)
            allow_oversize: Whether to mark as oversize
            oversize_reason: Reason for oversize

        Returns:
            New Chunk
        """
        body = "\n\n".join(segments)

        if header_stack and index > 0:
            # Continuation chunk - repeat header_stack
            content = f"{header_stack}\n\n{body}"
            continued = True
        elif header_stack:
            # First chunk - header_stack already present
            content = f"{header_stack}\n\n{body}"
            continued = False
        else:
            content = body
            continued = False  # No header_stack means no continuation

        # Copy and update metadata
        metadata = original.metadata.copy()
        metadata["continued_from_header"] = continued
        metadata["split_index"] = index
        metadata["original_section_size"] = len(original.content)

        if allow_oversize:
            metadata["allow_oversize"] = True
            metadata["oversize_reason"] = oversize_reason

        return Chunk(
            content=content,
            start_line=original.start_line,
            end_line=original.end_line,
            metadata=metadata,
        )
