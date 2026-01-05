# Migration Guide: dify-markdown-chunker → Chunkana

This guide helps you migrate from dify-markdown-chunker v2 plugin to the Chunkana library.

## Overview

Chunkana extracts the core chunking logic from dify-markdown-chunker v2 into a standalone library. The chunking algorithm is identical — only the API is simplified.

### What "Full Compatibility" Means

- **Canonical output:** `chunk_markdown()` produces identical `list[Chunk]` with same content, line numbers, and metadata
- **View-level output:** Renderers produce byte-for-byte identical strings to plugin's `include_metadata=True/False` modes
- **Verified by:** Baseline tests against golden outputs generated from plugin at pinned commit (120d008bafd0)

## Quick Start

```python
# Before (dify-markdown-chunker plugin)
from markdown_chunker_v2 import MarkdownChunker, ChunkConfig
config = ChunkConfig(max_chunk_size=4096)
chunker = MarkdownChunker(config)
result = chunker.chunk(text, include_metadata=True)

# After (Chunkana)
from chunkana import chunk_markdown, ChunkerConfig
from chunkana.renderers import render_dify_style
config = ChunkerConfig(max_chunk_size=4096)
chunks = chunk_markdown(text, config)
result = render_dify_style(chunks)
```

## Breaking Changes

### 1. Return Types

**Before (v2 plugin):**
```python
# Could return List[str] or List[Chunk] depending on parameters
result = chunker.chunk(text, include_metadata=True)
```

**After (Chunkana):**
```python
# Always returns List[Chunk]
chunks = chunk_markdown(text)

# Use renderers for string output
from chunkana.renderers import render_dify_style
strings = render_dify_style(chunks)
```

### 2. include_metadata Parameter

**Before:**
```python
# include_metadata controlled output format
result = chunker.chunk(text, include_metadata=True)   # with <metadata> blocks
result = chunker.chunk(text, include_metadata=False)  # with embedded overlap
```

**After:**
```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_with_embedded_overlap

chunks = chunk_markdown(text)

# Equivalent to include_metadata=True
output = render_dify_style(chunks)

# Equivalent to include_metadata=False
output = render_with_embedded_overlap(chunks)
```

## Step-by-Step Migration

### Step 1: Update Dependencies

```diff
# requirements.txt
- dify-markdown-chunker>=2.0.0
+ chunkana>=0.2.0
```

### Step 2: Update Imports

```diff
- from markdown_chunker_v2 import MarkdownChunker, ChunkConfig
+ from chunkana import chunk_markdown, ChunkerConfig
```

### Step 3: Update Chunking Code

```diff
- config = ChunkConfig(max_chunk_size=4096)
- chunker = MarkdownChunker(config)
- result = chunker.chunk(text, include_metadata=True)
+ config = ChunkerConfig(max_chunk_size=4096)
+ chunks = chunk_markdown(text, config)
+ result = render_dify_style(chunks)
```

### Step 4: Select Renderer Based on include_metadata

| Plugin Parameter | Chunkana Renderer |
|------------------|-------------------|
| `include_metadata=True` | `render_dify_style(chunks)` |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` |

## Complete Parameter Mapping

### Dify Tool Input Parameters → Chunkana

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

### ChunkConfig Fields → ChunkerConfig

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

### Chunkana-Only Extensions

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
Need output for Dify plugin?
├── Yes, with metadata → render_dify_style()
├── Yes, without metadata → render_with_embedded_overlap()
└── No
    ├── Need JSON/dict → render_json()
    ├── Need bidirectional context → render_with_embedded_overlap()
    └── Need sliding window → render_with_prev_overlap()
```

## Code Migration Examples

### Basic Chunking

**Before:**
```python
from markdown_chunker_v2 import MarkdownChunker, ChunkConfig

config = ChunkConfig(max_chunk_size=4096)
chunker = MarkdownChunker(config)
result = chunker.chunk(text)
```

**After:**
```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(max_chunk_size=4096)
chunks = chunk_markdown(text, config)
```

### With Metadata Output

**Before:**
```python
result = chunker.chunk(text, include_metadata=True)
# result is List[str] with <metadata> blocks
```

**After:**
```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

chunks = chunk_markdown(text)
result = render_dify_style(chunks)
# result is List[str] with <metadata> blocks
```

### Without Metadata (Embedded Overlap)

**Before:**
```python
result = chunker.chunk(text, include_metadata=False)
# result is List[str] with embedded overlap
```

**After:**
```python
from chunkana import chunk_markdown
from chunkana.renderers import render_with_embedded_overlap

chunks = chunk_markdown(text)
result = render_with_embedded_overlap(chunks)
# result is List[str] with embedded overlap
```

### Hierarchical Chunking

**Before:**
```python
result = chunker.chunk(text, enable_hierarchy=True)
```

**After:**
```python
from chunkana import chunk_hierarchical, ChunkConfig

# With validation (default)
config = ChunkConfig(
    max_chunk_size=1000,
    validate_invariants=True,  # Validates tree structure (default)
    strict_mode=False,         # Auto-fix issues (default)
)
result = chunk_hierarchical(text, config)

# Access leaf chunks (backward compatible)
flat_chunks = result.get_flat_chunks()

# Navigate hierarchy
for chunk in flat_chunks:
    parent = result.get_parent(chunk.metadata["chunk_id"])
    children = result.get_children(chunk.metadata["chunk_id"])
```

**New in v0.2.0:**
- `validate_invariants=True` (default): Validates tree invariants after construction
- `strict_mode=False` (default): Auto-fixes violations; set to `True` to raise exceptions
- `get_flat_chunks()` now includes non-leaf chunks with significant content (>100 chars) to prevent content loss
```

### Strategy Selection

**Before:**
```python
config = ChunkConfig(strategy="code_aware")
```

**After:**
```python
config = ChunkerConfig(strategy_override="code_aware")
# Valid values: "code_aware", "list_aware", "structural", "fallback", None (auto)
```

## Advanced Features

### Streaming Large Files

```python
from chunkana import chunk_file_streaming
from chunkana.streaming import StreamingConfig

streaming_config = StreamingConfig(
    buffer_size=100_000,
    overlap_lines=20,
)

for chunk in chunk_file_streaming("large_file.md", config, streaming_config):
    process(chunk)
```

### Adaptive Sizing

```python
from chunkana import ChunkerConfig
from chunkana.adaptive_sizing import AdaptiveSizeConfig

config = ChunkerConfig(
    use_adaptive_sizing=True,
    adaptive_config=AdaptiveSizeConfig(
        base_size=1500,
        code_weight=0.4,
    ),
)
```

### Table Grouping

```python
from chunkana import ChunkerConfig
from chunkana.table_grouping import TableGroupingConfig

config = ChunkerConfig(
    group_related_tables=True,
    table_grouping_config=TableGroupingConfig(
        max_distance_lines=10,
        require_same_section=True,
    ),
)
```

### LaTeX Preservation

```python
config = ChunkerConfig(
    preserve_latex_blocks=True,  # Default
    preserve_atomic_blocks=True,
)
```

## Compatibility Guarantees

### Guaranteed to Match Plugin (Byte-for-Byte)

- Chunk boundaries (`start_line`, `end_line`)
- Chunk content (canonical, without embedded overlap)
- All metadata: `chunk_index`, `strategy`, `header_path`, `content_type`, `previous_content`, `next_content`
- `chunk_id` format (8-char SHA256 hash)
- Renderer output format (verified against baseline golden outputs)

### Not Guaranteed

- **Streaming chunk boundaries:** `chunk_file_streaming()` may produce different boundaries at buffer splits
- **Streaming overlap metadata:** May differ at buffer boundaries

### Behavioral Differences

#### Small Chunk Merging

Chunkana optimizes chunk boundaries by merging small H1 header chunks with their following section content.

**Plugin behavior:** Creates separate small chunks for H1 headers with `small_chunk: true` metadata.

**Chunkana behavior:** Merges small H1 header chunks with their following section content, producing fewer but more contextually complete chunks.

**Example:**
```markdown
# Document Title

Brief intro.

## Section One

Content here...
```

| Aspect | Plugin | Chunkana |
|--------|--------|----------|
| Chunk count | 2 (title + section) | 1 (merged) |
| First chunk | `# Document Title\n\nBrief intro.` | `# Document Title\n\nBrief intro.\n\n## Section One\n\nContent here...` |
| Metadata | `small_chunk: true` | No `small_chunk` flag |

**Impact:** Chunkana produces fewer, larger chunks that preserve more context. This is generally better for RAG retrieval quality.

**Migration note:** If your application relies on separate small chunks for H1 headers, you may need to adjust your retrieval logic.

## Migration Verification Checklist

To verify your migration is correct:

1. **Run baseline canonical tests:**
   ```bash
   pytest tests/baseline/test_canonical.py -v
   ```

2. **Run view-level tests:**
   ```bash
   pytest tests/baseline/test_view_level.py -v
   ```

3. **Run property tests:**
   ```bash
   pytest tests/property/ -v
   ```

4. **Compare key fixtures:**
   - Nested code fences
   - Complex lists
   - Tables
   - LaTeX formulas

## Getting Help

- [GitHub Issues](https://github.com/asukh/chunkana/issues)
- [Documentation](docs/)
- [BASELINE.md](BASELINE.md) — baseline reference for compatibility
- [Parity Matrix](docs/migration/parity_matrix.md) — detailed field-by-field compatibility

## Troubleshooting

### HierarchicalInvariantError Exceptions

If you encounter `HierarchicalInvariantError` in strict mode, here's how to handle common cases:

#### is_leaf_consistency

```python
# Error: is_leaf=True but chunk has children
HierarchicalInvariantError: is_leaf_consistency violated in chunk abc123

# Solution: This is auto-fixed in non-strict mode. In strict mode:
config = ChunkConfig(strict_mode=False)  # Enable auto-fix
```

#### parent_child_bidirectionality

```python
# Error: Parent-child relationship is not symmetric
HierarchicalInvariantError: parent_child_bidirectionality violated

# Solution: Usually indicates corrupted tree state. Re-chunk the document:
result = chunker.chunk_hierarchical(text)  # Fresh chunking
```

#### orphaned_chunk

```python
# Error: Chunk is not reachable from root
HierarchicalInvariantError: orphaned_chunk detected

# Solution: Auto-fixed in non-strict mode by attaching to nearest parent
config = ChunkConfig(strict_mode=False)
```

### Debugging Hierarchical Issues

Enable strict mode temporarily to see all violations:

```python
from chunkana import MarkdownChunker, ChunkConfig
from chunkana import HierarchicalInvariantError

config = ChunkConfig(
    validate_invariants=True,
    strict_mode=True,  # Raise exceptions instead of auto-fix
)

try:
    result = chunker.chunk_hierarchical(text)
except HierarchicalInvariantError as e:
    print(f"Invariant: {e.invariant}")
    print(f"Chunk ID: {e.chunk_id}")
    print(f"Details: {e.details}")
    print(f"Suggested fix: {e.suggested_fix}")
```

### Performance Considerations

If chunking is slow for large documents:

```python
# Disable validation for performance-critical paths
config = ChunkConfig(
    validate_invariants=False,  # Skip tree validation
)
```

Typical performance benchmarks:
- Small docs (~100 lines): ~0.1ms
- Medium docs (~1000 lines): ~0.7ms
- Large docs (~10000 lines): ~2.7ms
