"""
Output formatters for Chunkana chunks.

These are pure functions that format chunks for different output systems.
They do NOT modify Chunk objects - they only produce formatted strings/dicts.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types import Chunk


def render_json(chunks: list["Chunk"]) -> list[dict[str, object]]:
    """
    Convert chunks to list of dictionaries.

    Does not modify chunks - returns new dict objects.

    Args:
        chunks: List of Chunk objects

    Returns:
        List of dictionaries with chunk data
    """
    return [chunk.to_dict() for chunk in chunks]


def render_inline_metadata(chunks: list["Chunk"]) -> list[str]:
    """
    Render chunks with inline JSON metadata tags.

    Format:
        <metadata>
        {json metadata}
        </metadata>

        {content}

    Does not modify chunks.

    Args:
        chunks: List of Chunk objects

    Returns:
        List of formatted strings
    """
    result = []
    for chunk in chunks:
        metadata_json = json.dumps(chunk.metadata, ensure_ascii=False, indent=2, sort_keys=True)
        result.append(f"<metadata>\n{metadata_json}\n</metadata>\n\n{chunk.content}")
    return result


def render_dify_style(chunks: list["Chunk"]) -> list[str]:
    """
    Render chunks in Dify-compatible format with <metadata> block.

    Includes chunk.metadata + start_line + end_line in the metadata block.
    This matches v2 behavior with include_metadata=True.

    Format:
        <metadata>
        {json with metadata + start_line + end_line}
        </metadata>
        {content}

    Does not modify chunks.

    Args:
        chunks: List of Chunk objects

    Returns:
        List of formatted strings
    """
    result = []
    for chunk in chunks:
        output_metadata = chunk.metadata.copy()
        output_metadata["start_line"] = chunk.start_line
        output_metadata["end_line"] = chunk.end_line
        metadata_json = json.dumps(output_metadata, ensure_ascii=False, indent=2)
        result.append(f"<metadata>\n{metadata_json}\n</metadata>\n{chunk.content}")
    return result


def render_with_embedded_overlap(chunks: list["Chunk"]) -> list[str]:
    """
    Render chunks with bidirectional overlap embedded into content string.

    This is a VIEW operation - it does NOT modify chunk.content.
    Produces: previous_content + "\\n" + content + "\\n" + next_content

    Use case: "rich context" mode. Whether this matches v2 include_metadata=False
    is determined by BASELINE.md and renderer golden outputs.

    Does not modify chunks.

    Args:
        chunks: List of Chunk objects

    Returns:
        List of strings with embedded overlap
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


def render_with_prev_overlap(chunks: list["Chunk"]) -> list[str]:
    """
    Render chunks with only previous overlap embedded (sliding window).

    This is a VIEW operation - it does NOT modify chunk.content.
    Produces: previous_content + "\\n" + content

    Use case: "sliding window" mode. Whether this matches v2 include_metadata=False
    is determined by BASELINE.md and renderer golden outputs.

    Does not modify chunks.

    Args:
        chunks: List of Chunk objects

    Returns:
        List of strings with previous overlap only
    """
    result = []
    for chunk in chunks:
        parts = []
        prev = chunk.metadata.get("previous_content", "")
        if prev:
            parts.append(prev)
        parts.append(chunk.content)
        result.append("\n".join(parts))
    return result
