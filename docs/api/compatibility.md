# Compatibility Guarantees

This document outlines what is guaranteed to be compatible and what behavioral differences exist.

## Guaranteed Compatibility (Byte-for-Byte)

### Chunk Boundaries
- `start_line` and `end_line` positions
- Chunk content (canonical, without embedded overlap)
- Chunk boundary decisions

### Metadata
- `chunk_index` - Sequential chunk numbering
- `strategy` - Strategy used for chunking
- `header_path` - Hierarchical header path
- `content_type` - Type of content (section, code, list, etc.)
- `previous_content` and `next_content` - Context metadata
- `chunk_id` format - 8-character SHA256 hash

### Renderer Output
- `render_dify_style()` produces byte-for-byte identical output to `include_metadata=True`
- `render_with_embedded_overlap()` produces byte-for-byte identical output to `include_metadata=False`
- Verified against baseline golden outputs

## Behavioral Differences

### Small Chunk Merging

Chunkana optimizes chunk boundaries by merging small H1 header chunks with their following section content.

**Previous behavior:** Creates separate small chunks for H1 headers with `small_chunk: true` metadata.

**Chunkana behavior:** Merges small H1 header chunks with their following section content, producing fewer but more contextually complete chunks.

**Example:**
```markdown
# Document Title

Brief intro.

## Section One

Content here...
```

| Aspect | Previous | Chunkana |
|--------|----------|----------|
| Chunk count | 2 (title + section) | 1 (merged) |
| First chunk | `# Document Title\n\nBrief intro.` | `# Document Title\n\nBrief intro.\n\n## Section One\n\nContent here...` |
| Metadata | `small_chunk: true` | No `small_chunk` flag |

**Impact:** Chunkana produces fewer, larger chunks that preserve more context. This is generally better for RAG retrieval quality.

## Not Guaranteed

### Streaming Boundaries
- `chunk_file_streaming()` may produce different boundaries at buffer splits
- Streaming overlap metadata may differ at buffer boundaries
- This is due to the nature of streaming processing

### Performance Characteristics
- Processing time may vary between implementations
- Memory usage patterns may differ
- Optimization strategies may produce different performance profiles

## Compatibility Verification

### Baseline Tests
Run these tests to verify compatibility:

```bash
# Canonical chunk compatibility
pytest tests/baseline/test_canonical.py -v

# View-level output compatibility  
pytest tests/baseline/test_view_level.py -v

# Property-based tests
pytest tests/property/ -v
```

### Key Test Fixtures
These fixtures are particularly important for compatibility verification:

- `nested_fences.md` - Nested code fences
- `complex_lists.md` - Complex list structures
- `large_tables.md` - Tables exceeding chunk size
- `latex_formulas.md` - LaTeX formula handling

## Performance Benchmarks

Typical performance characteristics:

| Document Size | Processing Time | Memory Usage |
|---------------|----------------|--------------|
| Small (~100 lines) | ~0.1ms | ~1MB |
| Medium (~1000 lines) | ~0.7ms | ~5MB |
| Large (~10000 lines) | ~2.7ms | ~25MB |

**Performance Formula:**
```
Processing Time = coefficient × Document Size (KB) + baseline overhead
```

- **Coefficient**: ~0.5-1.0 ms per KB
- **Baseline Overhead**: ~5-10 ms (parsing, analysis, strategy selection)
- **R-squared**: > 0.95 (strong linear relationship)

## Troubleshooting Compatibility Issues

### HierarchicalInvariantError Exceptions

If you encounter `HierarchicalInvariantError` in strict mode:

#### is_leaf_consistency
```python
# Error: is_leaf=True but chunk has children
HierarchicalInvariantError: is_leaf_consistency violated in chunk abc123

# Solution: Enable auto-fix mode
config = ChunkConfig(strict_mode=False)
```

#### parent_child_bidirectionality
```python
# Error: Parent-child relationship is not symmetric
HierarchicalInvariantError: parent_child_bidirectionality violated

# Solution: Re-chunk the document
result = chunk_hierarchical(text)  # Fresh chunking
```

#### orphaned_chunk
```python
# Error: Chunk is not reachable from root
HierarchicalInvariantError: orphaned_chunk detected

# Solution: Auto-fixed in non-strict mode
config = ChunkConfig(strict_mode=False)
```

### Debugging Hierarchical Issues

Enable strict mode temporarily to see all violations:

```python
from chunkana import chunk_hierarchical, ChunkConfig
from chunkana import HierarchicalInvariantError

config = ChunkConfig(
    validate_invariants=True,
    strict_mode=True,  # Raise exceptions instead of auto-fix
)

try:
    result = chunk_hierarchical(text, config)
except HierarchicalInvariantError as e:
    print(f"Invariant: {e.invariant}")
    print(f"Chunk ID: {e.chunk_id}")
    print(f"Details: {e.details}")
    print(f"Suggested fix: {e.suggested_fix}")
```

### Performance Issues

If chunking is slow for large documents:

```python
# Disable validation for performance-critical paths
config = ChunkConfig(
    validate_invariants=False,  # Skip tree validation
)
```

## Migration Notes

If your application relies on specific behaviors that have changed:

1. **Small chunk separation**: If you need separate small chunks for H1 headers, you may need to adjust your retrieval logic
2. **Streaming boundaries**: If you depend on specific streaming chunk boundaries, consider using non-streaming APIs
3. **Performance assumptions**: Update any performance assumptions based on the new benchmarks