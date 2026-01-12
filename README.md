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

````python
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
````

## What You Get

- **Structure-safe chunks**: never split code blocks, tables, lists, or LaTeX blocks
- **Useful metadata**: `header_path`, `content_type`, line ranges, and strategy used
- **Multiple strategies**: automatic selection or manual override
- **Hierarchy support**: navigate a chunk tree or flatten it for indexing
- **Streaming options**: process large files without loading them all into memory

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
- **Code-context binding**: Keep code with the explanation around it
- **Adaptive sizing**: Optional size tuning based on document complexity
- **Table grouping**: Keep related tables together for better retrieval
- **Obsidian cleanup**: Strip `^block-id` references when desired

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

### Content Analysis and Metrics

```python
from chunkana import analyze_markdown, chunk_with_metrics

analysis = analyze_markdown(text)
print(f"Code ratio: {analysis.code_ratio}")

chunks, metrics = chunk_with_metrics(text)
print(f"Average chunk size: {metrics.avg_chunk_size}")
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

### Advanced Configuration Highlights

```python
from chunkana import ChunkConfig
from chunkana.adaptive_sizing import AdaptiveSizeConfig
from chunkana.table_grouping import TableGroupingConfig

config = ChunkConfig(
    max_chunk_size=4096,
    overlap_size=200,
    enable_code_context_binding=True,
    preserve_latex_blocks=True,
    strip_obsidian_block_ids=True,
    use_adaptive_sizing=True,
    adaptive_config=AdaptiveSizeConfig(base_size=1500, code_weight=0.4),
    group_related_tables=True,
    table_grouping_config=TableGroupingConfig(max_distance_lines=10),
)
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

## Core API Surface

Primary convenience functions:

- `chunk_markdown(text, config=None)` → `List[Chunk]`
- `chunk_hierarchical(text, config=None)` → `HierarchicalChunkingResult`
- `chunk_file(path, config=None)` / `chunk_file_streaming(path, config=None)`
- `analyze_markdown(text, config=None)` → `ContentAnalysis`
- `chunk_with_metrics(text, config=None)` → `(List[Chunk], ChunkingMetrics)`
- `iter_chunks(text, config=None)` → `Iterator[Chunk]`

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
- **[Metadata Reference](docs/metadata.md)** - Chunk metadata definitions
- **[Performance Guide](docs/performance.md)** - Tuning for speed and memory
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
