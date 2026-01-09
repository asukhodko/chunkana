# Advanced Usage Examples

This document provides examples of advanced Chunkana features and usage patterns.

## Streaming Large Files

For processing very large files that don't fit in memory:

```python
from chunkana import chunk_file_streaming
from chunkana.streaming import StreamingConfig

streaming_config = StreamingConfig(
    buffer_size=100_000,  # 100KB buffer
    overlap_lines=20,     # 20 lines overlap between buffers
)

config = ChunkerConfig(max_chunk_size=2048)

for chunk in chunk_file_streaming("large_file.md", config, streaming_config):
    # Process each chunk as it's generated
    process_chunk(chunk)
```

### Streaming Configuration Options

```python
streaming_config = StreamingConfig(
    buffer_size=50_000,      # Smaller buffer for memory-constrained environments
    overlap_lines=10,        # Minimal overlap
    encoding='utf-8',        # File encoding
    chunk_size=8192,         # File read chunk size
)
```

## Adaptive Sizing

Automatically adjust chunk sizes based on content characteristics:

```python
from chunkana import ChunkerConfig
from chunkana.adaptive_sizing import AdaptiveSizeConfig

config = ChunkerConfig(
    use_adaptive_sizing=True,
    adaptive_config=AdaptiveSizeConfig(
        base_size=1500,           # Base chunk size
        code_weight=0.4,          # Weight for code content
        list_weight=0.3,          # Weight for list content
        table_weight=0.5,         # Weight for table content
        min_size_ratio=0.5,       # Minimum size as ratio of base_size
        max_size_ratio=2.0,       # Maximum size as ratio of base_size
    ),
)

chunks = chunk_markdown(text, config)
```

### Adaptive Sizing Strategies

```python
# Conservative adaptive sizing
adaptive_config = AdaptiveSizeConfig(
    base_size=2000,
    code_weight=0.2,      # Less aggressive for code
    min_size_ratio=0.7,   # Don't go too small
    max_size_ratio=1.5,   # Don't go too large
)

# Aggressive adaptive sizing
adaptive_config = AdaptiveSizeConfig(
    base_size=1000,
    code_weight=0.6,      # More aggressive for code
    min_size_ratio=0.3,   # Allow very small chunks
    max_size_ratio=3.0,   # Allow very large chunks
)
```

## Table Grouping

Group related tables together for better context:

```python
from chunkana import ChunkerConfig
from chunkana.table_grouping import TableGroupingConfig

config = ChunkerConfig(
    group_related_tables=True,
    table_grouping_config=TableGroupingConfig(
        max_distance_lines=10,        # Max lines between related tables
        require_same_section=True,    # Tables must be in same section
        max_group_size=8192,          # Max size of grouped tables
        preserve_table_headers=True,  # Keep table headers intact
    ),
)

chunks = chunk_markdown(text, config)
```

### Table Grouping Examples

```python
# Strict table grouping
table_config = TableGroupingConfig(
    max_distance_lines=5,     # Tables must be close
    require_same_section=True,
    max_group_size=4096,
)

# Loose table grouping
table_config = TableGroupingConfig(
    max_distance_lines=20,    # Allow distant tables
    require_same_section=False,
    max_group_size=12288,     # Allow larger groups
)
```

## LaTeX Preservation

Handle LaTeX formulas and mathematical content:

```python
config = ChunkerConfig(
    preserve_latex_blocks=True,      # Default: True
    preserve_atomic_blocks=True,     # Keep atomic blocks intact
    latex_delimiters=[               # Custom LaTeX delimiters
        ('$$', '$$'),                # Display math
        ('$', '$'),                  # Inline math
        ('\\[', '\\]'),             # Alternative display math
        ('\\(', '\\)'),             # Alternative inline math
    ],
)

chunks = chunk_markdown(text, config)
```

### LaTeX Handling Examples

```python
# Strict LaTeX preservation
config = ChunkerConfig(
    preserve_latex_blocks=True,
    preserve_atomic_blocks=True,
    # Don't break LaTeX blocks even if they're large
    latex_max_size=None,  # No size limit
)

# Balanced LaTeX handling
config = ChunkerConfig(
    preserve_latex_blocks=True,
    latex_max_size=2048,  # Break very large LaTeX blocks
    latex_break_strategy="equation",  # Break at equation boundaries
)
```

## Hierarchical Chunking

Advanced hierarchical chunking with validation:

```python
from chunkana import chunk_hierarchical, ChunkConfig

# With validation (recommended)
config = ChunkConfig(
    max_chunk_size=1000,
    validate_invariants=True,  # Validates tree structure
    strict_mode=False,         # Auto-fix issues
)

result = chunk_hierarchical(text, config)

# Access different chunk sets
leaf_chunks = result.get_flat_chunks()      # Only leaf chunks
all_chunks = result.get_all_chunks()        # All chunks including intermediate
significant_chunks = result.get_significant_chunks()  # Chunks with >100 chars

# Navigate hierarchy
for chunk in leaf_chunks:
    chunk_id = chunk.metadata["chunk_id"]
    parent = result.get_parent(chunk_id)
    children = result.get_children(chunk_id)
    siblings = result.get_siblings(chunk_id)
```

### Hierarchical Configuration

```python
# Strict hierarchical validation
config = ChunkConfig(
    validate_invariants=True,
    strict_mode=True,          # Raise exceptions on violations
    max_depth=6,               # Limit tree depth
    min_chunk_size=100,        # Minimum chunk size
)

# Performance-optimized hierarchical
config = ChunkConfig(
    validate_invariants=False,  # Skip validation for speed
    max_chunk_size=2048,
    preserve_hierarchy_metadata=False,  # Reduce metadata overhead
)
```

## Custom Renderers

Create custom output formats:

```python
from chunkana.renderers.base import BaseRenderer

class CustomRenderer(BaseRenderer):
    def render_chunk(self, chunk, index: int) -> str:
        """Render a single chunk in custom format."""
        return f"CHUNK_{index}: {chunk.content[:100]}..."
    
    def render_chunks(self, chunks) -> list[str]:
        """Render all chunks."""
        return [self.render_chunk(chunk, i) for i, chunk in enumerate(chunks)]

# Use custom renderer
renderer = CustomRenderer()
chunks = chunk_markdown(text)
custom_output = renderer.render_chunks(chunks)
```

## Performance Optimization

Optimize for different use cases:

```python
# Memory-optimized configuration
memory_config = ChunkerConfig(
    max_chunk_size=1024,       # Smaller chunks
    overlap_size=50,           # Minimal overlap
    validate_invariants=False, # Skip validation
    preserve_metadata=False,   # Minimal metadata
)

# Speed-optimized configuration
speed_config = ChunkerConfig(
    strategy_override="fallback",  # Fastest strategy
    preserve_atomic_blocks=False,  # Skip complex analysis
    enable_code_context_binding=False,  # Skip context binding
    validate_invariants=False,     # Skip validation
)

# Quality-optimized configuration
quality_config = ChunkerConfig(
    use_adaptive_sizing=True,      # Better chunk boundaries
    group_related_tables=True,     # Better table handling
    preserve_latex_blocks=True,    # Better LaTeX handling
    validate_invariants=True,      # Ensure quality
)
```

## Batch Processing

Process multiple documents efficiently:

```python
from chunkana import chunk_markdown
from concurrent.futures import ThreadPoolExecutor
import os

def process_document(file_path: str, config: ChunkerConfig) -> list:
    """Process a single document."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    chunks = chunk_markdown(text, config)
    return [(file_path, chunk) for chunk in chunks]

def batch_process(directory: str, config: ChunkerConfig, max_workers: int = 4):
    """Process all markdown files in a directory."""
    md_files = [
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if f.endswith('.md')
    ]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_document, file_path, config)
            for file_path in md_files
        ]
        
        for future in futures:
            yield from future.result()

# Usage
config = ChunkerConfig(max_chunk_size=2048)
for file_path, chunk in batch_process("docs/", config):
    print(f"File: {file_path}, Chunk: {chunk.metadata['chunk_index']}")
```

## Error Handling

Robust error handling patterns:

```python
from chunkana import chunk_markdown, ChunkingError
from chunkana.exceptions import HierarchicalInvariantError

def safe_chunk_markdown(text: str, config: ChunkerConfig):
    """Safely chunk markdown with fallback strategies."""
    try:
        return chunk_markdown(text, config)
    except HierarchicalInvariantError as e:
        # Try with auto-fix mode
        fallback_config = config.copy()
        fallback_config.strict_mode = False
        return chunk_markdown(text, fallback_config)
    except ChunkingError as e:
        # Try with simpler strategy
        fallback_config = config.copy()
        fallback_config.strategy_override = "fallback"
        return chunk_markdown(text, fallback_config)
    except Exception as e:
        # Last resort: minimal chunking
        minimal_config = ChunkerConfig(
            max_chunk_size=1024,
            strategy_override="fallback",
            preserve_atomic_blocks=False,
        )
        return chunk_markdown(text, minimal_config)
```