# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-05

### Added
- **Hierarchical Invariant Validation**: Tree structure validation with `validate_invariants` and `strict_mode` parameters
- **Exception Hierarchy**: New exceptions for better error handling
  - `ChunkanaError` - base exception
  - `HierarchicalInvariantError` - tree structure violations
  - `ValidationError` - validation failures
  - `ConfigurationError` - invalid configuration
  - `TreeConstructionError` - tree building failures
- **Dangling Header Prevention**: Automatic prevention of headers being separated from their content
- **HeaderProcessor Component**: New `DanglingHeaderDetector`, `HeaderMover`, `HeaderProcessor` classes
- **Performance Tests**: Comprehensive performance regression test suite
- **Documentation**: Debug mode documentation, troubleshooting guide

### Changed
- `get_flat_chunks()` now includes non-leaf chunks with significant content (>100 chars) to prevent content loss
- `ChunkConfig` now accepts `validate_invariants` (default: True) and `strict_mode` (default: False) parameters
- Improved `is_leaf` calculation logic for consistency

### Fixed
- Fixed parent-child bidirectionality issues in hierarchical chunking
- Fixed orphaned chunk detection and handling
- Fixed micro-chunk handling to preserve structural significance

### Performance
- Small docs (~100 lines): ~0.1ms
- Medium docs (~1000 lines): ~0.7ms
- Large docs (~10000 lines): ~2.7ms
- Validation overhead: <20%
- Linear scaling confirmed

## [0.1.0] - 2024-12-XX

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
