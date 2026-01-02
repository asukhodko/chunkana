# Dify Integration

Using Chunkana with Dify workflows.

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

## Parameter Mapping

| Dify Parameter | Chunkana Equivalent |
|----------------|---------------------|
| `max_chunk_size` | `ChunkerConfig.max_chunk_size` |
| `overlap_size` | `ChunkerConfig.overlap_size` |
| `include_metadata=True` | `render_dify_style()` |
| `include_metadata=False` | `render_with_embedded_overlap()` |

## Metadata Format

With `render_dify_style()`, each chunk includes:

```
<metadata>
{
  "chunk_index": 0,
  "content_type": "section",
  "header_path": "/Introduction",
  "start_line": 1,
  "end_line": 10,
  "strategy": "structural"
}
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

## Migration from dify-markdown-chunker

See [MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md) for detailed migration instructions.
