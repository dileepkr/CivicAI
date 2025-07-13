# CrewAI Policy Discovery Agent Development Prompt

## Your Role
You are an expert AI Agent developer specializing in CrewAI framework. Your task is to create a sophisticated **Universal Policy Discovery Agent** that serves as a critical component in the CivicAI multi-agent debate system.

## Agent Overview
Create a CrewAI agent that dynamically discovers relevant policies across multiple government levels (Federal, State of California, City of San Francisco) using the Exa API. This agent must intelligently search for policies based on user location, stakeholder roles, and policy domains.

## Technical Requirements

### 1. Agent Configuration
```python
# Base agent structure you should implement
policy_discovery_agent = Agent(
    role='Universal Policy Discovery Specialist',
    goal='Discover and categorize relevant policies across all government levels based on user context and stakeholder roles',
    backstory='Expert in navigating complex government policy landscapes...',
    # Configure additional parameters
)
```

### 2. Core Capabilities Required

#### A. Multi-Level Government Search
- **Federal Level**: Search federal policies, regulations, and proposed legislation
- **State Level**: Focus on California state policies, bills, and regulations
- **Local Level**: San Francisco city ordinances, proposals, and local initiatives

#### B. Exa API Integration
Implement comprehensive Exa API usage:
```python
# Key Exa API endpoints to utilize:
# - exa.search() for policy discovery
# - exa.find_similar() for related policy identification
# - exa.get_contents() for detailed policy content
```

#### C. Policy Domain Classification
The agent must categorize policies into domains:
- Housing (rent control, zoning, tenant rights)
- Labor (worker classification, minimum wage, benefits)
- Public Safety (policing, community safety, emergency services)
- Environment (climate policies, pollution control)
- Transportation (transit, parking, infrastructure)
- Business (licensing, regulations, taxation)

### 3. Search Strategy Implementation

#### A. User Context Analysis
```python
def analyze_user_context(user_location, stakeholder_roles, uploaded_documents):
    """
    Analyze user context to determine relevant policy search parameters
    Args:
        user_location: Geographic location for jurisdictional relevance
        stakeholder_roles: List of user's civic roles (renter, employee, business owner, etc.)
        uploaded_documents: Context documents that may indicate specific interests
    Returns:
        SearchParameters object with optimized search terms and filters
    """
```

#### B. Intelligent Query Generation
Create sophisticated search queries that:
- Use stakeholder-specific terminology
- Include relevant geographic qualifiers
- Incorporate policy domain keywords
- Account for both current and proposed legislation

#### C. Multi-Jurisdiction Search Logic
```python
def execute_policy_search(search_parameters):
    """
    Execute searches across multiple government levels
    Priority order: Local -> State -> Federal
    Focus on policies that directly impact user's stakeholder roles
    """
```

### 4. Exa API Implementation Details

#### A. Search Configuration
```python
# Configure Exa searches for government content
exa_search_config = {
    'include_domains': [
        'sf.gov', 'sfgov.org', 'sfdph.org',  # SF local
        'ca.gov', 'leginfo.legislature.ca.gov',  # California state
        'congress.gov', 'regulations.gov', 'federalregister.gov'  # Federal
    ],
    'date_cutoff': '2023-01-01',  # Recent policies
    'num_results': 20,
    'use_autoprompt': True
}
```

#### B. Content Processing
```python
def process_policy_documents(exa_results):
    """
    Process Exa search results to extract:
    - Policy titles and summaries
    - Stakeholder impact areas
    - Implementation timelines
    - Relevant government contacts
    """
```

### 5. Output Structure

#### A. Policy Discovery Results
```python
class PolicyDiscoveryResult:
    def __init__(self):
        self.federal_policies = []
        self.state_policies = []
        self.local_policies = []
        self.stakeholder_impact_map = {}
        self.priority_ranking = []
        self.related_policies = []
```

#### B. Stakeholder Relevance Mapping
For each discovered policy, provide:
- Primary affected stakeholder groups
- Impact severity (high/medium/low)
- Policy status (proposed/active/under review)
- Key dates and deadlines

### 6. Integration with CivicAI System

#### A. Orchestration Agent Communication
```python
def communicate_with_orchestrator(policy_results):
    """
    Format results for the Dynamic Orchestration Agent
    Include stakeholder mapping to inform agent instantiation decisions
    """
```

#### B. Research Agent Coordination
```python
def provide_research_context(selected_policies):
    """
    Provide detailed policy context to the Contextual Research Agent
    Include background information and precedent analysis
    """
```

### 7. Error Handling and Robustness

#### A. API Limitations Management
- Implement rate limiting for Exa API calls
- Handle API errors gracefully
- Provide fallback search strategies

#### B. Data Quality Assurance
- Validate policy document authenticity
- Cross-reference information across sources
- Flag potentially outdated or superseded policies

### 8. Performance Optimization

#### A. Caching Strategy
```python
def implement_policy_cache():
    """
    Cache frequently accessed policies
    Implement TTL for policy freshness
    Optimize for common stakeholder combinations
    """
```

#### B. Parallel Processing
- Execute multi-jurisdiction searches concurrently
- Implement async processing for large result sets
- Optimize for user experience with progressive loading

## Implementation Tasks

### Phase 1: Core Agent Development
1. Set up CrewAI agent with proper role and capabilities
2. Implement basic Exa API integration
3. Create multi-level government search logic
4. Develop policy classification system

### Phase 2: Advanced Features
1. Implement intelligent query generation
2. Add stakeholder relevance mapping
3. Create policy impact analysis
4. Develop caching and optimization features

### Phase 3: Integration & Testing
1. Integrate with CivicAI orchestration system
2. Test across multiple policy domains
3. Validate results quality and relevance
4. Optimize performance for real-time usage

## Success Criteria

### Technical Success
- Agent successfully discovers relevant policies across all government levels
- Exa API integration handles various search scenarios robustly
- Policy classification accurately categorizes diverse policy types
- System scales to handle multiple simultaneous user requests

### Functional Success
- Users receive comprehensive policy information relevant to their stakeholder roles
- Search results include both current and proposed legislation
- Policy relevance ranking accurately reflects user context
- Integration with other CivicAI agents works seamlessly

### Demo Readiness
- Agent can demonstrate policy discovery for housing and labor domains
- Real-time search capabilities work smoothly in demo scenarios
- Results format supports the multi-agent debate system
- Clear differentiation between government levels and policy types

## Code Structure Template

```python
from crewai import Agent, Task, Crew
from exa_py import Exa
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from enum import Enum

class PolicyDomain(Enum):
    HOUSING = "housing"
    LABOR = "labor"
    PUBLIC_SAFETY = "public_safety"
    ENVIRONMENT = "environment"
    TRANSPORTATION = "transportation"
    BUSINESS = "business"

class GovernmentLevel(Enum):
    FEDERAL = "federal"
    STATE = "state"
    LOCAL = "local"

@dataclass
class PolicyResult:
    title: str
    summary: str
    url: str
    government_level: GovernmentLevel
    domain: PolicyDomain
    stakeholder_impacts: List[str]
    status: str
    last_updated: str

class PolicyDiscoveryAgent:
    def __init__(self, exa_api_key: str):
        self.exa = Exa(api_key=exa_api_key)
        self.agent = self._create_agent()
        
    def _create_agent(self) -> Agent:
        """Create and configure the CrewAI agent"""
        # Your agent implementation here
        pass
        
    async def discover_policies(self, user_context: Dict[str, Any]) -> List[PolicyResult]:
        """Main policy discovery method"""
        # Your discovery logic here
        pass
        
    def _generate_search_queries(self, context: Dict[str, Any]) -> List[str]:
        """Generate intelligent search queries based on user context"""
        # Your query generation logic here
        pass
        
    async def _search_government_level(self, level: GovernmentLevel, queries: List[str]) -> List[PolicyResult]:
        """Search specific government level for policies"""
        # Your government-specific search logic here
        pass
```

## Additional Considerations

### 1. Privacy and Security
- Ensure user location data is handled securely
- Implement proper data sanitization for search queries
- Respect government website terms of service

### 2. Scalability
- Design for multiple concurrent users
- Implement efficient resource utilization
- Plan for expanding to additional jurisdictions

### 3. Maintainability
- Use clear, documented code structure
- Implement comprehensive logging
- Design for easy updates and modifications

Create this agent with production-ready code quality, comprehensive error handling, and clear documentation. The agent should be ready for integration into the larger CivicAI system while maintaining independence and reusability.