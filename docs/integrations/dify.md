# Dify Integration

Using Chunkana with Dify workflows.

## Quick Migration

```python
# Before (dify-markdown-chunker plugin)
result = chunker.chunk(text, include_metadata=True)

# After (Chunkana)
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style
chunks = chunk_markdown(text)
result = render_dify_style(chunks)
```

## Parameter Mapping

### Tool Input Parameters

| Dify Tool Param | Chunkana Equivalent |
|-----------------|---------------------|
| `input_text` | `chunk_markdown(text, ...)` |
| `max_chunk_size` | `ChunkerConfig.max_chunk_size` |
| `chunk_overlap` | `ChunkerConfig.overlap_size` |
| `strategy` | `ChunkerConfig.strategy_override` (None = "auto") |
| `include_metadata=True` | `render_dify_style(chunks)` |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` |
| `enable_hierarchy=True` | `chunk_hierarchical(text, config)` |

### Config Fields

All 17 plugin config fields are supported. See [Parity Matrix](../migration/parity_matrix.md).

## Basic Usage

```python
from chunkana import chunk_markdown, ChunkerConfig
from chunkana.renderers import render_dify_style, render_with_embedded_overlap

def process_document(text: str, include_metadata: bool = True) -> list[str]:
    """Process document for Dify workflow."""
    config = ChunkerConfig(
        max_chunk_size=4096,
        min_chunk_size=512,
        overlap_size=200,
    )
    
    chunks = chunk_markdown(text, config)
    
    if include_metadata:
        return render_dify_style(chunks)
    else:
        return render_with_embedded_overlap(chunks)
```

## Metadata Format

With `render_dify_style()`, each chunk includes:

```
<metadata>
{"chunk_index": 0, "content_type": "section", "header_path": "/Introduction", "start_line": 1, "end_line": 10, "strategy": "structural"}
</metadata>

Actual chunk content here...
```

## Workflow Example

```python
# In Dify Code node
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

def main(text: str) -> dict:
    chunks = chunk_markdown(text)
    formatted = render_dify_style(chunks)
    
    return {
        "chunks": formatted,
        "count": len(formatted),
    }
```

## Hierarchical Chunking

```python
from chunkana import chunk_hierarchical

def main(text: str, debug: bool = False) -> dict:
    result = chunk_hierarchical(text)
    
    if debug:
        # Include all chunks (root, intermediate, leaf)
        chunks = result.get_all_chunks()
    else:
        # Only leaf chunks (default)
        chunks = result.get_flat_chunks()
    
    return {"chunks": render_dify_style(chunks)}
```

## Common Pitfalls

1. **Return type changed**: Plugin could return `List[str]` or `List[Chunk]`. Chunkana always returns `List[Chunk]` — use renderers for strings.

2. **include_metadata is not a parameter**: Use renderer selection instead.

3. **strategy="auto"**: In Chunkana, use `strategy_override=None` (default).

4. **chunk_overlap vs overlap_size**: Plugin tool uses `chunk_overlap`, config uses `overlap_size`.

## Migration Verification

```bash
# Run baseline tests to verify parity
pytest tests/baseline/test_canonical.py -v
pytest tests/baseline/test_view_level.py -v
```

## Full Migration Guide

See [MIGRATION_GUIDE.md](../../MIGRATION_GUIDE.md) for detailed migration instructions.
