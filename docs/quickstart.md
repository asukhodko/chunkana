# Quick Start Guide

Get up and running with Chunkana in under 5 minutes.

## Installation

```bash
pip install chunkana
```

## Basic Usage

The simplest way to chunk Markdown:

```python
from chunkana import chunk_markdown

text = """
# User Guide

## Getting Started
Welcome to our application! This section covers the basics.

### Installation
Run the following command:

```bash
pip install our-app
```

### Configuration
Edit your config file with these settings:

| Setting | Value | Description |
|---------|-------|-------------|
| debug   | false | Enable debug mode |
| port    | 8080  | Server port |

## Advanced Features
This section covers advanced functionality.
"""

# Chunk the document
chunks = chunk_markdown(text)

# Examine the results
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ---")
    print(f"Lines: {chunk.start_line}-{chunk.end_line}")
    print(f"Header: {chunk.metadata['header_path']}")
    print(f"Type: {chunk.metadata['content_type']}")
    print(f"Size: {chunk.size} characters")
    print(f"Content preview: {chunk.content[:100]}...")
```

## Custom Configuration

Control chunk size and behavior:

```python
from chunkana import chunk_markdown, ChunkConfig

# Create custom configuration
config = ChunkConfig(
    max_chunk_size=2048,    # Maximum chunk size in characters
    min_chunk_size=256,     # Minimum chunk size
    overlap_size=100,       # Overlap between chunks
)

# Apply configuration
chunks = chunk_markdown(text, config)

print(f"Generated {len(chunks)} chunks with custom settings")
```

## Hierarchical Chunking

For documents with complex structure:

```python
from chunkana import MarkdownChunker, ChunkConfig

# Create chunker with validation
chunker = MarkdownChunker(ChunkConfig(validate_invariants=True))

# Get hierarchical result
result = chunker.chunk_hierarchical(text)

# Get different chunk sets
all_chunks = result.chunks              # All chunks (including parents)
flat_chunks = result.get_flat_chunks()  # Leaf chunks for indexing

print(f"Total chunks: {len(all_chunks)}")
print(f"Indexable chunks: {len(flat_chunks)}")

# Navigate the hierarchy
root_id = result.root_id
root_chunk = result.get_chunk(root_id)
children = result.get_children(root_id)

print(f"Root chunk has {len(children)} direct children")
```

## Streaming Large Files

For memory-efficient processing of large documents:

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()

# Stream chunks from a file
for chunk in chunker.chunk_file_streaming("large_document.md"):
    print(f"Processing chunk {chunk.metadata['chunk_index']}")
    print(f"  Size: {chunk.size} characters")
    print(f"  Header: {chunk.metadata['header_path']}")
    
    # Process chunk (e.g., send to vector database)
    # process_chunk(chunk)
```

## Output Formats

Convert chunks to different formats:

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_json, render_dify_style

chunks = chunk_markdown(text)

# JSON format (for APIs)
json_output = render_json(chunks)
print("JSON format:")
print(json_output[0])  # First chunk as dict

# Dify-compatible format
dify_output = render_dify_style(chunks)
print("\nDify format:")
print(dify_output[0])  # First chunk with metadata block
```

## Examining Metadata

Understanding what information each chunk provides:

```python
from chunkana import chunk_markdown

chunks = chunk_markdown(text)
chunk = chunks[0]  # First chunk

print("Chunk metadata:")
print(f"  Index: {chunk.metadata['chunk_index']}")
print(f"  Content type: {chunk.metadata['content_type']}")
print(f"  Header path: {chunk.metadata['header_path']}")
print(f"  Header level: {chunk.metadata.get('header_level', 'N/A')}")
print(f"  Strategy: {chunk.metadata['strategy']}")
print(f"  Has code: {chunk.metadata['has_code']}")
print(f"  Line range: {chunk.start_line}-{chunk.end_line}")
print(f"  Size: {chunk.size} characters")
```

## Common Patterns

### RAG Pipeline Integration

```python
from chunkana import chunk_markdown, ChunkConfig

# RAG-optimized configuration
rag_config = ChunkConfig(
    max_chunk_size=1500,    # Fit in embedding context
    min_chunk_size=300,     # Ensure meaningful content
    overlap_size=150,       # Context continuity
)

chunks = chunk_markdown(document_text, rag_config)

# Process for vector database
for chunk in chunks:
    # Create embedding
    embedding = create_embedding(chunk.content)
    
    # Store with metadata
    store_in_vector_db(
        content=chunk.content,
        embedding=embedding,
        metadata={
            "header_path": chunk.metadata["header_path"],
            "content_type": chunk.metadata["content_type"],
            "source_lines": f"{chunk.start_line}-{chunk.end_line}",
            "has_code": chunk.metadata["has_code"],
        }
    )
```

### Content Analysis

```python
from chunkana import chunk_markdown

chunks = chunk_markdown(text)

# Analyze content distribution
content_types = {}
for chunk in chunks:
    content_type = chunk.metadata["content_type"]
    content_types[content_type] = content_types.get(content_type, 0) + 1

print("Content distribution:")
for content_type, count in content_types.items():
    print(f"  {content_type}: {count} chunks")

# Find code-heavy chunks
code_chunks = [c for c in chunks if c.metadata["has_code"]]
print(f"\nFound {len(code_chunks)} chunks with code")
```

## Next Steps

Now that you've got the basics:

- **[Configuration Guide](config.md)** - Learn about all configuration options
- **[Strategies](strategies.md)** - Understand how chunking strategies work
- **[Renderers](renderers.md)** - Explore output format options
- **[Integrations](integrations/dify.md)** - Connect to your workflow
- **[Metadata Reference](metadata.md)** - Complete metadata documentation

## Need Help?

- Check the [troubleshooting guide](errors.md) for common issues
- Browse [examples](examples/) for more use cases
- [Open an issue](https://github.com/asukhodko/chunkana/issues) if you're stuck
