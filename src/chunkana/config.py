"""
Simplified configuration for markdown_chunker v2.

Only 8 core parameters instead of 32.
"""

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from .adaptive_sizing import AdaptiveSizeConfig

if TYPE_CHECKING:
    from .table_grouping import TableGrouper, TableGroupingConfig


@dataclass
class ChunkConfig:
    """
    Configuration for markdown chunking.

    Simplified from 32 parameters to 8 core parameters.
    All MC-* bugfix behaviors are now enabled by default.

    Attributes:
        max_chunk_size: Maximum size of a chunk in characters
            (default: 4096)
        min_chunk_size: Minimum size of a chunk in characters
            (default: 512)
        overlap_size: Size of overlap between chunks
            (0 = disabled, default: 200)
        preserve_atomic_blocks: Keep code blocks and tables intact
            (default: True)
        extract_preamble: Extract content before first header as preamble
            (default: True)
        code_threshold: Code ratio threshold for CodeAwareStrategy
            (default: 0.3)
        structure_threshold: Min headers for StructuralStrategy
            (default: 3)
        list_ratio_threshold: Minimum list ratio for ListAwareStrategy
            (default: 0.4)
        list_count_threshold: Minimum list block count for ListAwareStrategy
            (default: 5)
        strategy_override: Force specific strategy (default: None)
        enable_code_context_binding: Enable enhanced code-context binding
            (default: True)
        max_context_chars_before: Maximum characters to search backward for
            explanation in code-context binding (default: 500)
        max_context_chars_after: Maximum characters to search forward for
            explanation in code-context binding (default: 300)
        related_block_max_gap: Maximum line gap to consider blocks related
            in code-context binding (default: 5)
        bind_output_blocks: Automatically bind output blocks to code
            in code-context binding (default: True)
        preserve_before_after_pairs: Keep Before/After examples in single chunk
            in code-context binding (default: True)
        use_adaptive_sizing: Enable adaptive chunk sizing based on content
            complexity (default: False)
        adaptive_config: Configuration for adaptive sizing behavior
            (auto-created with defaults if use_adaptive_sizing=True)
        include_document_summary: Create root document-level chunk in
            hierarchical mode (default: True)
        strip_obsidian_block_ids: Remove Obsidian-style block reference IDs
            (^block-id) from content (default: False)
        preserve_latex_blocks: Treat LaTeX formulas as atomic blocks
            (default: True)
        latex_display_only: Only extract display math ($$...$$) and environments,
            skip inline math ($...$) (default: True)
        latex_max_context_chars: Maximum characters of surrounding text to bind
            with LaTeX formulas (default: 300)
        group_related_tables: Enable grouping of related tables into single chunks
            for better retrieval quality (default: False)
        table_grouping_config: Configuration for table grouping behavior
            (auto-created with defaults if group_related_tables=True)
    """

    # Size parameters
    max_chunk_size: int = 4096
    min_chunk_size: int = 512
    overlap_size: int = 200

    # Behavior parameters
    preserve_atomic_blocks: bool = True
    extract_preamble: bool = True

    # Strategy selection thresholds
    code_threshold: float = 0.3
    structure_threshold: int = 3
    list_ratio_threshold: float = 0.4
    list_count_threshold: int = 5

    # Override
    strategy_override: str | None = None

    # Code-context binding parameters
    enable_code_context_binding: bool = True
    max_context_chars_before: int = 500
    max_context_chars_after: int = 300
    related_block_max_gap: int = 5
    bind_output_blocks: bool = True
    preserve_before_after_pairs: bool = True

    # Adaptive sizing parameters
    use_adaptive_sizing: bool = False
    adaptive_config: AdaptiveSizeConfig | None = None

    # Hierarchical chunking parameters
    include_document_summary: bool = True
    validate_invariants: bool = True
    strict_mode: bool = False

    # Content preprocessing parameters
    strip_obsidian_block_ids: bool = False

    # LaTeX formula handling parameters
    preserve_latex_blocks: bool = True
    latex_display_only: bool = True
    latex_max_context_chars: int = 300

    # Table grouping parameters
    group_related_tables: bool = False
    table_grouping_config: Optional["TableGroupingConfig"] = None

    # Overlap cap ratio (limits overlap to fraction of adjacent chunk size)
    overlap_cap_ratio: float = 0.35

    def __post_init__(self) -> None:
        """Validate configuration."""
        self._validate_size_params()
        self._validate_threshold_params()
        self._validate_strategy_override()
        self._validate_code_context_params()
        self._validate_adaptive_sizing_params()
        self._validate_latex_params()
        self._validate_table_grouping_params()
        self._validate_overlap_cap_ratio()

    def _validate_size_params(self) -> None:
        """Validate size-related parameters."""
        if self.max_chunk_size <= 0:
            raise ValueError(f"max_chunk_size must be positive, got {self.max_chunk_size}")

        if self.min_chunk_size <= 0:
            raise ValueError(f"min_chunk_size must be positive, got {self.min_chunk_size}")

        if self.min_chunk_size > self.max_chunk_size:
            # Auto-adjust instead of error
            self.min_chunk_size = self.max_chunk_size // 2

        if self.overlap_size < 0:
            raise ValueError(f"overlap_size must be non-negative, got {self.overlap_size}")

        if self.overlap_size >= self.max_chunk_size:
            raise ValueError(
                f"overlap_size ({self.overlap_size}) must be less than "
                f"max_chunk_size ({self.max_chunk_size})"
            )

    def _validate_threshold_params(self) -> None:
        """Validate threshold parameters."""
        if not 0 <= self.code_threshold <= 1:
            raise ValueError(f"code_threshold must be between 0 and 1, got {self.code_threshold}")

        if self.structure_threshold < 1:
            raise ValueError(f"structure_threshold must be >= 1, got {self.structure_threshold}")

        if not 0 <= self.list_ratio_threshold <= 1:
            raise ValueError(
                f"list_ratio_threshold must be between 0 and 1, got {self.list_ratio_threshold}"
            )

        if self.list_count_threshold < 1:
            raise ValueError(f"list_count_threshold must be >= 1, got {self.list_count_threshold}")

    def _validate_strategy_override(self) -> None:
        """Validate strategy override parameter."""
        if self.strategy_override is not None:
            valid_strategies = {"code_aware", "list_aware", "structural", "fallback"}
            if self.strategy_override not in valid_strategies:
                raise ValueError(
                    f"strategy_override must be one of "
                    f"{valid_strategies}, got {self.strategy_override}"
                )

    def _validate_code_context_params(self) -> None:
        """Validate code-context binding parameters."""
        if self.max_context_chars_before < 0:
            raise ValueError(
                f"max_context_chars_before must be non-negative, "
                f"got {self.max_context_chars_before}"
            )

        if self.max_context_chars_after < 0:
            raise ValueError(
                f"max_context_chars_after must be non-negative, got {self.max_context_chars_after}"
            )

        if self.related_block_max_gap < 1:
            raise ValueError(
                f"related_block_max_gap must be >= 1, got {self.related_block_max_gap}"
            )

    def _validate_adaptive_sizing_params(self) -> None:
        """Validate adaptive sizing parameters."""
        if self.use_adaptive_sizing and self.adaptive_config is None:
            # Auto-create default config if adaptive sizing enabled
            self.adaptive_config = AdaptiveSizeConfig()

    def _validate_latex_params(self) -> None:
        """Validate LaTeX formula handling parameters."""
        if self.latex_max_context_chars < 0:
            raise ValueError(
                f"latex_max_context_chars must be non-negative, got {self.latex_max_context_chars}"
            )

    def _validate_table_grouping_params(self) -> None:
        """Validate table grouping parameters."""
        # TableGroupingConfig validates itself in __post_init__
        # Here we just ensure consistency
        pass

    def _validate_overlap_cap_ratio(self) -> None:
        """Validate overlap cap ratio parameter."""
        if not 0 < self.overlap_cap_ratio <= 1:
            raise ValueError(
                f"overlap_cap_ratio must be between 0 (exclusive) and 1 (inclusive), "
                f"got {self.overlap_cap_ratio}"
            )

    def get_table_grouper(self) -> Optional["TableGrouper"]:
        """
        Get TableGrouper instance if table grouping is enabled.

        Returns:
            TableGrouper instance if group_related_tables is True,
            None otherwise.

        Requirements: 2.3
        """
        if not self.group_related_tables:
            return None

        from .table_grouping import TableGrouper, TableGroupingConfig

        config = self.table_grouping_config or TableGroupingConfig()
        return TableGrouper(config)

    @property
    def enable_overlap(self) -> bool:
        """Whether overlap is enabled."""
        return self.overlap_size > 0

    @classmethod
    def from_legacy(cls, **kwargs: object) -> "ChunkConfig":
        """
        Create config from legacy parameters with deprecation warnings.

        Maps old parameter names to new ones and ignores removed parameters.
        """
        # Parameter mapping: old_name -> new_name
        param_mapping = {
            "max_size": "max_chunk_size",
            "min_size": "min_chunk_size",
        }

        # Parameters that are removed (always enabled or removed)
        removed_params = {
            "enable_overlap",  # Use overlap_size > 0
            "block_based_splitting",  # Always enabled
            "preserve_code_blocks",  # Always enabled
            "preserve_tables",  # Always enabled
            "enable_deduplication",  # Removed
            "enable_regression_validation",  # Removed
            "enable_header_path_validation",  # Removed
            "use_enhanced_parser",  # Always enabled
            "use_legacy_overlap",  # Removed
            "enable_block_overlap",  # Use overlap_size > 0
            "enable_sentence_splitting",  # Removed
            "enable_paragraph_merging",  # Removed
            "enable_list_preservation",  # Always enabled
            "enable_metadata_enrichment",  # Always enabled
            "enable_size_normalization",  # Removed
            "enable_fallback_strategy",  # Always enabled
        }

        new_kwargs: dict[str, Any] = {}

        for key, value in kwargs.items():
            if key in removed_params:
                warnings.warn(
                    f"Parameter '{key}' is deprecated and ignored in v2.0. "
                    f"See MIGRATION.md for details.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            elif key in param_mapping:
                new_key = param_mapping[key]
                warnings.warn(
                    f"Parameter '{key}' is renamed to '{new_key}' in v2.0.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                new_kwargs[new_key] = value
            else:
                new_kwargs[key] = value

        return cls(**new_kwargs)

    @classmethod
    def default(cls) -> "ChunkConfig":
        """Create default configuration."""
        return cls()

    @classmethod
    def for_code_heavy(cls) -> "ChunkConfig":
        """Configuration optimized for code-heavy documents."""
        return cls(
            max_chunk_size=8192,
            min_chunk_size=1024,
            overlap_size=100,
            code_threshold=0.2,
        )

    @classmethod
    def for_structured(cls) -> "ChunkConfig":
        """Configuration optimized for structured documents."""
        return cls(
            max_chunk_size=4096,
            min_chunk_size=512,
            overlap_size=200,
            structure_threshold=2,
        )

    @classmethod
    def minimal(cls) -> "ChunkConfig":
        """Minimal configuration with small chunks."""
        return cls(
            max_chunk_size=1024,
            min_chunk_size=256,
            overlap_size=50,
        )

    @classmethod
    def for_changelogs(cls) -> "ChunkConfig":
        """Configuration optimized for changelog documents."""
        return cls(
            max_chunk_size=6144,
            min_chunk_size=256,
            overlap_size=100,
            list_ratio_threshold=0.35,
            list_count_threshold=4,
        )

    @classmethod
    def with_adaptive_sizing(cls) -> "ChunkConfig":
        """Configuration with adaptive sizing enabled (default profile)."""
        return cls(
            max_chunk_size=4096,
            min_chunk_size=512,
            overlap_size=200,
            use_adaptive_sizing=True,
            adaptive_config=AdaptiveSizeConfig(
                base_size=1500,
                min_scale=0.5,
                max_scale=1.5,
            ),
        )

    @classmethod
    def for_code_heavy_adaptive(cls) -> "ChunkConfig":
        """Configuration for code-heavy documents with adaptive sizing."""
        return cls(
            max_chunk_size=8192,
            min_chunk_size=1024,
            overlap_size=100,
            code_threshold=0.2,
            use_adaptive_sizing=True,
            adaptive_config=AdaptiveSizeConfig(
                base_size=2000,
                min_scale=0.7,
                max_scale=1.8,
                code_weight=0.6,
                table_weight=0.2,
                list_weight=0.1,
                sentence_length_weight=0.1,
            ),
        )

    @classmethod
    def for_text_heavy_adaptive(cls) -> "ChunkConfig":
        """Configuration for text-heavy documents with adaptive sizing."""
        return cls(
            max_chunk_size=4096,
            min_chunk_size=512,
            overlap_size=200,
            use_adaptive_sizing=True,
            adaptive_config=AdaptiveSizeConfig(
                base_size=1200,
                min_scale=0.5,
                max_scale=1.2,
                code_weight=0.2,
                table_weight=0.1,
                list_weight=0.3,
                sentence_length_weight=0.4,
            ),
        )

    def to_dict(self) -> dict[str, object]:
        """
        Serialize config to dictionary.

        Returns:
            Dictionary with all config parameters including computed properties.
            Includes both plugin parity fields and Chunkana extension fields.
        """
        result: dict[str, object] = {
            # Plugin parity fields (from plugin_config_keys.json)
            "max_chunk_size": self.max_chunk_size,
            "min_chunk_size": self.min_chunk_size,
            "overlap_size": self.overlap_size,
            "preserve_atomic_blocks": self.preserve_atomic_blocks,
            "extract_preamble": self.extract_preamble,
            "code_threshold": self.code_threshold,
            "structure_threshold": self.structure_threshold,
            "list_ratio_threshold": self.list_ratio_threshold,
            "list_count_threshold": self.list_count_threshold,
            "strategy_override": self.strategy_override,
            "enable_code_context_binding": self.enable_code_context_binding,
            "max_context_chars_before": self.max_context_chars_before,
            "max_context_chars_after": self.max_context_chars_after,
            "related_block_max_gap": self.related_block_max_gap,
            "bind_output_blocks": self.bind_output_blocks,
            "preserve_before_after_pairs": self.preserve_before_after_pairs,
            "enable_overlap": self.enable_overlap,  # computed property
            # Chunkana extension fields
            "overlap_cap_ratio": self.overlap_cap_ratio,
            "use_adaptive_sizing": self.use_adaptive_sizing,
            "adaptive_config": (self.adaptive_config.to_dict() if self.adaptive_config else None),
            "include_document_summary": self.include_document_summary,
            "strip_obsidian_block_ids": self.strip_obsidian_block_ids,
            "preserve_latex_blocks": self.preserve_latex_blocks,
            "latex_display_only": self.latex_display_only,
            "latex_max_context_chars": self.latex_max_context_chars,
            "group_related_tables": self.group_related_tables,
            "table_grouping_config": (
                self.table_grouping_config.to_dict() if self.table_grouping_config else None
            ),
        }
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChunkConfig":
        """
        Create config from dictionary.

        Handles legacy parameters, nested configs, and uses defaults for missing keys.
        Unknown fields are ignored for forward compatibility.

        Args:
            data: Dictionary with config parameters

        Returns:
            ChunkConfig instance
        """
        import dataclasses

        from .table_grouping import TableGroupingConfig

        config_data = data.copy()

        # Handle legacy enable_overlap parameter
        if "enable_overlap" in config_data:
            enable = config_data.pop("enable_overlap")
            if enable and "overlap_size" not in config_data:
                config_data["overlap_size"] = 200  # default
            elif not enable:
                config_data["overlap_size"] = 0

        # Handle nested adaptive_config
        if (
            "adaptive_config" in config_data
            and config_data["adaptive_config"] is not None
            and isinstance(config_data["adaptive_config"], dict)
        ):
            config_data["adaptive_config"] = AdaptiveSizeConfig.from_dict(
                config_data["adaptive_config"]
            )

        # Handle nested table_grouping_config
        if (
            "table_grouping_config" in config_data
            and config_data["table_grouping_config"] is not None
        ) and isinstance(config_data["table_grouping_config"], dict):
            config_data["table_grouping_config"] = TableGroupingConfig.from_dict(
                config_data["table_grouping_config"]
            )

        # Filter to only valid parameters (ignore unknown fields for forward compatibility)
        valid_params = {f.name for f in dataclasses.fields(cls)}
        config_data = {k: v for k, v in config_data.items() if k in valid_params}

        return cls(**config_data)


# Alias for public API (ChunkConfig is the original name from v2)
ChunkerConfig = ChunkConfig
