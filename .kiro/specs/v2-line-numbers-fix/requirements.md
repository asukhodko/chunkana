# Requirements: Line Numbers Fix for Split Chunks

## Problem Statement

**CRITICAL-02:** Split chunks have incorrect `start_line/end_line` values.

When `SectionSplitter` splits an oversize chunk into multiple parts, all resulting chunks inherit the same `start_line/end_line` from the original chunk, instead of having accurate line numbers for their actual content.

### Example

Original chunk:
- Content: "## Scope\n\n1. Item 1\n2. Item 2\n...\n8. Item 8"
- `start_line: 333, end_line: 345`

After split:
- Chunk 0 (`split_index=0`): Items 1-7 → `start_line: 333, end_line: 345` ❌
- Chunk 1 (`split_index=1`): Item 8 → `start_line: 333, end_line: 345` ❌

**Expected:**
- Chunk 0: `start_line: 333, end_line: 341` (actual range for items 1-7)
- Chunk 1: `start_line: 342, end_line: 345` (actual range for item 8)

## Root Cause Analysis

### Technical Cause

In `SectionSplitter._create_chunk()`:
```python
return Chunk(
    content=content,
    start_line=original.start_line,  # ← Copies original
    end_line=original.end_line,      # ← Copies original
    metadata=metadata,
)
```

### Architectural Cause

`SectionSplitter` operates on `content` (text) without knowledge of:
1. Original document structure
2. Line mapping for segments
3. Position of segments within the original chunk

### Process Cause

1. **Insufficient test coverage** — No tests verify line numbers for split chunks
2. **Missing integration tests** — Unit tests don't catch metadata accuracy issues
3. **Incomplete design** — Line number recalculation not considered during SectionSplitter design

## Requirements

### Functional Requirements

#### FR-1: Accurate Line Numbers for Split Chunks
- **Priority:** Critical
- **Description:** Each split chunk must have correct `start_line/end_line` reflecting its actual position in the original document
- **Acceptance Criteria:**
  - Split chunks have different line ranges when content differs
  - Line ranges are ordered (chunk N+1 starts after chunk N ends)
  - Line ranges cover the actual content without overlap gaps

#### FR-2: Line Number Calculation Strategy
- **Priority:** Critical  
- **Description:** Define how line numbers are calculated for split chunks
- **Options:**
  1. **Content-only:** Line numbers reflect only the `content` field
  2. **Full-chunk:** Line numbers include header_stack repetition
  3. **Hybrid:** Separate fields for content vs full chunk ranges
- **Decision:** Content-only (most intuitive for users)

#### FR-3: Backward Compatibility
- **Priority:** High
- **Description:** Changes must not break existing functionality
- **Acceptance Criteria:**
  - Non-split chunks maintain exact same line numbers
  - All existing tests continue to pass
  - API remains unchanged

### Non-Functional Requirements

#### NFR-1: Performance
- **Priority:** Medium
- **Description:** Line number calculation should not significantly impact performance
- **Target:** < 10% overhead for documents with splits

#### NFR-2: Maintainability
- **Priority:** High
- **Description:** Solution should be maintainable and testable
- **Requirements:**
  - Clear separation of concerns
  - Comprehensive test coverage
  - Documentation of line number calculation logic

## Test Requirements

### Unit Tests
1. **Split chunk line numbers are different** when content differs
2. **Split chunk line numbers are ordered** (chunk N+1 > chunk N)
3. **Non-split chunks unchanged** (regression test)
4. **Edge cases:** Single segment, empty segments, header-only chunks

### Integration Tests
1. **End-to-end line number accuracy** on real documents
2. **Metadata consistency** across the full pipeline
3. **Performance impact** measurement

### Property-Based Tests
1. **Line number monotonicity** (always increasing)
2. **Coverage completeness** (no gaps in line ranges)
3. **Split invariants** (sum of split ranges ≤ original range)

## Success Criteria

1. **Correctness:** All split chunks have accurate line numbers
2. **Regression-free:** All existing tests pass
3. **Test coverage:** 100% coverage for line number calculation logic
4. **Performance:** < 10% overhead
5. **Documentation:** Clear explanation of line number semantics

## Out of Scope

1. **Overlap line numbers** — Line numbers reflect content only, not overlap
2. **Cross-chunk references** — No tracking of relationships between split chunks
3. **UI integration** — Library provides data, UI interpretation is out of scope

## Dependencies

- No external dependencies
- Requires access to original document structure during splitting
- May require refactoring of SectionSplitter architecture

## Risks

1. **Complexity:** Accurate line mapping may require significant architectural changes
2. **Performance:** Line number calculation could impact splitting performance
3. **Edge cases:** Complex documents may have unexpected line mapping scenarios

## Mitigation Strategies

1. **Incremental approach:** Start with simple cases, expand to complex ones
2. **Performance monitoring:** Benchmark before/after changes
3. **Comprehensive testing:** Property-based tests for edge cases