"""
Property tests for renderer functions (Task 8.7-8.9).

Tests:
- render_with_prev_overlap format
- render_json round-trip
- render_inline_metadata sorted keys
"""

import json

from hypothesis import given
from hypothesis import strategies as st

from chunkana import chunk_markdown
from chunkana.renderers import (
    render_dify_style,
    render_inline_metadata,
    render_json,
    render_with_embedded_overlap,
    render_with_prev_overlap,
)

# =============================================================================
# Strategies
# =============================================================================

simple_markdown = st.sampled_from(
    [
        "# Hello\n\nWorld",
        "## Section\n\nContent here.\n\n## Another\n\nMore content.",
        "# Doc\n\n```python\ncode\n```\n\nText after.",
        "Plain text without headers.",
        "# H1\n\n## H2\n\n### H3\n\nDeep nesting.",
        "# Title\n\nFirst paragraph.\n\nSecond paragraph with more text to ensure overlap.",
    ]
)


# =============================================================================
# Task 8.7: render_with_prev_overlap Format
# =============================================================================


class TestRenderWithPrevOverlapFormat:
    """Property 9: render_with_prev_overlap produces correct format."""

    @given(text=simple_markdown)
    def test_format_prev_content_newline_content(self, text: str):
        """
        For any chunk with previous_content, output is:
        {previous_content}\n{content} or just {content} if no previous.

        **Validates: Requirements 3.3**
        """
        chunks = chunk_markdown(text)
        outputs = render_with_prev_overlap(chunks)

        assert len(outputs) == len(chunks)

        for i, (chunk, output) in enumerate(zip(chunks, outputs, strict=False)):
            prev = chunk.metadata.get("previous_content", "")

            if prev:
                # Should be prev + newline + content
                expected = prev + "\n" + chunk.content
                assert output == expected, f"Chunk {i}: expected prev+newline+content format"
            else:
                # Should be just content
                assert output == chunk.content, f"Chunk {i}: expected just content when no previous"

    @given(text=simple_markdown)
    def test_first_chunk_no_previous(self, text: str):
        """First chunk should not have previous_content prefix."""
        chunks = chunk_markdown(text)
        if not chunks:
            return

        outputs = render_with_prev_overlap(chunks)
        first_output = outputs[0]
        first_chunk = chunks[0]

        # First chunk typically has no previous_content
        prev = first_chunk.metadata.get("previous_content", "")
        if not prev:
            assert first_output == first_chunk.content

    @given(text=simple_markdown)
    def test_does_not_include_next_content(self, text: str):
        """render_with_prev_overlap should NOT include next_content."""
        chunks = chunk_markdown(text)
        outputs = render_with_prev_overlap(chunks)

        for _i, (chunk, output) in enumerate(zip(chunks, outputs, strict=False)):
            next_content = chunk.metadata.get("next_content", "")
            if next_content and next_content not in chunk.content:
                # next_content should not appear in output
                # (unless it's part of the actual content)
                prev = chunk.metadata.get("previous_content", "")
                expected_parts = [prev, chunk.content] if prev else [chunk.content]
                expected = "\n".join(p for p in expected_parts if p)
                assert output == expected


# =============================================================================
# Task 8.8: render_json Round-Trip
# =============================================================================


class TestRenderJsonRoundTrip:
    """Property 10: render_json produces valid JSON that can be parsed back."""

    @given(text=simple_markdown)
    def test_json_is_valid(self, text: str):
        """
        For any chunks, render_json produces valid JSON-serializable dicts.

        **Validates: Requirements 3.4**
        """
        chunks = chunk_markdown(text)
        json_output = render_json(chunks)

        # Should be a list of dicts
        assert isinstance(json_output, list)
        for item in json_output:
            assert isinstance(item, dict)

        # Should be JSON-serializable
        json_str = json.dumps(json_output, ensure_ascii=False)
        assert json_str  # Non-empty

        # Should parse back
        parsed = json.loads(json_str)
        assert len(parsed) == len(json_output)

    @given(text=simple_markdown)
    def test_json_contains_required_fields(self, text: str):
        """render_json output contains required chunk fields."""
        chunks = chunk_markdown(text)
        json_output = render_json(chunks)

        for i, item in enumerate(json_output):
            assert "content" in item, f"Chunk {i} missing 'content'"
            assert "start_line" in item, f"Chunk {i} missing 'start_line'"
            assert "end_line" in item, f"Chunk {i} missing 'end_line'"
            assert "metadata" in item, f"Chunk {i} missing 'metadata'"

    @given(text=simple_markdown)
    def test_json_roundtrip_preserves_content(self, text: str):
        """JSON serialization preserves chunk content."""
        chunks = chunk_markdown(text)
        json_output = render_json(chunks)

        # Serialize and deserialize
        json_str = json.dumps(json_output, ensure_ascii=False)
        parsed = json.loads(json_str)

        for i, (original, restored) in enumerate(zip(json_output, parsed, strict=False)):
            assert original["content"] == restored["content"], (
                f"Chunk {i}: content not preserved through JSON"
            )
            assert original["start_line"] == restored["start_line"]
            assert original["end_line"] == restored["end_line"]


# =============================================================================
# Task 8.9: render_inline_metadata Sorted Keys
# =============================================================================


class TestRenderInlineMetadataSortedKeys:
    """Property 11: render_inline_metadata uses sorted keys for determinism."""

    @given(text=simple_markdown)
    def test_metadata_keys_are_sorted(self, text: str):
        """
        For any chunks, render_inline_metadata produces JSON with sorted keys.

        **Validates: Requirements 3.5**
        """
        chunks = chunk_markdown(text)
        outputs = render_inline_metadata(chunks)

        for i, output in enumerate(outputs):
            # Extract JSON from <metadata> block
            assert "<metadata>" in output, f"Chunk {i}: missing <metadata> tag"
            assert "</metadata>" in output, f"Chunk {i}: missing </metadata> tag"

            start = output.index("<metadata>") + len("<metadata>\n")
            end = output.index("</metadata>")
            json_str = output[start:end].strip()

            # Parse JSON
            metadata = json.loads(json_str)

            # Verify keys are sorted by checking JSON string
            # Re-serialize with sort_keys=True and compare
            sorted_json = json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True)
            assert json_str == sorted_json, f"Chunk {i}: metadata keys not sorted"

    @given(text=simple_markdown)
    def test_deterministic_output(self, text: str):
        """Multiple calls produce identical output (deterministic)."""
        chunks = chunk_markdown(text)

        output1 = render_inline_metadata(chunks)
        output2 = render_inline_metadata(chunks)

        assert output1 == output2, "render_inline_metadata not deterministic"

    @given(text=simple_markdown)
    def test_format_metadata_then_content(self, text: str):
        """Output format is <metadata>...</metadata> followed by content."""
        chunks = chunk_markdown(text)
        outputs = render_inline_metadata(chunks)

        for i, (chunk, output) in enumerate(zip(chunks, outputs, strict=False)):
            # Should end with chunk content
            assert output.endswith(chunk.content), f"Chunk {i}: output should end with content"

            # Should start with <metadata>
            assert output.startswith("<metadata>"), (
                f"Chunk {i}: output should start with <metadata>"
            )


# =============================================================================
# Additional Renderer Tests
# =============================================================================


class TestRenderDifyStyleFormat:
    """Tests for render_dify_style format."""

    @given(text=simple_markdown)
    def test_contains_metadata_block(self, text: str):
        """render_dify_style output contains <metadata> block."""
        chunks = chunk_markdown(text)
        outputs = render_dify_style(chunks)

        for i, output in enumerate(outputs):
            assert "<metadata>" in output, f"Chunk {i}: missing <metadata>"
            assert "</metadata>" in output, f"Chunk {i}: missing </metadata>"

    @given(text=simple_markdown)
    def test_metadata_contains_line_numbers(self, text: str):
        """render_dify_style metadata includes start_line and end_line."""
        chunks = chunk_markdown(text)
        outputs = render_dify_style(chunks)

        for i, output in enumerate(outputs):
            start = output.index("<metadata>") + len("<metadata>\n")
            end = output.index("</metadata>")
            json_str = output[start:end].strip()
            metadata = json.loads(json_str)

            assert "start_line" in metadata, f"Chunk {i}: missing start_line"
            assert "end_line" in metadata, f"Chunk {i}: missing end_line"


class TestRenderWithEmbeddedOverlapFormat:
    """Tests for render_with_embedded_overlap format."""

    @given(text=simple_markdown)
    def test_includes_bidirectional_overlap(self, text: str):
        """render_with_embedded_overlap includes both prev and next content."""
        chunks = chunk_markdown(text)
        outputs = render_with_embedded_overlap(chunks)

        for i, (chunk, output) in enumerate(zip(chunks, outputs, strict=False)):
            prev = chunk.metadata.get("previous_content", "")
            next_ = chunk.metadata.get("next_content", "")

            # Build expected output
            parts = []
            if prev:
                parts.append(prev)
            parts.append(chunk.content)
            if next_:
                parts.append(next_)
            expected = "\n".join(parts)

            assert output == expected, f"Chunk {i}: bidirectional overlap mismatch"
