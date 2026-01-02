# Windmill Integration

Using Chunkana with Windmill workflows.

## Setup

Add `chunkana` to your script dependencies:

```python
#requirements:
#chunkana
```

## Basic Script

```python
#requirements:
#chunkana

from chunkana import chunk_markdown
from chunkana.renderers import render_json

def main(text: str) -> dict:
    chunks = chunk_markdown(text)
    
    return {
        "chunks": render_json(chunks),
        "count": len(chunks),
    }
```

## With Configuration

```python
#requirements:
#chunkana

from chunkana import chunk_markdown, ChunkerConfig
from chunkana.renderers import render_json

def main(
    text: str,
    max_chunk_size: int = 4096,
    overlap_size: int = 200,
) -> dict:
    config = ChunkerConfig(
        max_chunk_size=max_chunk_size,
        overlap_size=overlap_size,
    )
    
    chunks = chunk_markdown(text, config)
    
    return {
        "chunks": render_json(chunks),
        "count": len(chunks),
    }
```

## Processing Files

```python
#requirements:
#chunkana

from chunkana import MarkdownChunker
from chunkana.renderers import render_json

def main(file_content: str) -> dict:
    chunker = MarkdownChunker()
    chunks = chunker.chunk(file_content)
    
    return {
        "chunks": render_json(chunks),
        "metadata": {
            "strategy": chunks[0].metadata.get("strategy") if chunks else None,
            "total_chunks": len(chunks),
        },
    }
```

## Hierarchical Output

```python
#requirements:
#chunkana

from chunkana import MarkdownChunker

def main(text: str) -> dict:
    chunker = MarkdownChunker()
    result = chunker.chunk_hierarchical(text)
    
    return {
        "tree": result.to_tree_dict(),
        "flat_chunks": [c.to_dict() for c in result.get_flat_chunks()],
        "root_id": result.root_id,
    }
```

## Error Handling

```python
#requirements:
#chunkana

from chunkana import chunk_markdown

def main(text: str) -> dict:
    if not text or not text.strip():
        return {"chunks": [], "error": None}
    
    try:
        chunks = chunk_markdown(text)
        return {
            "chunks": [c.to_dict() for c in chunks],
            "error": None,
        }
    except Exception as e:
        return {
            "chunks": [],
            "error": str(e),
        }
```
