# Best Practices

<cite>
**Referenced Files in This Document**   
- [README.md](file://README.md)
- [docs/quickstart.md](file://docs/quickstart.md)
- [docs/config.md](file://docs/config.md)
- [docs/strategies.md](file://docs/strategies.md)
- [docs/renderers.md](file://docs/renderers.md)
- [docs/debug_mode.md](file://docs/debug_mode.md)
- [src/chunkana/config.py](file://src/chunkana/config.py)
- [src/chunkana/strategies/base.py](file://src/chunkana/strategies/base.py)
- [src/chunkana/strategies/code_aware.py](file://src/chunkana/strategies/code_aware.py)
- [src/chunkana/strategies/list_aware.py](file://src/chunkana/strategies/list_aware.py)
- [src/chunkana/strategies/structural.py](file://src/chunkana/strategies/structural.py)
- [src/chunkana/strategies/fallback.py](file://src/chunkana/strategies/fallback.py)
- [src/chunkana/renderers/formatters.py](file://src/chunkana/renderers/formatters.py)
- [tests/unit/test_strategies.py](file://tests/unit/test_strategies.py)
- [tests/baseline/test_renderer_compatibility.py](file://tests/baseline/test_renderer_compatibility.py)
</cite>

## Table of Contents
1. [Content Preparation Tips](#content-preparation-tips)
2. [Configuration Tuning for Different Document Types](#configuration-tuning-for-different-document-types)
3. [Strategy Selection Guidance](#strategy-selection-guidance)
4. [Hierarchical vs Flat Chunking](#hierarchical-vs-flat-chunking)
5. [Renderer Selection for Downstream Systems](#renderer-selection-for-downstream-systems)
6. [Error Handling Patterns and Monitoring](#error-handling-patterns-and-monitoring)
7. [Testing Chunked Output Quality](#testing-chunked-output-quality)
8. [Successful Implementations and Lessons Learned](#successful-implementations-and-lessons-learned)

## Content Preparation Tips

When preparing content for Chunkana, follow these best practices to ensure optimal chunking results:

- **Use consistent header hierarchy**: Maintain a logical structure with proper header levels (H1, H2, H3, etc.) to enable effective hierarchical chunking.
- **Preserve atomic blocks**: Keep code blocks, tables, and LaTeX formulas intact with proper Markdown syntax (``` for code blocks, $$ for LaTeX).
- **Structure lists properly**: Use consistent indentation for nested lists and maintain proper list item formatting.
- **Include meaningful section introductions**: When introducing lists or code blocks, use clear introductory text that helps with context binding.
- **Avoid excessive micro-chunks**: Structure content to minimize very small sections that could lead to fragmentation.

**Section sources**
- [README.md](file://README.md#L7-L13)
- [docs/quickstart.md](file://docs/quickstart.md#L16-L28)

## Configuration Tuning for Different Document Types

Chunkana provides flexible configuration options through the `ChunkerConfig` class. Here are recommended configurations for different document types:

### Documentation Sites
```python
config = ChunkerConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=150,
    structure_threshold=2,
)
```

### Code Repositories
```python
config = ChunkerConfig(
    max_chunk_size=8192,
    min_chunk_size=1024,
    overlap_size=100,
    code_threshold=0.2,
    enable_code_context_binding=True,
)
```

### Changelogs / Release Notes
```python
config = ChunkerConfig(
    max_chunk_size=6144,
    min_chunk_size=256,
    overlap_size=100,
    list_ratio_threshold=0.35,
    list_count_threshold=4,
)
```

### Scientific Documents (LaTeX)
```python
config = ChunkerConfig(
    max_chunk_size=4096,
    preserve_latex_blocks=True,
    preserve_atomic_blocks=True,
)
```

### Factory Methods for Common Configurations
Chunkana provides factory methods for common use cases:
- `ChunkerConfig.default()` - Default configuration
- `ChunkerConfig.for_code_heavy()` - Optimized for code-heavy documents
- `ChunkerConfig.for_structured()` - Optimized for structured documents
- `ChunkerConfig.minimal()` - Minimal configuration with small chunks
- `ChunkerConfig.for_changelogs()` - Optimized for changelog documents
- `ChunkerConfig.with_adaptive_sizing()` - Configuration with adaptive sizing enabled

**Section sources**
- [docs/config.md](file://docs/config.md#L124-L168)
- [src/chunkana/config.py](file://src/chunkana/config.py#L310-L387)

## Strategy Selection Guidance

Chunkana automatically selects the best strategy based on document content analysis. Understanding the strategy selection process helps in optimizing document preparation and configuration.

### Strategy Selection Order
1. **CodeAware** (priority 1) — documents with code blocks or tables
2. **ListAware** (priority 2) — list-heavy documents
3. **Structural** (priority 3) — documents with hierarchical headers
4. **Fallback** (priority 4) — universal fallback

### Strategy Activation Criteria

#### CodeAware Strategy
Selected when:
- `code_block_count >= 1`, OR
- `table_count >= 1`, OR
- `code_ratio >= code_threshold` (default 0.3)

#### ListAware Strategy
Selected when (for non-structural documents):
- `list_ratio > list_ratio_threshold` (default 0.4), OR
- `list_count >= list_count_threshold` (default 5)

For structural documents (many headers), requires BOTH conditions.

#### Structural Strategy
Selected when:
- `header_count >= structure_threshold` (default 3), AND
- `max_header_depth > 1`

### Forcing a Strategy
You can override automatic strategy selection by setting the `strategy_override` parameter:

```python
config = ChunkerConfig(strategy_override="structural")
chunks = chunk_markdown(text, config)
```

Valid values: `"code_aware"`, `"list_aware"`, `"structural"`, `"fallback"`

Each chunk includes the strategy used in its metadata:
```python
chunk.metadata["strategy"]  # e.g., "code_aware"
```

**Section sources**
- [docs/strategies.md](file://docs/strategies.md#L5-L81)
- [src/chunkana/strategies/base.py](file://src/chunkana/strategies/base.py#L38-L40)
- [src/chunkana/strategies/code_aware.py](file://src/chunkana/strategies/code_aware.py#L32-L40)
- [src/chunkana/strategies/list_aware.py](file://src/chunkana/strategies/list_aware.py#L48-L89)
- [src/chunkana/strategies/structural.py](file://src/chunkana/strategies/structural.py#L52-L56)

## Hierarchical vs Flat Chunking

Chunkana supports both hierarchical and flat chunking approaches, each with specific use cases and benefits.

### Hierarchical Chunking
Hierarchical chunking preserves the document structure and enables navigation through the content hierarchy.

```python
config = ChunkConfig(
    max_chunk_size=1000,
    min_chunk_size=100,
    overlap_size=100,
    validate_invariants=True,
    strict_mode=False,
)

chunker = MarkdownChunker(config)
result = chunker.chunk_hierarchical(text)

# Navigate the hierarchy
root = result.get_chunk(result.root_id)
children = result.get_children(result.root_id)
flat_chunks = result.get_flat_chunks()
```

**Benefits:**
- Preserves document structure
- Enables hierarchical navigation
- Maintains context relationships
- Supports tree invariant validation

### Flat Chunking
Flat chunking produces a simple list of chunks suitable for direct retrieval.

```python
chunks = chunk_markdown(text)
for chunk in chunks:
    print(f"Lines {chunk.start_line}-{chunk.end_line}: {chunk.metadata['header_path']}")
```

**Benefits:**
- Simpler processing pipeline
- Direct retrieval without navigation
- Lower memory overhead
- Faster processing for simple documents

### When to Use Each Approach

**Use Hierarchical Chunking When:**
- Document structure is important for understanding
- You need to navigate between related sections
- Content has deep nesting and complex hierarchy
- You want to maintain parent-child relationships
- Tree invariant validation is required

**Use Flat Chunking When:**
- Document structure is flat or simple
- You need maximum processing speed
- Memory usage is a concern
- The downstream system expects simple chunk lists
- Content is primarily linear with minimal hierarchy

**Line Range Contract (Hierarchical Mode)**
In hierarchical chunking mode, `start_line` and `end_line` follow a specific contract:
- **Leaf nodes**: Line range covers only the chunk's own content
- **Internal nodes**: Line range covers only the node's own content (not children)
- **Root node**: Line range covers the entire document (1 to last line)

**Section sources**
- [README.md](file://README.md#L62-L165)
- [docs/debug_mode.md](file://docs/debug_mode.md#L19-L43)

## Renderer Selection for Downstream Systems

Chunkana provides multiple renderers to format chunk output for different downstream systems.

### Available Renderers

#### render_dify_style
Formats chunks with `<metadata>` blocks (Dify-compatible, equivalent to `include_metadata=True`).

```python
from chunkana.renderers import render_dify_style
output = render_dify_style(chunks)
```

Output format:
```
<metadata>
{"chunk_index": 0, "content_type": "section", "header_path": "/Introduction", ...}
</metadata>

Actual chunk content here...
```

#### render_with_embedded_overlap
Embeds bidirectional overlap into content strings (equivalent to `include_metadata=False`).

```python
from chunkana.renderers import render_with_embedded_overlap
output = render_with_embedded_overlap(chunks)
# ["previous_content\nchunk_content\nnext_content", ...]
```

#### render_with_prev_overlap
Embeds only previous overlap (sliding window style).

```python
from chunkana.renderers import render_with_prev_overlap
output = render_with_prev_overlap(chunks)
# ["previous_content\nchunk_content", ...]
```

#### render_json
Converts chunks to list of dictionaries.

```python
from chunkana.renderers import render_json
output = render_json(chunks)
# [{"content": "...", "start_line": 1, "end_line": 5, "metadata": {...}}, ...]
```

#### render_inline_metadata
Embeds metadata as inline comment at the start of content.

```python
from chunkana.renderers import render_inline_metadata
output = render_inline_metadata(chunks)
# ["<!-- chunk_index=0 content_type=section -->\nContent...", ...]
```

### Renderer Selection Guide

| Use Case | Renderer |
|----------|----------|
| Dify plugin (include_metadata=True) | `render_dify_style()` |
| Dify plugin (include_metadata=False) | `render_with_embedded_overlap()` |
| JSON API output | `render_json()` |
| RAG with bidirectional context | `render_with_embedded_overlap()` |
| RAG with sliding window | `render_with_prev_overlap()` |
| Debugging / inspection | `render_inline_metadata()` |

### Decision Tree for Renderer Selection
```
Need output for Dify plugin?
├── Yes, with metadata → render_dify_style()
├── Yes, without metadata → render_with_embedded_overlap()
└── No
    ├── Need JSON/dict → render_json()
    ├── Need bidirectional context → render_with_embedded_overlap()
    ├── Need sliding window → render_with_prev_overlap()
    └── Need inline metadata → render_inline_metadata()
```

**Important Notes:**
1. Renderers don't modify chunks — they only format output
2. Overlap is in metadata — `chunk.content` is always canonical (no embedded overlap)
3. Unicode safe — all renderers handle unicode correctly
4. Empty overlap handled — missing `previous_content`/`next_content` is fine
5. Deterministic — same input always produces same output

**Section sources**
- [docs/renderers.md](file://docs/renderers.md#L5-L135)
- [src/chunkana/renderers/formatters.py](file://src/chunkana/renderers/formatters.py#L15-L146)

## Error Handling Patterns and Monitoring

Chunkana provides a comprehensive error handling system with specific exception types and monitoring capabilities.

### Exception Hierarchy
Chunkana provides a hierarchy of exceptions for error handling:

```python
from chunkana import (
    ChunkanaError,              # Base exception for all chunkana errors
    HierarchicalInvariantError, # Tree structure violations
    ValidationError,            # Validation failures
    ConfigurationError,         # Invalid configuration
    TreeConstructionError,      # Tree building failures
)
```

### Error Handling Example
```python
try:
    result = chunker.chunk_hierarchical(text)
except HierarchicalInvariantError as e:
    print(f"Invariant violation: {e.invariant}")
    print(f"Chunk ID: {e.chunk_id}")
    print(f"Suggested fix: {e.suggested_fix}")
except ChunkanaError as e:
    print(f"Chunking error: {e}")
```

### Configuration Validation
Chunkana validates configuration parameters and raises appropriate exceptions:

```python
# Invalid configuration will raise ConfigurationError
try:
    config = ChunkerConfig(max_chunk_size=-1)
except ValueError as e:
    print(f"Invalid configuration: {e}")
```

### Monitoring Strategies
Implement monitoring to track chunking quality and performance:

1. **Log strategy selection**: Monitor which strategy is selected for different document types
2. **Track chunk sizes**: Monitor distribution of chunk sizes to ensure optimal sizing
3. **Monitor invariant violations**: Track hierarchical invariant violations for quality assessment
4. **Log oversize chunks**: Identify chunks that exceed size limits for content optimization
5. **Track processing time**: Monitor performance for large documents

### Quality Features
Chunkana includes several quality features that help prevent common issues:

- **Dangling Header Prevention**: Automatically prevents headers from being separated from their content
- **Micro-Chunk Minimization**: Intelligently merges small chunks with adjacent content
- **Tree Invariant Validation**: Validates hierarchical structure integrity
- **Fence Balance Validation**: Ensures code fences are properly balanced across chunks

**Section sources**
- [README.md](file://README.md#L90-L111)
- [docs/debug_mode.md](file://docs/debug_mode.md#L81-L98)
- [src/chunkana/config.py](file://src/chunkana/config.py#L127-L228)

## Testing Chunked Output Quality

To ensure high-quality chunked output, implement comprehensive testing strategies.

### Automated Testing
Use the provided test suite to validate chunking behavior:

```python
# Test strategy selection
def test_code_aware_for_code_heavy():
    md_text = """# Code Example
    ```python
    def function1():
        pass
    ```
    """
    parser = Parser()
    analysis = parser.analyze(md_text)
    selector = StrategySelector()
    config = ChunkConfig()
    
    strategy = selector.select(analysis, config)
    assert strategy.name == "code_aware"
```

### Quality Validation
Validate chunked output using these criteria:

1. **Content Preservation**: Ensure all original content is preserved in the chunks
2. **Atomic Block Integrity**: Verify code blocks, tables, and LaTeX formulas are not split
3. **Header Context**: Check that headers are not separated from their content
4. **Size Compliance**: Validate chunks respect size limits (except for atomic blocks)
5. **Metadata Accuracy**: Verify metadata fields are correctly populated

### Golden File Testing
Use golden file testing to ensure consistency:

```python
def load_golden_jsonl(path: Path) -> list[str]:
    """Load golden outputs from JSONL file."""
    outputs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                outputs.append(data["text"])
    return outputs
```

### Performance Testing
Monitor performance characteristics:

```python
import time

def benchmark_chunking(text, config):
    start_time = time.time()
    chunks = chunk_markdown(text, config)
    end_time = time.time()
    
    processing_time = end_time - start_time
    chunk_count = len(chunks)
    avg_chunk_size = sum(len(c.content) for c in chunks) / chunk_count if chunk_count > 0 else 0
    
    return {
        "processing_time": processing_time,
        "chunk_count": chunk_count,
        "avg_chunk_size": avg_chunk_size,
    }
```

**Section sources**
- [tests/unit/test_strategies.py](file://tests/unit/test_strategies.py#L12-L364)
- [tests/baseline/test_renderer_compatibility.py](file://tests/baseline/test_renderer_compatibility.py#L1-L157)

## Successful Implementations and Lessons Learned

Based on analysis of the Chunkana codebase and documentation, here are successful implementation patterns and lessons learned from common anti-patterns.

### Successful Implementations

#### Code Documentation Processing
For code-heavy documentation, use the CodeAware strategy with context binding:

```python
config = ChunkerConfig.for_code_heavy()
config.enable_code_context_binding = True
config.max_context_chars_before = 500
config.max_context_chars_after = 300
```

This preserves code blocks while binding them to surrounding explanations, maintaining context for better retrieval.

#### Technical Documentation with Hierarchical Structure
For technical documentation with deep hierarchy, use hierarchical chunking:

```python
config = ChunkConfig(
    max_chunk_size=2048,
    min_chunk_size=256,
    overlap_size=150,
    validate_invariants=True,
    strict_mode=False,
)
```

This preserves the document structure while enabling navigation through the hierarchy.

#### Changelog Processing
For changelogs and release notes with list-heavy content:

```python
config = ChunkerConfig.for_changelogs()
config.list_ratio_threshold = 0.35
config.list_count_threshold = 4
```

This ensures lists are preserved intact while maintaining reasonable chunk sizes.

### Common Anti-Patterns and Lessons Learned

#### Anti-Pattern: Ignoring Atomic Block Preservation
**Problem**: Documents with code blocks or tables are chunked without preserving atomic blocks, leading to fragmented content.

**Solution**: Always ensure `preserve_atomic_blocks=True` and use appropriate strategies that respect atomic block boundaries.

#### Anti-Pattern: Inconsistent Header Hierarchy
**Problem**: Documents with inconsistent header levels make hierarchical chunking ineffective.

**Solution**: Standardize header hierarchy and use the `structure_threshold` parameter to control when structural chunking is applied.

#### Anti-Pattern: Overlapping Configuration Conflicts
**Problem**: Setting `overlap_size=0` while expecting overlap in output.

**Solution**: Understand that `overlap_size > 0` enables overlap, which is stored in metadata (`previous_content`, `next_content`), not embedded in `chunk.content`.

#### Anti-Pattern: Forcing Inappropriate Strategies
**Problem**: Forcing a strategy that doesn't match the document content type.

**Solution**: Allow automatic strategy selection unless there's a specific reason to override, and validate that the forced strategy produces appropriate results.

#### Anti-Pattern: Ignoring Quality Features
**Problem**: Disabling quality features like dangling header prevention and micro-chunk minimization.

**Solution**: Keep quality features enabled by default and only disable them when specific use cases require it, with proper testing.

### Key Lessons Learned

1. **Content-aware chunking produces better results**: Let the content determine the strategy rather than applying a one-size-fits-all approach.
2. **Hierarchical structure adds value**: When document structure is meaningful, preserving it through hierarchical chunking enhances retrieval quality.
3. **Atomic block preservation is critical**: Code blocks, tables, and formulas should never be split across chunks.
4. **Validation improves reliability**: Enable invariant validation to catch structural issues early.
5. **Testing against golden files ensures consistency**: Use golden file testing to maintain consistent output across versions.

**Section sources**
- [README.md](file://README.md#L128-L136)
- [docs/strategies.md](file://docs/strategies.md#L7-L81)
- [docs/config.md](file://docs/config.md#L124-L168)
- [src/chunkana/strategies/code_aware.py](file://src/chunkana/strategies/code_aware.py#L32-L40)
- [src/chunkana/strategies/list_aware.py](file://src/chunkana/strategies/list_aware.py#L48-L89)
- [src/chunkana/strategies/structural.py](file://src/chunkana/strategies/structural.py#L52-L56)