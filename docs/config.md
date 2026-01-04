# Configuration Guide

Chunkana uses `ChunkerConfig` (alias: `ChunkConfig`) to control chunking behavior.

## Basic Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_chunk_size` | int | 4096 | Maximum chunk size in characters |
| `min_chunk_size` | int | 512 | Minimum chunk size (smaller chunks may be merged) |
| `overlap_size` | int | 200 | Context overlap between chunks (stored in metadata) |
| `preserve_atomic_blocks` | bool | True | Keep code blocks, tables, LaTeX intact |
| `extract_preamble` | bool | True | Extract content before first header as preamble |

## Strategy Selection Thresholds

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code_threshold` | float | 0.3 | Code ratio threshold for CodeAware strategy |
| `structure_threshold` | int | 3 | Minimum headers for Structural strategy |
| `list_ratio_threshold` | float | 0.4 | List content ratio for ListAware strategy |
| `list_count_threshold` | int | 5 | Minimum lists for ListAware strategy |
| `strategy_override` | str\|None | None | Force specific strategy: "code_aware", "list_aware", "structural", "fallback" |

## Code-Context Binding

These parameters control how code blocks are bound to surrounding explanations:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_code_context_binding` | bool | True | Enable code-context binding |
| `max_context_chars_before` | int | 500 | Max chars of explanation before code |
| `max_context_chars_after` | int | 300 | Max chars of explanation after code |
| `related_block_max_gap` | int | 5 | Max lines between related code blocks |
| `bind_output_blocks` | bool | True | Bind code with its output blocks |
| `preserve_before_after_pairs` | bool | True | Keep before/after code pairs together |

## Adaptive Sizing

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_adaptive_sizing` | bool | False | Enable adaptive chunk sizing |
| `adaptive_config` | AdaptiveSizeConfig | None | Adaptive sizing configuration |

### AdaptiveSizeConfig

```python
from chunkana.adaptive_sizing import AdaptiveSizeConfig

adaptive_config = AdaptiveSizeConfig(
    base_size=1500,       # Base chunk size
    code_weight=0.4,      # Weight for code content
    min_size=500,         # Minimum adaptive size
    max_size=8000,        # Maximum adaptive size
)
```

## Table Grouping

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `group_related_tables` | bool | False | Group related tables together |
| `table_grouping_config` | TableGroupingConfig | None | Table grouping configuration |

### TableGroupingConfig

```python
from chunkana.table_grouping import TableGroupingConfig

table_config = TableGroupingConfig(
    max_distance_lines=10,      # Max lines between related tables
    require_same_section=True,  # Tables must be in same section
)
```

## Overlap Behavior

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `overlap_size` | int | 200 | Characters to overlap between chunks |
| `overlap_cap_ratio` | float | 0.35 | Max overlap as fraction of chunk size |

The overlap is stored in metadata (`previous_content`, `next_content`), not embedded in `chunk.content`.

## LaTeX Handling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `preserve_latex_blocks` | bool | True | Keep LaTeX blocks intact |

When enabled, LaTeX blocks (`$$...$$`, `\[...\]`, `\begin{...}...\end{...}`) are treated as atomic units.

## Computed Fields

| Field | Description |
|-------|-------------|
| `enable_overlap` | Computed as `overlap_size > 0` |

## Factory Methods

```python
from chunkana import ChunkerConfig

# Default configuration
config = ChunkerConfig.default()

# Optimized for code-heavy documents
config = ChunkerConfig.for_code_heavy()
```

## Serialization

```python
# Save config
config_dict = config.to_dict()

# Restore config
config = ChunkerConfig.from_dict(config_dict)
```

Round-trip is guaranteed: `ChunkerConfig.from_dict(config.to_dict()) == config`

## Example Configurations

### Documentation Sites

```python
config = ChunkerConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=150,
    structure_threshold=2,
)
```

### Code Repositories

```python
config = ChunkerConfig(
    max_chunk_size=8192,
    min_chunk_size=1024,
    overlap_size=100,
    code_threshold=0.2,
    enable_code_context_binding=True,
)
```

### Changelogs / Release Notes

```python
config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    list_ratio_threshold=0.3,
    list_count_threshold=3,
)
```

### Scientific Documents (LaTeX)

```python
config = ChunkerConfig(
    max_chunk_size=4096,
    preserve_latex_blocks=True,
    preserve_atomic_blocks=True,
)
```

## Plugin Compatibility

All 17 fields from dify-markdown-chunker's `ChunkConfig` are supported. See [Parity Matrix](migration/parity_matrix.md) for details.
