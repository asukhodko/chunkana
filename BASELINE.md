# Baseline Reference

This document tracks the baseline from dify-markdown-chunker v2 used to ensure Chunkana compatibility.

## Source Commit

- **Repository**: dify-markdown-chunker
- **Commit Hash**: `120d008bafd0525853cc977ab62fab6a94a410d7`
- **Date Generated**: 2026-01-04

## Source of Truth

All parity is defined relative to this pinned commit. Golden outputs are generated from plugin at this commit.

**Generated Artifacts:**
- `tests/baseline/plugin_config_keys.json` — keys from ChunkConfig.to_dict()
- `tests/baseline/plugin_tool_params.json` — parameters from tool schema
- `tests/baseline/golden_canonical/` — canonical chunk output (JSONL)
- `tests/baseline/golden_dify_style/` — view-level output for include_metadata=True (JSONL)
- `tests/baseline/golden_no_metadata/` — view-level output for include_metadata=False (JSONL)

## Baseline Parameters

Default ChunkConfig values used for baseline generation:

```python
max_chunk_size = 4096
min_chunk_size = 512
overlap_size = 200
preserve_atomic_blocks = True
extract_preamble = True
enable_code_context_binding = True
```

## Fixtures

Baseline fixtures are located in `tests/baseline/fixtures/`:

| Fixture | Description |
|---------|-------------|
| `simple_text.md` | Basic text without special structures |
| `nested_fences.md` | Nested code fences (``` inside ~~~~) |
| `large_tables.md` | Multiple tables, some exceeding chunk size |
| `list_heavy.md` | Nested lists, mixed ordered/unordered |
| `code_heavy.md` | Code-heavy document with multiple languages |
| `code_context.md` | Code blocks with surrounding explanations |
| `headers_deep.md` | Deep header hierarchy (h1-h6) |
| `mixed_content.md` | Combination of all element types |
| `structural.md` | Clear hierarchical structure |
| `latex_formulas.md` | LaTeX formulas (inline and display) |
| `adaptive_sizing.md` | Varying content density |
| `table_grouping.md` | Related tables grouping scenarios |

## Golden Outputs

### Canonical Output (`tests/baseline/golden_canonical/`)

JSONL files containing canonical chunks:
- `{fixture_name}.jsonl` — one JSON object per line

Schema:
```json
{"chunk_index": 0, "content": "...", "start_line": 1, "end_line": 10, "metadata": {...}}
```

### View-Level Output

- `golden_dify_style/{fixture_name}.jsonl` — plugin output with `include_metadata=True`
- `golden_no_metadata/{fixture_name}.jsonl` — plugin output with `include_metadata=False`

Schema:
```json
{"chunk_index": 0, "text": "<metadata>\n{...}\n</metadata>\n..."}
```

**IMPORTANT:** View-level goldens are saved as-is from plugin output WITHOUT any reformatting. Renderers must match byte-for-byte.

## Renderer Mapping

Based on v2 `_format_chunk_output()` analysis:

| v2 Parameter | v2 Behavior | Chunkana Renderer |
|--------------|-------------|-------------------|
| `include_metadata=True` | `<metadata>` block + content | `render_dify_style()` |
| `include_metadata=False` | prev + content + next (bidirectional) | `render_with_embedded_overlap()` |

**Note**: v2 uses bidirectional overlap embedding (prev + content + next) when `include_metadata=False`.

## Regenerating Baseline

```bash
# From chunkana root directory
python scripts/generate_baseline.py --plugin-path /path/to/dify-markdown-chunker

# This will:
# 1. Extract plugin_config_keys.json from ChunkConfig.to_dict()
# 2. Extract plugin_tool_params.json from tool schema
# 3. Read fixtures from tests/baseline/fixtures/
# 4. Run plugin chunker on each fixture
# 5. Save canonical goldens to tests/baseline/golden_canonical/
# 6. Save view-level goldens to golden_dify_style/ and golden_no_metadata/
```

**Requirements:**
- Plugin must be at pinned commit (see Source Commit above)
- Plugin dependencies must be installed
- PyYAML must be installed for tool schema parsing

## Not Guaranteed

- **Streaming chunk boundaries**: `chunk_file_streaming()` may produce different boundaries at buffer splits
- **Streaming overlap metadata**: May differ at buffer boundaries

These are documented in MIGRATION_GUIDE.md.
