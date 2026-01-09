# Parameter Mapping

Complete reference for parameter mapping between different interfaces and configurations.

## Dify Tool Input Parameters → Chunkana

These are the parameters exposed in the Dify plugin UI (from tool schema):

| Plugin Tool Param | Type | Default | Chunkana Equivalent | Notes |
|-------------------|------|---------|---------------------|-------|
| `input_text` | string | (required) | First argument to `chunk_markdown()` | The Markdown text to chunk |
| `max_chunk_size` | number | 4096 | `ChunkerConfig.max_chunk_size` | Maximum chunk size in characters |
| `chunk_overlap` | number | 200 | `ChunkerConfig.overlap_size` | Characters to overlap between chunks |
| `strategy` | select | "auto" | `ChunkerConfig.strategy_override` | "auto" = None in Chunkana |
| `include_metadata` | boolean | true | Renderer selection | `render_dify_style()` or `render_with_embedded_overlap()` |
| `enable_hierarchy` | boolean | false | `chunk_hierarchical()` | Use hierarchical chunking API |
| `debug` | boolean | false | `HierarchicalChunkingResult.get_all_chunks()` | Include non-leaf chunks |

## ChunkConfig Fields → ChunkerConfig

All internal configuration fields (from `ChunkConfig.to_dict()`):

| Plugin ChunkConfig | Type | Default | Chunkana ChunkerConfig | Status |
|--------------------|------|---------|------------------------|--------|
| `max_chunk_size` | int | 4096 | `max_chunk_size` | ✅ Supported |
| `min_chunk_size` | int | 512 | `min_chunk_size` | ✅ Supported |
| `overlap_size` | int | 200 | `overlap_size` | ✅ Supported |
| `enable_overlap` | bool | (computed) | (computed from overlap_size > 0) | ✅ Computed |
| `preserve_atomic_blocks` | bool | True | `preserve_atomic_blocks` | ✅ Supported |
| `extract_preamble` | bool | True | `extract_preamble` | ✅ Supported |
| `code_threshold` | float | 0.3 | `code_threshold` | ✅ Supported |
| `structure_threshold` | int | 3 | `structure_threshold` | ✅ Supported |
| `list_ratio_threshold` | float | 0.4 | `list_ratio_threshold` | ✅ Supported |
| `list_count_threshold` | int | 5 | `list_count_threshold` | ✅ Supported |
| `strategy_override` | str\|None | None | `strategy_override` | ✅ Supported |
| `enable_code_context_binding` | bool | True | `enable_code_context_binding` | ✅ Supported |
| `max_context_chars_before` | int | 500 | `max_context_chars_before` | ✅ Supported |
| `max_context_chars_after` | int | 300 | `max_context_chars_after` | ✅ Supported |
| `related_block_max_gap` | int | 5 | `related_block_max_gap` | ✅ Supported |
| `bind_output_blocks` | bool | True | `bind_output_blocks` | ✅ Supported |
| `preserve_before_after_pairs` | bool | True | `preserve_before_after_pairs` | ✅ Supported |

## Chunkana-Only Extensions

These fields are available only in Chunkana:

| ChunkerConfig Field | Type | Default | Description |
|---------------------|------|---------|-------------|
| `use_adaptive_sizing` | bool | False | Enable adaptive chunk sizing |
| `adaptive_config` | AdaptiveSizeConfig | None | Adaptive sizing parameters |
| `group_related_tables` | bool | False | Group related tables together |
| `table_grouping_config` | TableGroupingConfig | None | Table grouping parameters |
| `overlap_cap_ratio` | float | 0.35 | Max overlap as fraction of chunk |
| `preserve_latex_blocks` | bool | True | Keep LaTeX blocks intact |

## Renderer Selection Decision Tree

```
Need output format?
├── Dify plugin compatibility with metadata → render_dify_style()
├── Dify plugin compatibility without metadata → render_with_embedded_overlap()
└── Other formats
    ├── Need JSON/dict → render_json()
    ├── Need bidirectional context → render_with_embedded_overlap()
    └── Need sliding window → render_with_prev_overlap()
```

## Strategy Selection

| Strategy Value | ChunkerConfig Parameter | Description |
|----------------|------------------------|-------------|
| "auto" | `strategy_override=None` | Automatic strategy selection |
| "code_aware" | `strategy_override="code_aware"` | Optimized for code-heavy content |
| "list_aware" | `strategy_override="list_aware"` | Optimized for list-heavy content |
| "structural" | `strategy_override="structural"` | Based on document structure |
| "fallback" | `strategy_override="fallback"` | Simple sentence-based chunking |

## Usage Examples

### Basic Configuration

```python
from chunkana import ChunkerConfig

# Equivalent to plugin defaults
config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
    preserve_atomic_blocks=True,
    extract_preamble=True,
)
```

### Advanced Configuration

```python
config = ChunkerConfig(
    max_chunk_size=2048,
    strategy_override="code_aware",
    use_adaptive_sizing=True,
    adaptive_config=AdaptiveSizeConfig(
        base_size=1500,
        code_weight=0.4,
    ),
    group_related_tables=True,
)
```

### Renderer Selection

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_with_embedded_overlap

chunks = chunk_markdown(text, config)

# For Dify plugin compatibility
dify_output = render_dify_style(chunks)  # include_metadata=True equivalent
no_metadata_output = render_with_embedded_overlap(chunks)  # include_metadata=False equivalent
```