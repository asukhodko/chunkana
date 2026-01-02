"""
Buffer management for streaming processing.

Handles file reading and buffer window management.
"""

import io
from typing import Iterator, List, Tuple

from .config import StreamingConfig


class BufferManager:
    """
    Manage buffer windows for streaming.

    Reads file in chunks and maintains overlap between windows.
    """

    def __init__(self, config: StreamingConfig):
        """
        Initialize buffer manager.

        Args:
            config: Streaming configuration
        """
        self.config = config

    def read_windows(
        self, stream: io.TextIOBase
    ) -> Iterator[Tuple[List[str], List[str], int]]:
        """
        Read buffer windows from stream.

        Yields:
            Tuple of (buffer_lines, overlap_lines, bytes_processed)
        """
        buffer: List[str] = []
        buffer_size = 0
        overlap_buffer: List[str] = []
        bytes_processed = 0

        for line in stream:
            buffer.append(line)
            buffer_size += len(line)
            bytes_processed += len(line)

            if buffer_size >= self.config.buffer_size:
                yield (buffer, overlap_buffer, bytes_processed)
                overlap_buffer = self._extract_overlap(buffer)
                buffer = []
                buffer_size = 0

        # Process remaining buffer
        if buffer:
            yield (buffer, overlap_buffer, bytes_processed)

    def _extract_overlap(self, buffer: List[str]) -> List[str]:
        """Extract overlap lines from buffer end."""
        n = self.config.overlap_lines
        if len(buffer) <= n:
            return buffer[:]
        return buffer[-n:]
