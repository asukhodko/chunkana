# FAQ

<cite>
**Referenced Files in This Document**   
- [faq.md](file://docs/faq.md)
- [README.md](file://README.md)
- [config.py](file://src/chunkana/config.py)
- [chunker.py](file://src/chunkana/chunker.py)
- [types.py](file://src/chunkana/types.py)
- [base.py](file://src/chunkana/strategies/base.py)
- [streaming_chunker.py](file://src/chunkana/streaming/streaming_chunker.py)
- [exceptions.py](file://src/chunkana/exceptions.py)
- [api.py](file://src/chunkana/api.py)
</cite>

## Table of Contents
1. [General Questions](#general-questions)
2. [Configuration Questions](#configuration-questions)
3. [Strategy Questions](#strategy-questions)
4. [Hierarchical Chunking Questions](#hierarchical-chunking-questions)
5. [Performance Questions](#performance-questions)
6. [Integration Questions](#integration-questions)
7. [Troubleshooting Questions](#troubleshooting-questions)
8. [Migration Questions](#migration-questions)
9. [Advanced Questions](#advanced-questions)
10. [Still Have Questions?](#still-have-questions)

## General Questions

### What makes Chunkana different from other text splitters?

Chunkana is a **semantic chunker** that preserves Markdown structure, while most splitters treat documents as plain text. Key differences:
- **Structure preservation**: Never breaks code blocks, tables, lists, or LaTeX formulas
- **Rich metadata**: Every chunk includes header paths, content types, and line ranges
- **Smart strategies**: Automatically adapts to code-heavy, list-heavy, or narrative content
- **Hierarchical support**: Can build chunk trees that mirror document structure

### When should I use Chunkana vs. a simple text splitter?

Use Chunkana when:
- ✅ Your documents contain code blocks, tables, or structured content
- ✅ You need metadata for filtering and ranking in retrieval
- ✅ Document structure matters for your use case
- ✅ You're building RAG systems that need semantic coherence

Use simple splitters when:
- ❌ You only have plain text documents
- ❌ You need maximum speed over quality
- ❌ Structure doesn't matter for your application

### Is Chunkana suitable for production use?

Yes, but with considerations:
- **Status**: Beta (APIs may evolve)
- **Performance**: Handles multi-megabyte documents efficiently
- **Memory**: Streaming support for large files
- **Testing**: Comprehensive test suite with baseline compatibility
- **Support**: Active maintenance and issue tracking

**Section sources**
- [faq.md](file://docs/faq.md#L29-L37)
- [README.md](file://README.md#L49-L59)

## Configuration Questions

### How do I choose the right chunk size?

Chunk size depends on your downstream system:
- **For embedding models** (typical: 512-2048 tokens): `max_chunk_size=1500` (~300-400 tokens)
- **For LLM context windows**: `max_chunk_size=4000` (~800-1000 tokens)
- **For search indexing**: `max_chunk_size=2500` (Balance detail vs. precision)

**Rule of thumb**: 4-5 characters ≈ 1 token for English text.

### What's the difference between `max_chunk_size` and `min_chunk_size`?

- **`max_chunk_size`**: Hard limit - chunks will never exceed this size
- **`min_chunk_size`**: Soft target - smaller chunks may be merged with neighbors

```python
config = ChunkConfig(
    max_chunk_size=2000,  # Never exceed 2000 chars
    min_chunk_size=500,   # Try to merge chunks smaller than 500 chars
)
```

### How does overlap work?

Overlap provides context continuity without duplicating content:
- **Storage**: Overlap is stored in metadata, not embedded in `chunk.content`
- **Access**: Use `chunk.metadata['previous_content']` and `chunk.metadata['next_content']`
- **Capping**: Overlap is limited to 35% of adjacent chunk size

```python
config = ChunkConfig(overlap_size=200)

chunks = chunk_markdown(text, config)
chunk = chunks[1]  # Second chunk

print("Current content:", chunk.content[:100])
print("Previous context:", chunk.metadata.get('previous_content', '')[:50])
print("Next context:", chunk.metadata.get('next_content', '')[:50])
```

**Section sources**
- [faq.md](file://docs/faq.md#L40-L86)
- [config.py](file://src/chunkana/config.py#L78-L80)
- [chunker.py](file://src/chunkana/chunker.py#L351-L377)

## Strategy Questions

### How does automatic strategy selection work?

Chunkana analyzes document content and selects the best strategy:
1. **Code-aware**: If code ratio > 30% (configurable)
2. **List-aware**: If list content > 40% and 5+ lists (configurable)
3. **Structural**: If 3+ headers (configurable)
4. **Fallback**: For edge cases and mixed content

```python
# Check which strategy was used
chunks = chunk_markdown(text)
print(f"Strategy used: {chunks[0].metadata['strategy']}")
```

### Can I force a specific strategy?

Yes, use `strategy_override`:
```python
config = ChunkConfig(strategy_override="code_aware")
chunks = chunk_markdown(text, config)
```

Available strategies: `"code_aware"`, `"list_aware"`, `"structural"`, `"fallback"`

### Why are my code blocks being split?

This shouldn't happen with default settings. Check:
1. **Atomic blocks enabled**: `preserve_atomic_blocks=True` (default)
2. **Chunk size**: Very small `max_chunk_size` might force splits
3. **Strategy**: Code-aware strategy handles code better

```python
# Debug configuration
config = ChunkConfig(
    preserve_atomic_blocks=True,  # Ensure this is True
    max_chunk_size=4096,          # Increase if too small
    strategy_override="code_aware"  # Force code-aware strategy
)
```

**Section sources**
- [faq.md](file://docs/faq.md#L90-L131)
- [config.py](file://src/chunkana/config.py#L87-L93)
- [base.py](file://src/chunkana/strategies/base.py#L39-L40)

## Hierarchical Chunking Questions

### What's the difference between flat and hierarchical chunking?

- **Flat chunking**: `chunk_markdown()` - returns a simple list of chunks
- **Hierarchical chunking**: `chunk_hierarchical()` - returns a tree structure

```python
# Flat chunking
chunks = chunk_markdown(text)  # List[Chunk]

# Hierarchical chunking
result = chunker.chunk_hierarchical(text)  # ChunkHierarchy
all_chunks = result.chunks                 # All nodes in tree
flat_chunks = result.get_flat_chunks()     # Leaf nodes for indexing
```

### When should I use hierarchical chunking?

Use hierarchical chunking when you need:
- **Navigation**: Moving between parent/child sections
- **Summarization**: Building section summaries from children
- **Context**: Understanding document structure
- **Filtering**: Finding chunks within specific sections

### What are "flat chunks" in hierarchical mode?

Flat chunks are the subset suitable for indexing:
- **Leaf chunks**: Chunks with no children
- **Significant parents**: Parent chunks with substantial content (>100 chars)

```python
result = chunker.chunk_hierarchical(text)

# For vector database indexing
indexable_chunks = result.get_flat_chunks()

# For navigation and summaries
all_chunks = result.chunks
```

**Section sources**
- [faq.md](file://docs/faq.md#L135-L172)
- [api.py](file://src/chunkana/api.py#L273-L304)
- [types.py](file://src/chunkana/types.py#L432-L477)

## Performance Questions

### How fast is Chunkana?

Performance scales linearly with document size:
- **Small docs** (~100 lines): ~0.1ms
- **Medium docs** (~1000 lines): ~0.7ms  
- **Large docs** (~10000 lines): ~2.7ms

Validation adds <20% overhead.

### How do I process large documents efficiently?

Use streaming for memory efficiency:
```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()

# Stream chunks without loading entire document
for chunk in chunker.chunk_file_streaming("large_document.md"):
    process_chunk(chunk)  # Process immediately
```

### Can I process multiple documents in parallel?

Yes, Chunkana is thread-safe:
```python
from concurrent.futures import ThreadPoolExecutor
from chunkana import chunk_markdown

def process_file(file_path):
    with open(file_path, 'r') as f:
        text = f.read()
    return chunk_markdown(text)

# Process multiple files in parallel
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_file, file_paths))
```

**Section sources**
- [faq.md](file://docs/faq.md#L176-L215)
- [streaming_chunker.py](file://src/chunkana/streaming/streaming_chunker.py#L18-L99)
- [api.py](file://src/chunkana/api.py#L228-L271)

## Integration Questions

### How do I integrate with Dify?

Use the Dify renderer for compatible output:
```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

chunks = chunk_markdown(text)
dify_output = render_dify_style(chunks)

# Each item has metadata block format expected by Dify
print(dify_output[0])
```

See [Dify Integration Guide](docs/integrations/dify.md) for details.

### How do I integrate with vector databases?

Use JSON renderer and enrich metadata:
```python
from chunkana.renderers import render_json

chunks = chunk_markdown(text)
json_chunks = render_json(chunks)

# Enrich for your vector database
for chunk_data in json_chunks:
    chunk_data['metadata']['source'] = 'user_manual.md'
    chunk_data['metadata']['timestamp'] = '2024-01-01'
    
    # Create embedding
    embedding = create_embedding(chunk_data['content'])
    chunk_data['embedding'] = embedding
```

### Can I customize the output format?

Yes, create custom renderers:
```python
def render_custom(chunks):
    """Custom renderer for your specific format."""
    result = []
    for chunk in chunks:
        item = {
            'text': chunk.content,
            'section': chunk.metadata['header_path'],
            'type': chunk.metadata['content_type'],
            'position': f"{chunk.start_line}-{chunk.end_line}",
            # Add your custom fields
        }
        result.append(item)
    return result

# Usage
chunks = chunk_markdown(text)
custom_output = render_custom(chunks)
```

**Section sources**
- [faq.md](file://docs/faq.md#L217-L278)
- [__init__.py](file://src/chunkana/__init__.py#L51-L58)
- [api.py](file://src/chunkana/api.py#L18-L40)

## Troubleshooting Questions

### Why am I getting empty chunks?

Empty chunks usually indicate:
1. **Document structure issues**: Malformed Markdown
2. **Configuration problems**: `min_chunk_size` too high
3. **Content filtering**: Headers without content

Debug with:
```python
chunks = chunk_markdown(text)
empty_chunks = [i for i, c in enumerate(chunks) if not c.content.strip()]
print(f"Empty chunks at indices: {empty_chunks}")
```

### Why are my chunks too large/small?

Check your configuration:
```python
# For smaller chunks
config = ChunkConfig(
    max_chunk_size=1500,  # Reduce maximum
    min_chunk_size=200,   # Reduce minimum
)

# For larger chunks  
config = ChunkConfig(
    max_chunk_size=6000,  # Increase maximum
    min_chunk_size=800,   # Increase minimum
)
```

### How do I debug chunking behavior?

Enable debug mode and examine metadata:
```python
from chunkana import MarkdownChunker, ChunkConfig

config = ChunkConfig(validate_invariants=True)
chunker = MarkdownChunker(config)

chunks = chunk_markdown(text, config)

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"  Strategy: {chunk.metadata['strategy']}")
    print(f"  Content type: {chunk.metadata['content_type']}")
    print(f"  Header: {chunk.metadata['header_path']}")
    print(f"  Size: {chunk.size}")
    print(f"  Lines: {chunk.start_line}-{chunk.end_line}")
```

### What do the error messages mean?

Common errors and solutions:
- **`ChunkanaError`**: General chunking failure - check document format
- **`HierarchicalInvariantError`**: Tree structure issue - disable validation or fix document
- **`ValidationError`**: Configuration problem - check parameter values
- **`ConfigurationError`**: Invalid config - verify all parameters

See [Error Guide](docs/errors.md) for detailed troubleshooting.

**Section sources**
- [faq.md](file://docs/faq.md#L281-L344)
- [exceptions.py](file://src/chunkana/exceptions.py#L11-L248)
- [chunker.py](file://src/chunkana/chunker.py#L440-L486)

## Migration Questions

### How do I migrate from dify-markdown-chunker?

Chunkana maintains compatibility with dify-markdown-chunker v2:
```python
# Old way (dify-markdown-chunker)
from dify_markdown_chunker import chunk_markdown as old_chunk

# New way (Chunkana)
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style

# Same parameters work
chunks = chunk_markdown(text, max_chunk_size=4096)
dify_format = render_dify_style(chunks)
```

See [Migration Guide](docs/migration/) for complete details.

### Are there any breaking changes?

Main differences from dify-markdown-chunker:
1. **Return type**: Returns `List[Chunk]` objects instead of strings
2. **Metadata location**: Use renderers to get string output with metadata
3. **Import path**: `from chunkana import chunk_markdown`

Functionality is otherwise compatible.

**Section sources**
- [faq.md](file://docs/faq.md#L346-L374)
- [README.md](file://README.md#L350-L365)
- [api.py](file://src/chunkana/api.py#L18-L40)

## Advanced Questions

### Can I extend Chunkana with custom strategies?

Currently, strategies are internal. For custom behavior:
1. **Use configuration**: Tune thresholds and parameters
2. **Post-process chunks**: Modify results after chunking
3. **Custom renderers**: Format output for your needs

Future versions may support custom strategies.

### How does Chunkana handle edge cases?

Chunkana includes robust handling for:
- **Malformed Markdown**: Fallback strategies
- **Mixed content**: Adaptive strategy selection  
- **Large blocks**: Atomic preservation with size limits
- **Empty sections**: Intelligent merging
- **Nested structures**: Hierarchical processing

### Can I contribute to Chunkana?

Yes! See [CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Development setup
- Code style guidelines
- Testing procedures
- Pull request process

We welcome bug reports, feature requests, and code contributions.

**Section sources**
- [faq.md](file://docs/faq.md#L376-L405)
- [README.md](file://README.md#L216-L223)
- [config.py](file://src/chunkana/config.py#L127-L507)

## Still Have Questions?

- **Documentation**: Browse the [complete documentation](index.md)
- **Examples**: Check out [practical examples](examples.md)
- **Issues**: [Report bugs or ask questions](https://github.com/asukhodko/chunkana/issues)
- **Discussions**: [Join community discussions](https://github.com/asukhodko/chunkana/discussions)

**Section sources**
- [faq.md](file://docs/faq.md#L407-L412)
- [errors.md](file://docs/errors.md#L442-L460)