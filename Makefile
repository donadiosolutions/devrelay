.PHONY: help venv install dev test format lint lintmd typecheck check clean run

# Variables
PYTHON := python3.13
VENV := .venv
UV := uv
VENV_PYTHON := $(VENV)/bin/python
VENV_UV := $(VENV)/bin/uv

# Default target
help:
	@echo "Available targets:"
	@echo "  venv       - Create virtual environment"
	@echo "  install    - Install production dependencies"
	@echo "  dev        - Install development dependencies and pre-commit hooks"
	@echo "  test       - Run tests with coverage"
	@echo "  format     - Format code with black"
	@echo "  lint       - Lint code with flake8"
	@echo "  lintmd     - Lint markdown files with pymarkdownlnt"
	@echo "  typecheck  - Type check with pyright"
	@echo "  check      - Run all checks (format, lint, lintmd, typecheck, test)"
	@echo "  run        - Run the devrelay proxy"
	@echo "  clean      - Remove virtual environment and cache files"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		$(UV) venv $(VENV) --python $(PYTHON); \
	else \
		echo "Virtual environment already exists"; \
	fi

# Install production dependencies
install: venv
	@echo "Installing production dependencies..."
	@$(UV) pip install --python $(VENV_PYTHON) -e .

# Install development dependencies
dev: venv
	@echo "Installing development dependencies..."
	@$(UV) pip install --python $(VENV_PYTHON) -e ".[dev]"
	@echo "Installing pre-commit hooks..."
	@$(VENV)/bin/pre-commit install

# Run tests with coverage
test: dev
	@echo "Running tests with coverage..."
	@$(VENV)/bin/pytest

# Format code with black
format: dev
	@echo "Formatting code with black..."
	@$(VENV)/bin/black devrelay tests

# Lint code with flake8
lint: dev
	@echo "Linting code with flake8..."
	@$(VENV)/bin/flake8 devrelay tests --max-line-length=120 --extend-ignore=E203,W503

# Lint markdown files with pymarkdownlnt
lintmd: dev
	@echo "Linting markdown files with pymarkdownlnt..."
	@$(VENV)/bin/pymarkdown --config .pymarkdown.json scan *.md

# Type check with pyright
typecheck: dev
	@echo "Type checking with pyright..."
	@$(VENV)/bin/pyright

# Run all checks
check: format lint lintmd typecheck test
	@echo "All checks passed!"

# Run the devrelay proxy
run: install
	@$(VENV)/bin/devrelay

# Clean up
clean:
	@echo "Cleaning up..."
	@rm -rf $(VENV)
	@rm -rf __pycache__ .pytest_cache .coverage htmlcov
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"
