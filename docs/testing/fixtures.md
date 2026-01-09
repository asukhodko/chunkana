# Test Fixtures Documentation

This document describes the test fixtures used for baseline testing and compatibility verification.

## Fixture Location

Test fixtures are located in `tests/baseline/fixtures/`:

## Fixture Descriptions

| Fixture | Description | Purpose |
|---------|-------------|---------|
| `simple_text.md` | Basic text without special structures | Test basic chunking behavior |
| `nested_fences.md` | Nested code fences (``` inside ~~~~) | Test complex code block handling |
| `large_tables.md` | Multiple tables, some exceeding chunk size | Test table chunking and overflow |
| `list_heavy.md` | Nested lists, mixed ordered/unordered | Test list-aware chunking strategy |
| `code_heavy.md` | Code-heavy document with multiple languages | Test code-aware chunking strategy |
| `code_context.md` | Code blocks with surrounding explanations | Test code context binding |
| `headers_deep.md` | Deep header hierarchy (h1-h6) | Test hierarchical structure handling |
| `mixed_content.md` | Combination of all element types | Test strategy selection and mixed content |
| `structural.md` | Clear hierarchical structure | Test structural chunking strategy |
| `latex_formulas.md` | LaTeX formulas (inline and display) | Test LaTeX preservation |
| `adaptive_sizing.md` | Varying content density | Test adaptive sizing features |
| `table_grouping.md` | Related tables grouping scenarios | Test table grouping functionality |

## Golden Output Schemas

### Canonical Output Schema

Located in `tests/baseline/golden_canonical/`

JSONL files containing canonical chunks:
```json
{
  "chunk_index": 0,
  "content": "# Introduction\n\nThis is the introduction...",
  "start_line": 1,
  "end_line": 10,
  "metadata": {
    "chunk_id": "abc12345",
    "strategy": "structural",
    "header_path": "/Introduction",
    "content_type": "section",
    "previous_content": null,
    "next_content": "This is the next section..."
  }
}
```

### View-Level Output Schema

Located in `tests/baseline/golden_dify_style/` and `tests/baseline/golden_no_metadata/`

JSONL files containing rendered output:
```json
{
  "chunk_index": 0,
  "text": "<metadata>\n{\"chunk_index\": 0, \"strategy\": \"structural\"}\n</metadata>\n\n# Introduction\n\nThis is the introduction..."
}
```

## Baseline Parameters

Default ChunkConfig values used for baseline generation:

```python
baseline_config = ChunkerConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
    preserve_atomic_blocks=True,
    extract_preamble=True,
    enable_code_context_binding=True,
    code_threshold=0.3,
    structure_threshold=3,
    list_ratio_threshold=0.4,
    list_count_threshold=5,
    max_context_chars_before=500,
    max_context_chars_after=300,
    related_block_max_gap=5,
    bind_output_blocks=True,
    preserve_before_after_pairs=True,
)
```

## Renderer Mapping

Based on output format analysis:

| Output Format | Renderer Function | Description |
|---------------|-------------------|-------------|
| `include_metadata=True` | `render_dify_style()` | `<metadata>` block + content |
| `include_metadata=False` | `render_with_embedded_overlap()` | prev + content + next (bidirectional) |

**Note**: The `include_metadata=False` format uses bidirectional overlap embedding (prev + content + next).

## Using Fixtures in Tests

### Loading Fixtures

```python
import json
from pathlib import Path

def load_fixture(fixture_name: str) -> str:
    """Load a test fixture."""
    fixture_path = Path("tests/baseline/fixtures") / f"{fixture_name}.md"
    return fixture_path.read_text(encoding='utf-8')

def load_golden_canonical(fixture_name: str) -> list[dict]:
    """Load golden canonical output."""
    golden_path = Path("tests/baseline/golden_canonical") / f"{fixture_name}.jsonl"
    chunks = []
    with open(golden_path, 'r', encoding='utf-8') as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks
```

### Fixture-Based Testing

```python
import pytest
from chunkana import chunk_markdown, ChunkerConfig

@pytest.mark.parametrize("fixture_name", [
    "simple_text",
    "nested_fences", 
    "large_tables",
    "list_heavy",
    "code_heavy",
])
def test_fixture_compatibility(fixture_name: str):
    """Test compatibility against fixture."""
    # Load fixture and expected output
    text = load_fixture(fixture_name)
    expected = load_golden_canonical(fixture_name)
    
    # Run chunking
    config = ChunkerConfig(max_chunk_size=4096, overlap_size=200)
    chunks = chunk_markdown(text, config)
    
    # Verify compatibility
    assert len(chunks) == len(expected)
    for chunk, expected_chunk in zip(chunks, expected):
        assert chunk.content == expected_chunk["content"]
        assert chunk.start_line == expected_chunk["start_line"]
        assert chunk.end_line == expected_chunk["end_line"]
```

## Creating New Fixtures

### Fixture Guidelines

1. **Representative Content**: Include content that exercises specific chunking behaviors
2. **Reasonable Size**: Keep fixtures manageable (< 10KB typically)
3. **Clear Purpose**: Each fixture should test specific functionality
4. **Edge Cases**: Include edge cases that might break chunking logic

### Fixture Template

```markdown
# Fixture Name: {purpose}

Brief description of what this fixture tests.

## Section 1

Content that exercises the specific behavior...

### Subsection

More content...

## Section 2

Additional content to create multiple chunks...
```

### Adding New Fixtures

1. Create the fixture file in `tests/baseline/fixtures/`
2. Generate golden outputs using the baseline generation script
3. Add the fixture to relevant test parametrizations
4. Document the fixture purpose in this file

## Regenerating Golden Outputs

To regenerate golden outputs after changes:

```bash
# Generate all golden outputs
python scripts/generate_baseline.py

# Generate for specific fixture
python scripts/generate_baseline.py --fixture simple_text
```

**Warning**: Only regenerate golden outputs when you're confident the new behavior is correct, as this will update the compatibility baseline.

## Fixture Maintenance

### Regular Maintenance Tasks

1. **Review fixture coverage**: Ensure all chunking strategies are covered
2. **Update fixture content**: Keep content realistic and representative
3. **Validate golden outputs**: Periodically verify golden outputs are still correct
4. **Add edge cases**: Add new fixtures for discovered edge cases

### Fixture Quality Checklist

- [ ] Fixture has clear, documented purpose
- [ ] Content is representative of real-world usage
- [ ] Exercises specific chunking behavior
- [ ] Reasonable size (not too large or too small)
- [ ] Golden outputs are verified correct
- [ ] Included in relevant test parametrizations