# Makefile for CivicAI Policy Discovery project with UV support

.PHONY: help install install-dev sync lock clean test lint format type-check run-example run-webset-example init-websets setup-monitoring webset-status docs build

# Default target
help:
	@echo "CivicAI Policy Discovery - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install         Install production dependencies using UV"
	@echo "  install-dev     Install development dependencies using UV"
	@echo "  sync            Sync dependencies from lock file"
	@echo "  lock            Update dependency lock file"
	@echo ""
	@echo "Development:"
	@echo "  test            Run tests with pytest"
	@echo "  lint            Run linting with ruff"
	@echo "  format          Format code with black and ruff"
	@echo "  type-check      Run type checking with mypy"
	@echo "  clean           Clean cache and build artifacts"
	@echo ""
	@echo "Usage:"
	@echo "  run-example     Run the basic policy discovery example"
	@echo "  run-webset-example  Run the hybrid webset + search example"
	@echo ""
	@echo "Webset Management:"
	@echo "  init-websets    Initialize policy websets for structured collection"
	@echo "  setup-monitoring Set up automated policy monitoring"
	@echo "  webset-status   Check status of all managed websets"
	@echo ""
	@echo "Documentation & Build:"
	@echo "  docs            Generate documentation"
	@echo "  build           Build the package"

# Installation commands
install:
	uv sync --no-dev

install-dev:
	uv sync --extra dev

sync:
	uv sync

lock:
	uv lock

# Development commands
test:
	@if [ -d "tests/" ]; then uv run pytest tests/ -v; else echo "Tests directory not found, skipping tests"; fi

test-cov:
	@if [ -d "tests/" ]; then uv run pytest tests/ --cov=policy_discovery --cov-report=html --cov-report=term; else echo "Tests directory not found, skipping coverage"; fi

lint:
	uv run ruff check policy_discovery/
	uv run ruff check tests/ || true

format:
	uv run black policy_discovery/
	uv run ruff format policy_discovery/
	@if [ -d "tests/" ]; then uv run black tests/ && uv run ruff format tests/; fi

type-check:
	uv run mypy policy_discovery/

# Quality checks (run all)
check: lint type-check test

# Usage commands
run-example:
	uv run python policy_discovery/example.py

run-webset-example:
	uv run python policy_discovery/webset_example.py

# Webset management commands
init-websets:
	uv run python -c "import asyncio; from policy_discovery import PolicyDiscoveryAgent; agent = PolicyDiscoveryAgent(); asyncio.run(agent.initialize_websets())"

setup-monitoring:
	uv run python -c "import asyncio; from policy_discovery import PolicyDiscoveryAgent; agent = PolicyDiscoveryAgent(); asyncio.run(agent.setup_policy_monitoring())"

webset-status:
	uv run python -c "import asyncio; from policy_discovery import PolicyDiscoveryAgent; agent = PolicyDiscoveryAgent(); print(asyncio.run(agent.get_webset_status()))"

# Documentation
docs:
	uv run mkdocs serve

docs-build:
	uv run mkdocs build

# Build
build:
	uv build

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage

# Environment management
create-env:
	uv venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

# Pre-commit setup
pre-commit-install:
	uv run pre-commit install

pre-commit-run:
	uv run pre-commit run --all-files

# Development workflow shortcuts
dev-setup: install-dev pre-commit-install
	@echo "Development environment set up successfully!"

quick-check: format lint type-check
	@echo "Quick checks completed!"

# CI/CD related
ci-test: install-dev test-cov lint type-check
	@echo "CI tests completed!"

# Version management
version-patch:
	uv run python -c "import toml; data=toml.load('pyproject.toml'); v=data['project']['version'].split('.'); v[2]=str(int(v[2])+1); data['project']['version']='.'.join(v); toml.dump(data, open('pyproject.toml', 'w'))"

version-minor:
	uv run python -c "import toml; data=toml.load('pyproject.toml'); v=data['project']['version'].split('.'); v[1]=str(int(v[1])+1); v[2]='0'; data['project']['version']='.'.join(v); toml.dump(data, open('pyproject.toml', 'w'))"

version-major:
	uv run python -c "import toml; data=toml.load('pyproject.toml'); v=data['project']['version'].split('.'); v[0]=str(int(v[0])+1); v[1]='0'; v[2]='0'; data['project']['version']='.'.join(v); toml.dump(data, open('pyproject.toml', 'w'))"