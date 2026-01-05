# Chunkana

Intelligent Markdown chunking library for RAG systems.

## Features

- 🧠 **Smart chunking**: Automatically selects optimal strategy based on content
- 📦 **Atomic blocks**: Preserves code blocks, tables, and LaTeX formulas
- 🌳 **Hierarchical**: Navigate chunks by header structure with tree invariant validation
- 📊 **Rich metadata**: Header paths, content types, overlap context
- 🔄 **Streaming**: Process large files (>10MB) efficiently
- 🎯 **Multiple renderers**: JSON, inline metadata, Dify-compatible
- ✅ **Quality assurance**: Automatic dangling header prevention and micro-chunk minimization

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

### Hierarchical Chunking Configuration

For hierarchical chunking with tree structure validation:

```python
from chunkana import MarkdownChunker, ChunkConfig

config = ChunkConfig(
    max_chunk_size=1000,
    min_chunk_size=100,
    overlap_size=100,
    validate_invariants=True,  # Enable tree invariant validation (default: True)
    strict_mode=False,         # Auto-fix violations vs raise exceptions (default: False)
)

chunker = MarkdownChunker(config)
result = chunker.chunk_hierarchical(text)

# Navigate the hierarchy
root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
flat_chunks = result.get_flat_chunks()
```

**Configuration options:**
- `validate_invariants` (default: `True`): Validates tree invariants after construction
- `strict_mode` (default: `False`): When `True`, raises exceptions on invariant violations; when `False`, auto-fixes issues and logs warnings

## Exception Handling

Chunkana provides a hierarchy of exceptions for error handling:

```python
from chunkana import (
    ChunkanaError,              # Base exception for all chunkana errors
    HierarchicalInvariantError, # Tree structure violations
    ValidationError,            # Validation failures
    ConfigurationError,         # Invalid configuration
    TreeConstructionError,      # Tree building failures
)

try:
    result = chunker.chunk_hierarchical(text)
except HierarchicalInvariantError as e:
    print(f"Invariant violation: {e.invariant}")
    print(f"Chunk ID: {e.chunk_id}")
    print(f"Suggested fix: {e.suggested_fix}")
except ChunkanaError as e:
    print(f"Chunking error: {e}")
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

## Quality Features

### Dangling Header Prevention

Chunkana automatically prevents headers from being separated from their content. When a chunk would end with a header (like `#### Details`), the header is moved to the next chunk to maintain semantic coherence.

### Micro-Chunk Minimization

Small chunks are intelligently merged with adjacent content when they lack structural significance, reducing fragmentation while preserving important standalone elements like code blocks and tables.

### Tree Invariant Validation

Hierarchical chunking validates:
- **is_leaf consistency**: Leaf status matches children presence
- **Parent-child bidirectionality**: All relationships are symmetric
- **No orphaned chunks**: Every chunk is reachable from root

### Line Range Contract (Hierarchical Mode)

In hierarchical chunking mode, `start_line` and `end_line` follow a specific contract:

- **Leaf nodes**: Line range covers only the chunk's own content
- **Internal nodes**: Line range covers only the node's own content (not children)
- **Root node**: Line range covers the entire document (1 to last line)

**Important**: The sum of children's line ranges does NOT equal the parent's range. The parent contains only its "header" content, while children contain detailed content. This is by design for hierarchical navigation.

```python
result = chunker.chunk_hierarchical(text)
root = result.get_chunk(result.root_id)

# Root covers entire document
print(f"Root: lines {root.start_line}-{root.end_line}")

# Children cover their own sections
for child in result.get_children(result.root_id):
    print(f"Child: lines {child.start_line}-{child.end_line}")
```

## Documentation

- [Quick Start](docs/quickstart.md)
- [Configuration](docs/config.md)
- [Strategies](docs/strategies.md)
- [Renderers](docs/renderers.md)
- [Debug Mode](docs/debug_mode.md)
- [Migration Guide](MIGRATION_GUIDE.md)

## License

MIT
