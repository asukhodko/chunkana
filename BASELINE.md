# Baseline Reference

This document tracks the baseline from dify-markdown-chunker v2 used to ensure Chunkana compatibility.

## Source Commit

- **Repository**: dify-markdown-chunker
- **Commit Hash**: `120d008bafd0525853cc977ab62fab6a94a410d7`
- **Date Generated**: 2026-01-02

## Baseline Parameters

Default ChunkConfig values used for baseline generation:

```python
max_chunk_size = 4096
min_chunk_size = 512
overlap_size = 200
overlap_cap_ratio = 0.35
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
| `complex_lists.md` | Nested lists, mixed ordered/unordered |
| `code_context.md` | Code blocks with surrounding explanations |
| `headers_deep.md` | Deep header hierarchy (h1-h6) |
| `mixed_content.md` | Combination of all element types |

## Golden Outputs

### Core Output (`tests/baseline/golden/`)

JSON files containing canonical chunks (without embedded overlap):
- `{fixture_name}.json` — chunks with metadata

Structure:
```json
{
  "fixture": "simple_text.md",
  "config": { "max_chunk_size": 4096, "overlap_size": 200 },
  "chunks": [
    {
      "content": "...",
      "start_line": 1,
      "end_line": 10,
      "metadata": { "chunk_index": 0, "strategy": "...", ... }
    }
  ]
}
```

### View-Level Output (`tests/baseline/golden_dify_style/`, `tests/baseline/golden_no_metadata/`)

- `golden_dify_style/{fixture_name}.jsonl` — v2 output with `include_metadata=True`
- `golden_no_metadata/{fixture_name}.jsonl` — v2 output with `include_metadata=False`

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
python scripts/generate_baseline.py

# This will:
# 1. Read fixtures from tests/baseline/fixtures/
# 2. Run v2 chunker on each fixture
# 3. Save golden outputs to tests/baseline/golden/
# 4. Save view-level outputs to golden_dify_style/ and golden_no_metadata/
```

## Compatibility Guarantees

Chunkana guarantees the following match v2 baseline:

1. **Chunk boundaries**: `start_line`, `end_line` identical
2. **Chunk content**: Canonical content (without embedded overlap) identical
3. **Core metadata**: `chunk_index`, `strategy`, `header_path`, `content_type` identical
4. **Overlap metadata**: `previous_content`, `next_content` identical

## Not Guaranteed 1:1

- Output string formatting (whitespace, JSON indentation)
- Dify-specific parameters not in ChunkerConfig
- Internal implementation details
