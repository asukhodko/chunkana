# Contributing to Chunkana

Thank you for your interest in contributing to Chunkana! This guide will help you get started with development and understand our contribution process.

## Quick Start

1. **Fork and clone the repository**:
```bash
git clone https://github.com/YOUR_USERNAME/chunkana.git
cd chunkana
```

2. **Set up development environment**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

3. **Verify setup**:
```bash
# Run tests
pytest

# Check code style
ruff check src/chunkana
mypy src/chunkana
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following our [code style guidelines](#code-style)

3. **Add tests** for new functionality in the appropriate test directory

4. **Run the test suite**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=chunkana --cov-report=html

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/property/      # Property-based tests
pytest tests/baseline/      # Compatibility tests
```

5. **Check code quality**:
```bash
# Lint and format
ruff check src/chunkana
ruff format src/chunkana

# Type checking
mypy src/chunkana
```

### Submitting Changes

1. **Commit your changes**:
```bash
git add .
git commit -m "feat: add new chunking strategy for tables"
```

2. **Push to your fork**:
```bash
git push origin feature/your-feature-name
```

3. **Create a Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Test results and coverage info

## Code Style

We use automated tools to maintain consistent code style:

### Formatting and Linting
- **[Ruff](https://docs.astral.sh/ruff/)** for linting and formatting
- **Line length**: 100 characters
- **Target Python version**: 3.12+

```bash
# Check for issues
ruff check src/chunkana

# Auto-fix issues
ruff check --fix src/chunkana

# Format code
ruff format src/chunkana
```

### Type Checking
- **[MyPy](https://mypy.readthedocs.io/)** for static type checking
- **Strict mode** enabled
- All public APIs must be fully typed

```bash
mypy src/chunkana
```

### Code Organization
- **Modules**: Keep modules focused and cohesive
- **Classes**: Use clear, descriptive names
- **Functions**: Single responsibility principle
- **Documentation**: Docstrings for all public APIs

## Testing

### Test Structure

```
tests/
├── unit/           # Unit tests for individual components
├── property/       # Property-based tests using Hypothesis
├── baseline/       # Compatibility tests with dify-markdown-chunker
├── examples/       # Documentation example tests
└── fixtures/       # Test data and fixtures
```

### Writing Tests

#### Unit Tests
```python
def test_chunk_creation():
    """Test basic chunk creation functionality."""
    chunk = Chunk(
        content="# Test\nContent here",
        start_line=1,
        end_line=2,
        metadata={"content_type": "section"}
    )
    
    assert chunk.size == 18
    assert chunk.metadata["content_type"] == "section"
```

#### Property-Based Tests
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_chunking_preserves_content(text):
    """Test that chunking preserves all content."""
    chunks = chunk_markdown(text)
    reconstructed = "".join(chunk.content for chunk in chunks)
    
    # Content should be preserved (allowing for overlap)
    assert len(reconstructed) >= len(text)
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_chunk.py

# With coverage
pytest --cov=chunkana --cov-report=html

# Performance tests (marked as slow)
pytest -m performance

# Baseline compatibility tests
pytest tests/baseline/ -v
```

### Baseline Tests

Baseline tests ensure compatibility with `dify-markdown-chunker` v2:

```bash
# Generate new baseline data (requires dify-markdown-chunker)
python scripts/generate_baseline.py

# Run baseline tests
pytest tests/baseline/
```

## Documentation

### Writing Documentation

- **Docstrings**: Use Google-style docstrings for all public APIs
- **Type hints**: Include comprehensive type annotations
- **Examples**: Provide usage examples in docstrings
- **Markdown docs**: Update relevant documentation files

Example docstring:
```python
def chunk_markdown(text: str, config: ChunkConfig | None = None) -> list[Chunk]:
    """Chunk Markdown text into semantic units.
    
    Args:
        text: The Markdown text to chunk
        config: Optional configuration for chunking behavior
        
    Returns:
        List of chunks with metadata
        
    Example:
        >>> chunks = chunk_markdown("# Title\nContent here")
        >>> len(chunks)
        1
        >>> chunks[0].metadata["header_path"]
        "/Title"
    """
```

### Building Documentation

```bash
# Install docs dependencies
pip install ".[docs]"

# Build documentation (if using MkDocs)
mkdocs build

# Serve locally
mkdocs serve
```

## Issue Guidelines

### Reporting Bugs

When reporting bugs, please include:

1. **Python version** and Chunkana version
2. **Minimal reproducible example**
3. **Expected vs actual behavior**
4. **Full error traceback** if applicable
5. **System information** (OS, environment)

Example bug report:
```markdown
## Bug Description
Chunking fails on documents with nested code blocks

## Environment
- Python: 3.12.1
- Chunkana: 0.1.5
- OS: Ubuntu 22.04

## Minimal Example
```python
from chunkana import chunk_markdown

text = """
# Code Example
```python
def outer():
    ```
    nested code
    ```
```
"""

chunks = chunk_markdown(text)  # Raises ValueError
```

## Expected Behavior
Should create one chunk with the code block intact

## Actual Behavior
ValueError: Unmatched code fence
```

### Feature Requests

For feature requests, please describe:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives considered**: Other approaches you've thought about
4. **Breaking changes**: Would this affect existing APIs?

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Changelog

All changes are documented in [CHANGELOG.md](CHANGELOG.md) following [Keep a Changelog](https://keepachangelog.com/) format.

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Assume good intentions

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Requests**: Code review and collaboration

## Getting Help

- **Documentation**: Check [docs/](docs/) for guides and references
- **Examples**: Browse [examples/](examples/) for usage patterns
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Ask questions in GitHub Discussions

## Recognition

Contributors are recognized in:
- Release notes for significant contributions
- GitHub contributor graphs
- Special thanks in documentation

Thank you for contributing to Chunkana! 🚀
