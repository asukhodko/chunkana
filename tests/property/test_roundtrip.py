"""
Property-based tests for round-trip serialization.

Feature: chunkana-library
Properties 1, 2, 3: Round-trip serialization
"""

import json
from hypothesis import given, settings, strategies as st

from chunkana import Chunk, ChunkerConfig


# Strategies for generating valid test data
@st.composite
def valid_chunk_content(draw):
    """Generate valid non-empty chunk content."""
    # Must have at least one non-whitespace character
    content = draw(st.text(min_size=1, max_size=1000))
    # Ensure not all whitespace
    if not content.strip():
        content = "x" + content
    return content


@st.composite
def valid_metadata(draw):
    """Generate valid metadata dictionary."""
    return draw(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=20).filter(lambda x: x.isidentifier()),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000000, max_value=1000000),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.none(),
            ),
            max_size=10,
        )
    )


@st.composite
def valid_chunk(draw):
    """Generate a valid Chunk object."""
    content = draw(valid_chunk_content())
    start_line = draw(st.integers(min_value=1, max_value=10000))
    end_line = draw(st.integers(min_value=start_line, max_value=start_line + 1000))
    metadata = draw(valid_metadata())
    return Chunk(
        content=content,
        start_line=start_line,
        end_line=end_line,
        metadata=metadata,
    )


@st.composite
def valid_chunker_config(draw):
    """Generate a valid ChunkerConfig object."""
    max_chunk_size = draw(st.integers(min_value=100, max_value=100000))
    min_chunk_size = draw(st.integers(min_value=10, max_value=max_chunk_size // 2))
    overlap_size = draw(st.integers(min_value=0, max_value=max_chunk_size - 1))

    return ChunkerConfig(
        max_chunk_size=max_chunk_size,
        min_chunk_size=min_chunk_size,
        overlap_size=overlap_size,
        preserve_atomic_blocks=draw(st.booleans()),
        extract_preamble=draw(st.booleans()),
        code_threshold=draw(st.floats(min_value=0.0, max_value=1.0)),
        structure_threshold=draw(st.integers(min_value=1, max_value=100)),
        list_ratio_threshold=draw(st.floats(min_value=0.0, max_value=1.0)),
        list_count_threshold=draw(st.integers(min_value=1, max_value=100)),
        strategy_override=draw(
            st.sampled_from([None, "code_aware", "list_aware", "structural", "fallback"])
        ),
        enable_code_context_binding=draw(st.booleans()),
        max_context_chars_before=draw(st.integers(min_value=0, max_value=10000)),
        max_context_chars_after=draw(st.integers(min_value=0, max_value=10000)),
        related_block_max_gap=draw(st.integers(min_value=1, max_value=100)),
        bind_output_blocks=draw(st.booleans()),
        preserve_before_after_pairs=draw(st.booleans()),
    )


class TestChunkRoundTrip:
    """
    Property 1: Chunk Round-Trip (Dict)

    For any valid Chunk object, serializing to dict and deserializing back
    should produce an equivalent Chunk with identical content, line numbers,
    and metadata.

    Validates: Requirements 1.5, 1.7, 14.1
    """

    @given(chunk=valid_chunk())
    @settings(max_examples=100)
    def test_chunk_dict_roundtrip(self, chunk: Chunk):
        """
        Feature: chunkana-library, Property 1: Chunk Round-Trip (Dict)

        For any valid Chunk, to_dict() -> from_dict() produces equivalent Chunk.
        """
        # Serialize and deserialize
        serialized = chunk.to_dict()
        restored = Chunk.from_dict(serialized)

        # Verify equivalence
        assert restored.content == chunk.content
        assert restored.start_line == chunk.start_line
        assert restored.end_line == chunk.end_line
        assert restored.metadata == chunk.metadata


class TestChunkJsonRoundTrip:
    """
    Property 2: Chunk Round-Trip (JSON)

    For any valid Chunk object, serializing to JSON string and deserializing
    back should produce an equivalent Chunk.

    Validates: Requirements 1.6, 1.8, 14.2
    """

    @given(chunk=valid_chunk())
    @settings(max_examples=100)
    def test_chunk_json_roundtrip(self, chunk: Chunk):
        """
        Feature: chunkana-library, Property 2: Chunk Round-Trip (JSON)

        For any valid Chunk, to_json() -> from_json() produces equivalent Chunk.
        """
        # Serialize and deserialize
        json_str = chunk.to_json()
        restored = Chunk.from_json(json_str)

        # Verify equivalence
        assert restored.content == chunk.content
        assert restored.start_line == chunk.start_line
        assert restored.end_line == chunk.end_line
        assert restored.metadata == chunk.metadata

    @given(chunk=valid_chunk())
    @settings(max_examples=100)
    def test_chunk_json_is_valid_json(self, chunk: Chunk):
        """Verify to_json() produces valid JSON."""
        json_str = chunk.to_json()
        # Should not raise
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)


class TestChunkerConfigRoundTrip:
    """
    Property 3: ChunkerConfig Round-Trip

    For any valid ChunkerConfig object, serializing to dict and deserializing
    back should produce an equivalent config with identical parameters.

    Validates: Requirements 2.8, 14.3
    """

    @given(config=valid_chunker_config())
    @settings(max_examples=100)
    def test_config_dict_roundtrip(self, config: ChunkerConfig):
        """
        Feature: chunkana-library, Property 3: ChunkerConfig Round-Trip

        For any valid ChunkerConfig, to_dict() -> from_dict() produces
        equivalent config.
        """
        # Serialize and deserialize
        serialized = config.to_dict()
        restored = ChunkerConfig.from_dict(serialized)

        # Verify core parameters match
        assert restored.max_chunk_size == config.max_chunk_size
        assert restored.min_chunk_size == config.min_chunk_size
        assert restored.overlap_size == config.overlap_size
        assert restored.preserve_atomic_blocks == config.preserve_atomic_blocks
        assert restored.extract_preamble == config.extract_preamble
        assert restored.code_threshold == config.code_threshold
        assert restored.structure_threshold == config.structure_threshold
        assert restored.list_ratio_threshold == config.list_ratio_threshold
        assert restored.list_count_threshold == config.list_count_threshold
        assert restored.strategy_override == config.strategy_override
        assert restored.enable_code_context_binding == config.enable_code_context_binding
        assert restored.max_context_chars_before == config.max_context_chars_before
        assert restored.max_context_chars_after == config.max_context_chars_after
        assert restored.related_block_max_gap == config.related_block_max_gap
        assert restored.bind_output_blocks == config.bind_output_blocks
        assert restored.preserve_before_after_pairs == config.preserve_before_after_pairs
