# Quickstart

Get started with Chunkana in under a minute.

## Installation

```bash
pip install chunkana
```

## Basic Usage

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

## With Custom Configuration

```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=100,
)

chunks = chunk_markdown(text, config)
```

## Rendering Output

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_json

chunks = chunk_markdown(text)

# As JSON dictionaries
json_output = render_json(chunks)

# With metadata blocks (Dify-compatible)
dify_output = render_dify_style(chunks)
```

## Next Steps

- [Configuration Guide](config.md) — all configuration options
- [Strategies](strategies.md) — how chunking strategies work
- [Renderers](renderers.md) — output formatting options
