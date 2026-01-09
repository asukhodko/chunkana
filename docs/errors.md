# Errors & Troubleshooting

This guide helps you understand and resolve common issues when using Chunkana.

## Exception Types

### ChunkanaError (Base Class)

All Chunkana-specific errors inherit from `ChunkanaError`. This base exception includes:
- Human-readable error message
- `context` dictionary with debugging details
- Stack trace for error location

```python
from chunkana.exceptions import ChunkanaError

try:
    chunks = chunk_markdown(problematic_text)
except ChunkanaError as e:
    print(f"Error: {e}")
    print(f"Context: {e.get_context()}")
```

**When to catch**: Use this to catch all Chunkana-specific errors in one place.

### ValidationError

Raised when chunk validation fails due to invalid data or configuration.

**Common causes**:
- Invalid line ranges (`start_line > end_line`)
- Missing required metadata fields
- Corrupted chunk data during serialization/deserialization

```python
from chunkana.exceptions import ValidationError

try:
    chunks = chunk_markdown(text, config)
except ValidationError as e:
    print(f"Validation failed: {e}")
    print(f"Error type: {e.error_type}")
    print(f"Suggested fix: {e.suggested_fix}")
```

**Solutions**:
- Verify input text is valid Markdown
- Check configuration parameters are within valid ranges
- Re-run chunking with clean input data

### HierarchicalInvariantError

Raised when hierarchical chunk tree structure is invalid.

**Common causes**:
- Corrupted parent-child relationships
- Missing chunk IDs in hierarchical mode
- Inconsistent `is_leaf` flags
- Manual modification of hierarchy metadata

```python
from chunkana.exceptions import HierarchicalInvariantError

try:
    result = chunker.chunk_hierarchical(text)
except HierarchicalInvariantError as e:
    print(f"Tree structure error: {e}")
    print(f"Problematic chunk ID: {e.chunk_id}")
```

**Solutions**:
- Use `strict_mode=False` to get warnings instead of errors
- Avoid manually modifying hierarchy metadata
- Use helper methods (`get_children`, `get_parent`) instead of direct access

### ConfigurationError

Raised when configuration parameters are invalid or incompatible.

**Common causes**:
- `overlap_size` larger than `max_chunk_size`
- Negative size parameters
- Invalid strategy names
- Incompatible parameter combinations

```python
from chunkana.exceptions import ConfigurationError

try:
    config = ChunkConfig(
        max_chunk_size=1000,
        overlap_size=1500,  # Invalid: larger than max_chunk_size
    )
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Parameter: {e.parameter_name}")
    print(f"Valid values: {e.valid_values}")
```

**Solutions**:
- Validate configuration early
- Check parameter documentation
- Use factory methods like `ChunkConfig.default()`

### TreeConstructionError

Raised when hierarchical tree cannot be built from chunks.

**Common causes**:
- Malformed document structure
- Missing or duplicate headers
- Circular references in hierarchy

```python
from chunkana.exceptions import TreeConstructionError

try:
    result = chunker.chunk_hierarchical(text)
except TreeConstructionError as e:
    print(f"Tree construction failed: {e}")
    # Fall back to flat chunking
    chunks = chunk_markdown(text)
```

**Solutions**:
- Check document has proper header hierarchy
- Use flat chunking as fallback
- Validate Markdown structure

## Common Issues

### Empty or Very Small Chunks

**Symptoms**: Chunks with little or no content

**Causes**:
- Headers without content
- `min_chunk_size` set too low
- Document structure issues

**Solutions**:
```python
# Increase minimum chunk size
config = ChunkConfig(min_chunk_size=200)

# Check for empty chunks
empty_chunks = [i for i, c in enumerate(chunks) if len(c.content.strip()) < 10]
if empty_chunks:
    print(f"Empty chunks at indices: {empty_chunks}")
```

### Chunks Too Large

**Symptoms**: Chunks exceeding expected size limits

**Causes**:
- Large atomic blocks (code, tables)
- `max_chunk_size` set too high
- Strategy not handling content type well

**Solutions**:
```python
# Reduce maximum chunk size
config = ChunkConfig(max_chunk_size=1500)

# Force specific strategy
config = ChunkConfig(strategy_override="code_aware")

# Check chunk sizes
large_chunks = [i for i, c in enumerate(chunks) if c.size > 2000]
if large_chunks:
    print(f"Large chunks at indices: {large_chunks}")
```

### Code Blocks Being Split

**Symptoms**: Code blocks broken across multiple chunks

**Causes**:
- `preserve_atomic_blocks=False`
- Very small `max_chunk_size`
- Strategy not detecting code content

**Solutions**:
```python
# Ensure atomic blocks are preserved
config = ChunkConfig(
    preserve_atomic_blocks=True,
    max_chunk_size=4096,  # Increase if too small
    strategy_override="code_aware"  # Force code-aware strategy
)

# Check if code is being preserved
for chunk in chunks:
    if chunk.metadata['has_code']:
        print(f"Code chunk: {chunk.metadata['header_path']}")
        print(f"Strategy: {chunk.metadata['strategy']}")
```

### Missing Header Paths

**Symptoms**: Chunks with empty or generic header paths

**Causes**:
- Document without headers
- Malformed header structure
- Content before first header

**Solutions**:
```python
# Enable preamble extraction
config = ChunkConfig(extract_preamble=True)

# Check header paths
for chunk in chunks:
    header_path = chunk.metadata.get('header_path', 'N/A')
    if not header_path or header_path == '/':
        print(f"Chunk {chunk.metadata['chunk_index']} has no header path")
```

### Memory Issues with Large Documents

**Symptoms**: Out of memory errors or slow processing

**Causes**:
- Loading entire document into memory
- Not using streaming API
- Very large atomic blocks

**Solutions**:
```python
# Use streaming for large files
from chunkana import MarkdownChunker

chunker = MarkdownChunker()
for chunk in chunker.chunk_file_streaming("large_document.md"):
    process_chunk(chunk)  # Process immediately

# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

### Inconsistent Line Numbers

**Symptoms**: Line numbers don't match original document

**Causes**:
- Document modified after chunking
- Overlap affecting line calculations
- Split chunks with incorrect ranges

**Solutions**:
```python
# Validate line number consistency
def validate_line_numbers(chunks, original_text):
    lines = original_text.split('\n')
    total_lines = len(lines)
    
    for i, chunk in enumerate(chunks):
        if chunk.start_line < 1 or chunk.end_line > total_lines:
            print(f"Chunk {i} has invalid line range: {chunk.start_line}-{chunk.end_line}")
        
        if chunk.start_line > chunk.end_line:
            print(f"Chunk {i} has inverted line range")

validate_line_numbers(chunks, original_text)
```

## Debugging Strategies

### Enable Debug Mode

```python
from chunkana import MarkdownChunker, ChunkConfig

# Enable validation and debug info
config = ChunkConfig(validate_invariants=True)
chunker = MarkdownChunker(config)

try:
    chunks = chunk_markdown(text, config)
except Exception as e:
    print(f"Debug info: {e.get_context() if hasattr(e, 'get_context') else 'N/A'}")
```

### Analyze Document Structure

```python
def analyze_document(text):
    """Analyze document structure for debugging."""
    lines = text.split('\n')
    
    # Count different elements
    headers = [i for i, line in enumerate(lines) if line.strip().startswith('#')]
    code_blocks = [i for i, line in enumerate(lines) if line.strip().startswith('```')]
    tables = [i for i, line in enumerate(lines) if '|' in line]
    
    print(f"Document analysis:")
    print(f"  Total lines: {len(lines)}")
    print(f"  Headers: {len(headers)} at lines {headers[:5]}...")
    print(f"  Code blocks: {len(code_blocks)//2} pairs")
    print(f"  Table lines: {len(tables)}")
    
    return {
        'total_lines': len(lines),
        'headers': headers,
        'code_blocks': code_blocks,
        'tables': tables,
    }

# Usage
analysis = analyze_document(text)
```

### Test with Minimal Examples

```python
def test_minimal_case():
    """Test with minimal example to isolate issues."""
    
    minimal_text = """
# Test Header

Some content here.

```python
def test():
    return True
```

More content.
"""
    
    try:
        chunks = chunk_markdown(minimal_text)
        print(f"Minimal test passed: {len(chunks)} chunks")
        return True
    except Exception as e:
        print(f"Minimal test failed: {e}")
        return False

if test_minimal_case():
    print("Basic functionality works, issue is with your specific document")
else:
    print("Basic functionality broken, check installation")
```

### Compare Strategies

```python
def compare_strategies(text):
    """Compare results from different strategies."""
    
    strategies = ["code_aware", "list_aware", "structural", "fallback"]
    
    for strategy in strategies:
        try:
            config = ChunkConfig(strategy_override=strategy)
            chunks = chunk_markdown(text, config)
            
            print(f"\n{strategy} strategy:")
            print(f"  Chunks: {len(chunks)}")
            print(f"  Avg size: {sum(c.size for c in chunks) / len(chunks):.0f}")
            print(f"  Code chunks: {sum(1 for c in chunks if c.metadata['has_code'])}")
            
        except Exception as e:
            print(f"{strategy} strategy failed: {e}")

compare_strategies(text)
```

## Performance Issues

### Slow Processing

**Symptoms**: Chunking takes longer than expected

**Causes**:
- Very large documents
- Complex document structure
- Validation overhead
- Inefficient configuration

**Solutions**:
```python
import time

# Measure processing time
start_time = time.time()
chunks = chunk_markdown(text)
processing_time = time.time() - start_time

print(f"Processing time: {processing_time:.2f} seconds")
print(f"Rate: {len(text) / processing_time:.0f} chars/second")

# Optimize configuration
fast_config = ChunkConfig(
    validate_invariants=False,  # Disable validation
    overlap_size=0,             # Disable overlap
    strategy_override="fallback"  # Use fastest strategy
)
```

### High Memory Usage

**Symptoms**: Memory usage grows during processing

**Causes**:
- Not using streaming API
- Keeping all chunks in memory
- Large overlap sizes

**Solutions**:
```python
# Process chunks one at a time
def process_large_document(file_path):
    chunker = MarkdownChunker()
    
    for chunk in chunker.chunk_file_streaming(file_path):
        # Process immediately, don't store
        yield process_chunk(chunk)
        
        # Optional: force garbage collection
        import gc
        gc.collect()

# Monitor memory usage
import tracemalloc

tracemalloc.start()
chunks = chunk_markdown(text)
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

## Getting Help

If you're still having issues:

1. **Check the [FAQ](faq.md)** for common questions
2. **Review [examples](examples.md)** for similar use cases
3. **Search [existing issues](https://github.com/asukhodko/chunkana/issues)** on GitHub
4. **Create a minimal reproduction** of your problem
5. **Open a new issue** with:
   - Python version and Chunkana version
   - Minimal code example
   - Expected vs actual behavior
   - Full error traceback

## Related Documentation

- **[FAQ](faq.md)** - Frequently asked questions
- **[Debug Mode](debug_mode.md)** - Understanding chunking behavior
- **[Configuration](config.md)** - Configuration options
- **[Examples](examples.md)** - Practical usage examples
