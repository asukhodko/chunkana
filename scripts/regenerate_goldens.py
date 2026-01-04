#!/usr/bin/env python3
"""
Regenerate golden outputs using Chunkana library.

This script regenerates golden files based on current Chunkana behavior.
Use this when Chunkana behavior is considered correct and goldens need updating.

Usage:
    python scripts/regenerate_goldens.py
"""

import json

# Add src to path for local development
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chunkana import chunk_markdown
from chunkana.renderers import render_dify_style, render_with_embedded_overlap


def chunk_to_dict(chunk) -> dict:
    """Convert Chunk to dict for JSONL serialization."""
    return {
        "content": chunk.content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "metadata": chunk.metadata,
    }


def regenerate_goldens(fixtures_dir: Path, output_dir: Path):
    """Regenerate all golden outputs from fixtures using Chunkana."""

    canonical_dir = output_dir / "golden_canonical"
    dify_style_dir = output_dir / "golden_dify_style"
    no_metadata_dir = output_dir / "golden_no_metadata"

    canonical_dir.mkdir(parents=True, exist_ok=True)
    dify_style_dir.mkdir(parents=True, exist_ok=True)
    no_metadata_dir.mkdir(parents=True, exist_ok=True)

    fixtures = list(fixtures_dir.glob("*.md"))
    print(f"Found {len(fixtures)} fixtures")

    for fixture in fixtures:
        name = fixture.stem
        print(f"  Processing: {name}")

        text = fixture.read_text(encoding="utf-8")
        chunks = chunk_markdown(text)

        # Canonical golden (JSONL)
        canonical_file = canonical_dir / f"{name}.jsonl"
        with open(canonical_file, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                record = {"chunk_index": i, **chunk_to_dict(chunk)}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Dify-style golden (JSONL)
        dify_style_file = dify_style_dir / f"{name}.jsonl"
        rendered_dify = render_dify_style(chunks)
        with open(dify_style_file, "w", encoding="utf-8") as f:
            for i, rendered_text in enumerate(rendered_dify):
                record = {"chunk_index": i, "text": rendered_text}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # No-metadata golden (JSONL)
        no_metadata_file = no_metadata_dir / f"{name}.jsonl"
        rendered_no_meta = render_with_embedded_overlap(chunks)
        with open(no_metadata_file, "w", encoding="utf-8") as f:
            for i, rendered_text in enumerate(rendered_no_meta):
                record = {"chunk_index": i, "text": rendered_text}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Regenerated goldens for {len(fixtures)} fixtures")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    fixtures_dir = project_root / "tests" / "baseline" / "fixtures"
    output_dir = project_root / "tests" / "baseline"

    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory does not exist: {fixtures_dir}")
        sys.exit(1)

    print(f"Fixtures dir: {fixtures_dir}")
    print(f"Output dir: {output_dir}")
    print()

    regenerate_goldens(fixtures_dir, output_dir)

    print("\nDone! Golden files regenerated based on Chunkana behavior.")


if __name__ == "__main__":
    main()
