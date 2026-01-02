# Renderers

Renderers format chunk output without modifying the original chunks.

## Available Renderers

### render_json

Converts chunks to list of dictionaries.

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_json

chunks = chunk_markdown(text)
output = render_json(chunks)
# [{"content": "...", "start_line": 1, "end_line": 5, "metadata": {...}}, ...]
```

### render_dify_style

Formats chunks with `<metadata>` blocks (Dify-compatible).

```python
from chunkana.renderers import render_dify_style

output = render_dify_style(chunks)
# ["<metadata>\n{...}\n</metadata>\n\nContent here", ...]
```

Metadata includes `start_line`, `end_line`, and all chunk metadata.

### render_with_embedded_overlap

Embeds bidirectional overlap into content strings.

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

## Renderer Selection Guide

| Use Case | Renderer |
|----------|----------|
| JSON API output | `render_json` |
| Dify plugin (include_metadata=True) | `render_dify_style` |
| Dify plugin (include_metadata=False) | `render_with_embedded_overlap` |
| RAG with context | `render_with_embedded_overlap` |
| Simple text output | `render_with_prev_overlap` |

## Important Notes

1. **Renderers don't modify chunks** — they only format output
2. **Overlap is in metadata** — `chunk.content` is always canonical (no embedded overlap)
3. **Unicode safe** — all renderers handle unicode correctly
4. **Empty overlap handled** — missing `previous_content`/`next_content` is fine

## Custom Rendering

For custom formats, access chunk data directly:

```python
for chunk in chunks:
    content = chunk.content
    start = chunk.start_line
    end = chunk.end_line
    prev = chunk.metadata.get("previous_content", "")
    next_ = chunk.metadata.get("next_content", "")
    
    # Your custom formatting here
```
