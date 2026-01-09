"""
Invariant validator for chunking quality.

Validates that chunking results meet quality invariants:
1. No dangling headers (levels 1-6)
2. No invalid oversize chunks
3. Content coverage (recall-based metric)

v2.1 Changes:
- Recall-based coverage metric (not inflated by repetition/overlap)
- Dangling header check for ALL levels 1-6
- Removed section_integrity from valid oversize reasons
"""

import re
from dataclasses import dataclass, field

from .config import ChunkConfig
from .types import Chunk


@dataclass
class ValidationResult:
    """Result of invariant validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    coverage: float = 1.0  # Recall of original lines

    # Detailed info
    dangling_header_indices: list[int] = field(default_factory=list)
    invalid_oversize_indices: list[int] = field(default_factory=list)


class InvariantValidator:
    """
    Validates chunking quality invariants.

    Checks:
    1. No dangling headers (levels 1-6 for invariant check)
    2. No oversize without valid reason (code_block, table, list_item)
    3. Content coverage >= 95% (recall of original lines)

    Note: HeaderProcessor detects levels 2-6 for fixing,
    but invariant check covers ALL levels 1-6.
    """

    # Valid reasons for oversize chunks
    VALID_OVERSIZE_REASONS = {"code_block_integrity", "table_integrity", "list_item_integrity"}

    # Minimum line length for coverage calculation
    MIN_LINE_LENGTH = 20

    def __init__(self, config: ChunkConfig, strict: bool = False):
        """
        Initialize validator.

        Args:
            config: Chunk configuration
            strict: If True, dangling headers are errors; if False, warnings
        """
        self.config = config
        self.strict = strict
        self.header_pattern = re.compile(r"^#{1,6}\s+")  # All levels 1-6

    def validate(self, chunks: list[Chunk], original_text: str) -> ValidationResult:
        """
        Validate all invariants.

        Args:
            chunks: List of chunks to validate
            original_text: Original markdown text

        Returns:
            ValidationResult with errors, warnings, and coverage
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Invariant 1: No dangling headers (ALL levels 1-6)
        dangling_indices = self._check_no_dangling_headers(chunks)
        if dangling_indices:
            msg = f"Found {len(dangling_indices)} dangling headers at chunks: {dangling_indices}"
            if self.strict:
                errors.append(msg)
            else:
                warnings.append(msg)

        # Invariant 2: No invalid oversize
        oversize_indices = self._check_no_invalid_oversize(chunks)
        if oversize_indices:
            msg = f"Found {len(oversize_indices)} invalid oversize chunks: {oversize_indices}"
            if self.strict:
                errors.append(msg)
            else:
                warnings.append(msg)

        # Invariant 3: Content coverage (recall)
        coverage = self._calculate_line_recall(chunks, original_text)
        if coverage < 0.95:
            msg = f"Content coverage {coverage:.1%} < 95%"
            warnings.append(msg)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            coverage=coverage,
            dangling_header_indices=dangling_indices,
            invalid_oversize_indices=oversize_indices,
        )

    def _check_no_dangling_headers(self, chunks: list[Chunk]) -> list[int]:
        """
        Check for dangling headers (levels 1-6).

        A dangling header is a header at the end of a chunk
        without substantial content following it.

        Args:
            chunks: List of chunks

        Returns:
            List of chunk indices with dangling headers
        """
        dangling_indices = []

        for i in range(len(chunks) - 1):
            content = chunks[i].content.rstrip()
            lines = content.split("\n")

            # Find last non-empty line
            last_line = None
            for line in reversed(lines):
                if line.strip():
                    last_line = line.strip()
                    break

            if last_line and self.header_pattern.match(last_line):
                dangling_indices.append(i)

        return dangling_indices

    def _check_no_invalid_oversize(self, chunks: list[Chunk]) -> list[int]:
        """
        Check for oversize chunks without valid reason.

        Valid reasons: code_block_integrity, table_integrity, list_item_integrity
        REMOVED: section_integrity (was allowing text/list oversize)

        Args:
            chunks: List of chunks

        Returns:
            List of chunk indices with invalid oversize
        """
        invalid_indices = []

        for i, chunk in enumerate(chunks):
            if len(chunk.content) > self.config.max_chunk_size:
                reason = chunk.metadata.get("oversize_reason", "")
                if reason not in self.VALID_OVERSIZE_REASONS:
                    invalid_indices.append(i)

        return invalid_indices

    def _calculate_line_recall(self, chunks: list[Chunk], original: str) -> float:
        """
        Calculate recall of original lines.

        Metric: fraction of original lines (length >= 20 chars)
        that appear in at least one chunk.

        This is a fair metric that is NOT inflated by:
        - Header repetition
        - Overlap
        - Content duplication

        Args:
            chunks: List of chunks
            original: Original text

        Returns:
            Recall value (0.0 to 1.0)
        """

        def normalize(s: str) -> str:
            """Normalize whitespace for comparison."""
            return " ".join(s.split())

        # Collect significant lines from original
        original_lines: list[str] = []
        for line in original.split("\n"):
            normalized = normalize(line)
            if len(normalized) >= self.MIN_LINE_LENGTH:
                original_lines.append(normalized)

        if not original_lines:
            return 1.0

        # Collect all text from chunks (normalized)
        chunks_text = normalize(" ".join(c.content for c in chunks))

        # Count how many original lines are found
        found = 0
        for line in original_lines:
            if line in chunks_text:
                found += 1

        return found / len(original_lines)

    def validate_no_dangling(self, chunks: list[Chunk]) -> bool:
        """
        Quick check for dangling headers only.

        Args:
            chunks: List of chunks

        Returns:
            True if no dangling headers found
        """
        return len(self._check_no_dangling_headers(chunks)) == 0

    def validate_size_bounds(self, chunks: list[Chunk]) -> bool:
        """
        Quick check for size bounds only.

        Args:
            chunks: List of chunks

        Returns:
            True if all chunks within bounds or have valid oversize reason
        """
        return len(self._check_no_invalid_oversize(chunks)) == 0
