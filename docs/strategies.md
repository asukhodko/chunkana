# Chunking Strategies

Chunkana automatically selects the best strategy based on document content analysis.

## Strategy Selection Order

1. **CodeAware** (priority 1) — documents with code blocks or tables
2. **ListAware** (priority 2) — list-heavy documents
3. **Structural** (priority 3) — documents with hierarchical headers
4. **Fallback** (priority 4) — universal fallback

## CodeAware Strategy

Selected when:
- `code_block_count >= 1`, OR
- `table_count >= 1`, OR
- `code_ratio >= code_threshold` (default 0.3)

Features:
- Preserves code blocks intact (never splits mid-block)
- Preserves tables intact
- Preserves LaTeX display formulas
- Binds code blocks to surrounding explanations (if enabled)
- Groups related code blocks (before/after pairs, code/output)

## ListAware Strategy

Selected when (for non-structural documents):
- `list_ratio > list_ratio_threshold` (default 0.4), OR
- `list_count >= list_count_threshold` (default 5)

For structural documents (many headers), requires BOTH conditions.

Features:
- Preserves nested list hierarchies
- Binds introduction paragraphs to lists
- Groups related list items
- Handles checkbox lists with stats

## Structural Strategy

Selected when:
- `header_count >= structure_threshold` (default 3), AND
- `max_header_depth > 1`

Features:
- Splits by header boundaries
- Maintains header hierarchy in `header_path`
- Handles preamble (content before first header)
- Preserves atomic blocks within sections

## Fallback Strategy

Always available as last resort.

Features:
- Splits by paragraph boundaries
- Groups paragraphs to fit `max_chunk_size`
- Preserves atomic blocks if present

## Forcing a Strategy

```python
from chunkana import chunk_markdown, ChunkerConfig

# Force structural strategy
config = ChunkerConfig(strategy_override="structural")
chunks = chunk_markdown(text, config)
```

Valid values: `"code_aware"`, `"list_aware"`, `"structural"`, `"fallback"`

## Strategy in Metadata

Each chunk includes the strategy used:

```python
chunk.metadata["strategy"]  # e.g., "code_aware"
```

All chunks from the same document use the same strategy.
