# Chunkana

A semantic Markdown chunker that preserves document structure for RAG and LLM pipelines. Never breaks code blocks, tables, or headers—every chunk stays semantically complete.

[![GitHub Repository](https://img.shields.io/badge/GitHub-Chunkana-181717?logo=github)](https://github.com/asukhodko/chunkana)
[![PyPI version](https://img.shields.io/pypi/v/chunkana.svg)](https://pypi.org/project/chunkana/)
[![Python versions](https://img.shields.io/pypi/pyversions/chunkana.svg)](https://pypi.org/project/chunkana/)
[![License](https://img.shields.io/pypi/l/chunkana.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/chunkana.svg)](https://pypi.org/project/chunkana/)

## Quick Start

```bash
pip install chunkana
```

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
    print(f"Content: {chunk.content[:100]}...")
```

## Why Chunkana?

**Problem**: Traditional splitters break Markdown structure, fragmenting code blocks, tables, and lists.

**Solution**: Chunkana preserves semantic boundaries while providing rich metadata for retrieval:

- ✅ **Never breaks** code blocks, tables, or LaTeX formulas
- ✅ **Preserves hierarchy** with header paths like `/Introduction/Overview`
- ✅ **Rich metadata** for filtering, ranking, and context
- ✅ **Streaming support** for large documents
- ✅ **Multiple output formats** (JSON, Dify-compatible, etc.)

## Key Features

- **Semantic preservation**: Headers, lists, tables, code blocks, and LaTeX stay intact
- **Smart strategies**: Auto-selects optimal chunking approach per document
- **Hierarchical navigation**: Build chunk trees for section-aware retrieval
- **Overlap metadata**: Context continuity without content duplication
- **Memory efficient**: Stream large files without loading everything into RAM

## Usage Examples

### Basic Configuration

```python
from chunkana import chunk_markdown, ChunkConfig

config = ChunkConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=100,
)

chunks = chunk_markdown(text, config)
```

### Hierarchical Chunking

```python
from chunkana import MarkdownChunker, ChunkConfig

chunker = MarkdownChunker(ChunkConfig(validate_invariants=True))
result = chunker.chunk_hierarchical(text)

# Get leaf chunks for indexing
flat_chunks = result.get_flat_chunks()

# Navigate the hierarchy
root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
```

### Streaming Large Documents

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()
for chunk in chunker.chunk_file_streaming("large_document.md"):
    print(f"Chunk {chunk.metadata['chunk_index']}: {chunk.size} chars")
```

### Output Formats

```python
from chunkana.renderers import render_json, render_dify_style

chunks = chunk_markdown(text)

# JSON format
json_output = render_json(chunks)

# Dify-compatible format
dify_output = render_dify_style(chunks)
```

## Metadata Schema

Each chunk includes rich metadata for retrieval:

```python
{
    "content": "# Section\nContent here...",
    "start_line": 1,
    "end_line": 10,
    "size": 156,
    "metadata": {
        "chunk_index": 0,
        "content_type": "section",
        "header_path": "/Introduction/Overview",
        "header_level": 2,
        "strategy": "structural",
        "has_code": false,
        "overlap_size": 100
    }
}
```

## Requirements

- **Python 3.12+**
- No external dependencies for core functionality
- Optional: `pip install "chunkana[docs]"` for documentation tools

## Integrations

- **[Dify](docs/integrations/dify.md)**: Direct compatibility with Dify workflows
- **[n8n](docs/integrations/n8n.md)**: Automation pipeline integration  
- **[Windmill](docs/integrations/windmill.md)**: Batch processing workflows

## Documentation

- **[Quick Start Guide](docs/quickstart.md)** - Get started in minutes
- **[Configuration](docs/config.md)** - All configuration options
- **[Strategies](docs/strategies.md)** - How chunking strategies work
- **[Renderers](docs/renderers.md)** - Output format options
- **[API Reference](docs/api/)** - Complete API documentation

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Code style guidelines  
- Testing procedures
- Pull request process

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Need help?** Check the [documentation](docs/index.md) or [open an issue](https://github.com/asukhodko/chunkana/issues).
