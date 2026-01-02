"""
Code context binding for enhanced code-aware chunking.

This module provides intelligent binding of code blocks to their surrounding
explanations, recognizing patterns like Before/After comparisons, Code+Output
pairs, and sequential examples.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .types import FencedBlock


class CodeBlockRole(Enum):
    """
    Role classification for code blocks.

    Identifies the purpose of a code block within documentation to enable
    intelligent grouping and context binding.
    """

    EXAMPLE = "example"  # Demonstrative code example
    SETUP = "setup"  # Preparatory/setup code
    OUTPUT = "output"  # Output/result display
    ERROR = "error"  # Error message/traceback
    BEFORE = "before"  # "Before" in before/after comparison
    AFTER = "after"  # "After" in before/after comparison
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class CodeContext:
    """
    Contextual information for a code block.

    Encapsulates all detected context for a code block including its role,
    surrounding explanations, and relationships to other code blocks.

    Attributes:
        code_block: The code block being analyzed
        role: Classified role of the code block
        explanation_before: Extracted text before the code block
        explanation_after: Extracted text after the code block
        related_blocks: Other code blocks that are semantically related
        output_block: Associated output block (if any)
    """

    code_block: FencedBlock
    role: CodeBlockRole
    explanation_before: Optional[str] = None
    explanation_after: Optional[str] = None
    related_blocks: List[FencedBlock] = None
    output_block: Optional[FencedBlock] = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.related_blocks is None:
            self.related_blocks = []


class CodeContextBinder:
    """
    Analyzes code blocks and binds them to contextual information.

    Implements pattern recognition for common documentation patterns:
    - Before/After code comparisons
    - Code + Output pairs
    - Sequential examples (Step 1, Step 2, ...)
    - Setup code vs. example code

    The binder extracts surrounding explanations and identifies relationships
    between code blocks to enable intelligent chunking.
    """

    # Compiled regex patterns for role detection
    SETUP_PATTERNS = [
        re.compile(r"first,?\s+(you\s+)?need\s+to", re.IGNORECASE),
        re.compile(r"install|import|require", re.IGNORECASE),
        re.compile(r"setup|configuration|initialize", re.IGNORECASE),
    ]

    OUTPUT_PATTERNS = [
        re.compile(r"^output:?\s*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^result:?\s*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^console:?\s*$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^stdout:?\s*$", re.IGNORECASE | re.MULTILINE),
    ]

    BEFORE_AFTER_PATTERNS = [
        re.compile(r"before[:\s]", re.IGNORECASE),
        re.compile(r"after[:\s]", re.IGNORECASE),
        re.compile(r"old\s+(?:code|version)", re.IGNORECASE),
        re.compile(r"new\s+(?:code|version)", re.IGNORECASE),
        re.compile(r"problematic", re.IGNORECASE),
        re.compile(r"fixed", re.IGNORECASE),
    ]

    def __init__(
        self,
        max_context_chars_before: int = 500,
        max_context_chars_after: int = 300,
        related_block_max_gap: int = 5,
        lines: Optional[List[str]] = None,
    ):
        """
        Initialize code context binder.

        Args:
            max_context_chars_before: Max chars to search backward for explanation
            max_context_chars_after: Max chars to search forward for explanation
            related_block_max_gap: Max line gap to consider blocks related
            lines: Pre-split document lines (O1 optimization, optional)
        """
        self.max_context_chars_before = max_context_chars_before
        self.max_context_chars_after = max_context_chars_after
        self.related_block_max_gap = related_block_max_gap
        self._cached_lines = lines  # O1: Store for reuse

    def bind_context(
        self,
        code_block: FencedBlock,
        md_text: str,
        all_blocks: List[FencedBlock],
    ) -> CodeContext:
        """
        Create full context binding for a code block.

        Args:
            code_block: The code block to analyze
            md_text: Full markdown document text
            all_blocks: All code blocks in the document

        Returns:
            CodeContext with role, explanations, and relationships
        """
        # Determine role
        role = self._determine_role(code_block, md_text)

        # Extract explanations
        explanation_before = self._extract_explanation_before(
            code_block, md_text, self.max_context_chars_before
        )
        explanation_after = self._extract_explanation_after(
            code_block, md_text, self.max_context_chars_after
        )

        # Find related blocks
        related_blocks = self._find_related_blocks(code_block, all_blocks, md_text)

        # Find output block
        output_block = self._find_output_block(code_block, all_blocks, md_text)

        return CodeContext(
            code_block=code_block,
            role=role,
            explanation_before=explanation_before,
            explanation_after=explanation_after,
            related_blocks=related_blocks,
            output_block=output_block,
        )

    def _determine_role(self, block: FencedBlock, md_text: str) -> CodeBlockRole:
        """
        Determine the role of a code block.

        Args:
            block: Code block to classify
            md_text: Full markdown document text

        Returns:
            Classified role
        """
        # Check cached role first
        cached_role = self._get_cached_role(block)
        if cached_role:
            return cached_role

        # Check language tag
        role_from_lang = self._classify_by_language(block)
        if role_from_lang:
            return role_from_lang

        # Check preceding text patterns
        preceding = self._get_preceding_text(block, md_text, chars=100)
        role_from_pattern = self._classify_by_pattern(preceding)
        if role_from_pattern:
            return role_from_pattern

        # Default to example
        return CodeBlockRole.EXAMPLE

    def _get_cached_role(self, block: FencedBlock) -> Optional[CodeBlockRole]:
        """Get cached role from block if available."""
        if hasattr(block, "context_role") and block.context_role:
            try:
                return CodeBlockRole(block.context_role)
            except ValueError:
                pass
        return None

    def _classify_by_language(self, block: FencedBlock) -> Optional[CodeBlockRole]:
        """Classify code block by language tag."""
        if not block.language:
            return None

        lang_lower = block.language.lower()
        if lang_lower in ["output", "console", "stdout", "result"]:
            return CodeBlockRole.OUTPUT
        if lang_lower in ["error", "traceback"]:
            return CodeBlockRole.ERROR

        return None

    def _classify_by_pattern(self, preceding: str) -> Optional[CodeBlockRole]:
        """Classify code block by patterns in preceding text."""
        # Check for output patterns
        for pattern in self.OUTPUT_PATTERNS:
            if pattern.search(preceding):
                return CodeBlockRole.OUTPUT

        # Check for setup patterns
        for pattern in self.SETUP_PATTERNS:
            if pattern.search(preceding):
                return CodeBlockRole.SETUP

        # Check for before/after patterns
        for pattern in self.BEFORE_AFTER_PATTERNS:
            match = pattern.search(preceding)
            if match:
                return self._classify_before_after(match.group())

        return None

    def _classify_before_after(self, matched_text: str) -> CodeBlockRole:
        """Determine if matched text indicates BEFORE or AFTER."""
        text_lower = matched_text.lower()
        if "before" in text_lower or "old" in text_lower or "problematic" in text_lower:
            return CodeBlockRole.BEFORE
        if "after" in text_lower or "new" in text_lower or "fixed" in text_lower:
            return CodeBlockRole.AFTER
        return CodeBlockRole.EXAMPLE

    def _get_preceding_text(self, block: FencedBlock, md_text: str, chars: int) -> str:
        """
        Get text immediately before a code block.

        Args:
            block: Code block
            md_text: Full markdown text
            chars: Number of characters to extract

        Returns:
            Preceding text (trimmed to chars)
        """
        # O1: Use cached lines if available
        lines = (
            self._cached_lines
            if self._cached_lines is not None
            else md_text.split("\n")
        )

        if block.start_line < 1 or block.start_line > len(lines):
            return ""

        # Get line before code block fence (1-indexed)
        end_line_idx = block.start_line - 2  # Convert to 0-indexed, go before fence
        if end_line_idx < 0:
            return ""

        start_line_idx = max(0, end_line_idx - 5)  # Look back up to 5 lines

        text_lines = lines[start_line_idx : end_line_idx + 1]
        text = "\n".join(text_lines)

        # Trim to requested chars
        if len(text) > chars:
            text = text[-chars:]

        return text.strip()

    def _extract_explanation_before(
        self, code_block: FencedBlock, md_text: str, max_chars: int
    ) -> Optional[str]:
        """
        Extract explanation text before a code block.

        Args:
            code_block: Code block to find explanation for
            md_text: Full markdown text
            max_chars: Maximum characters to extract

        Returns:
            Extracted explanation or None
        """
        # O1: Use cached lines if available
        lines = (
            self._cached_lines
            if self._cached_lines is not None
            else md_text.split("\n")
        )

        # Start from line before code block fence
        end_line_idx = code_block.start_line - 2  # 0-indexed, exclude fence
        if end_line_idx < 0:
            return None

        start_line_idx = max(0, end_line_idx - 10)  # Look back up to 10 lines

        # Extract text
        text_lines = lines[start_line_idx : end_line_idx + 1]
        text = "\n".join(text_lines)

        # Trim to max_chars, respecting sentence boundaries
        if len(text) > max_chars:
            text = text[-max_chars:]
            # Find first sentence boundary
            sentence_start = text.find(". ")
            if sentence_start > 0:
                text = text[sentence_start + 2 :]

        text = text.strip()
        return text if text else None

    def _extract_explanation_after(
        self, code_block: FencedBlock, md_text: str, max_chars: int
    ) -> Optional[str]:
        """
        Extract explanation text after a code block.

        Args:
            code_block: Code block to find explanation for
            md_text: Full markdown text
            max_chars: Maximum characters to extract

        Returns:
            Extracted explanation or None
        """
        # O1: Use cached lines if available
        lines = (
            self._cached_lines
            if self._cached_lines is not None
            else md_text.split("\n")
        )

        # Start from line after code block closing fence
        start_line_idx = code_block.end_line  # 0-indexed (end_line is 1-indexed)
        if start_line_idx >= len(lines):
            return None

        end_line_idx = min(
            len(lines) - 1, start_line_idx + 10
        )  # Look ahead up to 10 lines

        # Extract text
        text_lines = lines[start_line_idx : end_line_idx + 1]
        text = "\n".join(text_lines)

        # Trim to max_chars, respecting sentence boundaries
        if len(text) > max_chars:
            text = text[:max_chars]
            # Find last sentence boundary
            sentence_end = text.rfind(". ")
            if sentence_end > 0:
                text = text[: sentence_end + 1]

        text = text.strip()
        return text if text else None

    def _find_related_blocks(
        self,
        block: FencedBlock,
        all_blocks: List[FencedBlock],
        md_text: str,
    ) -> List[FencedBlock]:
        """
        Find code blocks related to the given block.

        Args:
            block: Code block to find relations for
            all_blocks: All code blocks in document
            md_text: Full markdown text

        Returns:
            List of related blocks
        """
        related: List[FencedBlock] = []

        try:
            block_idx = all_blocks.index(block)
        except ValueError:
            return related

        # Check previous block
        if block_idx > 0:
            prev_block = all_blocks[block_idx - 1]
            if self._are_related(block, prev_block, md_text):
                related.append(prev_block)

        # Check next block
        if block_idx < len(all_blocks) - 1:
            next_block = all_blocks[block_idx + 1]
            if self._are_related(block, next_block, md_text):
                related.append(next_block)

        return related

    def _are_related(
        self,
        block1: FencedBlock,
        block2: FencedBlock,
        md_text: str,
    ) -> bool:
        """
        Check if two code blocks are semantically related.

        Args:
            block1: First code block
            block2: Second code block
            md_text: Full markdown text

        Returns:
            True if blocks are related
        """
        # Calculate gap
        gap = abs(block1.end_line - block2.start_line)

        # Criterion 1: Same language and close proximity
        if block1.language == block2.language and gap <= self.related_block_max_gap:
            return True

        # Criterion 2: Before/After pairing
        role1 = self._determine_role(block1, md_text)
        role2 = self._determine_role(block2, md_text)

        if (role1 == CodeBlockRole.BEFORE and role2 == CodeBlockRole.AFTER) or (
            role1 == CodeBlockRole.AFTER and role2 == CodeBlockRole.BEFORE
        ):
            return True

        # Criterion 3: Code/Output pairing (check both directions)
        if (
            role1 in [CodeBlockRole.EXAMPLE, CodeBlockRole.SETUP]
            and role2 == CodeBlockRole.OUTPUT
            and gap <= 6
        ):
            return True

        if (
            role2 in [CodeBlockRole.EXAMPLE, CodeBlockRole.SETUP]
            and role1 == CodeBlockRole.OUTPUT
            and gap <= 6
        ):
            return True

        return False

    def _find_output_block(
        self,
        block: FencedBlock,
        all_blocks: List[FencedBlock],
        md_text: str,
    ) -> Optional[FencedBlock]:
        """
        Find associated output block for a code block.

        Args:
            block: Code block to find output for
            all_blocks: All code blocks in document
            md_text: Full markdown text

        Returns:
            Output block if found, None otherwise
        """
        # Only look for output if this is an example or setup block
        role = self._determine_role(block, md_text)
        if role not in [CodeBlockRole.EXAMPLE, CodeBlockRole.SETUP]:
            return None

        try:
            block_idx = all_blocks.index(block)
        except ValueError:
            return None

        # Check next block
        if block_idx >= len(all_blocks) - 1:
            return None

        next_block = all_blocks[block_idx + 1]
        return self._check_if_output_block(block, next_block, md_text)

    def _check_if_output_block(
        self,
        block: FencedBlock,
        next_block: FencedBlock,
        md_text: str,
    ) -> Optional[FencedBlock]:
        """Check if next block is an output block for current block."""
        next_role = self._determine_role(next_block, md_text)
        gap = abs(block.end_line - next_block.start_line)

        # If next block is classified as OUTPUT and close enough
        if next_role == CodeBlockRole.OUTPUT and gap <= 6:
            return next_block

        # Check if empty-language block with "Output:" in between
        if (not next_block.language or next_block.language == "") and gap <= 6:
            if self._has_output_marker_between(block, next_block, md_text):
                return next_block

        return None

    def _has_output_marker_between(
        self, block: FencedBlock, next_block: FencedBlock, md_text: str
    ) -> bool:
        """Check if "Output:" marker exists between two blocks."""
        lines = md_text.split("\n")
        if block.end_line >= len(lines) or next_block.start_line < 2:
            return False

        between_start = block.end_line
        between_end = next_block.start_line - 2

        if between_start > between_end or between_end >= len(lines):
            return False

        between_text = "\n".join(lines[between_start : between_end + 1])
        return any(pattern.search(between_text) for pattern in self.OUTPUT_PATTERNS)
