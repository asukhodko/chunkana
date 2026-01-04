# Renderers

Renderers format chunk output without modifying the original chunks.

## Available Renderers

### render_dify_style

Formats chunks with `<metadata>` blocks (Dify-compatible, equivalent to `include_metadata=True`).

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

chunks = chunk_markdown(text)
output = render_dify_style(chunks)
```

Output format:
```
<metadata>
{"chunk_index": 0, "content_type": "section", "header_path": "/Introduction", ...}
</metadata>

Actual chunk content here...
```

### render_with_embedded_overlap

Embeds bidirectional overlap into content strings (equivalent to `include_metadata=False`).

```python
from chunkana.renderers import render_with_embedded_overlap

output = render_with_embedded_overlap(chunks)
# ["previous_content\nchunk_content\nnext_content", ...]
```

Use case: when you need overlap physically in the text, not just metadata.

### render_with_prev_overlap

Embeds only previous overlap (sliding window style).

```python
from chunkana.renderers import render_with_prev_overlap

output = render_with_prev_overlap(chunks)
# ["previous_content\nchunk_content", ...]
```

Format: `{previous_content}\n{content}` or just `{content}` if no previous overlap.

### render_json

Converts chunks to list of dictionaries.

```python
from chunkana.renderers import render_json

output = render_json(chunks)
# [{"content": "...", "start_line": 1, "end_line": 5, "metadata": {...}}, ...]
```

Round-trip safe: `Chunk.from_dict(render_json(chunks)[0])` reconstructs the chunk.

### render_inline_metadata

Embeds metadata as inline comment at the start of content.

```python
from chunkana.renderers import render_inline_metadata

output = render_inline_metadata(chunks)
# ["<!-- chunk_index=0 content_type=section -->\nContent...", ...]
```

Keys are sorted alphabetically for deterministic output.

## Renderer Selection Guide

| Use Case | Renderer |
|----------|----------|
| Dify plugin (include_metadata=True) | `render_dify_style` |
| Dify plugin (include_metadata=False) | `render_with_embedded_overlap` |
| JSON API output | `render_json` |
| RAG with bidirectional context | `render_with_embedded_overlap` |
| RAG with sliding window | `render_with_prev_overlap` |
| Debugging / inspection | `render_inline_metadata` |

## Decision Tree

```
Need output for Dify plugin?
├── Yes, with metadata → render_dify_style()
├── Yes, without metadata → render_with_embedded_overlap()
└── No
    ├── Need JSON/dict → render_json()
    ├── Need bidirectional context → render_with_embedded_overlap()
    ├── Need sliding window → render_with_prev_overlap()
    └── Need inline metadata → render_inline_metadata()
```

## Important Notes

1. **Renderers don't modify chunks** — they only format output
2. **Overlap is in metadata** — `chunk.content` is always canonical (no embedded overlap)
3. **Unicode safe** — all renderers handle unicode correctly
4. **Empty overlap handled** — missing `previous_content`/`next_content` is fine
5. **Deterministic** — same input always produces same output

## Custom Rendering

For custom formats, access chunk data directly:

```python
for chunk in chunks:
    content = chunk.content
    start = chunk.start_line
    end = chunk.end_line
    prev = chunk.metadata.get("previous_content", "")
    next_ = chunk.metadata.get("next_content", "")
    chunk_id = chunk.metadata.get("chunk_id", "")
    
    # Your custom formatting here
```

## Plugin Compatibility

| Plugin Parameter | Chunkana Renderer |
|------------------|-------------------|
| `include_metadata=True` | `render_dify_style()` |
| `include_metadata=False` | `render_with_embedded_overlap()` |

Both renderers produce byte-for-byte identical output to the plugin (verified by baseline tests).
