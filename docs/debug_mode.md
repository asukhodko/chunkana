# Debug Mode Documentation

## Overview

This document describes the metadata behavior in chunkana across different chunking modes.

## Metadata Behavior

### Standard Chunking Mode

When using `chunker.chunk(document)`, chunks contain:

- `content_type`: Type of content (section, preamble, etc.)
- `header_path`: Hierarchical path to the chunk
- `header_level`: Level of the header (1-6)
- `chunk_index`: Position in the chunk list
- `strategy`: Chunking strategy used

### Hierarchical Chunking Mode

When using `chunker.chunk_hierarchical(document)`, chunks contain additional metadata:

- All fields from standard mode
- `chunk_id`: Unique identifier for the chunk
- `parent_id`: ID of parent chunk
- `children_ids`: IDs of child chunks
- `is_leaf`: Whether chunk is a leaf node (no children)
- `is_root`: Whether chunk is the root node
- `hierarchy_level`: Depth in the tree (0=root, 1=sections, etc.)
- `prev_sibling_id`: ID of previous sibling (if any)
- `next_sibling_id`: ID of next sibling (if any)

## Hierarchical Mode Specifics

### get_flat_chunks()

The `get_flat_chunks()` method returns chunks suitable for flat retrieval:

1. **Leaf chunks** (no children) are always included
2. **Non-leaf chunks** with significant content (>100 chars excluding headers) are also included
3. **Root chunks** are excluded

This ensures no content is lost when using flat retrieval mode.

### Navigation Methods

Navigation methods (`get_parent()`, `get_children()`, `get_siblings()`, `get_ancestors()`) work in hierarchical mode using internal chunk IDs.

## Examples

### Basic Usage

```python
from chunkana import MarkdownChunker, ChunkConfig

# Standard chunking
config = ChunkConfig(max_chunk_size=1000)
chunker = MarkdownChunker(config)
chunks = chunker.chunk(document)
```

### Hierarchical Mode

```python
# Hierarchical chunking
config = ChunkConfig(max_chunk_size=1000)
chunker = MarkdownChunker(config)
result = chunker.chunk_hierarchical(document)

# Access all chunks
all_chunks = result.chunks

# Access only leaf chunks (for flat retrieval)
flat_chunks = result.get_flat_chunks()

# Navigate hierarchy
root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
```

## Invariant Validation

Enable invariant validation to catch tree structure issues:

```python
config = ChunkConfig(
    max_chunk_size=1000,
    min_chunk_size=100,
    validate_invariants=True,  # Enable invariant validation
    strict_mode=False  # Log warnings instead of raising exceptions
)
```

### Validated Invariants

1. **is_leaf consistency**: `is_leaf` equals `(children_ids is empty)`
2. **Parent-child bidirectionality**: Parent-child relationships are mutual
3. **Content range consistency**: Root chunks have consistent content ranges
