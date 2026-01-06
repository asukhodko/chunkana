# Debug Mode

<cite>
**Referenced Files in This Document**   
- [debug_mode.md](file://docs/debug_mode.md)
- [config.py](file://src/chunkana/config.py)
- [chunker.py](file://src/chunkana/chunker.py)
- [types.py](file://src/chunkana/types.py)
- [metadata_recalculator.py](file://src/chunkana/metadata_recalculator.py)
- [test_debug_mode.py](file://test_debug_mode.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Enabling Debug Mode](#enabling-debug-mode)
3. [Debug Configuration Options](#debug-configuration-options)
4. [Additional Metadata in Debug Mode](#additional-metadata-in-debug-mode)
5. [Interpreting Debug Output](#interpreting-debug-output)
6. [Using Debug Mode with Different Document Types](#using-debug-mode-with-different-document-types)
7. [Performance Implications](#performance-implications)
8. [Optimizing Configuration with Debug Information](#optimizing-configuration-with-debug-information)
9. [Conclusion](#conclusion)

## Introduction
Debug mode in Chunkana provides enhanced diagnostic capabilities for troubleshooting chunking issues and understanding the internal decision-making process of the chunking algorithm. This documentation explains how to enable and use debug mode, the additional metadata and analysis data exposed, and how to interpret this information to optimize chunking configurations for different document types. Debug mode is particularly useful for developers and system administrators who need to understand and fine-tune the chunking behavior for specific content.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L1-L99)

## Enabling Debug Mode
Debug mode is enabled through the hierarchical chunking API by accessing all chunks, including non-leaf nodes, which provides a complete view of the chunking hierarchy. This is equivalent to the `debug` parameter in the original Dify plugin, which when enabled with `enable_hierarchy=true`, includes all chunks (root, intermediate, and leaf) in the output.

To enable debug mode, use the `chunk_hierarchical` method and access all chunks through the `chunks` property of the `HierarchicalChunkingResult` object, rather than using `get_flat_chunks()` which filters out non-leaf chunks by default.

```python
from chunkana import MarkdownChunker, ChunkConfig

config = ChunkConfig(max_chunk_size=1000, validate_invariants=True)
chunker = MarkdownChunker(config)
result = chunker.chunk_hierarchical(document)

# In debug mode, access all chunks including non-leaf nodes
all_chunks = result.chunks  # This is equivalent to debug mode
```

The debug mode behavior is controlled by the hierarchical chunking result's ability to expose the complete tree structure, allowing inspection of intermediate chunks that would normally be filtered out in standard retrieval scenarios.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L19-L79)
- [config.py](file://src/chunkana/config.py#L108-L110)

## Debug Configuration Options
Debug mode functionality is influenced by several configuration options that control the verbosity and validation of the chunking process. The primary debug-related configuration parameters are `validate_invariants` and `strict_mode`, which work together to provide diagnostic information about the hierarchical structure of chunks.

The `validate_invariants` parameter enables validation of tree structure invariants, checking for issues like inconsistent leaf node flags, bidirectional parent-child relationships, and content range consistency. When set to `True`, the system validates these invariants after constructing the hierarchical chunk structure.

The `strict_mode` parameter determines how invariant violations are handled. When `False` (the default), violations are logged as warnings and automatically fixed. When `True`, violations raise exceptions, which can be useful for debugging but may interrupt processing in production environments.

```python
config = ChunkConfig(
    max_chunk_size=1000,
    min_chunk_size=100,
    validate_invariants=True,  # Enable invariant validation
    strict_mode=False  # Log warnings instead of raising exceptions
)
```

These configuration options allow users to control the level of diagnostic output and error handling, making it possible to detect and address structural issues in the chunking hierarchy during development and testing.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L83-L98)
- [config.py](file://src/chunkana/config.py#L108-L110)

## Additional Metadata in Debug Mode
Debug mode exposes additional metadata fields that provide insights into the chunking process, strategy selection, and content analysis. When using hierarchical chunking (debug mode), chunks contain enhanced metadata beyond the standard fields.

In addition to the standard metadata fields like `content_type`, `header_path`, `header_level`, `chunk_index`, and `strategy`, hierarchical chunks include tree structure information such as `chunk_id`, `parent_id`, `children_ids`, `is_leaf`, `is_root`, `hierarchy_level`, `prev_sibling_id`, and `next_sibling_id`. These fields enable navigation of the chunk hierarchy and understanding of the relationships between chunks.

The strategy selection rationale is exposed through the `strategy` metadata field, which indicates which chunking strategy was selected for each chunk. The content analysis metrics are also available through the `chunk_with_analysis` method, which returns the `ContentAnalysis` object containing metrics like `code_ratio`, `header_count`, `max_header_depth`, `table_count`, `list_count`, and `list_ratio`.

```python
# Example of metadata available in debug mode
{
    "content_type": "section",
    "header_path": "/Level1/Level2",
    "header_level": 2,
    "chunk_index": 0,
    "strategy": "structural",
    "chunk_id": "abc123",
    "parent_id": "root",
    "children_ids": ["child1", "child2"],
    "is_leaf": False,
    "is_root": True,
    "hierarchy_level": 0,
    "prev_sibling_id": null,
    "next_sibling_id": "sibling2"
}
```

This additional metadata allows users to understand not only the final chunk structure but also the reasoning behind chunk boundary decisions and the hierarchical relationships between chunks.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L9-L32)
- [types.py](file://src/chunkana/types.py#L255-L289)
- [chunker.py](file://src/chunkana/chunker.py#L217-L247)

## Interpreting Debug Output
Interpreting debug output requires understanding the chunking pipeline and the meaning of various metadata fields. The debug output provides information about strategy selection rationale, content analysis metrics, and hierarchical relationships that can be used to understand chunk boundary decisions.

The strategy selection is determined by the `StrategySelector` class, which evaluates the document based on content analysis metrics and selects the most appropriate strategy. The selection criteria are:
- `CodeAwareStrategy`: Activated when the document has code blocks, tables, or code ratio exceeds the `code_threshold`
- `ListAwareStrategy`: Activated when the document is list-heavy, based on `list_ratio_threshold` and `list_count_threshold`
- `StructuralStrategy`: Activated when the document has sufficient headers and hierarchy depth
- `FallbackStrategy`: Universal fallback when no other strategy applies

The content analysis metrics exposed in debug mode include `code_ratio` (code characters divided by total characters), `header_count`, `max_header_depth`, `table_count`, `list_count`, and `list_ratio`. These metrics help explain why a particular strategy was selected.

For example, if a document has a high `code_ratio` (e.g., 0.45) exceeding the default `code_threshold` of 0.3, the `CodeAwareStrategy` will be selected. Similarly, if a document has many headers (e.g., 10) exceeding the default `structure_threshold` of 3, the `StructuralStrategy` will be selected.

The hierarchical relationships in the debug output show how chunks are organized in a tree structure, with parent-child relationships indicating the document's section hierarchy. This helps identify issues like orphaned chunks or inconsistent tree structures that might affect retrieval quality.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L83-L98)
- [types.py](file://src/chunkana/types.py#L189-L220)
- [strategies/__init__.py](file://src/chunkana/strategies/__init__.py#L20-L60)

## Using Debug Mode with Different Document Types
Debug mode can be used with various document types to understand and optimize chunking behavior. The approach to using debug mode varies depending on the document type and its characteristics.

For code-heavy documents, debug mode helps verify that code blocks are preserved intact and that context binding is working correctly. The `code_ratio` metric indicates the proportion of code in the document, and the `code_context_binding` parameters control how explanations are bound to code blocks.

For structured documents with hierarchical headers, debug mode shows how the document is divided into sections based on header levels. The `header_path` metadata field reveals the hierarchical path to each chunk, while the `hierarchy_level` indicates the depth in the tree structure.

For list-heavy documents like changelogs or task lists, debug mode helps ensure that list hierarchies are preserved and that related list items are grouped together. The `list_ratio` and `list_count` metrics determine whether the `ListAwareStrategy` is selected.

For documents with tables or LaTeX formulas, debug mode verifies that these atomic blocks are kept intact and properly grouped. The `table_grouping` and `preserve_latex_blocks` configuration options can be tested and optimized using debug mode.

When using debug mode with different document types, it's important to examine the strategy selection rationale and content analysis metrics to understand why a particular strategy was chosen and whether it's appropriate for the document's structure and content.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L1-L99)
- [config.py](file://src/chunkana/config.py#L86-L91)
- [strategies/code_aware.py](file://src/chunkana/strategies/code_aware.py#L32-L40)
- [strategies/list_aware.py](file://src/chunkana/strategies/list_aware.py#L48-L89)
- [strategies/structural.py](file://src/chunkana/strategies/structural.py#L52-L56)

## Performance Implications
Debug mode has performance implications that should be considered when using it in production environments. The primary performance impact comes from the additional validation and metadata processing required in debug mode.

The `validate_invariants` parameter, when enabled, adds computational overhead by checking tree structure invariants after constructing the hierarchical chunk structure. This validation process checks for issues like inconsistent leaf node flags, bidirectional parent-child relationships, and content range consistency, which requires traversing the chunk hierarchy and verifying relationships.

The `strict_mode` parameter affects performance differently depending on its setting. When `False` (the default), invariant violations are logged as warnings and automatically fixed, which has minimal performance impact. When `True`, violations raise exceptions, which can be more expensive due to exception handling overhead but provides more detailed diagnostic information.

Hierarchical chunking, which enables debug mode, creates additional metadata and maintains parent-child relationships, which increases memory usage compared to standard chunking. The creation of chunk IDs and maintenance of the hierarchy tree structure adds computational overhead.

For performance-critical applications, it's recommended to disable validation in production by setting `validate_invariants=False`. This skips tree validation while still producing the same chunk boundaries and content, resulting in faster processing times.

Typical performance benchmarks show that chunking small documents (~100 lines) takes approximately 0.1ms, medium documents (~1000 lines) take about 0.7ms, and large documents (~10000 lines) take around 2.7ms. These times may increase when debug mode is fully enabled with validation.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L83-L98)
- [config.py](file://src/chunkana/config.py#L108-L110)
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L476-L485)

## Optimizing Configuration with Debug Information
Debug information can be used to optimize configuration for specific content types by analyzing the strategy selection rationale and content analysis metrics. By examining the debug output, users can adjust configuration parameters to achieve better chunking results for their specific documents.

The key configuration parameters that can be optimized based on debug information include:
- `code_threshold`: Adjust based on the typical code ratio of your documents
- `structure_threshold`: Set according to the typical header count in your structured documents
- `list_ratio_threshold` and `list_count_threshold`: Tune for list-heavy documents like changelogs
- `max_chunk_size` and `min_chunk_size`: Optimize based on the typical content distribution
- `overlap_size`: Adjust to control the amount of context provided between chunks

For example, if debug output shows that code-heavy documents are not being chunked optimally, the `code_threshold` can be lowered to ensure the `CodeAwareStrategy` is selected more frequently. Similarly, if structured documents with moderate header counts are not using the `StructuralStrategy`, the `structure_threshold` can be reduced.

The `chunk_with_analysis` method provides direct access to the `ContentAnalysis` object, which contains all the metrics used for strategy selection. This allows users to programmatically analyze documents and adjust configuration parameters accordingly.

```python
# Example of using analysis to optimize configuration
chunks, strategy_name, analysis = chunker.chunk_with_analysis(document)
print(f"Selected strategy: {strategy_name}")
print(f"Code ratio: {analysis.code_ratio}")
print(f"Header count: {analysis.header_count}")
print(f"List ratio: {analysis.list_ratio}")
```

By systematically analyzing debug output across a representative sample of documents, users can identify patterns and adjust configuration parameters to improve chunking quality and retrieval performance.

**Section sources**
- [debug_mode.md](file://docs/debug_mode.md#L1-L99)
- [chunker.py](file://src/chunkana/chunker.py#L191-L215)
- [types.py](file://src/chunkana/types.py#L189-L220)

## Conclusion
Debug mode in Chunkana provides valuable diagnostic capabilities for understanding and troubleshooting chunking behavior. By enabling hierarchical chunking and accessing all chunks, users can gain insights into strategy selection, content analysis, and hierarchical relationships that inform optimization of chunking configurations.

The debug configuration options `validate_invariants` and `strict_mode` allow control over validation and error handling, while the additional metadata exposed in debug mode reveals the internal decision-making process of the chunking algorithm. This information can be used to interpret chunk boundary decisions and optimize configuration parameters for specific document types.

While debug mode has performance implications due to additional validation and metadata processing, it is an essential tool for developers and system administrators who need to ensure high-quality chunking for their applications. By systematically analyzing debug output, users can fine-tune configuration parameters to achieve optimal results for their specific content.

For production use, it's recommended to disable validation by setting `validate_invariants=False` to minimize performance impact while still benefiting from the core chunking functionality. Debug mode should be used during development and testing phases to ensure the chunking behavior meets requirements before deployment to production environments.