"""
Exception classes for chunkana library.

Provides specific exception types for different error categories
with actionable error messages and debugging context.
"""

from typing import Any


class ChunkanaError(Exception):
    """
    Base exception class for all chunkana errors.

    Provides common functionality for error reporting and debugging.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """
        Initialize base exception.

        Args:
            message: Human-readable error message
            context: Additional context for debugging
        """
        super().__init__(message)
        self.context = context or {}

    def get_context(self) -> dict[str, Any]:
        """Get debugging context."""
        return self.context.copy()


class HierarchicalInvariantError(ChunkanaError):
    """
    Exception raised when hierarchical tree invariants are violated.

    Provides specific information about which invariant failed and
    actionable suggestions for resolution.
    """

    def __init__(
        self,
        chunk_id: str,
        invariant: str,
        details: dict[str, Any],
        suggested_fix: str | None = None,
    ):
        """
        Initialize hierarchical invariant error.

        Args:
            chunk_id: ID of the chunk that violates the invariant
            invariant: Name of the violated invariant
            details: Specific details about the violation
            suggested_fix: Suggested resolution for the issue
        """
        self.chunk_id = chunk_id
        self.invariant = invariant
        self.details = details
        self.suggested_fix = suggested_fix

        message = self._format_message()
        context = {
            "chunk_id": chunk_id,
            "invariant": invariant,
            "details": details,
            "suggested_fix": suggested_fix,
        }

        super().__init__(message, context)

    def _format_message(self) -> str:
        """Format detailed error message with suggestions."""
        base_msg = f"Hierarchical invariant '{self.invariant}' violated in chunk {self.chunk_id}"

        # Add specific details
        if self.details:
            detail_parts = []
            for key, value in self.details.items():
                detail_parts.append(f"{key}={value}")
            base_msg += f" ({', '.join(detail_parts)})"

        # Add suggestion if available
        if self.suggested_fix:
            base_msg += f". Suggested fix: {self.suggested_fix}"

        return base_msg

    def _get_suggestion(self) -> str:
        """Get suggestion based on invariant type."""
        suggestions = {
            "is_leaf_consistency": "Ensure is_leaf=True when children_ids is empty, is_leaf=False when children_ids has elements",
            "parent_child_bidirectionality": "Verify that parent's children_ids includes this chunk and child's parent_id points to parent",
            "content_range_consistency": "Check that chunk content matches its start_line and end_line range",
            "orphaned_chunk": "Link orphaned chunks to appropriate parent or root chunk",
            "circular_reference": "Remove circular references in parent-child relationships",
        }
        return suggestions.get(self.invariant, "Check chunk relationships and metadata consistency")


class ValidationError(ChunkanaError):
    """
    Exception raised during chunk validation.

    Provides information about validation failures with context
    for debugging and resolution.
    """

    def __init__(
        self,
        error_type: str,
        chunk_id: str | None = None,
        message: str = "",
        suggested_fix: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        """
        Initialize validation error.

        Args:
            error_type: Type of validation error
            chunk_id: ID of problematic chunk (if applicable)
            message: Detailed error message
            suggested_fix: Suggested resolution
            context: Additional debugging context
        """
        self.error_type = error_type
        self.chunk_id = chunk_id
        self.suggested_fix = suggested_fix

        if not message:
            message = self._generate_message()

        full_context = context or {}
        full_context.update(
            {"error_type": error_type, "chunk_id": chunk_id, "suggested_fix": suggested_fix}
        )

        super().__init__(message, full_context)

    def _generate_message(self) -> str:
        """Generate error message based on error type."""
        base_msg = f"Validation error: {self.error_type}"

        if self.chunk_id:
            base_msg += f" in chunk {self.chunk_id}"

        if self.suggested_fix:
            base_msg += f". {self.suggested_fix}"

        return base_msg


class ConfigurationError(ChunkanaError):
    """
    Exception raised for configuration-related errors.

    Provides guidance on valid parameter combinations and values.
    """

    def __init__(
        self,
        parameter: str,
        value: Any,
        message: str = "",
        valid_values: list[Any] | None = None,
    ):
        """
        Initialize configuration error.

        Args:
            parameter: Name of the problematic parameter
            value: Invalid value that was provided
            message: Custom error message
            valid_values: List of valid values (if applicable)
        """
        self.parameter = parameter
        self.value = value
        self.valid_values = valid_values

        if not message:
            message = self._generate_message()

        context = {"parameter": parameter, "value": value, "valid_values": valid_values}

        super().__init__(message, context)

    def _generate_message(self) -> str:
        """Generate configuration error message."""
        base_msg = f"Invalid configuration: {self.parameter}={self.value}"

        if self.valid_values:
            base_msg += f". Valid values: {self.valid_values}"

        return base_msg


class TreeConstructionError(ChunkanaError):
    """
    Exception raised when tree construction fails.

    Provides information about which relationships couldn't be established.
    """

    def __init__(
        self,
        operation: str,
        chunk_id: str,
        related_chunk_id: str | None = None,
        reason: str = "",
    ):
        """
        Initialize tree construction error.

        Args:
            operation: The operation that failed (e.g., "link_parent", "add_child")
            chunk_id: ID of the primary chunk involved
            related_chunk_id: ID of related chunk (if applicable)
            reason: Specific reason for failure
        """
        self.operation = operation
        self.chunk_id = chunk_id
        self.related_chunk_id = related_chunk_id
        self.reason = reason

        message = self._format_message()
        context = {
            "operation": operation,
            "chunk_id": chunk_id,
            "related_chunk_id": related_chunk_id,
            "reason": reason,
        }

        super().__init__(message, context)

    def _format_message(self) -> str:
        """Format tree construction error message."""
        base_msg = f"Tree construction failed: {self.operation} for chunk {self.chunk_id}"

        if self.related_chunk_id:
            base_msg += f" with {self.related_chunk_id}"

        if self.reason:
            base_msg += f" - {self.reason}"

        return base_msg
