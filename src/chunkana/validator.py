"""
Validator for markdown_chunker v2.

Validates chunking results against domain properties PROP-1 through PROP-5.

**Feature: architecture-redesign**
"""

from dataclasses import dataclass

from .config import ChunkConfig
from .types import Chunk


@dataclass
class ValidationResult:
    """Result of validation."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        return cls(is_valid=True, errors=[], warnings=[])

    @classmethod
    def failure(cls, errors: list[str], warnings: list[str] | None = None) -> "ValidationResult":
        return cls(is_valid=False, errors=errors, warnings=warnings or [])


class Validator:
    """
    Validates chunking results against domain properties.

    Properties checked:
    - PROP-1: No Content Loss
    - PROP-2: Size Bounds
    - PROP-3: Monotonic Ordering
    - PROP-4: No Empty Chunks
    - PROP-5: Valid Line Numbers
    """

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()

    def validate(
        self, chunks: list[Chunk], original_text: str, strict: bool = False
    ) -> ValidationResult:
        """
        Validate chunks against all domain properties.

        Args:
            chunks: List of chunks to validate
            original_text: Original markdown text
            strict: If True, treat warnings as errors

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # PROP-1: No Content Loss
        prop1_result = self._check_no_content_loss(chunks, original_text)
        if prop1_result:
            if strict:
                errors.append(prop1_result)
            else:
                warnings.append(prop1_result)

        # PROP-2: Size Bounds
        prop2_errors = self._check_size_bounds(chunks)
        errors.extend(prop2_errors)

        # PROP-3: Monotonic Ordering
        prop3_error = self._check_monotonic_ordering(chunks)
        if prop3_error:
            errors.append(prop3_error)

        # PROP-4: No Empty Chunks
        prop4_errors = self._check_no_empty_chunks(chunks)
        errors.extend(prop4_errors)

        # PROP-5: Valid Line Numbers
        prop5_errors = self._check_valid_line_numbers(chunks, original_text)
        errors.extend(prop5_errors)

        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult(is_valid=True, errors=[], warnings=warnings)

    def _check_no_content_loss(self, chunks: list[Chunk], original_text: str) -> str | None:
        """
        PROP-1: No Content Loss

        The total content in chunks should approximately equal original.
        Allows some variance due to overlap and whitespace normalization.
        """
        if not chunks:
            if original_text.strip():
                return "PROP-1: No chunks produced for non-empty input"
            return None

        total_output = sum(len(c.content) for c in chunks)
        total_input = len(original_text)

        # Allow 10% variance
        if total_output < total_input * 0.9:
            ratio = total_output / total_input if total_input > 0 else 0
            return f"PROP-1: Content loss detected ({ratio:.1%} of original)"

        return None

    def _check_size_bounds(self, chunks: list[Chunk]) -> list[str]:
        """
        PROP-2: Size Bounds

        All chunks should respect max_chunk_size unless marked as oversize.
        """
        errors = []

        for i, chunk in enumerate(chunks):
            if chunk.size > self.config.max_chunk_size:
                if not chunk.metadata.get("allow_oversize", False):
                    errors.append(
                        f"PROP-2: Chunk {i} exceeds max_chunk_size "
                        f"({chunk.size} > {self.config.max_chunk_size}) "
                        f"without allow_oversize flag"
                    )
                else:
                    # Check for valid reason
                    reason = chunk.metadata.get("oversize_reason")
                    valid_reasons = {
                        "code_block_integrity",
                        "table_integrity",
                        "section_integrity",
                    }
                    if reason not in valid_reasons:
                        errors.append(f"PROP-2: Chunk {i} has invalid oversize_reason: {reason}")

        return errors

    def _check_monotonic_ordering(self, chunks: list[Chunk]) -> str | None:
        """
        PROP-3: Monotonic Ordering

        Chunks should be in order by start_line.
        """
        for i in range(len(chunks) - 1):
            if chunks[i].start_line > chunks[i + 1].start_line:
                return (
                    f"PROP-3: Chunks out of order at index {i}: "
                    f"line {chunks[i].start_line} > line {chunks[i + 1].start_line}"
                )

        return None

    def _check_no_empty_chunks(self, chunks: list[Chunk]) -> list[str]:
        """
        PROP-4: No Empty Chunks

        All chunks should have non-empty content.
        """
        errors = []

        for i, chunk in enumerate(chunks):
            if not chunk.content.strip():
                errors.append(f"PROP-4: Chunk {i} has empty content")

        return errors

    def _check_valid_line_numbers(self, chunks: list[Chunk], original_text: str) -> list[str]:
        """
        PROP-5: Valid Line Numbers

        All line numbers should be valid (>= 1, end >= start).
        """
        errors = []
        total_lines = original_text.count("\n") + 1 if original_text else 0

        for i, chunk in enumerate(chunks):
            if chunk.start_line < 1:
                errors.append(f"PROP-5: Chunk {i} has invalid start_line: {chunk.start_line}")

            if chunk.end_line < chunk.start_line:
                errors.append(
                    f"PROP-5: Chunk {i} has end_line < start_line: "
                    f"{chunk.end_line} < {chunk.start_line}"
                )

            if chunk.end_line > total_lines:
                errors.append(
                    f"PROP-5: Chunk {i} has end_line > total_lines: "
                    f"{chunk.end_line} > {total_lines}"
                )

        return errors


def validate_chunks(
    chunks: list[Chunk],
    original_text: str,
    config: ChunkConfig | None = None,
    strict: bool = False,
) -> ValidationResult:
    """
    Convenience function to validate chunks.

    Args:
        chunks: List of chunks to validate
        original_text: Original markdown text
        config: Configuration (uses defaults if None)
        strict: If True, treat warnings as errors

    Returns:
        ValidationResult
    """
    validator = Validator(config)
    return validator.validate(chunks, original_text, strict)
