# Overview

Chunkana is a semantic Markdown chunking library designed for RAG pipelines, search indexing, and LLM ingestion. Unlike traditional text splitters, Chunkana preserves document structure and provides rich metadata for intelligent retrieval.

## The Problem with Traditional Splitters

Most text splitters treat Markdown as plain text, leading to:

- **Broken code blocks** - Syntax highlighting and context lost
- **Fragmented tables** - Headers separated from data rows  
- **Split lists** - Hierarchical structure destroyed
- **Orphaned headers** - Headings separated from their content
- **Broken LaTeX** - Mathematical formulas split mid-equation

## How Chunkana Solves This

Chunkana uses **semantic boundaries** to ensure every chunk is structurally complete:

### ✅ Structure Preservation
- Headers stay with their content
- Code blocks remain atomic
- Tables keep headers with data
- Lists maintain hierarchy
- LaTeX formulas stay intact

### ✅ Rich Metadata
Every chunk includes:
- **Header path**: `/Introduction/Getting Started`
- **Content type**: `section`, `code`, `table`, `list`
- **Line ranges**: Exact source location
- **Overlap context**: For sliding window retrieval
- **Strategy used**: How the chunk was created

### ✅ Smart Strategy Selection
Chunkana automatically chooses the best approach:
- **Code-aware**: For documentation with many code blocks
- **List-aware**: For structured content with nested lists
- **Structural**: For narrative content with clear sections
- **Fallback**: For edge cases and mixed content

## Core Concepts

### Chunks
A **chunk** is a semantically complete piece of Markdown that:
- Never breaks mid-structure (code, table, list, etc.)
- Includes rich metadata for retrieval
- Maintains source line references
- Preserves hierarchical context

### Strategies  
**Strategies** determine how content is split:
- Automatically selected based on document analysis
- Can be manually overridden if needed
- Optimized for different content types

### Hierarchy
**Hierarchical chunking** creates a tree structure:
- Mirrors document outline structure
- Enables section-aware navigation
- Supports both flat and tree-based retrieval

### Renderers
**Renderers** format output for different systems:
- JSON for APIs and databases
- Dify-style for workflow integration
- Inline metadata for debugging
- Custom formats as needed

## Use Cases

### RAG Pipelines
- Preserve code examples for technical documentation
- Maintain table structure for data-heavy content
- Keep mathematical formulas intact
- Provide header context for better retrieval

### LLM Context Preparation
- Ensure code blocks fit cleanly in context windows
- Maintain document structure for better understanding
- Provide overlap for context continuity
- Enable section-aware prompting

### Search Indexing
- Index by content type (code, tables, text)
- Filter by header hierarchy
- Rank by structural importance
- Maintain source traceability

### Document Processing
- Migrate from other chunking systems
- Batch process large document collections
- Stream large files without memory issues
- Validate chunking quality with invariants

## Performance Characteristics

- **Memory efficient**: Stream large documents without loading entirely
- **Fast processing**: Linear time complexity with document size
- **Scalable**: Handle multi-megabyte documents
- **Configurable**: Tune for your specific use case

## Next Steps

- **New to Chunkana?** Start with the [Quick Start Guide](quickstart.md)
- **Need configuration help?** See the [Configuration Guide](config.md)
- **Want to integrate?** Check out [Integrations](integrations/dify.md)
- **Having issues?** Visit [Troubleshooting](errors.md)
