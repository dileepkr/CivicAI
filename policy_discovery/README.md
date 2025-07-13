# Policy Discovery Agent

A sophisticated CrewAI-based agent for discovering relevant government policies across multiple jurisdictional levels using the Exa API.

## Features

### Core Policy Discovery
- **Multi-Level Government Search**: Discovers policies at Federal, State (California), and Local (San Francisco) levels
- **Intelligent Categorization**: Automatically classifies policies by domain (Housing, Labor, Public Safety, etc.)
- **Stakeholder-Aware**: Maps policy impacts to specific stakeholder groups (renters, business owners, employees, etc.)
- **Context-Driven Search**: Generates targeted queries based on user location, roles, and interests

### Hybrid Architecture (NEW)
- **Structured Collection**: Uses Exa Websets for organized policy repositories with automatic deduplication
- **Real-time Search**: Combines webset data with live search for the most current information
- **Automated Monitoring**: Continuous policy discovery with scheduled webset monitors
- **Enhanced Enrichment**: Extracts structured metadata (dates, stakeholders, status) from policies
- **Quality Scoring**: Advanced relevance ranking combining webset criteria and search confidence

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

### Hybrid Webset + Search Usage

```python
import asyncio
from policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain

async def hybrid_example():
    # Initialize agent
    agent = PolicyDiscoveryAgent()
    
    # One-time setup: Initialize websets for structured collection
    webset_ids = await agent.initialize_websets()
    print(f"Initialized {len(webset_ids)} websets")
    
    # Set up automated monitoring (daily policy updates)
    monitor_ids = await agent.setup_policy_monitoring()
    print(f"Created {len(monitor_ids)} monitors")
    
    # Use hybrid approach for policy discovery
    context = UserContext(
        location="San Francisco, CA",
        stakeholder_roles=["renter"],
        interests=["rent control"]
    )
    
    # Hybrid mode: combines webset data + live search
    results = await agent.discover_policies(
        user_context=context,
        domains=[PolicyDomain.HOUSING],
        use_websets=True  # Enable hybrid mode
    )
    
    print(f"Found {results.total_found} policies")
    print(f"Webset policies: {results.search_metadata['webset_policies_count']}")
    print(f"Live search policies: {results.search_metadata['search_policies_count']}")

asyncio.run(hybrid_example())
```

### Make Commands

```bash
# Run hybrid webset example
make run-webset-example

# Initialize websets (one-time setup)
make init-websets

# Set up automated monitoring
make setup-monitoring

# Check webset status
make webset-status
```

## Architecture

### Core Components

- **PolicyDiscoveryAgent**: Main CrewAI agent orchestrating hybrid policy discovery
- **PolicySearchEngine**: Exa API integration for real-time government content search  
- **WebsetManager**: Exa Websets integration for structured policy collection and monitoring
- **PolicyClassifier**: ML-based classification for domains and status
- **StakeholderAnalyzer**: Impact analysis for different user groups

### Hybrid Architecture Flow

```
User Query → PolicyDiscoveryAgent
    ├── WebsetManager.query_websets() → Structured Policy Collection
    ├── PolicySearchEngine.search_policies() → Real-time Search
    └── Combine & Deduplicate → Ranked Results
```

### Webset Organization

- **Federal Housing**: `federal_housing` - Federal housing policies and HUD regulations
- **State Housing**: `state_housing` - California housing legislation and rent control laws  
- **Local Housing**: `local_housing` - San Francisco housing ordinances and zoning policies
- **Federal Labor**: `federal_labor` - Federal labor laws and NLRB policies
- **State Labor**: `state_labor` - California labor legislation and worker protection laws
- **Local Labor**: `local_labor` - San Francisco labor ordinances and minimum wage policies
- **State General**: `state_general` - General California legislation across all domains

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

## Agent-to-Agent (A2A) Communication Standards

The Policy Discovery Agent supports standardized A2A communication protocols, enabling seamless integration with other AI agents in multi-agent systems.

### A2A Interface Specification

#### Standard Request Format

```python
from policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain, RegulationTiming

# Agent-to-Agent request structure
a2a_request = {
    "agent_id": "requesting_agent_id",
    "request_type": "policy_discovery",
    "user_context": {
        "location": "San Francisco, CA",
        "stakeholder_roles": ["renter", "employee"],
        "interests": ["rent control", "minimum wage"],
        "regulation_timing": "future"  # "current", "future", or "all"
    },
    "search_parameters": {
        "domains": ["housing", "labor"],  # Optional: specific domains
        "government_levels": ["state", "local"],  # Optional: specific levels
        "max_results": 10,  # Optional: result limit
        "include_analysis": True  # Optional: include AI policy analysis
    },
    "output_format": "structured_json"  # "structured_json" or "full_objects"
}
```

#### Standard Response Format

```python
# Agent-to-Agent response structure
a2a_response = {
    "agent_id": "policy_discovery_agent",
    "request_id": "request_123",
    "status": "success",  # "success", "partial", "error"
    "metadata": {
        "search_time": 3.2,
        "total_found": 15,
        "sources_searched": ["federal", "state", "local"],
        "timestamp": "2025-07-13T10:30:00Z"
    },
    "results": {
        "priority_ranking": [...],  # Top ranked policies
        "by_government_level": {
            "federal": [...],
            "state": [...],
            "local": [...]
        },
        "stakeholder_impact_map": {...},
        "policy_analysis": {  # If requested
            "answer": "AI-generated policy analysis",
            "citations": [...]
        }
    }
}
```

### A2A Agent Integration Examples

#### Example 1: Orchestration Agent Integration

```python
class OrchestrationAgent:
    def __init__(self):
        self.policy_agent = PolicyDiscoveryAgent()
    
    async def request_policy_context(self, user_input: str, user_roles: list[str]):
        """Request policy context for debate setup"""
        
        # Prepare A2A request
        request = {
            "agent_id": "orchestration_agent",
            "request_type": "policy_discovery",
            "user_context": {
                "location": self.extract_location(user_input),
                "stakeholder_roles": user_roles,
                "interests": self.extract_interests(user_input),
                "regulation_timing": "all"
            },
            "search_parameters": {
                "max_results": 5,
                "include_analysis": True
            },
            "output_format": "structured_json"
        }
        
        # Execute policy discovery
        context = UserContext(
            location=request["user_context"]["location"],
            stakeholder_roles=request["user_context"]["stakeholder_roles"],
            interests=request["user_context"]["interests"]
        )
        
        results = await self.policy_agent.discover_policies(user_context=context)
        
        # Return standardized A2A response
        return {
            "agent_id": "policy_discovery_agent",
            "status": "success",
            "results": {
                "priority_ranking": [
                    {
                        "title": policy.title,
                        "url": policy.url,
                        "government_level": policy.government_level.value,
                        "domain": policy.domain.value,
                        "summary": policy.summary,
                        "stakeholder_impacts": [
                            {
                                "group": impact.stakeholder_group,
                                "severity": impact.impact_severity.value,
                                "description": impact.description
                            } for impact in policy.stakeholder_impacts
                        ]
                    } for policy in results.priority_ranking[:5]
                ],
                "policy_analysis": results.search_metadata.get("policy_analysis")
            }
        }
```

#### Example 2: Research Agent Integration

```python
class ResearchAgent:
    def __init__(self):
        self.policy_agent = PolicyDiscoveryAgent()
    
    async def get_policy_background(self, policy_url: str):
        """Get detailed background for a specific policy"""
        
        # Use policy agent's content retrieval capabilities
        content = await self.policy_agent.search_engine.get_policy_content([policy_url])
        
        # Return A2A formatted response
        return {
            "agent_id": "research_agent",
            "policy_background": {
                "url": policy_url,
                "full_text": content.get(policy_url, {}).get("text", ""),
                "related_policies": await self._find_related_policies(policy_url),
                "historical_context": await self._get_historical_context(policy_url)
            }
        }
```

#### Example 3: Debate Agent Integration

```python
class DebateAgent:
    def __init__(self, stakeholder_role: str):
        self.stakeholder_role = stakeholder_role
        self.policy_agent = PolicyDiscoveryAgent()
    
    async def prepare_debate_position(self, policy_topic: str, user_location: str):
        """Prepare debate position based on policy discovery"""
        
        # Request relevant policies for this stakeholder
        context = UserContext(
            location=user_location,
            stakeholder_roles=[self.stakeholder_role],
            interests=[policy_topic]
        )
        
        results = await self.policy_agent.discover_policies(user_context=context)
        
        # Analyze impact on this stakeholder
        relevant_policies = []
        for policy in results.priority_ranking:
            for impact in policy.stakeholder_impacts:
                if self.stakeholder_role in impact.stakeholder_group.lower():
                    relevant_policies.append({
                        "policy": policy.title,
                        "impact": impact.description,
                        "severity": impact.impact_severity.value,
                        "stance_basis": policy.url
                    })
        
        return {
            "agent_id": f"debate_agent_{self.stakeholder_role}",
            "stakeholder_position": {
                "role": self.stakeholder_role,
                "relevant_policies": relevant_policies,
                "debate_readiness": len(relevant_policies) > 0
            }
        }
```

### A2A Protocol Standards

#### Request Types Supported
- `policy_discovery`: Standard policy search and discovery
- `policy_analysis`: Detailed analysis of specific policies
- `stakeholder_impact`: Impact analysis for specific stakeholder groups
- `policy_monitoring`: Ongoing monitoring for policy updates
- `related_policies`: Find policies related to a given policy

#### Status Codes
- `success`: Request completed successfully
- `partial`: Request completed with some limitations/warnings
- `error`: Request failed due to errors

#### Error Handling
```python
# Error response format
error_response = {
    "agent_id": "policy_discovery_agent",
    "status": "error",
    "error": {
        "code": "INVALID_LOCATION",
        "message": "Location 'Invalid City' not supported",
        "details": {
            "supported_locations": ["San Francisco, CA", "California", "United States"]
        }
    }
}
```

### A2A Communication Benefits

1. **Standardized Interface**: Consistent request/response format across all agent interactions
2. **Async Support**: Full async/await support for non-blocking agent communication
3. **Type Safety**: Structured data models ensure reliable agent-to-agent data exchange
4. **Error Handling**: Standardized error reporting for robust multi-agent systems
5. **Extensibility**: Easy to add new request types and response formats
6. **Scalability**: Supports concurrent requests from multiple agents

### Integration with CivicAI Multi-Agent System

The Policy Discovery Agent integrates seamlessly with the broader CivicAI multi-agent system through standardized A2A protocols:

- **Orchestration Agent**: Receives comprehensive policy contexts for debate setup
- **Research Agent**: Provides detailed policy background and historical context
- **Debate Agents**: Uses policy data for informed stakeholder-specific arguments
- **Action Agent**: Leverages policy information for personalized civic actions
- **Monitoring Agent**: Provides ongoing policy update notifications

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