# Performance Guide

This guide covers Chunkana's performance characteristics and optimization strategies.

## Performance Characteristics

### Processing Speed

Chunkana's performance scales linearly with document size:

| Document Size | Processing Time | Rate |
|---------------|-----------------|------|
| Small (~100 lines) | ~0.1ms | ~1M chars/sec |
| Medium (~1,000 lines) | ~0.7ms | ~800K chars/sec |
| Large (~10,000 lines) | ~2.7ms | ~600K chars/sec |

### Memory Usage

- **Base memory**: ~5-10MB for the library
- **Per document**: ~2-3x document size during processing
- **Streaming**: Constant memory usage regardless of document size
- **Validation overhead**: <20% additional memory

### Strategy Performance

Different strategies have varying performance characteristics:

| Strategy | Speed | Memory | Best For |
|----------|-------|--------|----------|
| `fallback` | Fastest | Lowest | Simple text |
| `structural` | Fast | Low | Narrative documents |
| `list_aware` | Medium | Medium | List-heavy content |
| `code_aware` | Slower | Higher | Code documentation |

## Optimization Strategies

### For Speed

```python
from chunkana import chunk_markdown, ChunkConfig

# Fastest configuration
fast_config = ChunkConfig(
    validate_invariants=False,    # Skip validation
    overlap_size=0,               # No overlap calculation
    strategy_override="fallback", # Use fastest strategy
    preserve_atomic_blocks=False, # Skip block detection
)

chunks = chunk_markdown(text, fast_config)
```

### For Memory Efficiency

```python
from chunkana import MarkdownChunker

# Stream large documents
chunker = MarkdownChunker()

def process_large_file(file_path):
    for chunk in chunker.chunk_file_streaming(file_path):
        # Process immediately, don't store
        yield process_chunk(chunk)
        
        # Optional: force garbage collection
        import gc
        if chunk.metadata['chunk_index'] % 100 == 0:
            gc.collect()

# Usage
for result in process_large_file("large_document.md"):
    save_to_database(result)
```

### For Quality vs Speed Balance

```python
# Balanced configuration
balanced_config = ChunkConfig(
    max_chunk_size=2048,          # Reasonable size
    validate_invariants=True,     # Keep validation
    overlap_size=100,             # Minimal overlap
    # Let strategy auto-select
)

chunks = chunk_markdown(text, balanced_config)
```

## Benchmarking

### Measuring Performance

```python
import time
import psutil
import tracemalloc

def benchmark_chunking(text, config=None):
    """Benchmark chunking performance."""
    
    # Memory tracking
    tracemalloc.start()
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Time tracking
    start_time = time.time()
    
    # Chunk the document
    chunks = chunk_markdown(text, config)
    
    # Measure results
    end_time = time.time()
    final_memory = process.memory_info().rss
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    # Calculate metrics
    processing_time = end_time - start_time
    memory_used = (final_memory - initial_memory) / 1024 / 1024  # MB
    peak_memory = peak / 1024 / 1024  # MB
    chars_per_second = len(text) / processing_time
    
    return {
        'chunks': len(chunks),
        'processing_time': processing_time,
        'chars_per_second': chars_per_second,
        'memory_used_mb': memory_used,
        'peak_memory_mb': peak_memory,
        'avg_chunk_size': sum(c.size for c in chunks) / len(chunks),
    }

# Usage
with open('document.md', 'r') as f:
    text = f.read()

results = benchmark_chunking(text)
print(f"Processed {results['chunks']} chunks in {results['processing_time']:.3f}s")
print(f"Rate: {results['chars_per_second']:.0f} chars/second")
print(f"Memory: {results['memory_used_mb']:.1f} MB used, {results['peak_memory_mb']:.1f} MB peak")
```

### Comparing Configurations

```python
def compare_configurations(text):
    """Compare performance of different configurations."""
    
    configs = {
        'default': ChunkConfig(),
        'fast': ChunkConfig(
            validate_invariants=False,
            overlap_size=0,
            strategy_override="fallback"
        ),
        'quality': ChunkConfig(
            validate_invariants=True,
            overlap_size=200,
            preserve_atomic_blocks=True
        ),
        'memory_efficient': ChunkConfig(
            max_chunk_size=1024,
            min_chunk_size=256,
            overlap_size=50
        ),
    }
    
    results = {}
    for name, config in configs.items():
        print(f"\nTesting {name} configuration...")
        results[name] = benchmark_chunking(text, config)
    
    # Print comparison
    print("\nPerformance Comparison:")
    print(f"{'Config':<15} {'Time (ms)':<10} {'Rate (K/s)':<12} {'Memory (MB)':<12} {'Chunks':<8}")
    print("-" * 60)
    
    for name, result in results.items():
        print(f"{name:<15} {result['processing_time']*1000:<10.1f} "
              f"{result['chars_per_second']/1000:<12.0f} "
              f"{result['peak_memory_mb']:<12.1f} {result['chunks']:<8}")
    
    return results

# Usage
results = compare_configurations(text)
```

## Large Document Handling

### Streaming API

For documents larger than available memory:

```python
from chunkana import MarkdownChunker
import json

def process_huge_document(file_path, output_path):
    """Process documents too large for memory."""
    
    chunker = MarkdownChunker()
    
    with open(output_path, 'w') as output_file:
        output_file.write('[\n')
        
        first_chunk = True
        for chunk in chunker.chunk_file_streaming(file_path):
            if not first_chunk:
                output_file.write(',\n')
            
            # Convert to JSON and write immediately
            chunk_data = {
                'content': chunk.content,
                'metadata': chunk.metadata,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'size': chunk.size,
            }
            
            json.dump(chunk_data, output_file, indent=2)
            first_chunk = False
        
        output_file.write('\n]')

# Process 100MB+ documents
process_huge_document('huge_manual.md', 'chunks.json')
```

### Parallel Processing

For multiple documents:

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import multiprocessing

def chunk_single_file(file_path):
    """Chunk a single file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    chunks = chunk_markdown(text)
    return file_path, len(chunks), sum(c.size for c in chunks)

def parallel_processing(directory, max_workers=None):
    """Process multiple files in parallel."""
    
    if max_workers is None:
        max_workers = multiprocessing.cpu_count()
    
    md_files = list(Path(directory).glob('**/*.md'))
    
    # Use ThreadPoolExecutor for I/O bound tasks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(chunk_single_file, md_files))
    
    # Summarize results
    total_files = len(results)
    total_chunks = sum(result[1] for result in results)
    total_chars = sum(result[2] for result in results)
    
    print(f"Processed {total_files} files")
    print(f"Generated {total_chunks} chunks")
    print(f"Total content: {total_chars:,} characters")
    
    return results

# Usage
results = parallel_processing('docs/', max_workers=4)
```

## Memory Profiling

### Detailed Memory Analysis

```python
import tracemalloc
from memory_profiler import profile

@profile
def memory_intensive_chunking(text):
    """Profile memory usage during chunking."""
    
    # Start detailed tracing
    tracemalloc.start()
    
    # Chunk with different configurations
    configs = [
        ChunkConfig(overlap_size=0),
        ChunkConfig(overlap_size=200),
        ChunkConfig(validate_invariants=True),
    ]
    
    results = []
    for i, config in enumerate(configs):
        snapshot_before = tracemalloc.take_snapshot()
        
        chunks = chunk_markdown(text, config)
        
        snapshot_after = tracemalloc.take_snapshot()
        top_stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        
        results.append({
            'config_index': i,
            'chunks': len(chunks),
            'memory_diff': sum(stat.size_diff for stat in top_stats[:10])
        })
    
    tracemalloc.stop()
    return results

# Usage (requires: pip install memory-profiler)
# python -m memory_profiler your_script.py
```

### Memory Leak Detection

```python
import gc
import weakref

def check_memory_leaks():
    """Check for memory leaks in chunking."""
    
    # Create weak references to track objects
    chunks_refs = []
    
    for i in range(10):
        text = f"# Test {i}\n\nContent for test {i}"
        chunks = chunk_markdown(text)
        
        # Create weak references
        for chunk in chunks:
            chunks_refs.append(weakref.ref(chunk))
        
        # Clear strong references
        del chunks
        del text
    
    # Force garbage collection
    gc.collect()
    
    # Check if objects were cleaned up
    alive_refs = [ref for ref in chunks_refs if ref() is not None]
    
    if alive_refs:
        print(f"Warning: {len(alive_refs)} chunk objects not garbage collected")
    else:
        print("No memory leaks detected")

check_memory_leaks()
```

## Performance Tips

### Configuration Optimization

1. **Disable validation** for production if not needed:
   ```python
   config = ChunkConfig(validate_invariants=False)
   ```

2. **Reduce overlap** for faster processing:
   ```python
   config = ChunkConfig(overlap_size=50)  # Instead of 200
   ```

3. **Use appropriate chunk sizes**:
   ```python
   # For embedding models
   config = ChunkConfig(max_chunk_size=1500)
   
   # For LLM context windows
   config = ChunkConfig(max_chunk_size=4000)
   ```

4. **Choose strategy based on content**:
   ```python
   # For code-heavy docs
   config = ChunkConfig(strategy_override="code_aware")
   
   # For simple text
   config = ChunkConfig(strategy_override="fallback")
   ```

### Processing Optimization

1. **Use streaming for large files**:
   ```python
   for chunk in chunker.chunk_file_streaming(file_path):
       process_immediately(chunk)
   ```

2. **Process in batches**:
   ```python
   batch_size = 100
   for i in range(0, len(files), batch_size):
       batch = files[i:i+batch_size]
       process_batch(batch)
   ```

3. **Cache results when possible**:
   ```python
   import hashlib
   import pickle
   
   def cached_chunk_markdown(text, config=None):
       # Create cache key
       key = hashlib.md5(f"{text}{config}".encode()).hexdigest()
       cache_file = f"cache/{key}.pkl"
       
       try:
           with open(cache_file, 'rb') as f:
               return pickle.load(f)
       except FileNotFoundError:
           chunks = chunk_markdown(text, config)
           with open(cache_file, 'wb') as f:
               pickle.dump(chunks, f)
           return chunks
   ```

### System-Level Optimization

1. **Use SSD storage** for better I/O performance
2. **Increase available RAM** for larger documents
3. **Use multiple CPU cores** for parallel processing
4. **Monitor system resources** during processing

```python
import psutil

def monitor_resources():
    """Monitor system resources during processing."""
    
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    print(f"CPU: {cpu_percent}%")
    print(f"Memory: {memory.percent}% ({memory.used // 1024 // 1024} MB used)")
    print(f"Disk: {disk.percent}% ({disk.free // 1024 // 1024 // 1024} GB free)")

# Monitor before and after processing
monitor_resources()
chunks = chunk_markdown(large_text)
monitor_resources()
```

## Troubleshooting Performance Issues

### Slow Processing

1. **Profile your code** to identify bottlenecks
2. **Check document complexity** (many nested structures)
3. **Reduce validation overhead** if not needed
4. **Use simpler strategies** for basic content

### High Memory Usage

1. **Use streaming API** for large documents
2. **Process in smaller batches**
3. **Reduce overlap size**
4. **Clear references** to processed chunks

### Inconsistent Performance

1. **Warm up** the chunker with a small document first
2. **Check for memory pressure** affecting performance
3. **Monitor system resources** during processing
4. **Use consistent configurations** for benchmarking

## Related Documentation

- **[Configuration Guide](config.md)** - Tuning parameters for performance
- **[Examples](examples.md)** - Practical performance optimization examples
- **[Troubleshooting](errors.md)** - Resolving performance-related issues