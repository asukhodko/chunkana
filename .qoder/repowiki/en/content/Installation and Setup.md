# Installation and Setup

<cite>
**Referenced Files in This Document**   
- [README.md](file://README.md)
- [pyproject.toml](file://pyproject.toml)
- [CONTRIBUTING.md](file://CONTRIBUTING.md)
- [Makefile](file://Makefile)
- [docs/quickstart.md](file://docs/quickstart.md)
- [docs/config.md](file://docs/config.md)
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md)
- [src/chunkana/__init__.py](file://src/chunkana/__init__.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Environment Requirements](#environment-requirements)
3. [Installing Chunkana via pip](#installing-chunkana-via-pip)
4. [Verifying Installation](#verifying-installation)
5. [Virtual Environment Best Practices](#virtual-environment-best-practices)
6. [Integration with Poetry and pipenv](#integration-with-poetry-and-pipenv)
7. [Configuration Prerequisites](#configuration-prerequisites)
8. [Post-Installation Steps](#post-installation-steps)
9. [Common Installation Issues](#common-installation-issues)
10. [Troubleshooting Guide](#troubleshooting-guide)

## Introduction

Chunkana is an intelligent Markdown chunking library designed for Retrieval-Augmented Generation (RAG) systems. This document provides comprehensive installation and setup instructions for developers and system administrators. The guide covers standard installation procedures, environment requirements, virtual environment management, integration with popular Python package managers, and troubleshooting common issues encountered during installation and configuration.

**Section sources**
- [README.md](file://README.md#L1-L179)

## Environment Requirements

Before installing Chunkana, ensure your system meets the following requirements:

### Python Version
Chunkana requires Python 3.12 or higher. This requirement is explicitly defined in the project's `pyproject.toml` file:

```toml
requires-python = ">=3.12"
```

To verify your Python version, run:
```bash
python --version
```

### System Dependencies
Chunkana is a pure Python package with no external system dependencies. It does not require compilation of C extensions or installation of system-level packages. The library is compatible with all major operating systems including Windows, macOS, and Linux distributions.

### Hardware Requirements
Chunkana has minimal hardware requirements:
- Minimum 256MB RAM (recommended 512MB+ for large document processing)
- No specific CPU requirements (works on x86_64 and ARM architectures)
- Minimal disk space (less than 10MB for installation)

The library is optimized for efficient memory usage and can process large Markdown files (>10MB) through its streaming capabilities.

**Section sources**
- [pyproject.toml](file://pyproject.toml#L1-L94)
- [README.md](file://README.md#L1-L179)

## Installing Chunkana via pip

Installing Chunkana is straightforward using pip, the Python package installer.

### Basic Installation
To install the latest stable version of Chunkana, execute:
```bash
pip install chunkana
```

This command installs Chunkana version 0.1.2, which is the current release specified in the `pyproject.toml` file.

### Version Constraints
To install a specific version of Chunkana, use version specifiers:
```bash
# Install exactly version 0.1.2
pip install chunkana==0.1.2

# Install version 0.1.2 or higher, but less than 0.2.0
pip install "chunkana>=0.1.2,<0.2.0"

# Install the latest version that is compatible with 0.1.x
pip install "chunkana~=0.1.0"
```

### Optional Dependencies
Chunkana supports optional dependency groups for development and documentation purposes. These can be installed using pip's extras syntax:

```bash
# Install with development dependencies (pytest, mypy, ruff, etc.)
pip install chunkana[dev]

# Install with documentation dependencies (mkdocs, mkdocs-material)
pip install chunkana[docs]
```

The optional dependencies are defined in the `pyproject.toml` file under the `[project.optional-dependencies]` section, which includes tools for testing, type checking, linting, and documentation generation.

**Section sources**
- [README.md](file://README.md#L15-L19)
- [pyproject.toml](file://pyproject.toml#L36-L49)
- [CONTRIBUTING.md](file://CONTRIBUTING.md#L20-L22)

## Verifying Installation

After installation, verify that Chunkana was installed correctly and is functioning properly.

### Import Test
Create a simple Python script to test the import:
```python
from chunkana import chunk_markdown
print("Chunkana imported successfully!")
```

If no ImportError is raised, the package is correctly installed.

### Version Verification
Check the installed version of Chunkana:
```python
import chunkana
print(f"Chunkana version: {chunkana.__version__}")
```

This should output "Chunkana version: 0.1.2", matching the version in `src/chunkana/__init__.py`.

### Basic Functionality Test
Run a quick test to verify core functionality:
```python
from chunkana import chunk_markdown

text = "# Test Document\n\nThis is a test paragraph."
chunks = chunk_markdown(text)

for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: {chunk.content.strip()}")
```

This test should successfully chunk the simple Markdown text and print the results.

### Diagnostic Commands
Run these diagnostic commands to verify the installation:
```bash
# Check if chunkana is listed in installed packages
pip show chunkana

# List all files installed by chunkana
pip show -f chunkana
```

The `pip show chunkana` command should display package information including name, version, summary, and location.

**Section sources**
- [README.md](file://README.md#L23-L46)
- [src/chunkana/__init__.py](file://src/chunkana/__init__.py#L1-L116)

## Virtual Environment Best Practices

Using virtual environments is strongly recommended when working with Chunkana to avoid dependency conflicts.

### Creating a Virtual Environment
Create a new virtual environment using Python's built-in venv module:
```bash
python -m venv chunkana-env
```

### Activating the Virtual Environment
Activate the virtual environment based on your operating system:

**On Windows:**
```bash
chunkana-env\Scripts\activate
```

**On macOS and Linux:**
```bash
source chunkana-env/bin/activate
```

When activated, your command prompt will show the environment name in parentheses.

### Installing Chunkana in the Virtual Environment
With the virtual environment activated, install Chunkana:
```bash
pip install chunkana
```

### Deactivating the Virtual Environment
When finished working, deactivate the environment:
```bash
deactivate
```

### Using the Makefile for Environment Management
The project includes a Makefile with convenient commands for environment setup:
```bash
# Create virtual environment
make venv

# Install chunkana in editable mode
make install

# Install with development dependencies
make install-dev
```

These commands are defined in the Makefile and automate the virtual environment creation and package installation process.

**Section sources**
- [CONTRIBUTING.md](file://CONTRIBUTING.md#L13-L22)
- [Makefile](file://Makefile#L1-L117)

## Integration with Poetry and pipenv

Chunkana can be integrated with modern Python dependency management tools like Poetry and pipenv.

### Poetry Integration
To use Chunkana with Poetry, add it to your `pyproject.toml` file:

```toml
[tool.poetry.dependencies]
python = "^3.12"
chunkana = "^0.1.2"
```

Then install the dependencies:
```bash
poetry install
```

For development dependencies, add them to the `[tool.poetry.group.dev.dependencies]` section:
```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
mypy = "^1.0"
ruff = "^0.1"
```

### pipenv Integration
To use Chunkana with pipenv, add it to your Pipfile:

```toml
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
chunkana = ">=0.1.2"

[dev-packages]
pytest = "*"
mypy = "*"
ruff = "*"

[requires]
python_version = "3.12"
```

Install the packages:
```bash
pipenv install
```

For development dependencies:
```bash
pipenv install --dev
```

### Comparison of Package Management Approaches

| Method | Pros | Cons |
|--------|------|------|
| pip + venv | Simple, built into Python | Manual dependency management |
| Poetry | Modern, lock file support, dependency resolution | Additional tool to install |
| pipenv | Combines pip and virtualenv | Can be slower than alternatives |

The choice of package manager depends on your project requirements and team preferences. For new projects, Poetry is recommended for its modern features and reliable dependency resolution.

**Section sources**
- [pyproject.toml](file://pyproject.toml#L1-L94)
- [Makefile](file://Makefile#L1-L117)

## Configuration Prerequisites

Before using Chunkana in production, understand the configuration prerequisites and options.

### Core Configuration Parameters
Chunkana uses `ChunkerConfig` to control chunking behavior. Key parameters include:

- `max_chunk_size`: Maximum chunk size in characters (default: 4096)
- `min_chunk_size`: Minimum chunk size (default: 512)
- `overlap_size`: Context overlap between chunks (default: 200)
- `preserve_atomic_blocks`: Keep code blocks, tables, LaTeX intact (default: True)

### Strategy Selection Thresholds
Chunkana automatically selects the optimal chunking strategy based on content analysis:

- `code_threshold`: Code ratio threshold for CodeAware strategy (default: 0.3)
- `structure_threshold`: Minimum headers for Structural strategy (default: 3)
- `list_ratio_threshold`: List content ratio for ListAware strategy (default: 0.4)

### Advanced Configuration Options
For specialized use cases, Chunkana provides advanced configuration:

- `use_adaptive_sizing`: Enable adaptive chunk sizing based on content
- `group_related_tables`: Group related tables together
- `preserve_latex_blocks`: Keep LaTeX blocks intact
- `overlap_cap_ratio`: Maximum overlap as fraction of chunk size

Configuration details are documented in the `docs/config.md` file, which provides comprehensive guidance on all available options and their use cases.

**Section sources**
- [docs/config.md](file://docs/config.md#L1-L172)
- [README.md](file://README.md#L50-L60)

## Post-Installation Steps

After successfully installing Chunkana, perform these post-installation steps to ensure optimal setup.

### Running Diagnostic Tests
Verify the installation by running the test suite:
```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test category
pytest tests/unit/
```

The Makefile provides convenient commands for running tests, which helps verify that all components are working correctly.

### Setting Up Development Environment
For development work, set up the complete development environment:
```bash
# Install with development dependencies
make install-dev

# Run all checks (linting, type checking, tests)
make check
```

This installs all development tools including pytest, mypy, and ruff, enabling comprehensive code quality checks.

### Exploring Documentation
Familiarize yourself with the available documentation:
- [Quick Start](docs/quickstart.md): Get started quickly
- [Configuration Guide](docs/config.md): Detailed configuration options
- [Strategies](docs/strategies.md): How chunking strategies work
- [Renderers](docs/renderers.md): Output formatting options
- [Migration Guide](MIGRATION_GUIDE.md): Migrating from dify-markdown-chunker

### Performance Benchmarking
For production deployment, understand the performance characteristics:
- Small documents (~100 lines): ~0.1ms processing time
- Medium documents (~1000 lines): ~0.7ms processing time
- Large documents (~10000 lines): ~2.7ms processing time

These benchmarks help in capacity planning and performance optimization.

**Section sources**
- [Makefile](file://Makefile#L1-L117)
- [CONTRIBUTING.md](file://CONTRIBUTING.md#L42-L54)
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L482-L485)

## Common Installation Issues

This section addresses common installation issues and their solutions.

### Dependency Conflicts
When Chunkana conflicts with existing packages:

**Symptom:** `ResolutionImpossible` error during installation
**Solution:** Use a virtual environment to isolate dependencies
```bash
python -m venv clean-env
source clean-env/bin/activate  # On Windows: clean-env\Scripts\activate
pip install chunkana
```

### Platform-Specific Compilation Errors
Although Chunkana has no C extensions, you might encounter platform-specific issues:

**On Windows:** Permission errors when installing
**Solution:** Run command prompt as administrator or use user site-packages
```bash
pip install --user chunkana
```

**On Linux/macOS:** Permission errors
**Solution:** Use virtual environment instead of system-wide installation
```bash
python -m venv myproject-env
source myproject-env/bin/activate
pip install chunkana
```

### Permission Problems
When you lack write permissions to the Python installation directory:

**Solution 1:** Use the `--user` flag to install in user directory
```bash
pip install --user chunkana
```

**Solution 2:** Use a virtual environment (recommended)
```bash
python -m venv myenv
source myenv/bin/activate
pip install chunkana
```

**Solution 3:** Use pipx for isolated application installation
```bash
pipx install chunkana
```

### Network Issues
When behind a corporate firewall or proxy:

**Solution:** Configure pip to use your proxy
```bash
pip install --proxy http://user:password@proxy.company.com:8080 chunkana
```

Or set environment variables:
```bash
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=https://proxy.company.com:8080
pip install chunkana
```

### Outdated pip Version
When installation fails due to old pip version:

**Symptom:** `ERROR: Could not find a version that satisfies the requirement`
**Solution:** Upgrade pip first
```bash
python -m pip install --upgrade pip
pip install chunkana
```

**Section sources**
- [CONTRIBUTING.md](file://CONTRIBUTING.md#L85-L90)
- [Makefile](file://Makefile#L1-L117)

## Troubleshooting Guide

This section provides guidance for troubleshooting common issues after installation.

### Import Errors
When you cannot import Chunkana modules:

**Symptom:** `ModuleNotFoundError: No module named 'chunkana'`
**Diagnosis steps:**
1. Verify the virtual environment is activated
2. Check if chunkana is listed in installed packages: `pip list | grep chunkana`
3. Verify Python path: `python -c "import sys; print(sys.path)"`

**Solutions:**
- Ensure the virtual environment is activated
- Reinstall chunkana: `pip uninstall chunkana && pip install chunkana`
- Check for multiple Python installations and ensure pip matches your Python version

### Missing Modules
When specific submodules cannot be imported:

**Symptom:** `ImportError: cannot import name 'chunk_hierarchical' from 'chunkana'`
**Solution:** Verify the module structure by checking `src/chunkana/__init__.py`, which exports all public APIs. Ensure you're using the correct import paths as documented in the README.

### Configuration Errors
When encountering configuration-related exceptions:

**Symptom:** `ConfigurationError` with messages about invalid parameters
**Solution:** Validate configuration parameters:
- `max_chunk_size` must be positive
- `min_chunk_size` must be positive
- `overlap_size` must be non-negative
- `code_threshold` must be between 0 and 1

Refer to the property-based tests in `tests/property/test_roundtrip.py` for valid parameter ranges.

### Hierarchical Invariant Errors
When using hierarchical chunking:

**Symptom:** `HierarchicalInvariantError` exceptions
**Solutions:**
- Set `strict_mode=False` to enable auto-fixing of violations
- Disable validation with `validate_invariants=False` for performance
- Check for corrupted input documents with malformed headers

Enable strict mode temporarily for debugging:
```python
config = ChunkConfig(
    validate_invariants=True,
    strict_mode=True,  # Raises exceptions instead of auto-fixing
)
```

### Performance Issues
When chunking is slow for large documents:

**Solutions:**
- Disable tree validation for performance-critical paths: `validate_invariants=False`
- Adjust chunk sizes to reduce the number of chunks
- Use streaming for very large files (>10MB)

Monitor performance using the benchmarks provided in the migration guide.

**Section sources**
- [src/chunkana/__init__.py](file://src/chunkana/__init__.py#L1-L116)
- [README.md](file://README.md#L94-L111)
- [MIGRATION_GUIDE.md](file://MIGRATION_GUIDE.md#L471-L480)
- [tests/property/test_roundtrip.py](file://tests/property/test_roundtrip.py#L320-L356)