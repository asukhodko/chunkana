# n8n Integration

Using Chunkana with n8n workflows.

## Setup

Install Chunkana in your n8n Python environment:

```bash
pip install chunkana
```

## Code Node Example

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_json

def process(items):
    results = []
    
    for item in items:
        text = item.get("text", "")
        chunks = chunk_markdown(text)
        
        results.append({
            "chunks": render_json(chunks),
            "chunk_count": len(chunks),
        })
    
    return results
```

## With Configuration

```python
from chunkana import chunk_markdown, ChunkerConfig
from chunkana.renderers import render_json

config = ChunkerConfig(
    max_chunk_size=2048,
    overlap_size=100,
)

def process(items):
    results = []
    
    for item in items:
        text = item.get("text", "")
        chunks = chunk_markdown(text, config)
        
        results.append({
            "chunks": render_json(chunks),
        })
    
    return results
```

## Output Format

Each chunk in `render_json()` output:

```json
{
  "content": "Chunk text content...",
  "start_line": 1,
  "end_line": 10,
  "size": 256,
  "line_count": 10,
  "metadata": {
    "chunk_index": 0,
    "strategy": "structural",
    "header_path": "/Section 1",
    "content_type": "section"
  }
}
```

## Streaming Large Documents

For large documents, use streaming:

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()

def process_large(items):
    results = []
    
    for item in items:
        file_path = item.get("file_path")
        chunks = list(chunker.chunk_file_streaming(file_path))
        
        results.append({
            "chunks": [c.to_dict() for c in chunks],
        })
    
    return results
```
