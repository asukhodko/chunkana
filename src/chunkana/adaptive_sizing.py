"""
Adaptive chunk sizing based on content complexity.

This module provides automatic chunk size adjustment based on
content characteristics like code ratio, table presence, and text complexity.
"""

from dataclasses import dataclass
from typing import Optional

from .types import ContentAnalysis


@dataclass
class AdaptiveSizeConfig:
    """
    Configuration for adaptive chunk sizing.

    Attributes:
        base_size: Base chunk size for medium complexity content
        min_scale: Minimum scaling factor (for simple text)
        max_scale: Maximum scaling factor (for complex code)
        code_weight: Weight for code ratio in complexity calculation
        table_weight: Weight for table ratio in complexity calculation
        list_weight: Weight for list ratio in complexity calculation
        sentence_length_weight: Weight for sentence length in complexity calculation
    """

    base_size: int = 1500
    min_scale: float = 0.5
    max_scale: float = 1.5
    code_weight: float = 0.4
    table_weight: float = 0.3
    list_weight: float = 0.2
    sentence_length_weight: float = 0.1

    def __post_init__(self):
        """Validate configuration parameters."""
        if self.base_size <= 0:
            raise ValueError(f"base_size must be positive, got {self.base_size}")

        if self.min_scale <= 0:
            raise ValueError(f"min_scale must be positive, got {self.min_scale}")

        if self.max_scale <= 0:
            raise ValueError(f"max_scale must be positive, got {self.max_scale}")

        if self.min_scale >= self.max_scale:
            raise ValueError(
                f"min_scale ({self.min_scale}) must be less than "
                f"max_scale ({self.max_scale})"
            )

        if self.code_weight < 0:
            raise ValueError(
                f"code_weight must be non-negative, got {self.code_weight}"
            )

        if self.table_weight < 0:
            raise ValueError(
                f"table_weight must be non-negative, got {self.table_weight}"
            )

        if self.list_weight < 0:
            raise ValueError(
                f"list_weight must be non-negative, got {self.list_weight}"
            )

        if self.sentence_length_weight < 0:
            raise ValueError(
                f"sentence_length_weight must be non-negative, "
                f"got {self.sentence_length_weight}"
            )

        weight_sum = (
            self.code_weight
            + self.table_weight
            + self.list_weight
            + self.sentence_length_weight
        )
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(
                f"Weights must sum to 1.0 (±0.001), got {weight_sum:.4f}. "
                f"Weights: code={self.code_weight}, table={self.table_weight}, "
                f"list={self.list_weight}, sentence={self.sentence_length_weight}"
            )


class AdaptiveSizeCalculator:
    """
    Calculate optimal chunk size based on content complexity.

    This class provides stateless methods for computing complexity scores
    and optimal chunk sizes. All methods are pure functions with no side effects.
    """

    def __init__(self, config: Optional[AdaptiveSizeConfig] = None):
        """
        Initialize calculator with configuration.

        Args:
            config: Adaptive sizing configuration (uses defaults if None)
        """
        self.config = config or AdaptiveSizeConfig()

    def calculate_complexity(self, analysis: ContentAnalysis) -> float:
        """
        Calculate content complexity score (0.0 to 1.0).

        Higher complexity indicates need for larger chunks.

        Args:
            analysis: Content analysis with ratios and metrics

        Returns:
            Complexity score between 0.0 and 1.0
        """
        code_factor = min(analysis.code_ratio, 1.0)
        table_ratio = self._calculate_table_ratio(analysis)
        table_factor = min(table_ratio, 1.0)
        list_factor = min(analysis.list_ratio, 1.0)
        sentence_factor = min(analysis.avg_sentence_length / 100.0, 1.0)

        complexity = (
            code_factor * self.config.code_weight
            + table_factor * self.config.table_weight
            + list_factor * self.config.list_weight
            + sentence_factor * self.config.sentence_length_weight
        )

        return min(complexity, 1.0)

    def calculate_optimal_size(self, text: str, analysis: ContentAnalysis) -> int:
        """
        Calculate optimal chunk size based on content.

        Args:
            text: Document text (for future extensions)
            analysis: Content analysis results

        Returns:
            Optimal chunk size in characters
        """
        complexity = self.calculate_complexity(analysis)
        scale_factor = self.get_scale_factor(complexity)
        target_size = self.config.base_size * scale_factor

        optimal_size = max(
            self.config.base_size * self.config.min_scale,
            min(target_size, self.config.base_size * self.config.max_scale),
        )

        return int(optimal_size)

    def get_scale_factor(self, complexity: float) -> float:
        """
        Get scale factor from complexity score.

        Args:
            complexity: Complexity score (0.0 to 1.0)

        Returns:
            Scale factor between min_scale and max_scale
        """
        scale_range = self.config.max_scale - self.config.min_scale
        return self.config.min_scale + (complexity * scale_range)

    def _calculate_table_ratio(self, analysis: ContentAnalysis) -> float:
        """
        Calculate table content ratio.

        Args:
            analysis: Content analysis

        Returns:
            Table ratio (0.0 to 1.0)
        """
        if analysis.total_chars == 0:
            return 0.0

        table_chars = sum(len(table.content) for table in analysis.tables)
        return table_chars / analysis.total_chars
