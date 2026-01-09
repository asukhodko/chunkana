# Examples

This page provides practical examples for common Chunkana use cases.

## Table of Contents

- [Basic Chunking](#basic-chunking)
- [RAG Pipeline Integration](#rag-pipeline-integration)
- [Code Documentation](#code-documentation)
- [Scientific Documents](#scientific-documents)
- [Large Document Processing](#large-document-processing)
- [Custom Output Formats](#custom-output-formats)
- [Error Handling](#error-handling)

## Basic Chunking

### Simple Document Chunking

```python
from chunkana import chunk_markdown

markdown_text = """
# Project Overview

This project provides a comprehensive solution for document processing.

## Features

### Core Features
- Fast processing
- Memory efficient
- Easy to use

### Advanced Features
- Custom configurations
- Multiple output formats
- Integration support

## Getting Started

Follow these steps to get started:

1. Install the package
2. Configure your settings
3. Process your documents

```python
# Example usage
from myproject import process_document

result = process_document("input.md")
print(result)
```

## API Reference

The main API consists of these functions:

| Function | Description | Parameters |
|----------|-------------|------------|
| `process` | Main processing function | `input`, `config` |
| `validate` | Validate input | `input` |
| `export` | Export results | `data`, `format` |
"""

chunks = chunk_markdown(markdown_text)

print(f"Generated {len(chunks)} chunks:")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i+1}:")
    print(f"  Header: {chunk.metadata['header_path']}")
    print(f"  Type: {chunk.metadata['content_type']}")
    print(f"  Lines: {chunk.start_line}-{chunk.end_line}")
    print(f"  Size: {chunk.size} chars")
    print(f"  Has code: {chunk.metadata['has_code']}")
```

### Custom Configuration

```python
from chunkana import chunk_markdown, ChunkConfig

# Configuration for smaller chunks
config = ChunkConfig(
    max_chunk_size=1500,
    min_chunk_size=300,
    overlap_size=150,
)

chunks = chunk_markdown(markdown_text, config)
print(f"With custom config: {len(chunks)} chunks")
```

## RAG Pipeline Integration

### Vector Database Preparation

```python
from chunkana import chunk_markdown, ChunkConfig
from chunkana.renderers import render_json
import json

def prepare_for_vector_db(document_path: str, source_name: str):
    """Prepare document chunks for vector database ingestion."""
    
    # RAG-optimized configuration
    config = ChunkConfig(
        max_chunk_size=1500,    # Fit in embedding model context
        min_chunk_size=300,     # Ensure meaningful content
        overlap_size=150,       # Context continuity
    )
    
    # Read and chunk document
    with open(document_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    chunks = chunk_markdown(text, config)
    
    # Convert to JSON format
    json_chunks = render_json(chunks)
    
    # Enrich with source metadata
    for i, chunk_data in enumerate(json_chunks):
        chunk_data['metadata'].update({
            'source_file': source_name,
            'document_path': document_path,
            'chunk_id': f"{source_name}_{i}",
            'ingested_at': '2024-01-01T00:00:00Z',
        })
    
    return json_chunks

# Usage
chunks = prepare_for_vector_db('docs/user_guide.md', 'user_guide')

# Save for ingestion
with open('chunks_for_ingestion.json', 'w') as f:
    json.dump(chunks, f, indent=2)

print(f"Prepared {len(chunks)} chunks for vector database")
```

### Retrieval with Metadata Filtering

```python
def filter_chunks_for_query(chunks, query_type=None, has_code=None, header_contains=None):
    """Filter chunks based on metadata for targeted retrieval."""
    
    filtered = chunks
    
    if query_type:
        filtered = [c for c in filtered if c.metadata['content_type'] == query_type]
    
    if has_code is not None:
        filtered = [c for c in filtered if c.metadata['has_code'] == has_code]
    
    if header_contains:
        filtered = [c for c in filtered 
                   if header_contains.lower() in c.metadata['header_path'].lower()]
    
    return filtered

# Example usage
chunks = chunk_markdown(text)

# Find code examples
code_chunks = filter_chunks_for_query(chunks, has_code=True)
print(f"Found {len(code_chunks)} chunks with code")

# Find API documentation
api_chunks = filter_chunks_for_query(chunks, header_contains="API")
print(f"Found {len(api_chunks)} API-related chunks")
```

## Code Documentation

### Technical Documentation with Code Examples

```python
from chunkana import chunk_markdown, ChunkConfig

# Configuration optimized for code-heavy documents
code_config = ChunkConfig(
    max_chunk_size=3000,
    min_chunk_size=500,
    overlap_size=100,
    code_threshold=0.2,  # Lower threshold for code-aware strategy
    enable_code_context_binding=True,
    max_context_chars_before=400,
    max_context_chars_after=200,
)

technical_doc = """
# API Documentation

## Authentication

All API requests require authentication using API keys.

### Getting an API Key

1. Log into your dashboard
2. Navigate to API settings
3. Generate a new key

```python
import requests

# Set up authentication
headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}
```

### Making Requests

Use the following pattern for all API calls:

```python
def make_api_request(endpoint, data=None):
    url = f"https://api.example.com/{endpoint}"
    
    if data:
        response = requests.post(url, json=data, headers=headers)
    else:
        response = requests.get(url, headers=headers)
    
    return response.json()

# Example usage
result = make_api_request('users/profile')
print(result)
```

The response will include:

```json
{
    "user": {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com"
    },
    "status": "success"
}
```

## Error Handling

Handle API errors gracefully:

```python
try:
    result = make_api_request('invalid/endpoint')
except requests.exceptions.RequestException as e:
    print(f"API request failed: {e}")
```
"""

chunks = chunk_markdown(technical_doc, code_config)

# Analyze code distribution
code_chunks = [c for c in chunks if c.metadata['has_code']]
print(f"Code chunks: {len(code_chunks)}/{len(chunks)}")

for chunk in code_chunks:
    print(f"\nCode chunk: {chunk.metadata['header_path']}")
    print(f"  Strategy: {chunk.metadata['strategy']}")
    print(f"  Size: {chunk.size} chars")
```

## Scientific Documents

### LaTeX and Mathematical Content

```python
from chunkana import chunk_markdown, ChunkConfig

# Configuration for scientific documents
science_config = ChunkConfig(
    max_chunk_size=2500,
    preserve_latex_blocks=True,
    preserve_atomic_blocks=True,
)

scientific_doc = """
# Mathematical Analysis

## Linear Algebra

### Vector Spaces

A vector space $V$ over a field $F$ is a set equipped with two operations:

1. Vector addition: $u + v \in V$ for all $u, v \in V$
2. Scalar multiplication: $c \cdot v \in V$ for all $c \in F, v \in V$

These operations must satisfy the following axioms:

\\begin{align}
u + v &= v + u \\\\
(u + v) + w &= u + (v + w) \\\\
c(u + v) &= cu + cv \\\\
(c + d)u &= cu + du
\\end{align}

### Matrix Operations

For matrices $A \in \mathbb{R}^{m \\times n}$ and $B \in \mathbb{R}^{n \\times p}$:

$$C = AB \quad \text{where} \quad C_{ij} = \sum_{k=1}^{n} A_{ik}B_{kj}$$

## Calculus

### Derivatives

The derivative of a function $f(x)$ is defined as:

$$f'(x) = \lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$

Common derivatives include:

| Function | Derivative |
|----------|------------|
| $x^n$ | $nx^{n-1}$ |
| $e^x$ | $e^x$ |
| $\ln(x)$ | $\\frac{1}{x}$ |
| $\sin(x)$ | $\cos(x)$ |
"""

chunks = chunk_markdown(scientific_doc, science_config)

print(f"Scientific document chunked into {len(chunks)} pieces")
for chunk in chunks:
    # Check if chunk contains LaTeX
    has_latex = '$' in chunk.content or '\\begin{' in chunk.content
    print(f"\nChunk: {chunk.metadata['header_path']}")
    print(f"  Contains LaTeX: {has_latex}")
    print(f"  Size: {chunk.size} chars")
```

## Large Document Processing

### Memory-Efficient Streaming

```python
from chunkana import MarkdownChunker
import os

def process_large_document(file_path: str, output_dir: str):
    """Process large documents without loading entirely into memory."""
    
    chunker = MarkdownChunker()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    chunk_count = 0
    total_size = 0
    
    # Stream chunks from file
    for chunk in chunker.chunk_file_streaming(file_path):
        chunk_count += 1
        total_size += chunk.size
        
        # Save each chunk separately
        chunk_file = os.path.join(output_dir, f"chunk_{chunk_count:04d}.md")
        
        with open(chunk_file, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Chunk {chunk_count} -->\n")
            f.write(f"<!-- Header: {chunk.metadata['header_path']} -->\n")
            f.write(f"<!-- Lines: {chunk.start_line}-{chunk.end_line} -->\n")
            f.write(f"<!-- Size: {chunk.size} chars -->\n\n")
            f.write(chunk.content)
        
        # Progress indicator
        if chunk_count % 100 == 0:
            print(f"Processed {chunk_count} chunks...")
    
    print(f"\nCompleted: {chunk_count} chunks, {total_size:,} total characters")
    return chunk_count

# Usage
chunk_count = process_large_document('large_manual.md', 'output_chunks/')
```

### Batch Processing Multiple Files

```python
import os
from pathlib import Path
from chunkana import chunk_markdown, ChunkConfig

def batch_process_documents(input_dir: str, output_file: str):
    """Process multiple Markdown files and combine results."""
    
    config = ChunkConfig(max_chunk_size=2000, overlap_size=100)
    all_chunks = []
    
    # Process all .md files in directory
    for md_file in Path(input_dir).glob('**/*.md'):
        print(f"Processing {md_file}...")
        
        with open(md_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        chunks = chunk_markdown(text, config)
        
        # Add source file to metadata
        for chunk in chunks:
            chunk.metadata['source_file'] = str(md_file.relative_to(input_dir))
        
        all_chunks.extend(chunks)
    
    # Save combined results
    from chunkana.renderers import render_json
    import json
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(render_json(all_chunks), f, indent=2)
    
    print(f"Processed {len(all_chunks)} total chunks from {len(list(Path(input_dir).glob('**/*.md')))} files")
    return all_chunks

# Usage
chunks = batch_process_documents('docs/', 'all_chunks.json')
```

## Custom Output Formats

### Creating Custom Renderers

```python
from chunkana import chunk_markdown
from typing import List, Dict, Any

def render_for_elasticsearch(chunks) -> List[Dict[str, Any]]:
    """Render chunks for Elasticsearch indexing."""
    
    documents = []
    
    for chunk in chunks:
        doc = {
            '_index': 'documents',
            '_source': {
                'content': chunk.content,
                'header_path': chunk.metadata['header_path'],
                'content_type': chunk.metadata['content_type'],
                'size': chunk.size,
                'line_range': f"{chunk.start_line}-{chunk.end_line}",
                'has_code': chunk.metadata['has_code'],
                'strategy': chunk.metadata['strategy'],
                # Add searchable text without markdown
                'plain_text': chunk.content.replace('#', '').replace('*', '').replace('`', ''),
                # Extract code blocks for separate indexing
                'code_blocks': extract_code_blocks(chunk.content) if chunk.metadata['has_code'] else [],
            }
        }
        documents.append(doc)
    
    return documents

def extract_code_blocks(content: str) -> List[str]:
    """Extract code blocks from markdown content."""
    import re
    
    # Find fenced code blocks
    pattern = r'```(?:\w+)?\n(.*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    
    return [match.strip() for match in matches]

# Usage
chunks = chunk_markdown(text)
es_docs = render_for_elasticsearch(chunks)

print(f"Generated {len(es_docs)} Elasticsearch documents")
```

### XML Output Format

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

def render_as_xml(chunks) -> str:
    """Render chunks as XML for structured processing."""
    
    root = ET.Element('document')
    root.set('chunk_count', str(len(chunks)))
    
    for i, chunk in enumerate(chunks):
        chunk_elem = ET.SubElement(root, 'chunk')
        chunk_elem.set('index', str(i))
        chunk_elem.set('id', str(chunk.metadata.get('chunk_id', i)))
        
        # Content
        content_elem = ET.SubElement(chunk_elem, 'content')
        content_elem.text = chunk.content
        
        # Metadata
        metadata_elem = ET.SubElement(chunk_elem, 'metadata')
        
        for key, value in chunk.metadata.items():
            if isinstance(value, (str, int, float, bool)):
                meta_elem = ET.SubElement(metadata_elem, key)
                meta_elem.text = str(value)
        
        # Position info
        position_elem = ET.SubElement(chunk_elem, 'position')
        position_elem.set('start_line', str(chunk.start_line))
        position_elem.set('end_line', str(chunk.end_line))
        position_elem.set('size', str(chunk.size))
    
    # Pretty print
    rough_string = ET.tostring(root, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

# Usage
chunks = chunk_markdown(text)
xml_output = render_as_xml(chunks)

with open('chunks.xml', 'w', encoding='utf-8') as f:
    f.write(xml_output)
```

## Error Handling

### Robust Processing with Error Recovery

```python
from chunkana import chunk_markdown, ChunkConfig
from chunkana.exceptions import ChunkanaError
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_chunk_document(text: str, config: ChunkConfig = None) -> tuple[list, list]:
    """Safely chunk document with error handling and recovery."""
    
    chunks = []
    errors = []
    
    try:
        # Try normal chunking first
        chunks = chunk_markdown(text, config)
        logger.info(f"Successfully chunked document into {len(chunks)} pieces")
        
    except ChunkanaError as e:
        logger.error(f"Chunkana error: {e}")
        errors.append(f"Chunking failed: {e}")
        
        # Try with fallback configuration
        try:
            fallback_config = ChunkConfig(
                max_chunk_size=8192,  # Larger chunks
                min_chunk_size=100,   # Smaller minimum
                overlap_size=0,       # No overlap
                strategy_override="fallback"  # Force fallback strategy
            )
            
            chunks = chunk_markdown(text, fallback_config)
            logger.warning(f"Fallback chunking succeeded: {len(chunks)} chunks")
            errors.append("Used fallback configuration")
            
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            errors.append(f"Fallback failed: {fallback_error}")
            
            # Last resort: split by paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            chunks = create_simple_chunks(paragraphs)
            errors.append("Used simple paragraph splitting")
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        errors.append(f"Unexpected error: {e}")
        
        # Emergency fallback
        chunks = create_simple_chunks([text])
        errors.append("Used emergency fallback")
    
    return chunks, errors

def create_simple_chunks(paragraphs: list[str]):
    """Create simple chunks from paragraphs as last resort."""
    from chunkana.core import Chunk
    
    chunks = []
    for i, para in enumerate(paragraphs):
        chunk = Chunk(
            content=para,
            start_line=i + 1,
            end_line=i + 1,
            metadata={
                'chunk_index': i,
                'content_type': 'text',
                'header_path': '/Emergency',
                'strategy': 'emergency_fallback',
                'has_code': False,
            }
        )
        chunks.append(chunk)
    
    return chunks

# Usage
text = "Your markdown content here..."
chunks, errors = safe_chunk_document(text)

if errors:
    print("Warnings/Errors encountered:")
    for error in errors:
        print(f"  - {error}")

print(f"Final result: {len(chunks)} chunks")
```

### Validation and Quality Checks

```python
def validate_chunks(chunks, original_text: str) -> dict:
    """Validate chunk quality and completeness."""
    
    validation_results = {
        'total_chunks': len(chunks),
        'total_size': sum(chunk.size for chunk in chunks),
        'original_size': len(original_text),
        'coverage_ratio': 0.0,
        'issues': [],
        'warnings': [],
    }
    
    # Check coverage
    total_content = ''.join(chunk.content for chunk in chunks)
    validation_results['coverage_ratio'] = len(total_content) / len(original_text)
    
    if validation_results['coverage_ratio'] < 0.95:
        validation_results['issues'].append(
            f"Low coverage: {validation_results['coverage_ratio']:.2%}"
        )
    
    # Check for empty chunks
    empty_chunks = [i for i, chunk in enumerate(chunks) if not chunk.content.strip()]
    if empty_chunks:
        validation_results['issues'].append(f"Empty chunks found: {empty_chunks}")
    
    # Check for very small chunks
    small_chunks = [i for i, chunk in enumerate(chunks) if chunk.size < 50]
    if small_chunks:
        validation_results['warnings'].append(f"Very small chunks: {small_chunks}")
    
    # Check line number consistency
    for i, chunk in enumerate(chunks):
        if chunk.start_line > chunk.end_line:
            validation_results['issues'].append(f"Invalid line range in chunk {i}")
    
    # Check metadata consistency
    for i, chunk in enumerate(chunks):
        if not chunk.metadata.get('header_path'):
            validation_results['warnings'].append(f"Missing header_path in chunk {i}")
    
    return validation_results

# Usage
chunks = chunk_markdown(text)
validation = validate_chunks(chunks, text)

print(f"Validation Results:")
print(f"  Chunks: {validation['total_chunks']}")
print(f"  Coverage: {validation['coverage_ratio']:.2%}")

if validation['issues']:
    print("  Issues:")
    for issue in validation['issues']:
        print(f"    - {issue}")

if validation['warnings']:
    print("  Warnings:")
    for warning in validation['warnings']:
        print(f"    - {warning}")
```

## Next Steps

- **[Configuration Guide](config.md)** - Learn about all configuration options
- **[Integrations](integrations/dify.md)** - Connect to your workflow
- **[API Reference](api/)** - Complete API documentation
- **[Troubleshooting](errors.md)** - Common issues and solutions