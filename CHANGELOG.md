# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.4] - 2026-01-06

### Fixed
- **CRITICAL-02: Accurate Line Numbers for Split Chunks**
  - Split chunks now have different, accurate `start_line`/`end_line` values
  - Line numbers reflect actual content position in original document
  - Split chunks are ordered by line numbers (monotonic)
  - Non-split chunks maintain unchanged line numbers (backward compatible)

### Added
- **SegmentWithPosition**: New dataclass for tracking segment positions during splitting
  - Fields: `content`, `start_line_offset`, `end_line_offset`, `original_text`
  - Enables accurate line number calculation for each split segment
- **Enhanced SectionSplitter Methods**:
  - `_find_segments_with_positions()`: Position-aware segment finding
  - `_calculate_segment_positions()`: Line offset calculation for segments
  - `_create_chunk_with_lines()`: Chunk creation with accurate line numbers
  - `_pack_segments_into_chunks_with_lines()`: Packing with line number tracking
- **Comprehensive Test Suite**:
  - Unit tests for line number calculation (`test_section_splitter_line_numbers.py`)
  - Integration tests for split chunk accuracy (`test_split_chunk_line_numbers.py`)
  - Property-based tests for line number invariants (`test_line_numbers_properties.py`)
  - Performance tests for overhead measurement (`test_line_numbers_performance.py`)
  - Regression tests in existing test suite

### Changed
- **Line Number Semantics**: Clarified that line numbers reflect content-only (not including overlap)
- **SectionSplitter Architecture**: Enhanced to track segment positions throughout splitting process
- **Error Handling**: Improved fallback positioning when segments cannot be found in body text

### Technical Details
- Line number calculation uses content-only semantics for consistency
- Segment search with fallback to sequential positioning
- Edge case handling: header-only chunks, empty segments, single segments
- Performance overhead < 10% for documents with splits
- All existing functionality preserved (100% backward compatible)

## [0.1.3] - 2026-01-06

### Added
- **SectionSplitter Component**: New component for splitting oversize sections with header_stack repetition
  - Extracts all consecutive headers at chunk start as `header_stack`
  - Repeats header_stack in continuation chunks for context preservation
  - Splits by list items, paragraphs, or sentences (priority order)
  - Adds metadata: `continued_from_header`, `split_index`, `original_section_size`
- **InvariantValidator Component**: New component for validating chunking quality
  - Recall-based coverage metric (not inflated by repetition/overlap)
  - Dangling header check for ALL levels 1-6
  - Valid oversize reasons: `code_block_integrity`, `table_integrity`, `list_item_integrity`
- **New Exports**: `SectionSplitter`, `InvariantValidator`, `InvariantValidationResult`
- **Regression Tests**: 21 new tests for v2 critical fixes

### Changed
- **CRITICAL Pipeline Order Fix**: Dangling header fix now runs BEFORE section splitting
  - This ensures headers are "attached" to content before any splitting occurs
  - Split chunks can now properly repeat the header_stack
- **HeaderProcessor Improvements**:
  - Detection expanded from levels 3-6 to levels 2-6
  - Threshold reduced from 50 to 30 characters
  - Max iterations increased from 10 to 20
  - Now uses `header_moved_from_id` (chunk_id) instead of `header_moved_from` (index) for stable tracking
- **Removed `section_integrity` as valid oversize reason**: Text and list sections should be split, not marked as oversize
  - Only `code_block_integrity`, `table_integrity`, `list_item_integrity` are now valid

### Fixed
- Fixed dangling headers in all sections (Scope, Impact, Leadership, Improvement, Technical Complexity)
- Fixed max_chunk_size violations for text/list content (now properly split)
- Fixed header context loss when splitting large sections

## [0.1.2] - 2026-01-05

### Added
- **Universal Dangling Header Fix**: Detection now works for all sections (Scope, Impact, Leadership, Improvement, etc.), not just specific header paths
- **MetadataRecalculator Component**: New component that recalculates `section_tags` after all post-processing to ensure consistency with actual content
- **header_moved_from Tracking**: Now properly tracks source chunk index when headers are moved (uses `chunk_index` instead of `chunk_id`)
- **Line Range Contract Documentation**: Added documentation explaining `start_line`/`end_line` semantics in hierarchical mode
- **Debug Mode Validation**: Added `validate_in_debug_mode()` method for section_tags consistency checking
- **Regression Tests**: 13 new tests for issues identified in TEST_REPORT_v2
- **Test Fixture**: Added `tests/fixtures/sde_criteria.md` for regression testing

### Changed
- `DanglingHeaderDetector` now detects headers at levels 3-6 (was only level 4+)
- `HeaderProcessor.prevent_dangling_headers()` increased max iterations from 5 to 10 for complex documents
- `section_tags` metadata now always reflects actual headers in chunk content after post-processing

### Fixed
- Fixed dangling headers not being detected in Impact, Leadership, Improvement sections
- Fixed `section_tags` desync after header moves (tags now match actual content)
- Fixed `header_moved_from` always being null (now properly populated with source chunk index)
- Fixed duplicate `_mark_leaves` method definition in hierarchy.py

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
