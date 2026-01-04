"""
Unit tests for ChunkerConfig validation.

Task 13.2: Tests for invalid values, factory methods.
Validates: Requirements 2.7
"""

import pytest

from chunkana import ChunkConfig, ChunkerConfig


class TestConfigValidation:
    """Tests for ChunkerConfig validation."""

    def test_default_config_is_valid(self):
        """Default config should have valid values."""
        config = ChunkerConfig()
        assert config.max_chunk_size > 0
        assert config.min_chunk_size > 0
        assert config.overlap_size >= 0
        assert config.max_chunk_size >= config.min_chunk_size

    def test_invalid_max_chunk_size_zero(self):
        """max_chunk_size=0 should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(max_chunk_size=0)

    def test_invalid_max_chunk_size_negative(self):
        """Negative max_chunk_size should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(max_chunk_size=-100)

    def test_invalid_min_chunk_size_negative(self):
        """Negative min_chunk_size should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(min_chunk_size=-1)

    def test_min_greater_than_max_raises_error(self):
        """min_chunk_size > max_chunk_size should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(max_chunk_size=100, min_chunk_size=200)

    def test_invalid_overlap_size_negative(self):
        """Negative overlap_size should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(overlap_size=-10)

    def test_overlap_greater_than_max_raises_error(self):
        """overlap_size > max_chunk_size should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(max_chunk_size=100, overlap_size=200)


class TestConfigFactoryMethods:
    """Tests for ChunkerConfig factory methods."""

    def test_default_factory(self):
        """default() should return valid default config."""
        config = ChunkerConfig.default()
        assert config.max_chunk_size == 4096
        assert config.min_chunk_size == 512
        assert config.overlap_size == 200

    def test_for_code_heavy_factory(self):
        """for_code_heavy() should return config optimized for code."""
        config = ChunkerConfig.for_code_heavy()
        # Code-heavy config should have larger chunks
        assert config.max_chunk_size >= 4096
        # Lower code threshold for earlier code detection
        assert config.code_threshold <= 0.3


class TestConfigSerialization:
    """Tests for ChunkerConfig serialization."""

    def test_to_dict_contains_all_fields(self):
        """to_dict should contain all configuration fields."""
        config = ChunkerConfig()
        d = config.to_dict()

        # Core fields
        assert "max_chunk_size" in d
        assert "min_chunk_size" in d
        assert "overlap_size" in d

        # Strategy thresholds
        assert "code_threshold" in d
        assert "structure_threshold" in d

        # Code-context binding fields
        assert "enable_code_context_binding" in d
        assert "max_context_chars_before" in d
        assert "max_context_chars_after" in d

    def test_from_dict_creates_valid_config(self):
        """from_dict should create valid config."""
        data = {
            "max_chunk_size": 2048,
            "min_chunk_size": 256,
            "overlap_size": 100,
        }
        config = ChunkerConfig.from_dict(data)

        assert config.max_chunk_size == 2048
        assert config.min_chunk_size == 256
        assert config.overlap_size == 100

    def test_roundtrip_preserves_values(self):
        """Serialization roundtrip should preserve all values."""
        original = ChunkerConfig(
            max_chunk_size=8192,
            min_chunk_size=1024,
            overlap_size=300,
            code_threshold=0.25,
            enable_code_context_binding=False,
        )

        restored = ChunkerConfig.from_dict(original.to_dict())

        assert restored.max_chunk_size == original.max_chunk_size
        assert restored.min_chunk_size == original.min_chunk_size
        assert restored.overlap_size == original.overlap_size
        assert restored.code_threshold == original.code_threshold
        assert restored.enable_code_context_binding == original.enable_code_context_binding


class TestConfigAlias:
    """Tests for ChunkerConfig/ChunkConfig alias."""

    def test_chunker_config_is_chunk_config(self):
        """ChunkerConfig should be alias for ChunkConfig."""
        assert ChunkerConfig is ChunkConfig

    def test_both_names_work(self):
        """Both ChunkerConfig and ChunkConfig should work."""
        config1 = ChunkerConfig(max_chunk_size=1000)
        config2 = ChunkConfig(max_chunk_size=1000)

        assert type(config1) is type(config2)
        assert config1.max_chunk_size == config2.max_chunk_size


class TestCodeContextBindingConfig:
    """Tests for code-context binding configuration."""

    def test_code_context_binding_defaults(self):
        """Code-context binding should have sensible defaults."""
        config = ChunkerConfig()

        assert config.enable_code_context_binding is True
        assert config.max_context_chars_before > 0
        assert config.max_context_chars_after > 0
        assert config.related_block_max_gap > 0

    def test_code_context_binding_can_be_disabled(self):
        """Code-context binding can be disabled."""
        config = ChunkerConfig(enable_code_context_binding=False)
        assert config.enable_code_context_binding is False

    def test_code_context_binding_params_preserved(self):
        """Code-context binding params should be preserved in serialization."""
        config = ChunkerConfig(
            enable_code_context_binding=True,
            max_context_chars_before=1000,
            max_context_chars_after=500,
            related_block_max_gap=10,
            bind_output_blocks=False,
            preserve_before_after_pairs=False,
        )

        d = config.to_dict()
        restored = ChunkerConfig.from_dict(d)

        assert restored.enable_code_context_binding == config.enable_code_context_binding
        assert restored.max_context_chars_before == config.max_context_chars_before
        assert restored.max_context_chars_after == config.max_context_chars_after
        assert restored.related_block_max_gap == config.related_block_max_gap
        assert restored.bind_output_blocks == config.bind_output_blocks
        assert restored.preserve_before_after_pairs == config.preserve_before_after_pairs


class TestOverlapCapRatioConfig:
    """Tests for overlap_cap_ratio configuration."""

    def test_overlap_cap_ratio_default(self):
        """overlap_cap_ratio should default to 0.35."""
        config = ChunkerConfig()
        assert config.overlap_cap_ratio == 0.35

    def test_overlap_cap_ratio_can_be_customized(self):
        """overlap_cap_ratio can be set to custom value."""
        config = ChunkerConfig(overlap_cap_ratio=0.5)
        assert config.overlap_cap_ratio == 0.5

    def test_overlap_cap_ratio_zero_raises_error(self):
        """overlap_cap_ratio=0 should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(overlap_cap_ratio=0)

    def test_overlap_cap_ratio_negative_raises_error(self):
        """Negative overlap_cap_ratio should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(overlap_cap_ratio=-0.1)

    def test_overlap_cap_ratio_greater_than_one_raises_error(self):
        """overlap_cap_ratio > 1 should raise ValueError."""
        with pytest.raises(ValueError):
            ChunkerConfig(overlap_cap_ratio=1.5)

    def test_overlap_cap_ratio_one_is_valid(self):
        """overlap_cap_ratio=1.0 should be valid (100% of chunk)."""
        config = ChunkerConfig(overlap_cap_ratio=1.0)
        assert config.overlap_cap_ratio == 1.0

    def test_overlap_cap_ratio_preserved_in_serialization(self):
        """overlap_cap_ratio should be preserved in to_dict/from_dict."""
        config = ChunkerConfig(overlap_cap_ratio=0.25)
        d = config.to_dict()

        assert "overlap_cap_ratio" in d
        assert d["overlap_cap_ratio"] == 0.25

        restored = ChunkerConfig.from_dict(d)
        assert restored.overlap_cap_ratio == 0.25
