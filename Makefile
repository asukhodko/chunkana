# Chunkana Makefile
# Development workflow automation

.PHONY: help venv install install-dev clean test lint typecheck format build check all baseline

PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
VENV_PYTHON := $(VENV_BIN)/python
VENV_PIP := $(VENV_BIN)/pip
VENV_TWINE := $(VENV_BIN)/twine

# Default target
help:
	@echo "Chunkana Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make venv        - Create virtual environment"
	@echo "  make install     - Install package in editable mode"
	@echo "  make install-dev - Install with dev dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linter (ruff)"
	@echo "  make typecheck   - Run type checker (mypy)"
	@echo "  make format      - Format code (ruff)"
	@echo "  make check       - Run all checks (lint + typecheck + test)"
	@echo ""
	@echo "Build:"
	@echo "  make build       - Build package"
	@echo "  make baseline    - Generate baseline golden outputs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean       - Remove build artifacts"
	@echo "  make clean-all   - Remove venv and all artifacts"

# Create virtual environment
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install --upgrade pip
	@echo ""
	@echo "Virtual environment created. Activate with:"
	@echo "  source $(VENV)/bin/activate"

# Install package in editable mode
install: venv
	@echo "Installing chunkana..."
	$(VENV_PIP) install -e .

# Install with dev dependencies
install-dev: venv
	@echo "Installing chunkana with dev dependencies..."
	$(VENV_PIP) install -e ".[dev]"

# Run tests
test:
	@echo "Running tests..."
	$(VENV_BIN)/pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	$(VENV_BIN)/pytest tests/ -v --cov=chunkana --cov-report=term-missing

# Run linter
lint:
	@echo "Running linter..."
	$(VENV_BIN)/ruff check .

# Run type checker
typecheck:
	@echo "Running type checker..."
	$(VENV_BIN)/mypy src/chunkana

# Format code
format:
	@echo "Formatting code..."
	$(VENV_BIN)/ruff format .
	$(VENV_BIN)/ruff check --fix .

# Run all checks
check: lint typecheck test-cov

# Build package
build:
	@echo "Building package..."
	$(VENV_PYTHON) -m build
	$(VENV_BIN)/twine check dist/*

# Generate baseline golden outputs
baseline:
	@echo "Generating baseline golden outputs..."
	$(VENV_PYTHON) scripts/generate_baseline.py

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf src/*.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Clean everything including venv
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV)

# Full setup from scratch
all: clean-all install-dev test
	@echo "Setup complete!"

upload-test:
	$(VENV_TWINE) upload --repository testpypi dist/*

upload:
	$(VENV_TWINE) upload dist/*
