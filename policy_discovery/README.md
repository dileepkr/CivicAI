# Policy Discovery Agent

A sophisticated CrewAI-based agent for discovering relevant government policies across multiple jurisdictional levels using the Exa API.

## Features

- **Multi-Level Government Search**: Discovers policies at Federal, State (California), and Local (San Francisco) levels
- **Intelligent Categorization**: Automatically classifies policies by domain (Housing, Labor, Public Safety, etc.)
- **Stakeholder-Aware**: Maps policy impacts to specific stakeholder groups (renters, business owners, employees, etc.)
- **Context-Driven Search**: Generates targeted queries based on user location, roles, and interests
- **Real-time Discovery**: Uses Exa API for up-to-date policy information from government sources

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

#### Option 1: Using UV (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd CivicAI

# Install dependencies
uv sync

# Install with development dependencies
uv sync --extra dev

# Install all optional dependencies
uv sync --extra all
```

#### Option 2: Using pip (Fallback)

```bash
# Install the package
pip install -e .

# Install with development dependencies
pip install -e .[dev]
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your Exa API key:
```bash
EXA_API_KEY=your_exa_api_key_here
```

### Basic Usage

#### Running with UV

```bash
# Run the example script
uv run python policy_discovery/example.py

# Or run individual commands
uv run python -c "
import asyncio
from policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain

async def main():
    agent = PolicyDiscoveryAgent()
    context = UserContext(
        location='San Francisco, CA',
        stakeholder_roles=['renter', 'employee'],
        interests=['rent control', 'tenant rights']
    )
    results = await agent.discover_policies(
        user_context=context,
        domains=[PolicyDomain.HOUSING]
    )
    for policy in results.priority_ranking[:5]:
        print(f'{policy.title} ({policy.government_level.value})')

asyncio.run(main())
"
```

#### Python Code Usage

```python
import asyncio
from policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain

async def main():
    # Initialize agent
    agent = PolicyDiscoveryAgent()
    
    # Define user context
    context = UserContext(
        location="San Francisco, CA",
        stakeholder_roles=["renter", "employee"],
        interests=["rent control", "tenant rights"]
    )
    
    # Discover policies
    results = await agent.discover_policies(
        user_context=context,
        domains=[PolicyDomain.HOUSING]
    )
    
    # Display results
    for policy in results.priority_ranking[:5]:
        print(f"{policy.title} ({policy.government_level.value})")
        print(f"URL: {policy.url}")
        print(f"Summary: {policy.summary}\n")

asyncio.run(main())
```

## Architecture

### Core Components

- **PolicyDiscoveryAgent**: Main CrewAI agent orchestrating policy discovery
- **PolicySearchEngine**: Exa API integration for government content search
- **PolicyClassifier**: ML-based classification for domains and status
- **StakeholderAnalyzer**: Impact analysis for different user groups

### Data Models

- **PolicyResult**: Complete policy information with metadata
- **UserContext**: User's location, roles, and interests
- **PolicyDomain**: Housing, Labor, Public Safety, Environment, Transportation, Business
- **GovernmentLevel**: Federal, State, Local

## Government Sources

### Federal Level
- congress.gov (legislation)
- regulations.gov (federal regulations)
- federalregister.gov (federal register)

### State Level (California)
- ca.gov (official state website)
- leginfo.legislature.ca.gov (legislative information)

### Local Level (San Francisco)
- sf.gov (city and county website)
- sfgov.org (city services)
- sfdph.org (public health)

## Policy Domains

- **Housing**: Rent control, zoning, tenant rights, affordable housing
- **Labor**: Worker classification, minimum wage, benefits, employment law
- **Public Safety**: Policing, community safety, emergency services
- **Environment**: Climate policies, pollution control, sustainability
- **Transportation**: Transit, parking, infrastructure
- **Business**: Licensing, regulations, taxation, permits

## Stakeholder Roles

- **Renter**: Tenant rights, housing costs, eviction protection
- **Homeowner**: Property taxes, zoning, property rights
- **Employee**: Wages, benefits, working conditions
- **Business Owner**: Licensing, regulations, tax obligations
- **Student**: Education policies, transportation, housing
- **Parent**: Family benefits, education, childcare
- **Senior**: Healthcare, social security, senior services
- **Immigrant**: Immigration law, citizenship, services

## Search Strategy

### Query Generation
- Domain-specific keywords
- Stakeholder role terminology
- Geographic qualifiers
- Government level indicators

### Result Processing
- Content classification
- Stakeholder impact analysis
- Relevance scoring
- Related policy discovery

### Caching
- 24-hour TTL for policy results
- Rate limiting for API calls
- Intelligent cache invalidation

## Integration with CivicAI

The Policy Discovery Agent is designed to integrate seamlessly with the broader CivicAI multi-agent system:

- **Orchestration Agent**: Receives comprehensive policy contexts
- **Research Agent**: Provides detailed policy background
- **Debate Agents**: Uses policy data for informed discussions

## Examples

See `example.py` for comprehensive usage examples including:
- Renter housing policy search
- Business owner labor policy discovery
- Multi-domain civic engagement scenarios

## Performance

- **Search Speed**: 2-5 seconds for comprehensive multi-level search
- **Rate Limits**: 60 API calls per minute with intelligent throttling
- **Result Quality**: Government source prioritization with confidence scoring
- **Scalability**: Concurrent search execution across government levels

## Error Handling

- Graceful API failure recovery
- Fallback search strategies
- Comprehensive logging
- Data validation and sanitization

## Development

### Development Setup

```bash
# Set up development environment
make dev-setup

# Or manually:
uv sync --extra dev
uv run pre-commit install
```

### Available Commands

#### Using Make (Recommended)

```bash
# View all available commands
make help

# Install dependencies
make install          # Production dependencies
make install-dev      # Development dependencies

# Development workflow
make test             # Run tests
make lint             # Run linting
make format           # Format code
make type-check       # Run type checking
make check            # Run all quality checks

# Usage
make run-example      # Run example script
make clean            # Clean cache files
```

#### Using UV directly

```bash
# Running Tests
uv run pytest tests/ -v

# Code Quality
uv run black policy_discovery/ tests/
uv run ruff check policy_discovery/
uv run mypy policy_discovery/

# Running the example
uv run python policy_discovery/example.py
```

### Project Structure

```
CivicAI/
├── pyproject.toml          # UV project configuration
├── uv.lock                 # Dependency lock file
├── Makefile               # Development commands
├── .uvignore              # UV ignore patterns
├── requirements.txt       # Pip compatibility
├── policy_discovery/      # Main package
│   ├── __init__.py
│   ├── agent.py          # Core PolicyDiscoveryAgent
│   ├── search.py         # Exa API integration
│   ├── models.py         # Data models
│   ├── utils.py          # Classification utilities
│   ├── config.py         # Configuration
│   ├── example.py        # Usage examples
│   └── README.md
└── tests/                # Test suite
```

### Adding New Government Sources
1. Update `GOVERNMENT_DOMAINS` in `config.py`
2. Add domain-specific search logic in `search.py`
3. Update classification patterns if needed

## License

This project is part of the CivicAI platform for enhancing civic engagement through AI-powered policy discovery and analysis.