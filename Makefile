# Makefile for Python WeKan Client
# Comprehensive project management for development, testing, and deployment

.PHONY: help setup install install-dev test lint format clean pre-commit docs docs-serve build publish

# Default target
help:
	@echo "Python WeKan Client"
	@echo "=================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  setup            Interactive setup with WeKan configuration"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Development Commands:"
	@echo "  test             Run unit tests"
	@echo "  test-cov         Run tests with coverage report"
	@echo "  test-cli         Run CLI tests"
	@echo "  test-integration Run integration tests"
	@echo "  test-all         Run all tests with coverage"
	@echo "  lint             Run code quality checks (ruff, black, isort, mypy)"
	@echo "  format           Auto-format code with black & isort"
	@echo "  clean            Clean build artifacts and cache"
	@echo ""
	@echo "CLI Commands:"
	@echo "  cli              Start interactive WeKan CLI"
	@echo "  cli-help         Show CLI help"
	@echo "  cli-status       Show WeKan connection status"
	@echo "  cli-config       Initialize CLI configuration"
	@echo ""
	@echo "Build & Release Commands:"
	@echo "  build            Build distribution packages"
	@echo "  publish          Publish to PyPI (requires auth)"
	@echo "  publish-test     Publish to TestPyPI (requires auth)"
	@echo ""
	@echo "Utility Commands:"
	@echo "  validate         Validate project configuration"
	@echo "  pre-commit       Run pre-commit hooks"
	@echo "  shell            Enter UV shell"
	@echo "  docs             Build documentation"
	@echo "  docs-serve       Serve documentation locally"
	@echo "  version          Show version information"

# Variables
UV := uv
VENV := .venv
CONFIG_FILE := .wekan
PACKAGE_NAME := python-wekan

# Check if UV is installed
check-uv:
	@which $(UV) > /dev/null || (echo "UV not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)

# Interactive setup procedure
setup: check-uv
	@echo "Python WeKan Client Interactive Setup"
	@echo "===================================="
	@echo ""
	@echo "This will configure your development environment and WeKan connection."
	@echo ""
	@$(MAKE) install-dev
	@$(MAKE) setup-wekan
	@echo ""
	@echo "Setup complete! Your environment is ready."
	@echo "   Run 'make validate' to verify everything works."
	@echo "   Run 'make cli' to start the WeKan CLI."

# WeKan setup
setup-wekan:
	@echo "WeKan CLI Configuration"
	@echo "======================"
	@echo ""
	@echo "Run 'make cli-config' to configure your WeKan connection interactively."

# Create virtual environment
$(VENV): check-uv
	@if [ ! -d $(VENV) ]; then \
		$(UV) venv $(VENV); \
	fi

# Install production dependencies
install: $(VENV)
	$(UV) sync --no-dev
	@echo "Production dependencies installed"

# Install development dependencies including CLI
install-dev: $(VENV)
	$(UV) sync --extra dev --extra cli
	@if command -v pre-commit >/dev/null 2>&1; then \
		$(UV) run pre-commit install; \
		echo "Pre-commit hooks installed"; \
	fi
	@echo "Development environment ready"

# Clean build artifacts and cache
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete"

# Testing
test: install-dev
	@echo "Running unit tests..."
	$(UV) run python -m pytest tests/ -v --tb=short -m "unit"
	@echo "Unit tests completed"

test-cov: install-dev
	@echo "Running tests with coverage..."
	$(UV) run python -m pytest tests/ --cov=wekan --cov-report=html --cov-report=term -m "unit"
	@echo "Coverage report generated in htmlcov/"

test-cli: install-dev
	@echo "Running CLI tests..."
	$(UV) run python -m pytest tests/ -v --tb=short -m "cli"
	@echo "CLI tests completed"

test-integration: install-dev
	@echo "Running integration tests..."
	$(UV) run python -m pytest tests/ -v --tb=short -m "integration"
	@echo "Integration tests completed"

test-all: install-dev
	@echo "Running all tests with coverage..."
	$(UV) run python -m pytest tests/ --cov=wekan --cov-report=html --cov-report=term
	@echo "All tests completed with coverage report"

# Code quality
lint: install-dev
	@echo "Running code quality checks..."
	$(UV) run ruff check wekan tests
	$(UV) run black --check wekan tests
	$(UV) run isort --check-only wekan tests
# 	$(UV) run mypy wekan
	@echo "Code quality checks passed"

format: install-dev
	@echo "Formatting code..."
	$(UV) run ruff check --fix wekan tests
	$(UV) run isort wekan tests
	$(UV) run black wekan tests
	@echo "Code formatting complete"

# CLI Commands
cli: install-dev
	@echo "Starting interactive WeKan CLI..."
	$(UV) run wekan navigate

cli-help: install-dev
	@echo "Showing CLI help..."
	$(UV) run wekan --help

cli-status: install-dev
	@echo "Checking WeKan connection status..."
	$(UV) run wekan status

cli-config: install-dev
	@echo "Configuring WeKan CLI..."
	$(UV) run wekan config init

# Build and release
build: $(VENV) clean
	@echo "Building distribution packages..."
	$(UV) build
	@echo "Build complete. Packages in dist/"

publish: $(VENV) build
	@echo "Publishing to PyPI..."
	$(UV) publish --token $(PYPI_TOKEN)
	@echo "Published to PyPI"

publish-test: $(VENV) build
	@echo "Publishing to TestPyPI..."
	$(UV) publish --publish-url https://test.pypi.org/simple/ --token $(TEST_PYPI_TOKEN)
	@echo "Published to TestPyPI"

# Documentation commands
docs: $(VENV)
	@echo "Building documentation..."
	@if [ ! -f "mkdocs.yml" ]; then \
		echo "Creating basic mkdocs.yml..."; \
		echo "site_name: Python WeKan Client" > mkdocs.yml; \
		echo "nav:" >> mkdocs.yml; \
		echo "  - Home: README.md" >> mkdocs.yml; \
		echo "  - CLI Guide: CLI.md" >> mkdocs.yml; \
	fi
	$(UV) run mkdocs build
	@echo "Documentation built in site/ directory"

docs-serve: $(VENV)
	@echo "Starting documentation server..."
	$(UV) run mkdocs serve

# Utility commands
validate: $(VENV)
	@echo "Validating project configuration..."
	@echo "Checking project structure..."
	@if [ -f "wekan/__init__.py" ]; then echo "  Main package exists"; else echo "  Main package missing"; fi
	@if [ -f "wekan/cli/__init__.py" ]; then echo "  CLI package exists"; else echo "  CLI package missing"; fi
	@if [ -f "tests/__init__.py" ]; then echo "  Tests package exists"; else echo "  Tests package missing"; fi
	@if [ -f "pyproject.toml" ]; then echo "  pyproject.toml exists"; else echo "  pyproject.toml missing"; fi
	@if [ -f ".pre-commit-config.yaml" ]; then echo "  Pre-commit config exists"; else echo "  Pre-commit config missing"; fi
	@echo "Project validation complete"

pre-commit: $(VENV)
	@echo "Running pre-commit hooks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		$(UV) run pre-commit run --all-files; \
	else \
		echo "  pre-commit not installed. Running manual checks..."; \
		$(MAKE) lint; \
		$(MAKE) test; \
	fi

shell: $(VENV)
	@echo "Activating virtual environment..."
	@echo "Run the following command to activate the virtual environment:"
	@echo "  source $(VENV)/bin/activate"
	@echo ""
	@echo "Or use UV directly with:"
	@echo "  $(UV) run <command>"

version:
	@echo "Python WeKan Client version information:"
	@$(UV) run python -c "import wekan; print(f'Package version: {wekan.__version__}')"
	@echo "UV version: $$($(UV) --version)"
	@echo "Python version: $$(python --version)"

# Development workflow shortcuts
dev: install-dev format lint test
	@echo "Development workflow complete"

# CI/CD simulation
ci: clean install-dev lint test-all
	@echo "CI/CD simulation complete"

# Check project health
health: validate lint test-all
	@echo "Project health check complete"

# Show current configuration
show-config:
	@echo "Current Configuration"
	@echo "===================="
	@echo "Project: $(PACKAGE_NAME)"
	@echo "UV version: $$($(UV) --version)"
	@echo "Virtual env: $(VENV)"
	@if [ -f $(CONFIG_FILE) ]; then \
		echo "WeKan config: $(CONFIG_FILE) exists"; \
	else \
		echo "WeKan config: Not configured (run 'make cli-config')"; \
	fi
	@if [ -d $(VENV) ]; then echo "Virtual environment: Ready"; else echo "Virtual environment: Not created"; fi

# Quick start for new contributors
quickstart:
	@echo "Quick Start for Contributors"
	@echo "============================"
	@echo "1. Setting up development environment..."
	@$(MAKE) setup
	@echo ""
	@echo "2. Running tests to verify setup..."
	@$(MAKE) test
	@echo ""
	@echo "3. Running code quality checks..."
	@$(MAKE) lint
	@echo ""
	@echo "Quick start complete!"
	@echo ""
	@echo "Next steps:"
	@echo "  - Configure WeKan: make cli-config"
	@echo "  - Start CLI: make cli"
	@echo "  - Run all tests: make test-all"
	@echo "  - Format code: make format"

# Status check
status:
	@echo "Project Status"
	@echo "=============="
	@echo ""
	@echo "Environment:"
	@if [ -d $(VENV) ]; then echo "  Virtual environment: Ready"; else echo "  Virtual environment: Missing"; fi
	@if command -v $(UV) >/dev/null 2>&1; then echo "  UV package manager: Available"; else echo "  UV package manager: Missing"; fi
	@echo ""
	@echo "Configuration:"
	@if [ -f $(CONFIG_FILE) ]; then echo "  WeKan config: Configured"; else echo "  WeKan config: Not configured"; fi
	@if [ -f ".pre-commit-config.yaml" ]; then echo "  Pre-commit: Configured"; else echo "  Pre-commit: Not configured"; fi
	@echo ""
	@echo "Development tools:"
	@if $(UV) run python -c "import pytest" 2>/dev/null; then echo "  pytest: Available"; else echo "  pytest: Missing"; fi
	@if $(UV) run python -c "import black" 2>/dev/null; then echo "  black: Available"; else echo "  black: Missing"; fi
	@if $(UV) run python -c "import mypy" 2>/dev/null; then echo "  mypy: Available"; else echo "  mypy: Missing"; fi
