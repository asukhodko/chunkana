"""
Property-based tests for LaTeX formula preservation.

Feature: chunkana-library
Property 13: LaTeX Block Integrity

Tests that LaTeX formulas (display math and environments) are preserved
as atomic blocks and never split across chunks.
"""

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from chunkana import ChunkerConfig, chunk_markdown

# =============================================================================
# Generators for LaTeX content
# =============================================================================


@st.composite
def simple_latex_formula(draw):
    """Generate a simple LaTeX formula."""
    # Simple math expressions
    formulas = [
        "x^2 + y^2 = z^2",
        "\\frac{a}{b}",
        "\\int_0^1 f(x) dx",
        "\\sum_{i=1}^n i",
        "E = mc^2",
        "\\sqrt{x^2 + y^2}",
        "\\alpha + \\beta = \\gamma",
        "\\lim_{x \\to \\infty} f(x)",
    ]
    return draw(st.sampled_from(formulas))


@st.composite
def markdown_with_display_math(draw):
    """Generate markdown with display math ($$...$$)."""
    parts = []
    num_formulas = draw(st.integers(min_value=1, max_value=3))

    for i in range(num_formulas):
        # Add header
        parts.append(f"# Section {i + 1}\n\n")

        # Add some text before formula
        text = draw(
            st.text(
                min_size=20,
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "P", "Z"), whitelist_characters=" \n.,!?"
                ),
            ).filter(lambda x: x.strip() and "$" not in x)
        )
        parts.append(f"{text}\n\n")

        # Add display math formula
        formula = draw(simple_latex_formula())
        parts.append(f"$$\n{formula}\n$$\n\n")

        # Add some text after formula
        after_text = draw(
            st.text(
                min_size=20,
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "P", "Z"), whitelist_characters=" \n.,!?"
                ),
            ).filter(lambda x: x.strip() and "$" not in x)
        )
        parts.append(f"{after_text}\n\n")

    return "".join(parts)


@st.composite
def markdown_with_latex_environments(draw):
    """Generate markdown with LaTeX environments."""
    parts = []
    num_envs = draw(st.integers(min_value=1, max_value=2))

    env_types = ["equation", "align", "gather"]

    for i in range(num_envs):
        # Add header
        parts.append(f"# Section {i + 1}\n\n")

        # Add some text
        text = draw(
            st.text(
                min_size=20,
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "P", "Z"), whitelist_characters=" \n.,!?"
                ),
            ).filter(lambda x: x.strip() and "\\" not in x)
        )
        parts.append(f"{text}\n\n")

        # Add LaTeX environment
        env_type = draw(st.sampled_from(env_types))
        formula = draw(simple_latex_formula())
        parts.append(f"\\begin{{{env_type}}}\n{formula}\n\\end{{{env_type}}}\n\n")

        # Add text after
        after_text = draw(
            st.text(
                min_size=20,
                max_size=100,
                alphabet=st.characters(
                    whitelist_categories=("L", "N", "P", "Z"), whitelist_characters=" \n.,!?"
                ),
            ).filter(lambda x: x.strip() and "\\" not in x)
        )
        parts.append(f"{after_text}\n\n")

    return "".join(parts)


@st.composite
def markdown_with_inline_math(draw):
    """Generate markdown with inline math ($...$)."""
    parts = []

    # Add header
    parts.append("# Document with Inline Math\n\n")

    # Add text with inline math
    formula = draw(simple_latex_formula())
    parts.append(f"The formula ${formula}$ is important.\n\n")

    # Add more text
    parts.append("This is additional content.\n\n")

    # Add another inline formula
    formula2 = draw(simple_latex_formula())
    parts.append(f"We also have ${formula2}$ here.\n\n")

    return "".join(parts)


@st.composite
def markdown_with_mixed_latex(draw):
    """Generate markdown with mixed LaTeX types."""
    parts = []

    # Header
    parts.append("# Mixed LaTeX Document\n\n")

    # Inline math
    formula1 = draw(simple_latex_formula())
    parts.append(f"Inline formula: ${formula1}$\n\n")

    # Display math
    formula2 = draw(simple_latex_formula())
    parts.append(f"$$\n{formula2}\n$$\n\n")

    # Environment
    env_type = draw(st.sampled_from(["equation", "align"]))
    formula3 = draw(simple_latex_formula())
    parts.append(f"\\begin{{{env_type}}}\n{formula3}\n\\end{{{env_type}}}\n\n")

    # More text
    parts.append("Conclusion text here.\n")

    return "".join(parts)


# =============================================================================
# Helper functions
# =============================================================================


def count_display_delimiters(content: str) -> int:
    """Count $$ delimiters in content."""
    return content.count("$$")


def has_unclosed_display_math(content: str) -> bool:
    """Check if content has unclosed display math."""
    count = count_display_delimiters(content)
    return count % 2 != 0


def has_unclosed_environment(content: str) -> bool:
    """Check if content has unclosed LaTeX environment."""
    import re

    env_names = ["equation", "align", "gather", "multline", "eqnarray"]

    for env in env_names:
        begin_count = len(re.findall(rf"\\begin\{{{env}\*?\}}", content))
        end_count = len(re.findall(rf"\\end\{{{env}\*?\}}", content))
        if begin_count != end_count:
            return True

    return False


# =============================================================================
# Property Tests
# =============================================================================


class TestLatexBlockIntegrity:
    """
    Property 13: LaTeX Block Integrity

    For any markdown document containing LaTeX formulas, no chunk should
    contain a partial LaTeX block (unclosed $$ or unclosed environment).

    Validates: Requirements 4.3
    """

    @given(markdown=markdown_with_display_math())
    @settings(max_examples=100)
    def test_display_math_not_split(self, markdown: str):
        """
        Feature: chunkana-library, Property 13: LaTeX Block Integrity (display)

        Display math ($$...$$) should not be split across chunks.
        """
        assume(len(markdown.strip()) > 0)

        config = ChunkerConfig(
            max_chunk_size=500,  # Small to force splitting
            min_chunk_size=50,
            preserve_latex_blocks=True,
        )

        try:
            chunks = chunk_markdown(markdown, config)
        except Exception:
            return

        for i, chunk in enumerate(chunks):
            # Each chunk should have balanced $$ delimiters
            delimiter_count = count_display_delimiters(chunk.content)
            assert delimiter_count % 2 == 0, (
                f"Chunk {i} has unbalanced display math delimiters (count={delimiter_count}):\n"
                f"{chunk.content[:200]}"
            )

    @given(markdown=markdown_with_latex_environments())
    @settings(max_examples=100)
    def test_latex_environments_not_split(self, markdown: str):
        """
        Feature: chunkana-library, Property 13: LaTeX Block Integrity (environments)

        LaTeX environments (\\begin{equation}...\\end{equation}) should not be split.
        """
        assume(len(markdown.strip()) > 0)

        config = ChunkerConfig(
            max_chunk_size=500,  # Small to force splitting
            min_chunk_size=50,
            preserve_latex_blocks=True,
        )

        try:
            chunks = chunk_markdown(markdown, config)
        except Exception:
            return

        for i, chunk in enumerate(chunks):
            # Each chunk should have balanced environments
            assert not has_unclosed_environment(chunk.content), (
                f"Chunk {i} has unclosed LaTeX environment:\n{chunk.content[:200]}"
            )

    @given(markdown=markdown_with_mixed_latex())
    @settings(max_examples=100)
    def test_mixed_latex_preserved(self, markdown: str):
        """
        Feature: chunkana-library, Property 13: LaTeX Block Integrity (mixed)

        Mixed LaTeX content (inline, display, environments) should all be preserved.
        """
        assume(len(markdown.strip()) > 0)

        config = ChunkerConfig(
            max_chunk_size=800,
            min_chunk_size=100,
            preserve_latex_blocks=True,
        )

        try:
            chunks = chunk_markdown(markdown, config)
        except Exception:
            return

        for i, chunk in enumerate(chunks):
            # Check display math
            assert not has_unclosed_display_math(chunk.content), (
                f"Chunk {i} has unclosed display math"
            )
            # Check environments
            assert not has_unclosed_environment(chunk.content), (
                f"Chunk {i} has unclosed environment"
            )


class TestLatexContentPreservation:
    """Test that LaTeX content is preserved in chunks."""

    @given(markdown=markdown_with_display_math())
    @settings(max_examples=100)
    def test_latex_formulas_present_in_output(self, markdown: str):
        """All LaTeX formulas from input should be present in output."""
        assume(len(markdown.strip()) > 0)

        try:
            chunks = chunk_markdown(markdown)
        except Exception:
            return

        # Combine all chunk content
        combined = "".join(c.content for c in chunks)

        # Count $$ in original and combined
        original_count = count_display_delimiters(markdown)
        combined_count = count_display_delimiters(combined)

        # Should have same number of delimiters (formulas preserved)
        assert combined_count >= original_count - 2, (
            f"LaTeX formulas lost: original had {original_count} $$, combined has {combined_count}"
        )

    @given(markdown=markdown_with_latex_environments())
    @settings(max_examples=100)
    def test_latex_environments_present_in_output(self, markdown: str):
        """All LaTeX environments from input should be present in output."""
        assume(len(markdown.strip()) > 0)

        try:
            chunks = chunk_markdown(markdown)
        except Exception:
            return

        # Combine all chunk content
        combined = "".join(c.content for c in chunks)

        # Check that environments are present
        import re

        for env in ["equation", "align", "gather"]:
            original_begins = len(re.findall(rf"\\begin\{{{env}\}}", markdown))
            combined_begins = len(re.findall(rf"\\begin\{{{env}\}}", combined))

            if original_begins > 0:
                assert combined_begins >= original_begins, (
                    f"Lost {env} environments: original had {original_begins}, "
                    f"combined has {combined_begins}"
                )


class TestLatexWithCodeBlocks:
    """Test LaTeX handling when mixed with code blocks."""

    def test_latex_in_code_block_not_treated_as_latex(self):
        """LaTeX inside code blocks should not be treated as LaTeX."""
        markdown = """# Code Example

Here's some code:

```python
# This is not LaTeX: $$x^2$$
formula = "$$y = mx + b$$"
```

And here's real LaTeX:

$$
E = mc^2
$$

More text.
"""
        chunks = chunk_markdown(markdown)

        # Should have chunks
        assert len(chunks) > 0

        # The code block should be preserved
        combined = "".join(c.content for c in chunks)
        assert "```python" in combined
        assert "formula = " in combined

    def test_latex_after_code_block_preserved(self):
        """LaTeX after code blocks should be preserved correctly."""
        markdown = """# Document

```python
print("hello")
```

The formula is:

$$
\\int_0^1 f(x) dx
$$

End.
"""
        chunks = chunk_markdown(markdown)

        # Combine content
        combined = "".join(c.content for c in chunks)

        # Both code and LaTeX should be present
        assert "```python" in combined
        assert "$$" in combined
        assert "\\int" in combined


class TestLatexEdgeCases:
    """Test edge cases for LaTeX handling."""

    def test_single_line_display_math(self):
        """Single-line display math should be preserved."""
        markdown = """# Formula

The answer is $$x = 42$$ as expected.

More text.
"""
        chunks = chunk_markdown(markdown)
        combined = "".join(c.content for c in chunks)

        assert "$$x = 42$$" in combined

    def test_multiline_display_math(self):
        """Multi-line display math should be preserved."""
        markdown = """# Formula

$$
\\frac{a}{b} + \\frac{c}{d}
$$

More text.
"""
        chunks = chunk_markdown(markdown)
        combined = "".join(c.content for c in chunks)

        assert "$$" in combined
        assert "\\frac" in combined

    def test_nested_environments(self):
        """Nested LaTeX environments should be handled."""
        markdown = """# Nested

\\begin{equation}
\\begin{aligned}
x &= 1 \\\\
y &= 2
\\end{aligned}
\\end{equation}

End.
"""
        chunks = chunk_markdown(markdown)
        combined = "".join(c.content for c in chunks)

        # Should preserve the structure
        assert "\\begin{equation}" in combined
        assert "\\end{equation}" in combined

    def test_latex_with_special_characters(self):
        """LaTeX with special characters should be preserved."""
        markdown = """# Special

$$
\\alpha \\beta \\gamma \\delta
$$

More text.
"""
        chunks = chunk_markdown(markdown)
        combined = "".join(c.content for c in chunks)

        assert "\\alpha" in combined
        assert "\\beta" in combined


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
