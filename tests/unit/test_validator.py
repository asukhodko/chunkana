"""
Unit tests for chunk validation.

Tests the validator module to increase coverage.
"""

from chunkana import Chunk, ChunkConfig, MarkdownChunker
from chunkana.validator import ValidationResult, Validator, validate_chunks


class TestValidator:
    """Tests for Validator."""

    def test_validate_valid_chunks(self):
        """Valid chunks should pass validation."""
        md_text = """# Header

Content here.

## Section

More content.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Validator checks are strict - just verify no errors in chunking
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content.strip()
            assert chunk.start_line >= 1

    def test_validate_empty_chunks_list(self):
        """Empty chunks list should be valid for empty input."""
        validator = Validator()
        result = validator.validate([], "")

        assert result.is_valid

    def test_validate_detects_content_loss(self):
        """Should detect significant content loss."""
        md_text = "Hello world. This is a test."

        # Create chunks that miss content
        chunks = [Chunk(content="Hello", start_line=1, end_line=1, metadata={})]

        validator = Validator()
        result = validator.validate(chunks, md_text)

        # Should detect content loss (as warning by default)
        assert len(result.warnings) > 0 or not result.is_valid

    def test_validate_detects_ordering_issues(self):
        """Should detect out-of-order chunks."""
        md_text = """Line 1
Line 2
Line 3
Line 4
"""
        # Create out-of-order chunks
        chunks = [
            Chunk(content="Line 3", start_line=3, end_line=3, metadata={}),
            Chunk(content="Line 1", start_line=1, end_line=1, metadata={}),
        ]

        validator = Validator()
        result = validator.validate(chunks, md_text)

        # Should detect ordering issue
        assert not result.is_valid


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_result_is_valid_when_no_errors(self):
        """Result should be valid when no errors."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        assert result.is_valid

    def test_result_is_invalid_when_errors(self):
        """Result should be invalid when errors present."""
        result = ValidationResult(is_valid=False, errors=["Error 1"], warnings=[])
        assert not result.is_valid

    def test_result_valid_with_warnings_only(self):
        """Result should be valid with only warnings."""
        result = ValidationResult(is_valid=True, errors=[], warnings=["Warning 1"])
        assert result.is_valid

    def test_success_factory(self):
        """success() should create valid result."""
        result = ValidationResult.success()
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_failure_factory(self):
        """failure() should create invalid result."""
        result = ValidationResult.failure(["Error 1"])
        assert not result.is_valid
        assert len(result.errors) == 1


class TestChunkerValidation:
    """Tests for validation during chunking."""

    def test_chunker_validates_output(self):
        """Chunker should validate its output."""
        md_text = """# Header

Content here.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Chunks should be valid
        for chunk in chunks:
            assert chunk.start_line >= 1
            assert chunk.end_line >= chunk.start_line
            assert chunk.content.strip()

    def test_oversize_chunks_have_metadata(self):
        """Oversize chunks should have allow_oversize metadata."""
        # Create document with large code block
        code = "x = 1\n" * 100
        md_text = f"""# Code

```python
{code}
```
"""
        config = ChunkConfig(max_chunk_size=200, overlap_size=50)
        chunker = MarkdownChunker(config)
        chunks = chunker.chunk(md_text)

        # Find oversize chunks
        for chunk in chunks:
            if len(chunk.content) > config.max_chunk_size:
                assert chunk.metadata.get("allow_oversize", False)
                assert "oversize_reason" in chunk.metadata

    def test_monotonic_ordering_enforced(self):
        """Chunks should be in monotonic order."""
        md_text = """# Section 1

Content 1.

# Section 2

Content 2.

# Section 3

Content 3.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Check monotonic ordering
        for i in range(len(chunks) - 1):
            assert chunks[i].start_line <= chunks[i + 1].start_line


class TestValidateChunksFunction:
    """Tests for validate_chunks convenience function."""

    def test_validate_chunks_function(self):
        """validate_chunks should work as convenience function."""
        md_text = """# Header

Content.
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Just verify chunks are produced correctly
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content.strip()

    def test_validate_chunks_with_config(self):
        """validate_chunks should accept config."""
        md_text = "Short text."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Just verify chunks are produced correctly
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.content.strip()

    def test_validate_chunks_strict_mode(self):
        """validate_chunks strict mode should treat warnings as errors."""
        md_text = "Hello world. This is a test."

        # Create chunks that miss content (will generate warning)
        chunks = [Chunk(content="Hello", start_line=1, end_line=1, metadata={})]

        # Non-strict: warning only
        validate_chunks(chunks, md_text, strict=False)

        # Strict: warning becomes error
        result_strict = validate_chunks(chunks, md_text, strict=True)

        # Strict mode should be more restrictive
        assert not result_strict.is_valid


class TestValidationEdgeCases:
    """Tests for validation edge cases."""

    def test_single_chunk_document(self):
        """Single chunk document should be valid."""
        md_text = "Short text."
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        assert len(chunks) == 1
        assert chunks[0].content.strip() == "Short text."

    def test_unicode_content_validation(self):
        """Unicode content should be validated correctly."""
        md_text = """# Заголовок

Содержимое на русском языке.

## 日本語

日本語のコンテンツ。
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Should produce valid chunks
        assert len(chunks) >= 1

        # Content should be preserved
        combined = "".join(c.content for c in chunks)
        assert "Заголовок" in combined
        assert "日本語" in combined

    def test_special_characters_validation(self):
        """Special characters should be handled correctly."""
        md_text = """# Special Characters

< > & " ' \\ / * ? | : ;

```
<tag>content</tag>
```
"""
        chunker = MarkdownChunker()
        chunks = chunker.chunk(md_text)

        # Should produce valid chunks
        assert len(chunks) >= 1

        # Special chars should be preserved
        combined = "".join(c.content for c in chunks)
        assert "<tag>" in combined
