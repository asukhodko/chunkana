# Renderers

Renderers transform Chunkana's `Chunk` objects into different output formats without modifying the original chunks. They provide flexibility to integrate with various downstream systems and workflows.

## Overview

After chunking your document, you get a list of `Chunk` objects. Renderers convert these into formats suitable for:
- Vector databases and search engines
- Workflow automation tools (Dify, n8n)
- JSON APIs and web services
- Debugging and inspection
- Custom processing pipelines

## Available Renderers

### render_json()

Converts chunks to a list of dictionaries - perfect for JSON APIs and serialization.

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_json

chunks = chunk_markdown(text)
json_output = render_json(chunks)

# Output: List[Dict[str, Any]]
print(json_output[0])
```

**Output format**:
```json
{
  "content": "# Introduction\n\nWelcome to our guide...",
  "start_line": 1,
  "end_line": 5,
  "size": 156,
  "line_count": 5,
  "metadata": {
    "chunk_index": 0,
    "content_type": "section",
    "header_path": "/Introduction",
    "strategy": "structural",
    "has_code": false,
    "overlap_size": 200
  }
}
```

**Use cases**:
- REST API responses
- Database storage
- File serialization
- Inter-service communication

**Features**:
- Round-trip safe: `Chunk.from_dict(json_output[0])` reconstructs the original chunk
- JSON serializable with `json.dumps()`
- Preserves all chunk metadata

### render_dify_style()

Formats chunks with `<metadata>` blocks for Dify workflow compatibility.

```python
from chunkana.renderers import render_dify_style

chunks = chunk_markdown(text)
dify_output = render_dify_style(chunks)

# Output: List[str]
print(dify_output[0])
```

**Output format**:
```
<metadata>
{"chunk_index": 0, "content_type": "section", "header_path": "/Introduction", "start_line": 1, "end_line": 5, "strategy": "structural"}
</metadata>

# Introduction

Welcome to our comprehensive guide...
```

**Use cases**:
- Dify workflow integration
- Systems expecting metadata headers
- Document processing pipelines
- Content management systems

**Features**:
- Dify-compatible format
- Metadata in structured JSON block
- Content preserved exactly as chunked

### render_with_embedded_overlap()

Embeds overlap context directly into the content for sliding window retrieval.

```python
from chunkana.renderers import render_with_embedded_overlap

chunks = chunk_markdown(text)
overlap_output = render_with_embedded_overlap(chunks)

# Output: List[str]
print(overlap_output[0])
```

**Output format**:
```
...previous context from prior chunk...

# Current Section

This is the main content of the current chunk.

...next context from following chunk...
```

**Use cases**:
- RAG systems needing context continuity
- Embedding models with context windows
- Search systems with snippet expansion
- LLM prompts requiring surrounding context

**Features**:
- Bidirectional overlap (previous + next)
- Seamless context flow
- No metadata headers

### render_with_prev_overlap()

Embeds only previous overlap for sliding window style processing.

```python
from chunkana.renderers import render_with_prev_overlap

chunks = chunk_markdown(text)
prev_output = render_with_prev_overlap(chunks)

# Output: List[str]
print(prev_output[0])
```

**Output format**:
```
...previous context...

# Current Section

This is the main content of the current chunk.
```

**Use cases**:
- Sequential document processing
- Streaming applications
- Memory-efficient context windows
- Progressive content analysis

**Features**:
- Only previous context included
- Lighter memory footprint
- Maintains reading flow

### render_inline_metadata()

Embeds metadata as HTML comments for debugging and inspection.

```python
from chunkana.renderers import render_inline_metadata

chunks = chunk_markdown(text)
debug_output = render_inline_metadata(chunks)

# Output: List[str]
print(debug_output[0])
```

**Output format**:
```html
<!-- chunk_index=0 content_type=section header_path=/Introduction start_line=1 end_line=5 strategy=structural -->
# Introduction

Welcome to our comprehensive guide...
```

**Use cases**:
- Development and debugging
- Content inspection
- Quality assurance
- Documentation generation

**Features**:
- Human-readable metadata
- Preserves original content
- Deterministic key ordering
- HTML comment format

## Renderer Selection Guide

Choose the right renderer based on your use case:

| Use Case | Recommended Renderer | Why |
|----------|---------------------|-----|
| **Vector Database** | `render_json()` | Structured data with metadata |
| **Dify Workflows** | `render_dify_style()` | Native Dify compatibility |
| **RAG with Context** | `render_with_embedded_overlap()` | Bidirectional context |
| **Sequential Processing** | `render_with_prev_overlap()` | Sliding window context |
| **API Responses** | `render_json()` | Standard JSON format |
| **Debugging** | `render_inline_metadata()` | Visible metadata |
| **File Storage** | `render_json()` | Serializable format |
| **LLM Prompts** | `render_with_embedded_overlap()` | Rich context |

## Advanced Usage

### Custom Enrichment

Enrich chunks before rendering:

```python
from chunkana.renderers import render_json

chunks = chunk_markdown(text)
json_output = render_json(chunks)

# Enrich with custom metadata
for item in json_output:
    item['metadata']['source_file'] = 'user_manual.md'
    item['metadata']['processed_at'] = '2024-01-01T00:00:00Z'
    item['metadata']['version'] = '1.0'
    
    # Add custom fields
    item['word_count'] = len(item['content'].split())
    item['language'] = 'en'

# Save enriched data
import json
with open('enriched_chunks.json', 'w') as f:
    json.dump(json_output, f, indent=2)
```

### Conditional Rendering

Choose renderer based on content:

```python
def smart_render(chunks):
    """Choose renderer based on chunk characteristics."""
    
    # Check if chunks have overlap
    has_overlap = any(
        chunk.metadata.get('overlap_size', 0) > 0 
        for chunk in chunks
    )
    
    # Check if chunks have code
    has_code = any(
        chunk.metadata.get('has_code', False) 
        for chunk in chunks
    )
    
    if has_code and has_overlap:
        # Code with context - use embedded overlap
        return render_with_embedded_overlap(chunks)
    elif has_overlap:
        # Regular content with context
        return render_with_prev_overlap(chunks)
    else:
        # No overlap - use JSON for structured access
        return render_json(chunks)

# Usage
output = smart_render(chunks)
```

### Batch Rendering

Process multiple documents efficiently:

```python
from pathlib import Path
from chunkana import chunk_markdown
from chunkana.renderers import render_json

def batch_render_documents(input_dir, output_file):
    """Render multiple documents to single JSON file."""
    
    all_chunks = []
    
    for md_file in Path(input_dir).glob('**/*.md'):
        with open(md_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunks = chunk_markdown(text)
        json_chunks = render_json(chunks)
        
        # Add source information
        for chunk_data in json_chunks:
            chunk_data['metadata']['source_file'] = str(md_file)
        
        all_chunks.extend(json_chunks)
    
    # Save combined output
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2)
    
    return len(all_chunks)

# Usage
chunk_count = batch_render_documents('docs/', 'all_chunks.json')
print(f"Rendered {chunk_count} chunks from multiple documents")
```

## Creating Custom Renderers

For specialized output formats, create custom renderers:

```python
def render_xml(chunks):
    """Custom XML renderer."""
    import xml.etree.ElementTree as ET
    
    root = ET.Element('document')
    root.set('chunk_count', str(len(chunks)))
    
    for chunk in chunks:
        chunk_elem = ET.SubElement(root, 'chunk')
        chunk_elem.set('index', str(chunk.metadata['chunk_index']))
        
        # Content
        content_elem = ET.SubElement(chunk_elem, 'content')
        content_elem.text = chunk.content
        
        # Metadata
        meta_elem = ET.SubElement(chunk_elem, 'metadata')
        for key, value in chunk.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                attr_elem = ET.SubElement(meta_elem, key)
                attr_elem.text = str(value)
    
    return ET.tostring(root, encoding='unicode')

def render_csv(chunks):
    """Custom CSV renderer."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'chunk_index', 'content', 'header_path', 
        'content_type', 'start_line', 'end_line', 'size'
    ])
    
    # Data rows
    for chunk in chunks:
        writer.writerow([
            chunk.metadata['chunk_index'],
            chunk.content.replace('\n', '\\n'),  # Escape newlines
            chunk.metadata['header_path'],
            chunk.metadata['content_type'],
            chunk.start_line,
            chunk.end_line,
            chunk.size,
        ])
    
    return output.getvalue()

# Usage
chunks = chunk_markdown(text)
xml_output = render_xml(chunks)
csv_output = render_csv(chunks)
```

## Performance Considerations

### Memory Usage

Different renderers have different memory characteristics:

```python
import sys

chunks = chunk_markdown(large_text)

# Memory-efficient: processes one chunk at a time
def memory_efficient_render(chunks):
    for chunk in chunks:
        yield render_json([chunk])[0]  # Process individually

# Memory-intensive: processes all at once
json_output = render_json(chunks)  # All in memory

print(f"JSON output size: {sys.getsizeof(json_output)} bytes")
```

### Processing Speed

Benchmark different renderers:

```python
import time

def benchmark_renderers(chunks):
    """Compare renderer performance."""
    
    renderers = {
        'json': render_json,
        'dify': render_dify_style,
        'overlap': render_with_embedded_overlap,
        'prev_overlap': render_with_prev_overlap,
        'inline': render_inline_metadata,
    }
    
    results = {}
    
    for name, renderer in renderers.items():
        start_time = time.time()
        output = renderer(chunks)
        end_time = time.time()
        
        results[name] = {
            'time': end_time - start_time,
            'output_size': len(str(output)),
            'items': len(output),
        }
    
    return results

# Usage
chunks = chunk_markdown(text)
benchmark_results = benchmark_renderers(chunks)

for name, result in benchmark_results.items():
    print(f"{name}: {result['time']:.3f}s, {result['output_size']} bytes")
```

## Integration Examples

### Vector Database Integration

```python
from chunkana.renderers import render_json

def prepare_for_vector_db(chunks, source_name):
    """Prepare chunks for vector database ingestion."""
    
    json_chunks = render_json(chunks)
    
    vector_docs = []
    for chunk_data in json_chunks:
        doc = {
            'id': f"{source_name}_{chunk_data['metadata']['chunk_index']}",
            'content': chunk_data['content'],
            'metadata': {
                'source': source_name,
                'header_path': chunk_data['metadata']['header_path'],
                'content_type': chunk_data['metadata']['content_type'],
                'has_code': chunk_data['metadata']['has_code'],
                'size': chunk_data['size'],
                'line_range': f"{chunk_data['start_line']}-{chunk_data['end_line']}",
            }
        }
        vector_docs.append(doc)
    
    return vector_docs

# Usage
chunks = chunk_markdown(text)
vector_docs = prepare_for_vector_db(chunks, 'user_manual')
```

### Elasticsearch Integration

```python
from chunkana.renderers import render_json

def prepare_for_elasticsearch(chunks, index_name):
    """Prepare chunks for Elasticsearch indexing."""
    
    json_chunks = render_json(chunks)
    
    es_docs = []
    for chunk_data in json_chunks:
        doc = {
            '_index': index_name,
            '_source': {
                'content': chunk_data['content'],
                'header_path': chunk_data['metadata']['header_path'],
                'content_type': chunk_data['metadata']['content_type'],
                'size': chunk_data['size'],
                'line_range': {
                    'start': chunk_data['start_line'],
                    'end': chunk_data['end_line']
                },
                'has_code': chunk_data['metadata']['has_code'],
                'strategy': chunk_data['metadata']['strategy'],
                # Add searchable plain text
                'plain_text': chunk_data['content'].replace('#', '').replace('*', ''),
            }
        }
        es_docs.append(doc)
    
    return es_docs

# Usage
chunks = chunk_markdown(text)
es_docs = prepare_for_elasticsearch(chunks, 'documents')
```

## Troubleshooting

### Common Issues

**Empty output**: Check if chunks list is empty
```python
if not chunks:
    print("No chunks to render")
else:
    output = render_json(chunks)
```

**Unicode errors**: Ensure proper encoding
```python
# When writing to file
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(render_json(chunks), f, ensure_ascii=False)
```

**Memory issues**: Use streaming for large outputs
```python
def stream_render_json(chunks):
    """Stream JSON rendering for large chunk lists."""
    yield '['
    for i, chunk in enumerate(chunks):
        if i > 0:
            yield ','
        yield json.dumps(render_json([chunk])[0])
    yield ']'

# Usage
with open('large_output.json', 'w') as f:
    for part in stream_render_json(chunks):
        f.write(part)
```

## Related Documentation

- **[Configuration Guide](config.md)** - Controlling chunk generation
- **[Examples](examples.md)** - Practical renderer usage
- **[Integrations](integrations/dify.md)** - Platform-specific rendering
- **[Performance Guide](performance.md)** - Optimizing renderer performance
