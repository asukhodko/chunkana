# Migration Guide

<cite>
**Referenced Files in This Document**   
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md)
- [docs/migration/parity_matrix.md](file://docs/migration/parity_matrix.md)
- [src/chunkana/config.py](file://src/chunkana/config.py)
- [src/chunkana/compat.py](file://src/chunkana/compat.py)
- [src/chunkana/types.py](file://src/chunkana/types.py)
- [src/chunkana/__init__.py](file://src/chunkana/__init__.py)
- [src/chunkana/api.py](file://src/chunkana/api.py)
- [src/chunkana/chunker.py](file://src/chunkana/chunker.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Breaking Changes](#breaking-changes)
3. [Step-by-Step Migration](#step-by-step-migration)
4. [Parity Matrix](#parity-matrix)
5. [Configuration Migration](#configuration-migration)
6. [Data Migration](#data-migration)
7. [Rationale for Major Changes](#rationale-for-major-changes)
8. [Deprecation Timeline and Compatibility](#deprecation-timeline-and-compatibility)
9. [Troubleshooting](#troubleshooting)
10. [Validation Steps](#validation-steps)

## Introduction

This migration guide provides comprehensive instructions for upgrading from dify-markdown-chunker v2 to Chunkana. The core chunking algorithm remains identical, ensuring full compatibility with existing outputs, while the API has been simplified and extended with new features.

Chunkana extracts the core functionality from the dify-markdown-chunker v2 plugin into a standalone library, offering improved usability, enhanced features, and better maintainability. The migration process is designed to be straightforward, with backward compatibility maintained for critical functionality.

The guide covers all aspects of the migration, including breaking changes, configuration updates, data migration strategies, and troubleshooting common issues. It also explains the rationale behind major changes to help users understand the benefits of upgrading.

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L1-L486)

## Breaking Changes

### Return Types

The most significant breaking change is in the return types of the chunking functions. In dify-markdown-chunker v2, the `chunk()` method could return either a list of strings or a list of Chunk objects depending on parameters. Chunkana standardizes this behavior.

**Before (dify-markdown-chunker v2):**
```python
result = chunker.chunk(text, include_metadata=True)  # Returns List[str]
```

**After (Chunkana):**
```python
chunks = chunk_markdown(text)  # Always returns List[Chunk]
result = render_dify_style(chunks)  # Use renderers for string output
```

This change ensures consistent return types and separates the concerns of chunking and rendering.

### include_metadata Parameter

The `include_metadata` parameter has been removed from the core chunking function and replaced with dedicated renderer functions.

**Before:**
```python
result = chunker.chunk(text, include_metadata=True)   # With metadata blocks
result = chunker.chunk(text, include_metadata=False)  # With embedded overlap
```

**After:**
```python
from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_with_embedded_overlap

chunks = chunk_markdown(text)
output = render_dify_style(chunks)                    # Equivalent to include_metadata=True
output = render_with_embedded_overlap(chunks)         # Equivalent to include_metadata=False
```

This change provides more explicit control over output format and enables additional rendering options.

### Configuration Class Renaming

The configuration class has been renamed from `ChunkConfig` to `ChunkerConfig` for clarity, though both names are supported via an alias.

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L32-L73)
- [src/chunkana/config.py](file://src/chunkana/config.py#L505-L506)

## Step-by-Step Migration

### Step 1: Update Dependencies

Update your project dependencies to replace the old plugin with Chunkana.

```diff
# requirements.txt
- dify-markdown-chunker>=2.0.0
+ chunkana>=0.2.0
```

Install the new package using pip:
```bash
pip install chunkana>=0.2.0
```

### Step 2: Update Imports

Update your import statements to use the new module structure.

```diff
- from markdown_chunker_v2 import MarkdownChunker, ChunkConfig
+ from chunkana import chunk_markdown, ChunkerConfig
+ from chunkana.renderers import render_dify_style
```

### Step 3: Update Chunking Code

Modify your chunking code to use the new API structure.

```diff
- config = ChunkConfig(max_chunk_size=4096)
- chunker = MarkdownChunker(config)
- result = chunker.chunk(text, include_metadata=True)
+ config = ChunkerConfig(max_chunk_size=4096)
+ chunks = chunk_markdown(text, config)
+ result = render_dify_style(chunks)
```

### Step 4: Select Renderer Based on include_metadata

Use the appropriate renderer function based on your previous `include_metadata` setting.

| Plugin Parameter | Chunkana Renderer |
|------------------|-------------------|
| `include_metadata=True` | `render_dify_style(chunks)` |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` |

### Step 5: Update Hierarchical Chunking

For hierarchical chunking, update your code to use the new API.

**Before:**
```python
result = chunker.chunk(text, enable_hierarchy=True)
```

**After:**
```python
from chunkana import chunk_hierarchical, ChunkerConfig

config = ChunkerConfig(
    max_chunk_size=1000,
    validate_invariants=True,  # Validates tree structure (default)
    strict_mode=False,         # Auto-fix issues (default)
)
result = chunk_hierarchical(text, config)

# Access leaf chunks (backward compatible)
flat_chunks = result.get_flat_chunks()
```

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L75-L264)

## Parity Matrix

The following matrix compares features between dify-markdown-chunker v2 and Chunkana, showing full compatibility for existing functionality and new extensions in Chunkana.

### ChunkConfig Fields

| Plugin ChunkConfig | Type | Default | Chunkana ChunkerConfig | Status |
|--------------------|------|---------|------------------------|--------|
| `max_chunk_size` | int | 4096 | `max_chunk_size` | ✅ Supported |
| `min_chunk_size` | int | 512 | `min_chunk_size` | ✅ Supported |
| `overlap_size` | int | 200 | `overlap_size` | ✅ Supported |
| `enable_overlap` | bool | (computed) | (computed from overlap_size > 0) | ✅ Computed |
| `preserve_atomic_blocks` | bool | True | `preserve_atomic_blocks` | ✅ Supported |
| `extract_preamble` | bool | True | `extract_preamble` | ✅ Supported |
| `code_threshold` | float | 0.3 | `code_threshold` | ✅ Supported |
| `structure_threshold` | int | 3 | `structure_threshold` | ✅ Supported |
| `list_ratio_threshold` | float | 0.4 | `list_ratio_threshold` | ✅ Supported |
| `list_count_threshold` | int | 5 | `list_count_threshold` | ✅ Supported |
| `strategy_override` | str\|None | None | `strategy_override` | ✅ Supported |
| `enable_code_context_binding` | bool | True | `enable_code_context_binding` | ✅ Supported |
| `max_context_chars_before` | int | 500 | `max_context_chars_before` | ✅ Supported |
| `max_context_chars_after` | int | 300 | `max_context_chars_after` | ✅ Supported |
| `related_block_max_gap` | int | 5 | `related_block_max_gap` | ✅ Supported |
| `bind_output_blocks` | bool | True | `bind_output_blocks` | ✅ Supported |
| `preserve_before_after_pairs` | bool | True | `preserve_before_after_pairs` | ✅ Supported |

### Chunkana-Only Extensions

| ChunkerConfig Field | Type | Default | Description |
|---------------------|------|---------|-------------|
| `use_adaptive_sizing` | bool | False | Enable adaptive chunk sizing |
| `adaptive_config` | AdaptiveSizeConfig | None | Adaptive sizing parameters |
| `group_related_tables` | bool | False | Group related tables together |
| `table_grouping_config` | TableGroupingConfig | None | Table grouping parameters |
| `overlap_cap_ratio` | float | 0.35 | Max overlap as fraction of chunk |
| `preserve_latex_blocks` | bool | True | Keep LaTeX blocks intact |

### Output Format Mapping

| Plugin Mode | Chunkana Renderer | Output |
|-------------|-------------------|--------|
| `include_metadata=True` | `render_dify_style(chunks)` | `<metadata>` blocks + content |
| `include_metadata=False` | `render_with_embedded_overlap(chunks)` | Embedded overlap in text |

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L110-L162)
- [docs/migration/parity_matrix.md](file://docs/migration/parity_matrix.md#L11-L112)

## Configuration Migration

### Complete Parameter Mapping

#### Dify Tool Input Parameters → Chunkana

| Plugin Tool Param | Type | Default | Chunkana Equivalent | Notes |
|-------------------|------|---------|---------------------|-------|
| `input_text` | string | (required) | First argument to `chunk_markdown()` | The Markdown text to chunk |
| `max_chunk_size` | number | 4096 | `ChunkerConfig.max_chunk_size` | Maximum chunk size in characters |
| `chunk_overlap` | number | 200 | `ChunkerConfig.overlap_size` | Characters to overlap between chunks |
| `strategy` | select | "auto" | `ChunkerConfig.strategy_override` | "auto" = None in Chunkana |
| `include_metadata` | boolean | true | Renderer selection | `render_dify_style()` or `render_with_embedded_overlap()` |
| `enable_hierarchy` | boolean | false | `chunk_hierarchical()` | Use hierarchical chunking API |
| `debug` | boolean | false | `HierarchicalChunkingResult.get_all_chunks()` | Include non-leaf chunks |

### Configuration Factory Methods

Chunkana provides factory methods for common configuration profiles:

```python
# Default configuration
config = ChunkerConfig.default()

# For code-heavy documents
config = ChunkerConfig.for_code_heavy()

# For structured documents
config = ChunkerConfig.for_structured()

# Minimal configuration with small chunks
config = ChunkerConfig.minimal()

# For changelogs
config = ChunkerConfig.for_changelogs()

# With adaptive sizing
config = ChunkerConfig.with_adaptive_sizing()
```

### Legacy Parameter Support

Chunkana maintains backward compatibility with legacy parameter names through the `from_legacy()` method:

```python
# This will work with deprecation warnings
config = ChunkerConfig.from_legacy(max_size=4096, min_size=512)
```

The following legacy parameters are supported with automatic conversion:
- `max_size` → `max_chunk_size`
- `min_size` → `min_chunk_size`

Removed parameters (always enabled or removed):
- `enable_overlap`, `block_based_splitting`, `preserve_code_blocks`, `preserve_tables`, `enable_deduplication`, `enable_regression_validation`, `enable_header_path_validation`, `use_enhanced_parser`, `use_legacy_overlap`, `enable_block_overlap`, `enable_sentence_splitting`, `enable_paragraph_merging`, `enable_list_preservation`, `enable_metadata_enrichment`, `enable_size_normalization`, `enable_fallback_strategy`

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L110-L162)
- [src/chunkana/config.py](file://src/chunkana/config.py#L254-L307)

## Data Migration

### Stored Chunks Migration

When migrating stored chunks from dify-markdown-chunker v2 to Chunkana, no data transformation is required for the canonical chunk format. The chunk boundaries, content, line numbers, and metadata are byte-for-byte identical.

For chunks stored in view-level format (rendered strings), you have two options:

1. **Re-chunk the original Markdown**: Process the original Markdown content with Chunkana to generate new chunks.
2. **Parse existing rendered output**: Extract the original content from the rendered strings and use Chunkana to re-chunk.

### Configuration Data Migration

Configuration data stored in JSON or other formats can be migrated directly, as Chunkana's `ChunkerConfig.from_dict()` method supports all fields from the v2 plugin.

```python
# Load existing configuration
with open('config.json') as f:
    config_data = json.load(f)

# Create Chunkana configuration
config = ChunkerConfig.from_dict(config_data)
```

The `from_dict()` method handles legacy parameters and ignores unknown fields for forward compatibility.

### Migration of Hierarchical Data

For hierarchical chunking results, the tree structure is rebuilt from the flat chunks using header paths. The `chunk_hierarchical()` function reconstructs the parent-child relationships based on the `header_path` metadata.

```python
# Rebuild hierarchy from stored chunks
result = chunk_hierarchical(original_markdown_text, config)
```

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L335-L379)
- [src/chunkana/chunker.py](file://src/chunkana/chunker.py#L273-L304)

## Rationale for Major Changes

### Simplified API Design

The primary rationale for the API changes is to simplify the interface and separate concerns. By standardizing the return type to always return `List[Chunk]` and moving rendering to dedicated functions, the API becomes more predictable and easier to use.

This separation of concerns allows for:
- More renderer options without complicating the core API
- Better type safety and IDE support
- Easier extension with new rendering formats
- Clearer distinction between chunking logic and output formatting

### Enhanced Configuration System

The configuration system was redesigned to reduce complexity from 32 parameters to 8 core parameters while maintaining all essential functionality. This simplification makes the API more approachable while still providing access to advanced features through extension fields.

The addition of factory methods (`for_code_heavy()`, `for_structured()`, etc.) provides optimized configurations for common use cases, improving usability.

### Improved Extensibility

Chunkana introduces several new features that were not available in the v2 plugin:

- **Adaptive sizing**: Dynamically adjusts chunk size based on content complexity
- **Table grouping**: Groups related tables into single chunks for better retrieval quality
- **LaTeX preservation**: Treats LaTeX formulas as atomic blocks
- **Overlap cap ratio**: Limits overlap as a fraction of chunk size to prevent bloat

These extensions are designed to improve RAG (Retrieval-Augmented Generation) performance by creating more contextually coherent chunks.

### Better Error Handling

The hierarchical chunking system now includes tree invariant validation with configurable strictness:

```python
config = ChunkerConfig(
    validate_invariants=True,  # Validate tree structure (default)
    strict_mode=False,         # Auto-fix issues; set to True to raise exceptions
)
```

This provides better reliability and easier debugging of hierarchical structures.

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L1-L486)
- [README.md](file://README.md#L1-L179)

## Deprecation Timeline and Compatibility

### Backward Compatibility Guarantees

Chunkana provides the following compatibility guarantees:

#### Guaranteed to Match Plugin (Byte-for-Byte)
- Chunk boundaries (`start_line`, `end_line`)
- Chunk content (canonical, without embedded overlap)
- All metadata: `chunk_index`, `strategy`, `header_path`, `content_type`, `previous_content`, `next_content`
- `chunk_id` format (8-char SHA256 hash)
- Renderer output format (verified against baseline golden outputs)

#### Not Guaranteed
- **Streaming chunk boundaries**: `chunk_file_streaming()` may produce different boundaries at buffer splits
- **Streaming overlap metadata**: May differ at buffer boundaries

### Deprecation Policy

The following v2 plugin features are deprecated and will be removed in future major versions:

- Direct parameter passing to `MarkdownChunker()` constructor (use `ChunkerConfig` instead)
- Union return types from chunking functions
- The `enable_overlap` parameter (use `overlap_size > 0` instead)

The `LegacyMarkdownChunker` class provides backward compatibility for existing code using v1 interfaces, but its use is discouraged for new development.

### Version Support

- **v0.2.x**: Current stable version with full v2 plugin compatibility
- **v1.0.0**: Planned release with removal of deprecated features
- **Long-term support**: Critical bug fixes will be provided for v0.2.x for 12 months after v1.0.0 release

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L335-L349)
- [BASELINE.md](file://BASELINE.md#L1-L115)

## Troubleshooting

### HierarchicalInvariantError Exceptions

If you encounter `HierarchicalInvariantError` in strict mode, here's how to handle common cases:

#### is_leaf_consistency

```python
# Error: is_leaf=True but chunk has children
HierarchicalInvariantError: is_leaf_consistency violated in chunk abc123

# Solution: This is auto-fixed in non-strict mode. In strict mode:
config = ChunkConfig(strict_mode=False)  # Enable auto-fix
```

#### parent_child_bidirectionality

```python
# Error: Parent-child relationship is not symmetric
HierarchicalInvariantError: parent_child_bidirectionality violated

# Solution: Usually indicates corrupted tree state. Re-chunk the document:
result = chunker.chunk_hierarchical(text)  # Fresh chunking
```

#### orphaned_chunk

```python
# Error: Chunk is not reachable from root
HierarchicalInvariantError: orphaned_chunk detected

# Solution: Auto-fixed in non-strict mode by attaching to nearest parent
config = ChunkConfig(strict_mode=False)
```

### Debugging Hierarchical Issues

Enable strict mode temporarily to see all violations:

```python
from chunkana import MarkdownChunker, ChunkConfig
from chunkana import HierarchicalInvariantError

config = ChunkConfig(
    validate_invariants=True,
    strict_mode=True,  # Raise exceptions instead of auto-fix
)

try:
    result = chunker.chunk_hierarchical(text)
except HierarchicalInvariantError as e:
    print(f"Invariant: {e.invariant}")
    print(f"Chunk ID: {e.chunk_id}")
    print(f"Details: {e.details}")
    print(f"Suggested fix: {e.suggested_fix}")
```

### Performance Considerations

If chunking is slow for large documents:

```python
# Disable validation for performance-critical paths
config = ChunkConfig(
    validate_invariants=False,  # Skip tree validation
)
```

Typical performance benchmarks:
- Small docs (~100 lines): ~0.1ms
- Medium docs (~1000 lines): ~0.7ms
- Large docs (~10000 lines): ~2.7ms

### Small Chunk Merging Behavior

Chunkana optimizes chunk boundaries by merging small H1 header chunks with their following section content, which differs from the v2 plugin behavior.

**Plugin behavior:** Creates separate small chunks for H1 headers with `small_chunk: true` metadata.

**Chunkana behavior:** Merges small H1 header chunks with their following section content, producing fewer but more contextually complete chunks.

If your application relies on separate small chunks for H1 headers, you may need to adjust your retrieval logic.

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L413-L485)
- [CHANGELOG.md](file://CHANGELOG.md#L1-L75)

## Validation Steps

To verify your migration is correct, follow these validation steps:

### Step 1: Run Baseline Canonical Tests

Verify that the canonical chunk output matches the golden outputs from the v2 plugin.

```bash
pytest tests/baseline/test_canonical.py -v
```

### Step 2: Run View-Level Tests

Verify that the rendered output matches the expected format.

```bash
pytest tests/baseline/test_view_level.py -v
```

### Step 3: Run Property Tests

Verify that all domain properties are satisfied.

```bash
pytest tests/property/ -v
```

### Step 4: Compare Key Fixtures

Manually compare the output for key fixture types:
- Nested code fences
- Complex lists
- Tables
- LaTeX formulas
- Adaptive sizing scenarios
- Table grouping scenarios

### Step 5: Verify Configuration Parity

Ensure that all configuration parameters are properly mapped and functioning.

```bash
pytest tests/baseline/test_config_parity.py -v
```

### Step 6: Test Real-World Documents

Test the migration with your actual production documents to ensure compatibility with your specific use cases.

**Section sources**
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L381-L405)
- [tests/baseline/test_canonical.py](file://tests/baseline/test_canonical.py#L1-L158)