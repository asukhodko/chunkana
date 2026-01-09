# Chunkana

Chunkana is a semantic Markdown chunker that turns documents into retrieval-ready chunks for RAG and LLM pipelines.
USP: Structure-preserving chunking with rich metadata in a single pass.

[![GitHub Repository](https://img.shields.io/badge/GitHub-Chunkana-181717?logo=github)](https://github.com/asukhodko/chunkana)
[![PyPI version](https://img.shields.io/pypi/v/chunkana.svg)](https://pypi.org/project/chunkana/)
[![Python versions](https://img.shields.io/pypi/pyversions/chunkana.svg)](https://pypi.org/project/chunkana/)
[![License](https://img.shields.io/pypi/l/chunkana.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/chunkana.svg)](https://pypi.org/project/chunkana/)

## Table of Contents

- [Installation](#installation)
- [Quickstart](#quickstart)
- [Overview](#overview)
- [Why Chunkana](#why-chunkana)
- [Key Features](#key-features)
- [Supported Markdown constructs](#supported-markdown-constructs)
- [Requirements](#requirements)
- [Output/Metadata schema](#outputmetadata-schema)
- [Performance/Scalability](#performancescalability)
- [Compatibility](#compatibility)
- [Use Cases](#use-cases)
- [Core Concepts](#core-concepts)
- [Usage examples](#usage-examples)
- [Configuration](#configuration)
- [Renderers](#renderers)
- [Integrations](#integrations)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Links](#links)

## Installation

Install quickly with pip and start chunking in minutes.
Optional extras keep docs tooling separate from runtime dependencies.

```bash
pip install chunkana
```

Optional extras:

```bash
pip install "chunkana[docs]"
```

## Quickstart

Get end-to-end chunking in a few lines while keeping headers and code blocks intact.
Every chunk includes line ranges and header paths for instant retrieval metadata.

```python
from chunkana import chunk_markdown

text = """
# My Document

## Section One

Some content here.

## Section Two

More content with code:

```python
def hello():
    print("Hello!")
```
"""

chunks = chunk_markdown(text)
for chunk in chunks:
    print(f"{chunk.start_line}-{chunk.end_line}: {chunk.metadata['header_path']}")
```

## Overview

**Chunkana** turns complex Markdown into retrieval-ready chunks for RAG and LLM ingestion without breaking structure. It preserves headers, code blocks, tables, and math so your context windows stay coherent. It also emits rich metadata so indexing, search, and reranking stay accurate.

Chunkana is a high-precision Markdown chunking library for RAG pipelines, search indexing, and LLM ingestion. It keeps semantic boundaries intact so downstream retrieval stays faithful to the original document. It is built for teams that need structure-preserving chunks at scale without custom parsers.

## Why Chunkana

### Concrete differentiators

- **Semantic guarantees**: never splits atomic structures (headers, lists, code fences, tables, LaTeX blocks) so each chunk stays valid and retrievable.
- **RAG metadata first**: every chunk carries header paths, line ranges, content type, overlap context, and strategy hints for filtering and ranking.
- **Plugin compatibility**: renderers emit structured payloads compatible with various downstream systems.
- **Adaptive strategies**: auto-selects structure-, list-, or code-aware strategies to keep mixed documents coherent.

### Problem → Solution

- **Naive splitter breaks code fences** → **Chunkana keeps code blocks atomic and binds nearby context.**
- **Tables get fragmented and lose headers** → **Chunkana preserves tables as single semantic units.**
- **Lists lose hierarchy** → **Chunkana respects nested list structure.**
- **Math/LaTeX gets split mid-formula** → **Chunkana keeps formulas intact for retrieval.**

### Practical defaults & limits

- **Chunk size defaults**: `max_chunk_size=4096`, `min_chunk_size=512`.
- **Overlap metadata**: `overlap_size=200` characters, capped to 35% of adjacent chunk size for consistency.
- **Large-file throughput**: streaming APIs process multi-megabyte Markdown without loading everything into memory.

### Project Status / Compatibility / Support

- **Stability:** Beta (actively maintained, APIs may evolve as features land).
- **Support:** Please report issues or feature requests in the [GitHub issue tracker](https://github.com/asukhodko/chunkana/issues).

## Key Features

- **Semantic correctness**: preserves headers, lists, tables, code blocks, and LaTeX without splitting mid-block.
- **RAG-ready metadata**: header paths, content types, line ranges, and overlap context for retrieval.
- **Smart strategy selection**: adapts to code-heavy, list-heavy, or structural documents automatically.
- **Hierarchical navigation**: build a chunk tree for section-aware retrieval and summarization.
- **Streaming for large files**: chunk multi-megabyte documents without loading everything into memory.
- **Compatibility**: output formats for Dify and JSON APIs.

## Supported Markdown constructs

- Headings and nested section structure.
- Ordered/unordered lists and nested list blocks.
- Fenced code blocks and inline code spans.
- Tables and mixed content (text + tables).
- LaTeX math (inline and block).

## Requirements

- Python **3.12+**
- Recommended: `pip install chunkana` (optional docs extras: `pip install "chunkana[docs]"`).

## Output/Metadata schema

Chunks are returned as `Chunk` objects or renderer-specific formats (JSON, Dify, inline metadata).
Core fields follow this shape:

```json
{
  "content": "Markdown content...",
  "start_line": 1,
  "end_line": 42,
  "size": 1234,
  "line_count": 42,
  "metadata": {
    "chunk_index": 0,
    "content_type": "section",
    "header_path": "/Intro/Overview",
    "header_level": 2,
    "strategy": "structural",
    "has_code": false,
    "sub_headers": ["Details"],
    "previous_content": "...",
    "next_content": "...",
    "overlap_size": 200,
    "small_chunk": false,
    "small_chunk_reason": "cannot_merge"
  }
}
```

## Performance/Scalability

- Stream large files without full-memory loads via `chunk_file_streaming()` or `chunk_stream()`.
- Adaptive strategy selection keeps chunking stable on code-heavy or list-heavy documents.
- Overlap metadata supports sliding-window retrieval without duplicating content.

## Compatibility

- [Dify](docs/integrations/dify.md): renderer parity for plugin ingestion.
- [n8n](docs/integrations/n8n.md): automation-friendly pipelines.
- [Windmill](docs/integrations/windmill.md): data workflows and batch jobs.

## Use Cases

- **RAG ingestion** for product docs, handbooks, and knowledge bases where structure matters.
- **LLM context window prep** for chatbots that need clean, scoped sections.
- **Search indexing** with metadata-rich chunks for precise filtering and ranking.
- **Markdown preservation** when your pipeline must keep headings, lists, and code intact.

## Core Concepts

- **Chunk**: a semantically complete slice of Markdown, never broken mid-structure.
- **Metadata**: header paths, content type, and line ranges to power retrieval and filtering.
- **Hierarchy**: optional tree structure for section-aware navigation and summaries.

## Usage examples

Use these patterns to scale from simple chunking to rich retrieval pipelines.
Each example shows a focused capability you can drop into production quickly.

### 1) Streaming for large documents (memory-safe)

**Why this matters:** stream multi-megabyte files without loading the whole document into RAM.

```python
from chunkana import MarkdownChunker

chunker = MarkdownChunker()
for chunk in chunker.chunk_file_streaming("docs/handbook.md"):
    print(chunk.metadata["chunk_index"], chunk.size)
```

**Memory note:** the streaming API yields chunks incrementally, so peak memory stays close to chunk size instead of document size.

### 2) Hierarchical mode + choosing flat vs all chunks

**Why this matters:** use `flat_chunks` for indexing, but keep `all_chunks` for tree navigation and summaries.

```python
from chunkana import MarkdownChunker, ChunkConfig

chunker = MarkdownChunker(ChunkConfig(validate_invariants=True))
result = chunker.chunk_hierarchical(text)

all_chunks = result.chunks  # all nodes (root + parents + leaves)
flat_chunks = result.get_flat_chunks()  # leaves + significant parents
```

**Tip:** prefer `flat_chunks` for retrieval, and keep `all_chunks` for navigation (`get_children`, `get_parent`).

### 3) Tables + LaTeX grouping

**Why this matters:** group related tables and keep formulas intact for better retrieval context.

```python
from chunkana import chunk_markdown, ChunkConfig

config = ChunkConfig(
    group_related_tables=True,
    preserve_latex_blocks=True,
)

chunks = chunk_markdown(text, config)
```

**Expected output format:** tables are grouped and LaTeX blocks stay atomic within each `Chunk`.

### 4) Custom render/export with metadata enrichment (JSON)

**Why this matters:** enrich chunks before exporting to a vector store or search index.

```python
from chunkana import chunk_markdown
from chunkana.renderers import render_json

chunks = chunk_markdown(text)
payload = render_json(chunks)

for item in payload:
    item["metadata"]["source"] = "docs/handbook.md"
    item["metadata"]["ingested_at"] = "2024-06-01"
```

**Expected output format:** a list of dicts you can serialize directly (e.g., `json.dumps(payload)`).

### 5) RAG preset with tuned chunk size + overlap

**Why this matters:** balance recall and token budget for retrieval.

```python
from chunkana import chunk_markdown, ChunkConfig

rag_config = ChunkConfig(
    max_chunk_size=2000,
    min_chunk_size=400,
    overlap_size=150,
)

chunks = chunk_markdown(text, rag_config)
```

**Sizing guide:** set `max_chunk_size` near your target context window slice, and `overlap_size` just large enough to keep cross-boundary context (typically 5–10% of `max_chunk_size`).

## Configuration

Tune chunk sizes to match your embedding limits and recall targets.
Overlap settings keep context continuity for downstream reranking.

```python
from chunkana import chunk_markdown, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
)

chunks = chunk_markdown(text, config)
```

## Renderers

Render chunks into formats that plug directly into your pipelines.
Switch outputs without re-chunking to support multiple consumers.

```python
from chunkana.renderers import (
    render_dify_style,
    render_json,
    render_inline_metadata,
    render_with_embedded_overlap,
)
```

- **render_dify_style** — `<metadata>` blocks for Dify.
- **render_json** — list of dictionaries for JSON APIs.
- **render_inline_metadata** — HTML comment metadata inline.
- **render_with_embedded_overlap** — injects overlap into text for RAG windows.

## Integrations

- [Dify](docs/integrations/dify.md) for ready-made ingestion workflows.
- [n8n](docs/integrations/n8n.md) for automation-friendly pipelines.
- [Windmill](docs/integrations/windmill.md) for data workflows and batch jobs.

## FAQ

**Q: What makes Chunkana different from a basic Markdown splitter?**
Chunkana is a semantic chunker that keeps structure intact (headers, lists, code blocks, tables, LaTeX) and enriches chunks with retrieval metadata.

**Q: Does Chunkana work for RAG and LLM ingestion?**
Yes. It is optimized for RAG chunking and LLM context preparation with overlap metadata and consistent hierarchy paths.

## Contributing

We welcome issues and pull requests that improve chunk quality or add integrations.
See the [contributing guide](CONTRIBUTING.md) for setup, tests, and style checks.

## License

Chunkana is released under the [MIT License](LICENSE) for commercial and open-source use.
Simple, permissive licensing keeps adoption friction low.

## Links

Follow these guides to go from first chunk to production-ready ingestion.
Each link highlights a focused capability you can adopt incrementally.

- [Overview](docs/overview.md)
- [Documentation Index](docs/index.md)
- [Quick Start](docs/quickstart.md)
- [Configuration](docs/config.md)
- [Renderers](docs/renderers.md)
- [Metadata reference](docs/metadata.md)
- [Errors & troubleshooting](docs/errors.md)
