# Chunkana

Intelligent Markdown chunking library for RAG systems.

## Features

- 🧠 **Smart chunking**: Automatically selects optimal strategy based on content
- 📦 **Atomic blocks**: Preserves code blocks, tables, and LaTeX formulas
- 🌳 **Hierarchical**: Navigate chunks by header structure
- 📊 **Rich metadata**: Header paths, content types, overlap context
- 🔄 **Streaming**: Process large files (>10MB) efficiently
- 🎯 **Multiple renderers**: JSON, inline metadata, Dify-compatible

## Installation

```bash
pip install chunkana
```

## Quick Start

```python
from chunkana import chunk_markdown

text = """
# My Document

## Section One

Some content here.

## Section Two

More content with code:

```python
def hello():
    print("Hello!")
```
"""

chunks = chunk_markdown(text)
for chunk in chunks:
    print(f"Lines {chunk.start_line}-{chunk.end_line}: {chunk.metadata['header_path']}")
```

## Configuration

```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
)

chunks = chunk_markdown(text, config)
```

## Renderers

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_json

chunks = chunk_markdown(text)

# JSON output
json_output = render_json(chunks)

# Dify-compatible format
dify_output = render_dify_style(chunks)
```

## Documentation

- [Quick Start](docs/quickstart.md)
- [Configuration](docs/config.md)
- [Strategies](docs/strategies.md)
- [Renderers](docs/renderers.md)

## License

MIT
