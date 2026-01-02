# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release extracted from dify-markdown-chunker v2
- Core chunking API: `chunk_markdown()`, `MarkdownChunker`
- Analysis API: `analyze_markdown()`, `chunk_with_analysis()`, `chunk_with_metrics()`
- Configuration system with `ChunkerConfig`
- Four chunking strategies: CodeAware, ListAware, Structural, Fallback
- Atomic block preservation (code, tables, LaTeX)
- Hierarchical chunking with `chunk_hierarchical()`
- Streaming support with `iter_chunks()`
- Multiple renderers: JSON, inline metadata, Dify-style
- Comprehensive test suite with baseline compatibility tests
