"""
Configuration for streaming processing.
"""

from dataclasses import dataclass


@dataclass
class StreamingConfig:
    """
    Configuration for streaming chunker.

    Attributes:
        buffer_size: Maximum bytes per buffer window (default: 100KB)
        overlap_lines: Lines to keep as context between buffers (default: 20)
        max_memory_mb: Memory usage ceiling in megabytes (default: 100)
        safe_split_threshold: Where to start looking for split point (default: 0.8)
    """

    buffer_size: int = 100_000
    overlap_lines: int = 20
    max_memory_mb: int = 100
    safe_split_threshold: float = 0.8
