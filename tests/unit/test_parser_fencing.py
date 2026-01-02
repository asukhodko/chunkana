"""
Unit tests for nested fencing support in the parser.

Ported from dify-markdown-chunker to increase test coverage.
Tests comprehensive fence detection including nested fences.
"""

from chunkana.parser import Parser


class TestBasicFenceDetection:
    """Tests for basic fence detection and backward compatibility."""

    def test_triple_backticks_basic(self):
        """Verify standard triple-backtick blocks still parse correctly."""
        text = """```python
def hello():
    print('Hello')
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.language == "python"
        assert block.fence_char == "`"
        assert block.fence_length == 3
        assert block.is_closed is True
        assert "def hello():" in block.content

    def test_triple_backticks_no_language(self):
        """Verify fence without language specifier works."""
        text = """```
code content
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.language is None or block.language == ""
        assert block.content.strip() == "code content"

    def test_multiple_simple_blocks(self):
        """Verify multiple non-nested blocks work correctly."""
        text = """```python
block1
```

Some text

```javascript
block2
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 2
        assert result.code_blocks[0].language == "python"
        assert result.code_blocks[1].language == "javascript"


class TestQuadrupleBackticks:
    """Tests for quadruple backtick nested fencing."""

    def test_quadruple_backticks_detection(self):
        """Verify quadruple-backtick opening fence is detected."""
        text = """````markdown
```python
code
```
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.language == "markdown"
        assert block.fence_char == "`"
        assert block.fence_length == 4
        assert block.is_closed is True

    def test_triple_backticks_inside_dont_close_quadruple(self):
        """Verify triple backticks inside don't close outer quadruple fence."""
        text = """````markdown
```python
def example():
    pass
```
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert "```python" in block.content
        assert "def example():" in block.content
        assert block.fence_length == 4

    def test_nested_content_preserved_exactly(self):
        """Verify inner fence syntax preserved exactly."""
        text = """````markdown
Here's how to show Python:

```python
def hello():
    print('Hello, World!')
```
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert "```python" in block.content
        assert "def hello():" in block.content
        assert block.content.count("```") == 2


class TestTildeFencing:
    """Tests for tilde fence support."""

    def test_tilde_triple_basic(self):
        """Verify triple-tilde fences work."""
        text = """~~~python
def hello():
    pass
~~~"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.fence_char == "~"
        assert block.fence_length == 3
        assert block.language == "python"
        assert block.is_closed is True

    def test_tilde_quadruple(self):
        """Verify quadruple-tilde fences work."""
        text = """~~~~markdown
~~~python
code
~~~
~~~~"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.fence_char == "~"
        assert block.fence_length == 4
        assert "~~~python" in block.content


class TestMixedFenceTypes:
    """Tests for mixing backtick and tilde fences."""

    def test_backtick_containing_tilde(self):
        """Verify backtick fence can contain tilde fence."""
        text = """````markdown
~~~python
code
~~~
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.fence_char == "`"
        assert "~~~python" in block.content

    def test_tilde_containing_backtick(self):
        """Verify tilde fence can contain backtick fence."""
        text = """~~~~markdown
```python
code
```
~~~~"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.fence_char == "~"
        assert "```python" in block.content


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_unclosed_fence(self):
        """Verify unclosed fence extends to document end."""
        text = """````python
code here
no closing fence"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.is_closed is False
        assert "code here" in block.content
        assert "no closing fence" in block.content

    def test_unclosed_fence_metadata(self):
        """Verify unclosed fence has is_closed=False."""
        text = """```python
unclosed"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        assert result.code_blocks[0].is_closed is False

    def test_fence_with_trailing_spaces(self):
        """Verify closing fence with trailing spaces is recognized."""
        text = """```python
code
```   """
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        assert result.code_blocks[0].is_closed is True

    def test_empty_code_block(self):
        """Verify fence with no content lines works."""
        text = """```python
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        block = result.code_blocks[0]
        assert block.content == ""
        assert block.is_closed is True


class TestContentPreservation:
    """Tests for content preservation guarantees."""

    def test_content_whitespace_preservation(self):
        """Verify leading/trailing whitespace in content preserved."""
        text = """```python
  leading spaces
trailing spaces
    tabs here
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        content = result.code_blocks[0].content
        lines = content.split("\n")
        assert lines[0] == "  leading spaces"
        assert lines[1] == "trailing spaces"
        assert lines[2] == "    tabs here"

    def test_empty_lines_within_fence_preserved(self):
        """Verify empty lines within fence are preserved."""
        text = """```python
line1

line3
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 1
        content = result.code_blocks[0].content
        assert "\n\n" in content


class TestMetadata:
    """Tests for fence metadata fields."""

    def test_fence_char_metadata_backtick(self):
        """Verify fence_char set correctly for backticks."""
        text = """```python
code
```"""
        parser = Parser()
        result = parser.analyze(text)

        assert result.code_blocks[0].fence_char == "`"

    def test_fence_char_metadata_tilde(self):
        """Verify fence_char set correctly for tildes."""
        text = """~~~python
code
~~~"""
        parser = Parser()
        result = parser.analyze(text)

        assert result.code_blocks[0].fence_char == "~"

    def test_fence_length_metadata(self):
        """Verify fence_length set correctly for each length."""
        for length in [3, 4, 5, 6]:
            fence = "`" * length
            text = f"""{fence}python
code
{fence}"""
            parser = Parser()
            result = parser.analyze(text)

            assert result.code_blocks[0].fence_length == length

    def test_line_numbers_correct(self):
        """Verify start_line and end_line are correct."""
        text = """Some text
```python
code
```
More text"""
        parser = Parser()
        result = parser.analyze(text)

        block = result.code_blocks[0]
        assert block.start_line == 2
        assert block.end_line == 4


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_multiple_nested_blocks(self):
        """Test document with multiple nested blocks."""
        text = """# Example

````markdown
```python
code1
```
````

More text

````markdown
```javascript
code2
```
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 2
        assert result.code_blocks[0].fence_length == 4
        assert result.code_blocks[1].fence_length == 4
        assert "```python" in result.code_blocks[0].content
        assert "```javascript" in result.code_blocks[1].content

    def test_alternating_fence_types(self):
        """Test alternating backtick and tilde fences."""
        text = """```python
code1
```

~~~python
code2
~~~

````markdown
~~~test
inner
~~~
````"""
        parser = Parser()
        result = parser.analyze(text)

        assert len(result.code_blocks) == 3
        assert result.code_blocks[0].fence_char == "`"
        assert result.code_blocks[1].fence_char == "~"
        assert result.code_blocks[2].fence_char == "`"
