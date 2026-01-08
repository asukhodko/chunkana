# Quickstart

Get started with Chunkana in under a minute.

## Installation

```bash
pip install chunkana
```

## Basic usage

```python
from chunkana import chunk_markdown

text = """
# Introduction

This is a sample document with multiple sections.

## Section 1

Content of section 1 with some details.

## Section 2

Content of section 2 with more information.
"""

chunks = chunk_markdown(text)

for chunk in chunks:
    print(f"Lines {chunk.start_line}-{chunk.end_line}: {chunk.content[:50]}...")
```

## With custom configuration

```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=100,
)

chunks = chunk_markdown(text, config)
```

## Hierarchical chunking

```python
from chunkana import MarkdownChunker, ChunkConfig

chunker = MarkdownChunker(ChunkConfig(validate_invariants=True))
result = chunker.chunk_hierarchical(text)

# Leaf + significant parent chunks
flat_chunks = result.get_flat_chunks()

# Navigate the hierarchy
root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
```

## Streaming large documents

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()
for chunk in chunker.chunk_file_streaming("docs/handbook.md"):
    print(chunk.metadata["chunk_index"], chunk.size)
```

## Rendering output

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_json

chunks = chunk_markdown(text)

# As JSON dictionaries
json_output = render_json(chunks)

# With metadata blocks (Dify-compatible)
dify_output = render_dify_style(chunks)
```

## Next steps

- [Overview](overview.md)
- [Configuration Guide](config.md)
- [Strategies](strategies.md)
- [Renderers](renderers.md)
- [Integrations](integrations/dify.md)
