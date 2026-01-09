# Metadata reference

This page explains the `Chunk` fields and the most important entries inside `chunk.metadata`.

## Chunk fields

Each chunk is a `Chunk` object with the following top-level fields:

- `content`: the Markdown content for the chunk (no overlap text is embedded).
- `start_line`: 1-indexed start line in the original document.
- `end_line`: 1-indexed end line in the original document.
- `size`: character length of `content`.
- `line_count`: number of lines in the chunk (`end_line - start_line + 1`).
- `metadata`: dictionary with retrieval and debugging metadata.

> **Line ranges can overlap.** When overlap is enabled, adjacent chunks can share line ranges because overlap context is stored in metadata. The line range always refers to the actual content inside `chunk.content`.

## Metadata fields

### `header_path`

A path-like string showing where the chunk sits in the document hierarchy, e.g. `/Guides/Setup`. It is built from the nearest header stack and is stable across sub-chunks in the same section.

### `content_type`

A high-level category for the chunk content. Typical values include:

- `text` — regular prose.
- `section` — section content produced by the structural strategy.
- `code` — code blocks.
- `table` — Markdown tables.
- `mixed` — mixed content (text + blocks).
- `preamble` — content before the first header.
- `document` — root chunk in hierarchical mode.

### `strategy`

The strategy that produced the chunk (for example `structural`, `code_aware`, `list_aware`, or `fallback`). Use this to trace why a chunk looks the way it does and to compare strategy behavior.

### Overlap metadata

When overlap is enabled (`overlap_size > 0`), chunks include context windows in metadata rather than embedding text directly:

- `previous_content`: overlap extracted from the end of the previous chunk.
- `next_content`: overlap extracted from the start of the next chunk.
- `overlap_size`: the actual number of characters stored in the overlap window (capped by the configured overlap ratio).

### `chunk_id`

A stable identifier added in hierarchical mode. It is used to build the chunk tree and to link parents/children/siblings. In hierarchical mode you will also see additional fields like `parent_id`, `children_ids`, `prev_sibling_id`, `next_sibling_id`, `is_leaf`, and `is_root`.

## Related docs

- [Overview](overview.md)
- [Debug mode](debug_mode.md)
- [Errors & troubleshooting](errors.md)
