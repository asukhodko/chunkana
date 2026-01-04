"""
Export verification tests for Chunkana (Task 10.3).

Verifies:
- All expected imports work
- No Dify SDK imports
- Public API is complete
"""


class TestMinimalStableAPI:
    """Test minimal stable API exports (Task 10.1)."""

    def test_chunk_exports(self):
        """Verify Chunk class is exported."""
        from chunkana import Chunk

        assert Chunk is not None

    def test_config_exports(self):
        """Verify config classes are exported."""
        from chunkana import ChunkConfig, ChunkerConfig

        assert ChunkConfig is not None
        assert ChunkerConfig is not None
        # ChunkConfig should be alias for ChunkerConfig
        assert ChunkConfig is ChunkerConfig

    def test_chunk_markdown_export(self):
        """Verify chunk_markdown function is exported."""
        from chunkana import chunk_markdown

        assert callable(chunk_markdown)

    def test_chunk_text_export(self):
        """Verify chunk_text function is exported."""
        from chunkana import chunk_text

        assert callable(chunk_text)

    def test_chunk_file_export(self):
        """Verify chunk_file function is exported."""
        from chunkana import chunk_file

        assert callable(chunk_file)

    def test_render_dify_style_export(self):
        """Verify render_dify_style function is exported."""
        from chunkana import render_dify_style

        assert callable(render_dify_style)

    def test_render_with_embedded_overlap_export(self):
        """Verify render_with_embedded_overlap function is exported."""
        from chunkana import render_with_embedded_overlap

        assert callable(render_with_embedded_overlap)


class TestExtendedAPI:
    """Test extended API exports (Task 10.2)."""

    def test_streaming_exports(self):
        """Verify streaming classes are exported."""
        from chunkana import StreamingChunker, StreamingConfig

        assert StreamingChunker is not None
        assert StreamingConfig is not None

    def test_hierarchy_exports(self):
        """Verify hierarchy classes are exported."""
        from chunkana import HierarchicalChunkingResult, HierarchyBuilder

        assert HierarchicalChunkingResult is not None
        assert HierarchyBuilder is not None

    def test_chunk_file_streaming_export(self):
        """Verify chunk_file_streaming function is exported."""
        from chunkana import chunk_file_streaming

        assert callable(chunk_file_streaming)

    def test_chunk_hierarchical_export(self):
        """Verify chunk_hierarchical function is exported."""
        from chunkana import chunk_hierarchical

        assert callable(chunk_hierarchical)

    def test_extended_renderers_export(self):
        """Verify extended renderer functions are exported."""
        from chunkana import (
            render_inline_metadata,
            render_json,
            render_with_prev_overlap,
        )

        assert callable(render_json)
        assert callable(render_inline_metadata)
        assert callable(render_with_prev_overlap)

    def test_analysis_exports(self):
        """Verify analysis functions are exported."""
        from chunkana import (
            analyze_markdown,
            chunk_with_analysis,
            chunk_with_metrics,
            iter_chunks,
        )

        assert callable(analyze_markdown)
        assert callable(chunk_with_analysis)
        assert callable(chunk_with_metrics)
        assert callable(iter_chunks)

    def test_validation_exports(self):
        """Verify validation classes are exported."""
        from chunkana import ValidationResult, Validator, validate_chunks

        assert Validator is not None
        assert ValidationResult is not None
        assert callable(validate_chunks)

    def test_types_exports(self):
        """Verify type classes are exported."""
        from chunkana import (
            ChunkingMetrics,
            ChunkingResult,
            ContentAnalysis,
            FencedBlock,
        )

        assert ContentAnalysis is not None
        assert FencedBlock is not None
        assert ChunkingResult is not None
        assert ChunkingMetrics is not None

    def test_chunker_class_export(self):
        """Verify MarkdownChunker class is exported."""
        from chunkana import MarkdownChunker

        assert MarkdownChunker is not None


class TestNoDifySDKImports:
    """Verify no Dify SDK imports in public API."""

    def test_no_dify_imports_in_init(self):
        """Verify __init__.py doesn't import from dify_plugin."""
        import inspect

        import chunkana

        source = inspect.getsourcefile(chunkana)
        with open(source) as f:
            content = f.read()

        assert "dify_plugin" not in content, "chunkana.__init__ should not import from dify_plugin"
        assert "from dify" not in content, "chunkana.__init__ should not import from dify"

    def test_no_dify_in_api_module(self):
        """Verify api.py doesn't import from dify_plugin."""
        import inspect

        from chunkana import api

        source = inspect.getsourcefile(api)
        with open(source) as f:
            content = f.read()

        assert "dify_plugin" not in content, "chunkana.api should not import from dify_plugin"

    def test_no_dify_in_renderers(self):
        """Verify renderers don't import from dify_plugin."""
        import inspect

        from chunkana import renderers

        source = inspect.getsourcefile(renderers)
        with open(source) as f:
            content = f.read()

        assert "dify_plugin" not in content, "chunkana.renderers should not import from dify_plugin"


class TestAllExportsWork:
    """Verify all __all__ exports actually work."""

    def test_all_exports_importable(self):
        """Every item in __all__ should be importable."""
        import chunkana

        for name in chunkana.__all__:
            obj = getattr(chunkana, name, None)
            assert obj is not None, f"Export '{name}' is None or missing"

    def test_version_export(self):
        """Verify __version__ is exported."""
        from chunkana import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestFunctionalImports:
    """Test that imports work functionally."""

    def test_basic_chunking_workflow(self):
        """Test basic chunking workflow with imports."""
        from chunkana import ChunkerConfig, chunk_markdown

        config = ChunkerConfig(max_chunk_size=1000)
        chunks = chunk_markdown("# Test\n\nContent", config)
        assert len(chunks) > 0

    def test_rendering_workflow(self):
        """Test rendering workflow with imports."""
        from chunkana import chunk_markdown, render_dify_style

        chunks = chunk_markdown("# Test\n\nContent")
        outputs = render_dify_style(chunks)
        assert len(outputs) == len(chunks)

    def test_hierarchical_workflow(self):
        """Test hierarchical chunking workflow with imports."""
        from chunkana import chunk_hierarchical

        result = chunk_hierarchical("# Test\n\nContent")
        assert result is not None
        assert result.root_id is not None
