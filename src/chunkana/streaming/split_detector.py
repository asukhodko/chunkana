"""
Safe split point detection for streaming processing.

Detects optimal boundaries for splitting buffer windows.
"""

from typing import List, Optional

from .fence_tracker import FenceTracker


class SplitDetector:
    """
    Detect safe split points in buffer.

    Prioritizes semantic boundaries (headers, paragraphs) over arbitrary splits.
    """

    def __init__(self, threshold: float = 0.8):
        """
        Initialize split detector.

        Args:
            threshold: Start looking for split at this fraction of buffer
        """
        self.threshold = threshold

    def find_split_point(self, buffer: List[str], fence_tracker: FenceTracker) -> int:
        """
        Find safe split point in buffer.

        Priority:
        1. Line before header
        2. Paragraph boundary (double newline)
        3. Single newline outside fence
        4. Fallback: threshold position

        Args:
            buffer: Lines in buffer
            fence_tracker: Fence state tracker

        Returns:
            Index to split at (exclusive)
        """
        start_idx = int(len(buffer) * self.threshold)

        # Try header boundary
        idx = self._try_split_at_header(buffer, start_idx)
        if idx is not None:
            return idx

        # Try paragraph boundary
        idx = self._try_split_at_paragraph(buffer, start_idx)
        if idx is not None:
            return idx

        # Try newline outside fence
        idx = self._try_split_at_newline(buffer, start_idx, fence_tracker)
        if idx is not None:
            return idx

        # Fallback: split at threshold
        return self._fallback_split(start_idx)

    def _try_split_at_header(self, buffer: List[str], start_idx: int) -> Optional[int]:
        """Detect line before header."""
        for i in range(start_idx, len(buffer)):
            if i + 1 < len(buffer):
                next_line = buffer[i + 1]
                if next_line.strip().startswith("#"):
                    return i + 1
        return None

    def _try_split_at_paragraph(
        self, buffer: List[str], start_idx: int
    ) -> Optional[int]:
        """Detect paragraph boundary."""
        for i in range(start_idx, len(buffer) - 1):
            if not buffer[i].strip() and buffer[i + 1].strip():
                return i + 1
        return None

    def _try_split_at_newline(
        self, buffer: List[str], start_idx: int, fence_tracker: FenceTracker
    ) -> Optional[int]:
        """Detect newline outside fence."""
        tracker_copy = FenceTracker()
        for i, line in enumerate(buffer):
            tracker_copy.track_line(line)
            if i >= start_idx and not tracker_copy.is_inside_fence():
                if not line.strip():
                    return i + 1
        return None

    def _fallback_split(self, start_idx: int) -> int:
        """Fallback split at threshold."""
        return start_idx
