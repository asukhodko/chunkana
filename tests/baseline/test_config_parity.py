"""
Config parity tests for Chunkana.

These tests ensure ChunkerConfig has all fields from the plugin's ChunkConfig.

Source of truth: tests/baseline/plugin_config_keys.json
Generated from plugin at commit specified in BASELINE.md
"""

import json
from pathlib import Path

from chunkana import ChunkerConfig

BASELINE_DIR = Path(__file__).parent
PLUGIN_CONFIG_KEYS_PATH = BASELINE_DIR / "plugin_config_keys.json"


def load_plugin_config_keys() -> list[str]:
    """Load plugin config keys from JSON file."""
    with open(PLUGIN_CONFIG_KEYS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["keys"]


class TestConfigParity:
    """
    Verify ChunkerConfig has all fields from plugin's ChunkConfig.

    Requirements: 10.1, 10.2, 10.3, 10.4
    """

    def test_plugin_config_keys_file_exists(self):
        """Verify plugin_config_keys.json exists."""
        assert PLUGIN_CONFIG_KEYS_PATH.exists(), (
            f"Plugin config keys file not found: {PLUGIN_CONFIG_KEYS_PATH}"
        )

    def test_to_dict_contains_all_plugin_keys(self):
        """
        Verify to_dict() contains all keys from plugin's ChunkConfig.

        This is the core parity test - ensures Chunkana can serialize
        all fields that the plugin expects.
        """
        plugin_keys = set(load_plugin_config_keys())
        config = ChunkerConfig()
        chunkana_keys = set(config.to_dict().keys())

        missing_keys = plugin_keys - chunkana_keys

        assert not missing_keys, (
            f"ChunkerConfig.to_dict() missing plugin keys: {sorted(missing_keys)}"
        )

    def test_from_dict_accepts_all_plugin_keys(self):
        """
        Verify from_dict() accepts all keys from plugin's ChunkConfig.

        This ensures Chunkana can deserialize configs from the plugin.
        """
        plugin_keys = load_plugin_config_keys()

        # Create a dict with all plugin keys set to valid defaults
        config_dict = {}
        for key in plugin_keys:
            if key == "enable_overlap":
                config_dict[key] = True  # computed property
            elif key == "max_chunk_size":
                config_dict[key] = 4096
            elif key == "min_chunk_size":
                config_dict[key] = 512
            elif key == "overlap_size":
                config_dict[key] = 200
            elif key in ("code_threshold", "list_ratio_threshold"):
                config_dict[key] = 0.5
            elif key in ("structure_threshold", "list_count_threshold"):
                config_dict[key] = 3
            elif key in ("max_context_chars_before", "max_context_chars_after"):
                config_dict[key] = 500
            elif key == "related_block_max_gap":
                config_dict[key] = 5
            elif key == "strategy_override":
                config_dict[key] = None
            else:
                config_dict[key] = True  # boolean fields

        # Should not raise
        config = ChunkerConfig.from_dict(config_dict)

        # Verify some key values were applied
        assert config.max_chunk_size == 4096
        assert config.code_threshold == 0.5

    def test_plugin_keys_count(self):
        """Verify expected number of plugin keys."""
        plugin_keys = load_plugin_config_keys()
        # Plugin has 17 keys as of commit 120d008bafd0
        assert len(plugin_keys) == 17, (
            f"Expected 17 plugin keys, got {len(plugin_keys)}: {plugin_keys}"
        )

    def test_chunkana_extension_keys_present(self):
        """
        Verify Chunkana extension keys are present in to_dict().

        These are keys that Chunkana adds beyond plugin parity.
        """
        config = ChunkerConfig()
        keys = set(config.to_dict().keys())

        extension_keys = {
            "overlap_cap_ratio",
            "use_adaptive_sizing",
            "adaptive_config",
            "include_document_summary",
            "strip_obsidian_block_ids",
            "preserve_latex_blocks",
            "latex_display_only",
            "latex_max_context_chars",
            "group_related_tables",
            "table_grouping_config",
        }

        missing = extension_keys - keys
        assert not missing, f"ChunkerConfig.to_dict() missing extension keys: {sorted(missing)}"
