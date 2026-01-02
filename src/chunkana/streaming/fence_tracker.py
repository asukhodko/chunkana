"""
Fence tracking for streaming processing.

Tracks code fence state across buffer windows to prevent mid-block splits.
"""

import re
from typing import Optional, Tuple


class FenceTracker:
    """
    Track code fence state across buffer boundaries.

    Maintains fence stack to detect when inside code blocks.
    """

    def __init__(self):
        """Initialize fence tracker."""
        self._fence_stack: list[Tuple[str, int]] = []
        self._fence_pattern = re.compile(r"^(\s*)(`{3,}|~{3,})(\w*)\s*$")

    def track_line(self, line: str) -> None:
        """
        Update fence state from line.

        Args:
            line: Line to analyze
        """
        if self._fence_stack:
            char, length = self._fence_stack[-1]
            if self._is_closing(line, char, length):
                self._fence_stack.pop()
                return

        fence_info = self._is_opening(line)
        if fence_info:
            self._fence_stack.append(fence_info)

    def is_inside_fence(self) -> bool:
        """Check if currently inside fence."""
        return len(self._fence_stack) > 0

    def get_fence_info(self) -> Optional[Tuple[str, int]]:
        """Get current fence details if inside fence."""
        if self._fence_stack:
            return self._fence_stack[-1]
        return None

    def reset(self) -> None:
        """Clear fence state."""
        self._fence_stack.clear()

    def _is_opening(self, line: str) -> Optional[Tuple[str, int]]:
        """Detect fence opening."""
        match = self._fence_pattern.match(line)
        if match:
            fence_chars = match.group(2)
            return (fence_chars[0], len(fence_chars))
        return None

    def _is_closing(self, line: str, char: str, length: int) -> bool:
        """Detect fence closing."""
        pattern = rf"^(\s*)({re.escape(char)}{{{length},}})\s*$"
        return bool(re.match(pattern, line))
