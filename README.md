# Chunkana

[![GitHub Repository](https://img.shields.io/badge/GitHub-Chunkana-181717?logo=github)](https://github.com/asukhodko/chunkana)
[![PyPI version](https://img.shields.io/pypi/v/chunkana.svg)](https://pypi.org/project/chunkana/)
[![Python versions](https://img.shields.io/pypi/pyversions/chunkana.svg)](https://pypi.org/project/chunkana/)
[![License](https://img.shields.io/pypi/l/chunkana.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/chunkana.svg)](https://pypi.org/project/chunkana/)

**Chunkana** is a high-precision Markdown chunking library for RAG pipelines, search indexing, and LLM ingestion. It produces semantically correct Markdown chunks by respecting headers, code blocks, tables, and LaTeX while keeping the output retrieval-ready.

If you're looking for a **semantic Markdown chunker**, **Markdown splitter**, or **Markdown document segmenter** that preserves structure for LLM context windows, Chunkana is built for exactly that.

## Why Chunkana

Chunkana turns messy Markdown into clean, structured chunks that retain meaning:

- **Semantic correctness**: preserves headers, lists, tables, code blocks, and math without splitting them mid-block.
- **RAG-ready metadata**: header paths, content types, line ranges, and overlap context.
- **Smart strategy selection**: automatically adapts to code-heavy, list-heavy, or structural documents.
- **Hierarchical navigation**: build a chunk tree for section-aware retrieval.
- **Streaming for large files**: chunk multi-megabyte documents without loading everything into memory.
- **Compatibility**: output formats for Dify and JSON APIs.

## Installation

```bash
pip install chunkana
```

Optional extras:

```bash
pip install "chunkana[docs]"
```

## Quick start

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
    print(f"{chunk.start_line}-{chunk.end_line}: {chunk.metadata['header_path']}")
```

## Usage examples

### 1) Tune chunk sizes and overlap

```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
)

chunks = chunk_markdown(text, config)
```

### 2) Build a hierarchical chunk tree

```python
from chunkana import MarkdownChunker, ChunkConfig

chunker = MarkdownChunker(ChunkConfig(validate_invariants=True))
result = chunker.chunk_hierarchical(text)

root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
flat_chunks = result.get_flat_chunks()  # leaf + significant parent chunks
```

### 3) Stream large Markdown files

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()
for chunk in chunker.chunk_file_streaming("docs/handbook.md"):
    print(chunk.metadata["chunk_index"], chunk.size)
```

### 4) Emit Dify-compatible output

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

chunks = chunk_markdown(text)
output = render_dify_style(chunks)
```

### 5) Adaptive chunk sizing for mixed documents

```python
from chunkana import chunk_markdown, ChunkerConfig
from chunkana.adaptive_sizing import AdaptiveSizeConfig

config = ChunkerConfig(
    use_adaptive_sizing=True,
    adaptive_config=AdaptiveSizeConfig(
        base_size=1500,
        code_weight=0.4,
        min_size=500,
        max_size=8000,
    ),
)

chunks = chunk_markdown(text, config)
```

## Renderers

```python
from chunkana.renderers import (
    render_dify_style,
    render_json,
    render_inline_metadata,
    render_with_embedded_overlap,
)
```

- **render_dify_style** — `<metadata>` blocks for Dify.
- **render_json** — list of dictionaries for JSON APIs.
- **render_inline_metadata** — HTML comment metadata inline.
- **render_with_embedded_overlap** — injects overlap into text for RAG windows.

## Integrations

- [Dify](docs/integrations/dify.md)
- [n8n](docs/integrations/n8n.md)
- [Windmill](docs/integrations/windmill.md)

## Documentation

- [Overview](docs/overview.md)
- [Quick Start](docs/quickstart.md)
- [Configuration](docs/config.md)
- [Strategies](docs/strategies.md)
- [Renderers](docs/renderers.md)
- [Debug Mode](docs/debug_mode.md)
- [Migration Guide](MIGRATION_GUIDE.md)

## FAQ

**Q: What makes Chunkana different from a basic Markdown splitter?**

Chunkana is a **semantic Markdown chunker** that keeps structure intact (headers, lists, code blocks, tables, LaTeX) and enriches each chunk with retrieval metadata. This yields more accurate search and RAG results than naive line-based splitting.

**Q: Does Chunkana work for RAG and LLM ingestion?**

Yes. Chunkana is optimized for **RAG chunking**, **LLM context window preparation**, and **semantic Markdown segmentation**. It provides overlap metadata and consistent hierarchy paths for retrieval pipelines.

## License

MIT
