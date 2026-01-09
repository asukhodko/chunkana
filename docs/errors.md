# Errors & troubleshooting

This page summarizes the main exception types raised by Chunkana and provides practical guidance for resolving them.

## ChunkanaError (base class)

All Chunkana-specific errors inherit from `ChunkanaError`. The exception includes a human-readable message plus a `context` dictionary with debugging details.

**Tips**
- Log or print `error.get_context()` to see structured debugging data.
- Use this base class if you want to catch all Chunkana-specific failures in one place.

## ValidationError

Raised when chunk validation fails (for example, invalid line ranges or missing required fields). Validation errors usually include the `error_type`, a problematic `chunk_id` (when available), and a `suggested_fix`.

**Common causes**
- `start_line` or `end_line` is invalid or inverted.
- Required fields are missing in serialized chunk data.

**Tips**
- Re-run chunking with a clean source document to ensure line ranges are consistent.
- If you are deserializing chunks, validate that `start_line` and `end_line` are present and numeric.

## HierarchicalInvariantError

Raised when hierarchical chunk tree invariants are violated (for example, children IDs are missing from parents or leaf flags are inconsistent). This exception is emitted when hierarchical validation is enabled and `strict_mode=True`.

**Common causes**
- Manual modification of `parent_id` / `children_ids` after chunking.
- Missing `chunk_id` values when building a tree.
- Inconsistent `is_leaf` flags vs. `children_ids`.

**Tips**
- Keep `validate_invariants=True` but set `strict_mode=False` during investigation to log warnings instead of raising.
- Prefer using helper APIs (like `get_children`, `get_parent`, `get_siblings`) rather than mutating hierarchy metadata directly.

## ConfigurationError

Raised when configuration values are invalid or incompatible. The error includes the parameter name, the provided value, and possible valid values.

**Common causes**
- `overlap_size` is negative or larger than `max_chunk_size`.
- Strategy overrides that do not match known strategy names.

**Tips**
- Validate configuration early (when instantiating `ChunkConfig`) to catch issues before chunking.
- Use `strategy_override` only with `code_aware`, `list_aware`, `structural`, or `fallback`.

## Related docs

- [Debug mode](debug_mode.md)
- [Metadata reference](metadata.md)
