#!/usr/bin/env python3
"""Generate baseline golden outputs from dify-markdown-chunker v2.

This script runs the v2 chunker on fixture files and saves the outputs
as golden files for baseline compatibility testing.

Usage:
    python scripts/generate_baseline.py

Requirements:
    - dify-markdown-chunker must be installed or accessible
    - Run from chunkana root directory
"""

import json
import sys
from pathlib import Path

# Add dify-markdown-chunker to path for imports
PLUGIN_PATH = Path(__file__).parent.parent.parent / "dify-markdown-chunker"
sys.path.insert(0, str(PLUGIN_PATH))

# Import from markdown_chunker_v2 directly (avoids dify_plugin dependency)
from markdown_chunker_v2.chunker import MarkdownChunker
from markdown_chunker_v2.config import ChunkConfig

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "baseline" / "fixtures"
GOLDEN_DIR = PROJECT_ROOT / "tests" / "baseline" / "golden"
GOLDEN_DIFY_STYLE_DIR = PROJECT_ROOT / "tests" / "baseline" / "golden_dify_style"
GOLDEN_NO_METADATA_DIR = PROJECT_ROOT / "tests" / "baseline" / "golden_no_metadata"

# Default config matching v2 defaults
DEFAULT_CONFIG = ChunkConfig(
    max_chunk_size=4096,
    min_chunk_size=512,
    overlap_size=200,
)


def extract_chunks(result):
    """Extract chunks from v2 result, handling different return types.
    
    v2 may return:
    - list[Chunk] directly
    - object with .chunks attribute
    - dict with 'chunks' key
    """
    if isinstance(result, list):
        return result
    if hasattr(result, 'chunks'):
        return result.chunks
    if isinstance(result, dict) and 'chunks' in result:
        return result['chunks']
    raise ValueError(f"Unknown result type: {type(result)}")


def chunk_to_dict(chunk) -> dict:
    """Convert chunk to dictionary for JSON serialization."""
    if hasattr(chunk, 'to_dict'):
        return chunk.to_dict()
    return {
        "content": chunk.content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "metadata": chunk.metadata or {},
    }


def format_dify_style(chunk) -> str:
    """Format chunk as v2 include_metadata=True output."""
    metadata = (chunk.metadata or {}).copy()
    metadata['start_line'] = chunk.start_line
    metadata['end_line'] = chunk.end_line
    metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
    return f"<metadata>\n{metadata_json}\n</metadata>\n{chunk.content}"


def format_no_metadata(chunk) -> str:
    """Format chunk as v2 include_metadata=False output (bidirectional overlap)."""
    metadata = chunk.metadata or {}
    previous_content = metadata.get("previous_content", "")
    next_content = metadata.get("next_content", "")
    
    parts = []
    if previous_content:
        parts.append(previous_content)
    parts.append(chunk.content)
    if next_content:
        parts.append(next_content)
    
    return "\n".join(parts)


def generate_golden_for_fixture(fixture_path: Path, config: ChunkConfig):
    """Generate all golden outputs for a single fixture."""
    print(f"Processing: {fixture_path.name}")
    
    markdown = fixture_path.read_text(encoding="utf-8")
    chunker = MarkdownChunker(config)
    result = chunker.chunk(markdown)
    chunks = extract_chunks(result)
    
    # Core golden output (canonical chunks)
    golden_data = {
        "fixture": fixture_path.name,
        "config": {
            "max_chunk_size": config.max_chunk_size,
            "min_chunk_size": config.min_chunk_size,
            "overlap_size": config.overlap_size,
        },
        "chunks": [chunk_to_dict(c) for c in chunks],
    }
    
    golden_path = GOLDEN_DIR / f"{fixture_path.stem}.json"
    golden_path.write_text(
        json.dumps(golden_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"  -> {golden_path.name}")
    
    # View-level: dify_style (include_metadata=True)
    dify_style_path = GOLDEN_DIFY_STYLE_DIR / f"{fixture_path.stem}.jsonl"
    with dify_style_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            line = json.dumps({"output": format_dify_style(chunk)}, ensure_ascii=False)
            f.write(line + "\n")
    print(f"  -> golden_dify_style/{dify_style_path.name}")
    
    # View-level: no_metadata (include_metadata=False, bidirectional)
    no_metadata_path = GOLDEN_NO_METADATA_DIR / f"{fixture_path.stem}.jsonl"
    with no_metadata_path.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            line = json.dumps({"output": format_no_metadata(chunk)}, ensure_ascii=False)
            f.write(line + "\n")
    print(f"  -> golden_no_metadata/{no_metadata_path.name}")


def main():
    """Generate baseline golden outputs for all fixtures."""
    # Ensure directories exist
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    GOLDEN_DIFY_STYLE_DIR.mkdir(parents=True, exist_ok=True)
    GOLDEN_NO_METADATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check fixtures exist
    if not FIXTURES_DIR.exists():
        print(f"Error: Fixtures directory not found: {FIXTURES_DIR}")
        print("Please create fixture files first.")
        sys.exit(1)
    
    fixtures = list(FIXTURES_DIR.glob("*.md"))
    if not fixtures:
        print(f"Warning: No .md fixtures found in {FIXTURES_DIR}")
        print("Creating sample fixtures...")
        create_sample_fixtures()
        fixtures = list(FIXTURES_DIR.glob("*.md"))
    
    print(f"Found {len(fixtures)} fixtures")
    print(f"Using config: max_chunk_size={DEFAULT_CONFIG.max_chunk_size}, "
          f"overlap_size={DEFAULT_CONFIG.overlap_size}")
    print()
    
    for fixture_path in sorted(fixtures):
        generate_golden_for_fixture(fixture_path, DEFAULT_CONFIG)
    
    print()
    print("Done! Golden outputs generated.")
    print(f"  Core: {GOLDEN_DIR}")
    print(f"  Dify style: {GOLDEN_DIFY_STYLE_DIR}")
    print(f"  No metadata: {GOLDEN_NO_METADATA_DIR}")


def create_sample_fixtures():
    """Create sample fixture files for baseline testing."""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Simple text
    (FIXTURES_DIR / "simple_text.md").write_text("""# Simple Document

This is a simple document with basic text content.

## Section One

Some text in section one. This paragraph contains enough content
to demonstrate basic chunking behavior.

## Section Two

Another section with more text. The chunker should handle
this straightforward structure without issues.
""", encoding="utf-8")
    
    # Nested fences
    (FIXTURES_DIR / "nested_fences.md").write_text('''# Nested Code Fences

Here is an example with nested fences:

~~~~markdown
This is outer fence content.

```python
def inner_code():
    return "nested"
```

More outer content.
~~~~

And some text after.
''', encoding="utf-8")
    
    # Code context
    (FIXTURES_DIR / "code_context.md").write_text("""# Code with Context

Here's an explanation of the following code:

```python
def hello_world():
    print("Hello, World!")
```

The function above prints a greeting message.

## Another Example

Before we show the code, let's explain what it does.
This function calculates the factorial of a number.

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

After running this, you get the factorial result.
""", encoding="utf-8")
    
    print(f"Created sample fixtures in {FIXTURES_DIR}")


if __name__ == "__main__":
    main()
