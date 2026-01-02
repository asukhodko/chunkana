"""
Streaming chunker for large markdown files.

Provides memory-efficient chunking through buffered processing.
"""

import io
from typing import Iterator, List, Optional

from ..chunker import MarkdownChunker
from ..config import ChunkConfig
from ..types import Chunk
from .buffer_manager import BufferManager
from .config import StreamingConfig
from .split_detector import SplitDetector


class StreamingChunker:
    """
    Stream-based markdown chunker for large files.

    Processes files in buffer windows to limit memory usage.
    """

    def __init__(
        self,
        chunk_config: ChunkConfig,
        streaming_config: Optional[StreamingConfig] = None,
    ):
        """
        Initialize streaming chunker.

        Args:
            chunk_config: Chunking configuration
            streaming_config: Streaming configuration (uses defaults if None)
        """
        self.chunk_config = chunk_config
        self.streaming_config = streaming_config or StreamingConfig()
        self.base_chunker = MarkdownChunker(chunk_config)
        self.buffer_manager = BufferManager(self.streaming_config)
        self.split_detector = SplitDetector(self.streaming_config.safe_split_threshold)

    def chunk_file(self, file_path: str) -> Iterator[Chunk]:
        """
        Chunk file in streaming mode.

        Args:
            file_path: Path to markdown file

        Yields:
            Chunk objects
        """
        with open(file_path, "r", encoding="utf-8") as f:
            yield from self.chunk_stream(f)

    def chunk_stream(self, stream: io.TextIOBase) -> Iterator[Chunk]:
        """
        Chunk stream in streaming mode.

        Args:
            stream: Text stream to process

        Yields:
            Chunk objects with streaming metadata
        """
        chunk_index = 0
        window_index = 0

        for buffer, overlap, bytes_processed in self.buffer_manager.read_windows(
            stream
        ):
            # Process window
            for chunk in self._process_window(
                buffer, overlap, window_index, chunk_index
            ):
                chunk.metadata["stream_chunk_index"] = chunk_index
                chunk.metadata["stream_window_index"] = window_index
                chunk.metadata["bytes_processed"] = bytes_processed
                yield chunk
                chunk_index += 1

            window_index += 1

    def _process_window(
        self,
        buffer: List[str],
        overlap: List[str],
        window_index: int,
        start_chunk_index: int,
    ) -> Iterator[Chunk]:
        """Process buffer window."""
        # Combine overlap with buffer
        full_lines = overlap + buffer
        text = "".join(full_lines)

        if not text.strip():
            return

        # Chunk window using base chunker
        chunks = self.base_chunker.chunk(text)

        # Yield chunks
        for chunk in chunks:
            yield chunk
