# Parity Matrix: dify-markdown-chunker → Chunkana

This document provides a detailed field-by-field compatibility matrix between the dify-markdown-chunker plugin and Chunkana library.

## Source of Truth

- **Plugin commit:** 120d008bafd0
- **Generated from:** `tests/baseline/plugin_config_keys.json`, `tests/baseline/plugin_tool_params.json`
- **Verification:** Baseline tests in `tests/baseline/`

## ChunkConfig Fields

All fields from plugin's `ChunkConfig.to_dict()`:

| # | Plugin Field | Type | Default | Chunkana Field | Status |
|---|--------------|------|---------|----------------|--------|
| 1 | `bind_output_blocks` | bool | True | `bind_output_blocks` | ✅ Full parity |
| 2 | `code_threshold` | float | 0.3 | `code_threshold` | ✅ Full parity |
| 3 | `enable_code_context_binding` | bool | True | `enable_code_context_binding` | ✅ Full parity |
| 4 | `enable_overlap` | bool | (computed) | (computed) | ✅ Computed from overlap_size > 0 |
| 5 | `extract_preamble` | bool | True | `extract_preamble` | ✅ Full parity |
| 6 | `list_count_threshold` | int | 5 | `list_count_threshold` | ✅ Full parity |
| 7 | `list_ratio_threshold` | float | 0.4 | `list_ratio_threshold` | ✅ Full parity |
| 8 | `max_chunk_size` | int | 4096 | `max_chunk_size` | ✅ Full parity |
| 9 | `max_context_chars_after` | int | 300 | `max_context_chars_after` | ✅ Full parity |
| 10 | `max_context_chars_before` | int | 500 | `max_context_chars_before` | ✅ Full parity |
| 11 | `min_chunk_size` | int | 512 | `min_chunk_size` | ✅ Full parity |
| 12 | `overlap_size` | int | 200 | `overlap_size` | ✅ Full parity |
| 13 | `preserve_atomic_blocks` | bool | True | `preserve_atomic_blocks` | ✅ Full parity |
| 14 | `preserve_before_after_pairs` | bool | True | `preserve_before_after_pairs` | ✅ Full parity |
| 15 | `related_block_max_gap` | int | 5 | `related_block_max_gap` | ✅ Full parity |
| 16 | `strategy_override` | str\|None | None | `strategy_override` | ✅ Full parity |
| 17 | `structure_threshold` | int | 3 | `structure_threshold` | ✅ Full parity |

**Summary:** 17/17 fields supported (100% parity)

## Tool Input Parameters

Parameters exposed in Dify plugin UI:

| # | Tool Param | Type | Required | Default | Chunkana Equivalent |
|---|------------|------|----------|---------|---------------------|
| 1 | `input_text` | string | Yes | — | `chunk_markdown(text, ...)` |
| 2 | `max_chunk_size` | number | No | 4096 | `ChunkerConfig.max_chunk_size` |
| 3 | `chunk_overlap` | number | No | 200 | `ChunkerConfig.overlap_size` |
| 4 | `strategy` | select | No | "auto" | `ChunkerConfig.strategy_override` (None = auto) |
| 5 | `include_metadata` | boolean | No | true | Renderer selection |
| 6 | `enable_hierarchy` | boolean | No | false | `chunk_hierarchical()` |
| 7 | `debug` | boolean | No | false | `result.get_all_chunks()` |

**Summary:** 7/7 parameters mapped (100% coverage)

## Output Format Mapping

| Plugin Mode | Chunkana Renderer | Output |
|-------------|-------------------|--------|
| `include_metadata=True` | `render_dify_style(chunks)` | `<metadata>` blocks + content |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` | Embedded overlap in text |

## Chunk Metadata Fields

| Plugin Metadata | Chunkana Metadata | Status |
|-----------------|-------------------|--------|
| `chunk_id` | `chunk_id` | ✅ Same format (8-char SHA256) |
| `chunk_index` | `chunk_index` | ✅ Full parity |
| `content_type` | `content_type` | ✅ Full parity |
| `header_path` | `header_path` | ✅ Full parity |
| `strategy` | `strategy` | ✅ Full parity |
| `previous_content` | `previous_content` | ✅ Full parity |
| `next_content` | `next_content` | ✅ Full parity |
| `small_chunk` | — | ⚠️ Not used (see Behavioral Differences) |

## Chunkana Extensions

Fields available only in Chunkana (not in plugin):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `use_adaptive_sizing` | bool | False | Enable adaptive chunk sizing |
| `adaptive_config` | AdaptiveSizeConfig | None | Adaptive sizing parameters |
| `group_related_tables` | bool | False | Group related tables |
| `table_grouping_config` | TableGroupingConfig | None | Table grouping parameters |
| `overlap_cap_ratio` | float | 0.35 | Max overlap as fraction of chunk |
| `preserve_latex_blocks` | bool | True | Keep LaTeX blocks intact |

## Behavioral Differences

### Small Chunk Merging

| Aspect | Plugin | Chunkana |
|--------|--------|----------|
| Small H1 chunks | Separate with `small_chunk: true` | Merged with following section |
| Impact | More chunks | Fewer, larger chunks |
| RAG quality | May retrieve incomplete context | Better context preservation |

See [MIGRATION_GUIDE.md](../../MIGRATION_GUIDE.md#behavioral-differences) for details.

## Verification

Run parity tests:

```bash
# Config parity
pytest tests/baseline/test_config_parity.py -v

# Canonical output parity
pytest tests/baseline/test_canonical.py -v

# View-level output parity
pytest tests/baseline/test_view_level.py -v
```
