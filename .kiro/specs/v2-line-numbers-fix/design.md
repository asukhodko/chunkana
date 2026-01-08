# Design Document: Line Numbers Fix for Split Chunks

## Overview

This design addresses CRITICAL-02 by implementing accurate line number calculation for split chunks. The solution involves tracking segment positions during splitting and recalculating line numbers for each resulting chunk.

## Architecture

### Current Architecture (Problematic)

```
SectionSplitter.split_oversize_sections()
├── _split_chunk(original_chunk)
│   ├── _extract_header_stack_and_body(content)
│   ├── _find_segments(body)  # ← Loses line position info
│   └── _pack_segments_into_chunks()
│       └── _create_chunk()  # ← Copies original line numbers
```

**Problem:** Segment extraction loses connection to original line positions.

### New Architecture (Solution)

```
SectionSplitter.split_oversize_sections()
├── _split_chunk(original_chunk)
│   ├── _extract_header_stack_and_body(content)
│   ├── _find_segments_with_positions(body, original)  # ← NEW: Track positions
│   └── _pack_segments_into_chunks_with_lines()        # ← NEW: Calculate lines
│       └── _create_chunk_with_lines()                 # ← NEW: Accurate lines
```

## Components

### 1. SegmentWithPosition

New data structure to track segment content and its position:

```python
@dataclass
class SegmentWithPosition:
    """Segment with its position in the original document."""
    content: str
    start_line_offset: int  # Offset from original chunk start
    end_line_offset: int    # Offset from original chunk start
    original_text: str      # For debugging/validation
```

### 2. Enhanced SectionSplitter

#### New Method: `_find_segments_with_positions()`

```python
def _find_segments_with_positions(
    self, 
    body: str, 
    original: Chunk
) -> list[SegmentWithPosition]:
    """
    Find segments with their line positions in the original document.
    
    Strategy:
    1. Split body into segments (existing logic)
    2. For each segment, find its position in original content
    3. Calculate line offsets from original.start_line
    
    Args:
        body: Body text (without header_stack)
        original: Original chunk being split
        
    Returns:
        List of segments with position information
    """
```

#### Algorithm: Line Position Calculation

```python
def _calculate_segment_positions(
    self, 
    segments: list[str], 
    body: str, 
    original: Chunk
) -> list[SegmentWithPosition]:
    """
    Calculate line positions for segments.
    
    Algorithm:
    1. Find body start line in original content
    2. For each segment:
       a. Find segment start position in body
       b. Count lines from body start to segment start
       c. Count lines in segment
       d. Calculate absolute line numbers
    """
    result = []
    body_start_line = self._find_body_start_line(original.content)
    
    current_pos = 0
    for segment in segments:
        # Find segment in body
        segment_start = body.find(segment, current_pos)
        if segment_start == -1:
            # Fallback: use current position
            segment_start = current_pos
        
        # Count lines from body start to segment start
        lines_before = body[:segment_start].count('\n')
        lines_in_segment = segment.count('\n')
        
        # Calculate absolute line numbers
        start_line = original.start_line + body_start_line + lines_before
        end_line = start_line + lines_in_segment
        
        result.append(SegmentWithPosition(
            content=segment,
            start_line_offset=lines_before,
            end_line_offset=lines_before + lines_in_segment,
            original_text=segment
        ))
        
        current_pos = segment_start + len(segment)
    
    return result
```

#### New Method: `_create_chunk_with_lines()`

```python
def _create_chunk_with_lines(
    self,
    original: Chunk,
    header_stack: str,
    segments: list[SegmentWithPosition],
    index: int,
    allow_oversize: bool = False,
    oversize_reason: str = "",
) -> Chunk:
    """
    Create chunk with accurate line numbers.
    
    Line number calculation:
    - start_line: First segment's start_line
    - end_line: Last segment's end_line
    - Accounts for header_stack repetition in continuation chunks
    """
    if not segments:
        return original
    
    # Calculate content line range
    content_start = min(seg.start_line_offset for seg in segments)
    content_end = max(seg.end_line_offset for seg in segments)
    
    # Adjust for header_stack in continuation chunks
    if header_stack and index > 0:
        # Continuation chunk: header_stack is repeated
        header_lines = header_stack.count('\n') + 1
        start_line = original.start_line + content_start
        end_line = original.start_line + content_end
    else:
        # First chunk: header_stack is original
        start_line = original.start_line + content_start
        end_line = original.start_line + content_end
    
    # Build content
    body = "\n\n".join(seg.content for seg in segments)
    if header_stack and index > 0:
        content = f"{header_stack}\n\n{body}"
    elif header_stack:
        content = f"{header_stack}\n\n{body}"
    else:
        content = body
    
    # Copy and update metadata
    metadata = original.metadata.copy()
    metadata["continued_from_header"] = index > 0 and bool(header_stack)
    metadata["split_index"] = index
    metadata["original_section_size"] = len(original.content)
    
    if allow_oversize:
        metadata["allow_oversize"] = True
        metadata["oversize_reason"] = oversize_reason
    
    return Chunk(
        content=content,
        start_line=start_line,
        end_line=end_line,
        metadata=metadata,
    )
```

### 3. Line Number Semantics

#### Decision: Content-Only Line Numbers

Line numbers reflect the **content field only**, not including overlap:

- `start_line`: First line of chunk.content in original document
- `end_line`: Last line of chunk.content in original document
- Overlap (previous_content/next_content) is separate and not counted

#### Rationale

1. **User intuition:** Users expect line numbers to point to visible content
2. **Consistency:** Same semantics for split and non-split chunks
3. **Simplicity:** Easier to implement and test

### 4. Edge Cases Handling

#### Case 1: Header-Only Chunks

```python
# Original: "## Section\n\n"
# After split: Still "## Section\n\n"
# Line numbers: Unchanged (no body to split)
```

#### Case 2: Single Segment

```python
# If splitting produces only one segment:
# - Return original chunk (no split needed)
# - Line numbers unchanged
```

#### Case 3: Empty Segments

```python
# Filter out empty segments before line calculation
segments = [seg for seg in segments if seg.content.strip()]
```

#### Case 4: Segment Not Found in Body

```python
# Fallback to sequential positioning
# Log warning for debugging
```

## Implementation Plan

### Phase 1: Core Infrastructure (1-2 days)

1. Create `SegmentWithPosition` dataclass
2. Implement `_find_segments_with_positions()`
3. Implement `_calculate_segment_positions()`
4. Unit tests for position calculation

### Phase 2: Integration (1 day)

1. Update `_split_chunk()` to use new methods
2. Implement `_create_chunk_with_lines()`
3. Integration tests with real documents

### Phase 3: Edge Cases & Polish (1 day)

1. Handle edge cases (header-only, single segment, etc.)
2. Performance optimization
3. Comprehensive test coverage

### Phase 4: Validation (0.5 day)

1. Run full test suite
2. Performance benchmarks
3. Documentation updates

## Testing Strategy

### Unit Tests

```python
def test_segment_position_calculation():
    """Test that segments get correct line positions."""
    
def test_split_chunk_line_numbers_different():
    """Test that split chunks have different line numbers."""
    
def test_split_chunk_line_numbers_ordered():
    """Test that split chunks are ordered by line numbers."""
    
def test_non_split_chunks_unchanged():
    """Regression test: non-split chunks keep same line numbers."""
```

### Integration Tests

```python
def test_end_to_end_line_accuracy():
    """Test line numbers on real document with splits."""
    
def test_split_chunks_cover_original_range():
    """Test that split chunks cover original line range."""
```

### Property-Based Tests

```python
@given(markdown_document())
def test_line_numbers_monotonic(doc):
    """Property: line numbers always increase."""
    
@given(markdown_document())  
def test_no_line_gaps(doc):
    """Property: no gaps in line coverage."""
```

## Performance Considerations

### Optimization Strategies

1. **Lazy calculation:** Only calculate positions when splitting occurs
2. **Caching:** Cache segment positions for repeated operations
3. **Efficient search:** Use optimized string search for segment positioning

### Performance Targets

- **Overhead:** < 10% for documents with splits
- **Memory:** No significant memory increase
- **Scalability:** Linear complexity O(n) with document size

## Backward Compatibility

### API Compatibility

- No changes to public API
- All existing method signatures preserved
- Chunk structure unchanged (only line numbers updated)

### Behavioral Compatibility

- Non-split chunks: Identical behavior
- Split chunks: Only line numbers change, content unchanged
- Metadata: Only line number fields affected

## Risk Mitigation

### Risk 1: Complex Line Mapping

**Mitigation:** Start with simple cases, add complexity incrementally

### Risk 2: Performance Impact

**Mitigation:** Benchmark at each phase, optimize hot paths

### Risk 3: Edge Case Bugs

**Mitigation:** Comprehensive property-based testing

## Success Metrics

1. **Correctness:** All split chunks have accurate line numbers
2. **Performance:** < 10% overhead on splitting operations
3. **Coverage:** 100% test coverage for new line calculation logic
4. **Regression:** All existing tests pass without modification