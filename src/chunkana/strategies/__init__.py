"""
Chunking strategies for markdown_chunker v2.

Four strategies:
- CodeAwareStrategy: For documents with code blocks or tables (priority 1)
- ListAwareStrategy: For list-heavy documents (priority 2)
- StructuralStrategy: For documents with hierarchical headers (priority 3)
- FallbackStrategy: Universal fallback for any document (priority 4)
"""

from ..config import ChunkConfig
from ..types import ContentAnalysis
from .base import BaseStrategy
from .code_aware import CodeAwareStrategy
from .fallback import FallbackStrategy
from .list_aware import ListAwareStrategy
from .structural import StructuralStrategy


class StrategySelector:
    """
    Selects the appropriate strategy for a document.

    Selection order (by priority):
    1. CodeAwareStrategy - if document has code blocks or tables
    2. ListAwareStrategy - if document is list-heavy
    3. StructuralStrategy - if document has hierarchical headers
    4. FallbackStrategy - always works (universal fallback)
    """

    def __init__(self) -> None:
        self.strategies: list[BaseStrategy] = [
            CodeAwareStrategy(),
            ListAwareStrategy(),
            StructuralStrategy(),
            FallbackStrategy(),
        ]

    def select(self, analysis: ContentAnalysis, config: ChunkConfig) -> BaseStrategy:
        """
        Select the best strategy for the document.

        Args:
            analysis: Document analysis results
            config: Chunking configuration

        Returns:
            Selected strategy
        """
        # Check for strategy override
        if config.strategy_override:
            return self.get_by_name(config.strategy_override)

        # Select by priority
        for strategy in self.strategies:
            if strategy.can_handle(analysis, config):
                return strategy

        # Fallback always works
        return self.strategies[-1]

    def get_by_name(self, name: str) -> BaseStrategy:
        """Get strategy by name."""
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        raise ValueError(f"Unknown strategy: {name}")


__all__ = [
    "StrategySelector",
    "BaseStrategy",
    "CodeAwareStrategy",
    "ListAwareStrategy",
    "StructuralStrategy",
    "FallbackStrategy",
]
