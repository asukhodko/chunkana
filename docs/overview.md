# Overview

Chunkana is a semantic Markdown chunking library designed for RAG pipelines, search indexing, and LLM ingestion. It splits Markdown into retrieval-ready chunks while preserving structure and context.

## What Chunkana solves

Traditional splitters break Markdown structure and cause semantic drift. Chunkana avoids that by:

- Preserving **headers, lists, tables, code blocks, and LaTeX** as atomic units.
- Recording **header paths** and **content types** for structured retrieval.
- Providing **overlap metadata** for sliding window context.
- Supporting **hierarchical chunk trees** for section-aware navigation.

## Typical use cases

- **RAG pipelines**: get semantically coherent chunks and metadata for vector search.
- **LLM ingestion**: keep code examples and tables intact inside context windows.
- **Search indexing**: store header paths and types for faceted search.
- **Docs migration**: replace naive Markdown splitting with structural chunking.

## How it works (high level)

1. Chunkana analyzes the document structure and content ratios.
2. It selects an optimal strategy (code-aware, list-aware, structural, or fallback).
3. It builds chunks that respect Markdown syntax and your size constraints.
4. It emits chunks with metadata to support downstream retrieval.

## Core concepts

- **Chunk**: a unit of text with metadata like `header_path`, `content_type`, and line range.
- **Strategy**: the chunking algorithm selected per document.
- **Hierarchy**: a tree of chunks that mirrors header structure.
- **Renderers**: output formatters for Dify or JSON APIs.

## Next steps

- [Quick Start](quickstart.md)
- [Configuration](config.md)
- [Strategies](strategies.md)
- [Renderers](renderers.md)
- [Integrations](integrations/dify.md)
