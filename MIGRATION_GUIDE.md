# Migration Guide: dify-markdown-chunker → Chunkana

This guide helps you migrate from dify-markdown-chunker v2 plugin to the Chunkana library.

## Overview

Chunkana extracts the core chunking logic from dify-markdown-chunker v2 into a standalone library. The chunking algorithm is identical — only the API is simplified.

## Breaking Changes

### 1. Return Type

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

## Parameter Mapping

| v2 Plugin | Chunkana |
|-----------|----------|
| `max_chunk_size` | `ChunkerConfig.max_chunk_size` |
| `min_chunk_size` | `ChunkerConfig.min_chunk_size` |
| `overlap_size` | `ChunkerConfig.overlap_size` |
| `include_metadata=True` | `render_dify_style(chunks)` |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` |

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

## Compatibility Guarantees

### Guaranteed to Match v2

- Chunk boundaries (`start_line`, `end_line`)
- Chunk content (canonical, without embedded overlap)
- Core metadata: `chunk_index`, `strategy`, `header_path`, `content_type`
- Overlap metadata: `previous_content`, `next_content`
- `chunk_id` format (8-char SHA256 hash)

### Not Guaranteed 1:1

- Output string formatting (whitespace, JSON indentation)
- Dify-specific parameters not in ChunkerConfig
- Internal implementation details

## Testing Your Migration

```python
# Compare outputs
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

# Your v2 output (saved as reference)
v2_output = [...]

# Chunkana output
chunks = chunk_markdown(text)
chunkana_output = render_dify_style(chunks)

# Compare chunk count
assert len(chunkana_output) == len(v2_output)

# Compare content (normalize whitespace)
for v2, ch in zip(v2_output, chunkana_output):
    # Extract content after </metadata>
    v2_content = v2.split("</metadata>")[1].strip()
    ch_content = ch.split("</metadata>")[1].strip()
    assert v2_content == ch_content
```

## Getting Help

- [GitHub Issues](https://github.com/your-repo/chunkana/issues)
- [Documentation](docs/)
- [BASELINE.md](BASELINE.md) — baseline reference for compatibility
