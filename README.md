# CivicAI

Multi-Agent Civic Policy Discovery and Engagement Platform

## Overview

CivicAI is a sophisticated multi-agent system that enables intelligent policy discovery and civic engagement across multiple levels of government. Using CrewAI framework and Exa API, it provides stakeholder-aware policy analysis for informed civic participation.

## Quick Start

### Prerequisites

Install [UV](https://docs.astral.sh/uv/) - the fast Python package manager:

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd CivicAI

# Install dependencies with UV
uv sync

# Install with development dependencies
uv sync --extra dev

# Or use pip (fallback)
pip install -e .
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your Exa API key:
```bash
EXA_API_KEY=your_exa_api_key_here
```

### Quick Test

```bash
# Run the policy discovery example
uv run python policy_discovery/example.py

# Or with make
make run-example
```

## Features

- **Multi-Level Government Search**: Federal, State (California), Local (San Francisco)
- **Intelligent Policy Classification**: Automated domain and stakeholder impact analysis
- **Real-time Discovery**: Up-to-date policy information from government sources
- **Stakeholder-Aware**: Personalized policy relevance based on user roles
- **Multi-Agent Architecture**: Scalable CrewAI-based design

## Development

### Available Commands

```bash
# View all commands
make help

# Development setup
make dev-setup

# Run tests and quality checks
make test
make lint
make type-check
make check        # Run all checks

# Format code
make format

# Clean up
make clean
```

### Project Structure

- `policy_discovery/` - Core policy discovery module
- `pyproject.toml` - UV project configuration
- `Makefile` - Development automation
- `uv.lock` - Dependency lock file

## Contributing

1. Set up development environment: `make dev-setup`
2. Make your changes
3. Run quality checks: `make check`
4. Submit a pull request

## License

This project is part of the CivicAI platform for enhancing civic engagement through AI-powered policy discovery and analysis.
