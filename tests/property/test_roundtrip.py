"""
Property-based tests for round-trip serialization.

Feature: chunkana-library
Properties 1, 2, 3: Round-trip serialization
"""

import json

from hypothesis import given, settings
from hypothesis import strategies as st

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
def valid_adaptive_config(draw):
    """Generate a valid AdaptiveSizeConfig object or None."""
    if draw(st.booleans()):
        return None

    from chunkana.adaptive_sizing import AdaptiveSizeConfig

    # Generate weights that sum to 1.0
    code_weight = draw(st.floats(min_value=0.1, max_value=0.4))
    table_weight = draw(st.floats(min_value=0.1, max_value=0.4))
    list_weight = draw(st.floats(min_value=0.1, max_value=0.4))
    # Calculate sentence_length_weight to make sum = 1.0
    sentence_length_weight = 1.0 - code_weight - table_weight - list_weight

    # Ensure non-negative
    if sentence_length_weight < 0:
        # Normalize all weights
        total = code_weight + table_weight + list_weight
        code_weight = code_weight / total * 0.9
        table_weight = table_weight / total * 0.9
        list_weight = list_weight / total * 0.9
        sentence_length_weight = 0.1

    return AdaptiveSizeConfig(
        base_size=draw(st.integers(min_value=500, max_value=5000)),
        min_scale=draw(st.floats(min_value=0.3, max_value=0.7)),
        max_scale=draw(st.floats(min_value=1.2, max_value=2.0)),
        code_weight=code_weight,
        table_weight=table_weight,
        list_weight=list_weight,
        sentence_length_weight=sentence_length_weight,
    )


@st.composite
def valid_table_grouping_config(draw):
    """Generate a valid TableGroupingConfig object or None."""
    if draw(st.booleans()):
        return None

    from chunkana.table_grouping import TableGroupingConfig

    return TableGroupingConfig(
        max_distance_lines=draw(st.integers(min_value=1, max_value=50)),
        max_grouped_tables=draw(st.integers(min_value=1, max_value=20)),
        max_group_size=draw(st.integers(min_value=100, max_value=20000)),
        require_same_section=draw(st.booleans()),
    )


@st.composite
def valid_chunker_config(draw):
    """Generate a valid ChunkerConfig object."""
    max_chunk_size = draw(st.integers(min_value=100, max_value=100000))
    min_chunk_size = draw(st.integers(min_value=10, max_value=max_chunk_size // 2))
    overlap_size = draw(st.integers(min_value=0, max_value=max_chunk_size - 1))

    # Generate optional nested configs
    adaptive_config = draw(valid_adaptive_config())
    table_grouping_config = draw(valid_table_grouping_config())

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
        # Chunkana extension fields
        overlap_cap_ratio=draw(st.floats(min_value=0.1, max_value=1.0)),
        use_adaptive_sizing=adaptive_config is not None,
        adaptive_config=adaptive_config,
        include_document_summary=draw(st.booleans()),
        strip_obsidian_block_ids=draw(st.booleans()),
        preserve_latex_blocks=draw(st.booleans()),
        latex_display_only=draw(st.booleans()),
        latex_max_context_chars=draw(st.integers(min_value=0, max_value=1000)),
        group_related_tables=table_grouping_config is not None,
        table_grouping_config=table_grouping_config,
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

        # Verify plugin parity parameters match
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

        # Verify Chunkana extension parameters match
        assert restored.overlap_cap_ratio == config.overlap_cap_ratio
        assert restored.use_adaptive_sizing == config.use_adaptive_sizing
        assert restored.include_document_summary == config.include_document_summary
        assert restored.strip_obsidian_block_ids == config.strip_obsidian_block_ids
        assert restored.preserve_latex_blocks == config.preserve_latex_blocks
        assert restored.latex_display_only == config.latex_display_only
        assert restored.latex_max_context_chars == config.latex_max_context_chars
        assert restored.group_related_tables == config.group_related_tables

        # Verify nested configs
        if config.adaptive_config is not None:
            assert restored.adaptive_config is not None
            assert restored.adaptive_config.base_size == config.adaptive_config.base_size
            assert restored.adaptive_config.min_scale == config.adaptive_config.min_scale
            assert restored.adaptive_config.max_scale == config.adaptive_config.max_scale
        else:
            assert restored.adaptive_config is None

        if config.table_grouping_config is not None:
            assert restored.table_grouping_config is not None
            assert (
                restored.table_grouping_config.max_distance_lines
                == config.table_grouping_config.max_distance_lines
            )
            assert (
                restored.table_grouping_config.max_grouped_tables
                == config.table_grouping_config.max_grouped_tables
            )
        else:
            assert restored.table_grouping_config is None

    @given(config=valid_chunker_config())
    @settings(max_examples=100)
    def test_config_unknown_fields_ignored(self, config: ChunkerConfig):
        """
        Property: Unknown fields in from_dict() are ignored for forward compatibility.
        """
        serialized = config.to_dict()
        # Add unknown fields
        serialized["unknown_future_field"] = "some_value"
        serialized["another_unknown"] = 12345

        # Should not raise, unknown fields ignored
        restored = ChunkerConfig.from_dict(serialized)

        # Core fields still match
        assert restored.max_chunk_size == config.max_chunk_size
        assert restored.overlap_size == config.overlap_size


class TestChunkerConfigValidation:
    """
    Property: Config Validation Errors

    Invalid configurations should raise ValueError with descriptive messages.

    Validates: Requirements 1.5
    """

    @given(st.integers(min_value=-1000, max_value=0))
    @settings(max_examples=50)
    def test_invalid_max_chunk_size_raises(self, invalid_size: int):
        """max_chunk_size must be positive."""
        import pytest

        with pytest.raises(ValueError, match="max_chunk_size must be positive"):
            ChunkerConfig(max_chunk_size=invalid_size)

    @given(st.integers(min_value=-1000, max_value=0))
    @settings(max_examples=50)
    def test_invalid_min_chunk_size_raises(self, invalid_size: int):
        """min_chunk_size must be positive."""
        import pytest

        with pytest.raises(ValueError, match="min_chunk_size must be positive"):
            ChunkerConfig(min_chunk_size=invalid_size)

    @given(st.integers(min_value=-1000, max_value=-1))
    @settings(max_examples=50)
    def test_invalid_overlap_size_raises(self, invalid_size: int):
        """overlap_size must be non-negative."""
        import pytest

        with pytest.raises(ValueError, match="overlap_size must be non-negative"):
            ChunkerConfig(overlap_size=invalid_size)

    @given(st.floats(min_value=-10.0, max_value=-0.01))
    @settings(max_examples=50)
    def test_invalid_code_threshold_negative_raises(self, invalid_threshold: float):
        """code_threshold must be between 0 and 1."""
        import pytest

        with pytest.raises(ValueError, match="code_threshold must be between 0 and 1"):
            ChunkerConfig(code_threshold=invalid_threshold)

    @given(st.floats(min_value=1.01, max_value=10.0))
    @settings(max_examples=50)
    def test_invalid_code_threshold_over_one_raises(self, invalid_threshold: float):
        """code_threshold must be between 0 and 1."""
        import pytest

        with pytest.raises(ValueError, match="code_threshold must be between 0 and 1"):
            ChunkerConfig(code_threshold=invalid_threshold)

    @given(st.integers(min_value=-100, max_value=0))
    @settings(max_examples=50)
    def test_invalid_structure_threshold_raises(self, invalid_threshold: int):
        """structure_threshold must be >= 1."""
        import pytest

        with pytest.raises(ValueError, match="structure_threshold must be >= 1"):
            ChunkerConfig(structure_threshold=invalid_threshold)

    @given(
        st.text(min_size=1, max_size=20).filter(
            lambda x: x not in {"code_aware", "list_aware", "structural", "fallback"}
        )
    )
    @settings(max_examples=50)
    def test_invalid_strategy_override_raises(self, invalid_strategy: str):
        """strategy_override must be a valid strategy name."""
        import pytest

        with pytest.raises(ValueError, match="strategy_override must be one of"):
            ChunkerConfig(strategy_override=invalid_strategy)

    @given(st.floats(min_value=-10.0, max_value=0.0))
    @settings(max_examples=50)
    def test_invalid_overlap_cap_ratio_low_raises(self, invalid_ratio: float):
        """overlap_cap_ratio must be > 0."""
        import pytest

        with pytest.raises(ValueError, match="overlap_cap_ratio must be between"):
            ChunkerConfig(overlap_cap_ratio=invalid_ratio)

    @given(st.floats(min_value=1.01, max_value=10.0))
    @settings(max_examples=50)
    def test_invalid_overlap_cap_ratio_high_raises(self, invalid_ratio: float):
        """overlap_cap_ratio must be <= 1."""
        import pytest

        with pytest.raises(ValueError, match="overlap_cap_ratio must be between"):
            ChunkerConfig(overlap_cap_ratio=invalid_ratio)
