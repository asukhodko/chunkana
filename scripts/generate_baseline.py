#!/usr/bin/env python3
"""
Generate baseline golden outputs from dify-markdown-chunker plugin.

This script generates:
1. Canonical goldens (JSONL) - list[Chunk] serialized
2. View-level goldens (JSONL) - rendered output as-is from plugin
3. plugin_config_keys.json - keys from ChunkConfig.to_dict()
4. plugin_tool_params.json - parameters from tool schema

Usage:
    python scripts/generate_baseline.py --plugin-path /path/to/dify-markdown-chunker

Requirements:
    - Plugin must be at pinned commit (see BASELINE.md)
    - Plugin dependencies must be installed
"""

import argparse
import json
import sys
from pathlib import Path


def get_plugin_commit(plugin_path: Path) -> str:
    """Get current git commit SHA of plugin."""
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=plugin_path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()[:12]


def load_plugin_modules(plugin_path: Path):
    """Add plugin to path and import modules."""
    sys.path.insert(0, str(plugin_path))

    from markdown_chunker_v2 import ChunkConfig, MarkdownChunker
    from markdown_chunker_v2.types import Chunk

    return MarkdownChunker, ChunkConfig, Chunk


def extract_config_keys(ChunkConfig) -> list[str]:
    """Extract keys from ChunkConfig.to_dict()."""
    config = ChunkConfig()
    return sorted(config.to_dict().keys())


def extract_tool_params(plugin_path: Path) -> list[dict]:
    """Extract parameters from tool schema YAML."""
    import yaml

    tool_yaml = plugin_path / "tools" / "markdown_chunk_tool.yaml"
    if not tool_yaml.exists():
        return []

    with open(tool_yaml) as f:
        schema = yaml.safe_load(f)

    params = []
    for param in schema.get("parameters", []):
        params.append(
            {
                "name": param.get("name"),
                "type": param.get("type"),
                "required": param.get("required", False),
                "default": param.get("default"),
                "description": param.get("human_description", {}).get("en_US", ""),
            }
        )

    return params


def chunk_to_dict(chunk) -> dict:
    """Convert Chunk to dict for JSONL serialization."""
    return {
        "content": chunk.content,
        "start_line": chunk.start_line,
        "end_line": chunk.end_line,
        "metadata": chunk.metadata,
    }


def render_dify_style(chunks: list) -> list[str]:
    """
    Render chunks in Dify-compatible format (include_metadata=True).

    This replicates plugin's output format exactly.
    """
    result = []
    for chunk in chunks:
        # Build metadata dict with start_line/end_line
        output_metadata = chunk.metadata.copy()
        output_metadata["start_line"] = chunk.start_line
        output_metadata["end_line"] = chunk.end_line

        # JSON formatting: match plugin exactly
        metadata_json = json.dumps(
            output_metadata,
            ensure_ascii=False,
            indent=2,
        )

        formatted = f"<metadata>\n{metadata_json}\n</metadata>\n{chunk.content}"
        result.append(formatted)

    return result


def render_with_embedded_overlap(chunks: list) -> list[str]:
    """
    Render chunks with embedded overlap (include_metadata=False).

    This replicates plugin's output format exactly.
    """
    result = []
    for chunk in chunks:
        parts = []

        prev = chunk.metadata.get("previous_content", "")
        next_ = chunk.metadata.get("next_content", "")

        if prev:
            parts.append(prev)
        parts.append(chunk.content)
        if next_:
            parts.append(next_)

        result.append("\n".join(parts))

    return result


def generate_goldens(
    plugin_path: Path,
    fixtures_dir: Path,
    output_dir: Path,
    MarkdownChunker,
    ChunkConfig,
):
    """Generate all golden outputs from fixtures."""

    canonical_dir = output_dir / "golden_canonical"
    dify_style_dir = output_dir / "golden_dify_style"
    no_metadata_dir = output_dir / "golden_no_metadata"

    canonical_dir.mkdir(parents=True, exist_ok=True)
    dify_style_dir.mkdir(parents=True, exist_ok=True)
    no_metadata_dir.mkdir(parents=True, exist_ok=True)

    chunker = MarkdownChunker(ChunkConfig())

    fixtures = list(fixtures_dir.glob("*.md"))
    print(f"Found {len(fixtures)} fixtures")

    for fixture in fixtures:
        name = fixture.stem
        print(f"  Processing: {name}")

        text = fixture.read_text(encoding="utf-8")
        chunks = chunker.chunk(text)

        # Canonical golden (JSONL)
        canonical_file = canonical_dir / f"{name}.jsonl"
        with open(canonical_file, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                record = {"chunk_index": i, **chunk_to_dict(chunk)}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Dify-style golden (JSONL) - as-is from plugin
        dify_style_file = dify_style_dir / f"{name}.jsonl"
        rendered_dify = render_dify_style(chunks)
        with open(dify_style_file, "w", encoding="utf-8") as f:
            for i, text in enumerate(rendered_dify):
                record = {"chunk_index": i, "text": text}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # No-metadata golden (JSONL) - as-is from plugin
        no_metadata_file = no_metadata_dir / f"{name}.jsonl"
        rendered_no_meta = render_with_embedded_overlap(chunks)
        with open(no_metadata_file, "w", encoding="utf-8") as f:
            for i, text in enumerate(rendered_no_meta):
                record = {"chunk_index": i, "text": text}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Generated goldens for {len(fixtures)} fixtures")


def main():
    parser = argparse.ArgumentParser(description="Generate baseline golden outputs from plugin")
    parser.add_argument(
        "--plugin-path",
        type=Path,
        required=True,
        help="Path to dify-markdown-chunker plugin",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=None,
        help="Path to fixtures directory (default: tests/baseline/fixtures)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Path to output directory (default: tests/baseline)",
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    fixtures_dir = args.fixtures_dir or project_root / "tests" / "baseline" / "fixtures"
    output_dir = args.output_dir or project_root / "tests" / "baseline"

    if not args.plugin_path.exists():
        print(f"Error: Plugin path does not exist: {args.plugin_path}")
        sys.exit(1)

    if not fixtures_dir.exists():
        print(f"Error: Fixtures directory does not exist: {fixtures_dir}")
        sys.exit(1)

    print(f"Plugin path: {args.plugin_path}")
    print(f"Fixtures dir: {fixtures_dir}")
    print(f"Output dir: {output_dir}")

    # Get plugin commit
    commit = get_plugin_commit(args.plugin_path)
    print(f"Plugin commit: {commit}")

    # Load plugin modules
    print("Loading plugin modules...")
    MarkdownChunker, ChunkConfig, Chunk = load_plugin_modules(args.plugin_path)

    # Extract config keys
    print("Extracting config keys...")
    config_keys = extract_config_keys(ChunkConfig)
    config_keys_file = output_dir / "plugin_config_keys.json"
    with open(config_keys_file, "w") as f:
        json.dump({"commit": commit, "keys": config_keys}, f, indent=2)
    print(f"  Saved {len(config_keys)} keys to {config_keys_file}")

    # Extract tool params
    print("Extracting tool params...")
    tool_params = extract_tool_params(args.plugin_path)
    tool_params_file = output_dir / "plugin_tool_params.json"
    with open(tool_params_file, "w") as f:
        json.dump({"commit": commit, "params": tool_params}, f, indent=2)
    print(f"  Saved {len(tool_params)} params to {tool_params_file}")

    # Generate goldens
    print("Generating golden outputs...")
    generate_goldens(
        args.plugin_path,
        fixtures_dir,
        output_dir,
        MarkdownChunker,
        ChunkConfig,
    )

    print("\nDone! Don't forget to update BASELINE.md with commit SHA.")


if __name__ == "__main__":
    main()
