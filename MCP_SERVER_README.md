# Policy Discovery MCP Server

An MCP (Model Context Protocol) server that provides AI-powered policy discovery across government levels using the Exa API.

## 🚀 Features

- **Multi-level Government Search**: Federal, State (California), and Local (San Francisco) policies
- **Stakeholder-focused Discovery**: Find policies relevant to specific stakeholder roles
- **Natural Language Search**: Query policies using conversational language
- **AI-powered Analysis**: Get intelligent answers to policy questions with citations
- **Structured Data**: Returns well-formatted policy information with stakeholder impacts

## 🛠️ Installation

1. **Install Dependencies**:
```bash
pip install -r mcp_requirements.txt
```

2. **Set Environment Variables**:
```bash
export EXA_API_KEY="your_exa_api_key_here"
```

3. **Run the Server**:
```bash
python mcp_policy_discovery_server.py
```

## 📋 Available Tools

### 1. `discover_policies`
Discover relevant policies based on user context and stakeholder roles.

**Parameters**:
- `location` (required): User's location (e.g., "San Francisco, CA")
- `stakeholder_roles` (required): List of stakeholder roles (e.g., ["renter", "employee"])
- `interests` (optional): List of policy interests (e.g., ["rent control", "minimum wage"])
- `domains` (optional): Policy domains to search (e.g., ["housing", "labor"])
- `government_levels` (optional): Government levels to search (e.g., ["federal", "state", "local"])
- `max_results` (optional): Maximum number of results (default: 10)

**Example**:
```json
{
  "location": "San Francisco, CA",
  "stakeholder_roles": ["renter", "employee"],
  "interests": ["rent control", "minimum wage"],
  "domains": ["housing", "labor"],
  "government_levels": ["local", "state"],
  "max_results": 5
}
```

### 2. `search_policies`
Search policies using natural language queries.

**Parameters**:
- `query` (required): Natural language search query
- `max_results` (optional): Maximum number of results (default: 10)

**Example**:
```json
{
  "query": "What are the latest rent control policies in San Francisco?",
  "max_results": 5
}
```

### 3. `analyze_policy_question`
Get AI-powered analysis of policy-related questions with citations.

**Parameters**:
- `question` (required): Policy-related question to analyze

**Example**:
```json
{
  "question": "How do minimum wage increases affect small businesses in California?"
}
```

### 4. `get_policy_domains`
Get available policy domains.

**Parameters**: None

### 5. `get_government_levels`
Get available government levels.

**Parameters**: None

## 🏛️ Policy Domains

- **housing**: Housing policies, rent control, zoning
- **labor**: Worker rights, minimum wage, employment
- **public_safety**: Policing, community safety, emergency services
- **environment**: Climate policies, pollution control, sustainability
- **transportation**: Transit, parking, infrastructure
- **business**: Licensing, regulations, taxation

## 🏛️ Government Levels

- **federal**: Federal government policies and regulations
- **state**: California state policies and legislation
- **local**: San Francisco local ordinances and initiatives

## 📊 Response Format

### Policy Discovery Response
```json
{
  "success": true,
  "total_found": 15,
  "search_time": 2.34,
  "priority_policies": [
    {
      "id": "policy_0",
      "title": "San Francisco Rent Control Ordinance",
      "url": "https://sfgov.org/rent-control",
      "government_level": "local",
      "domain": "housing",
      "summary": "Comprehensive rent control policy...",
      "status": "active",
      "source_agency": "San Francisco Rent Board",
      "document_type": "ordinance",
      "last_updated": "2024-01-15T00:00:00",
      "confidence_score": 0.95,
      "content_preview": "This ordinance establishes...",
      "stakeholder_impacts": [
        {
          "group": "tenants",
          "severity": "high",
          "description": "Provides rent stabilization",
          "affected_areas": ["rent_payments", "housing_security"]
        }
      ]
    }
  ],
  "search_metadata": {
    "domains_searched": ["housing"],
    "levels_searched": ["local", "state"],
    "search_quality_score": 0.87,
    "recent_policies_count": 8,
    "high_confidence_count": 12
  }
}
```

### Policy Analysis Response
```json
{
  "question": "How do minimum wage increases affect small businesses?",
  "answer": "Minimum wage increases can have both positive and negative effects...",
  "citations": [
    {
      "title": "Economic Impact of Minimum Wage Increases",
      "url": "https://example.com/study",
      "published_date": "2024-01-01",
      "author": "Economic Research Institute",
      "text": "Recent studies show..."
    }
  ],
  "total_citations": 3
}
```

## 🔧 Integration Examples

### With Claude Desktop
Add to your MCP configuration:
```json
{
  "mcpServers": {
    "policy-discovery": {
      "command": "python",
      "args": ["/path/to/mcp_policy_discovery_server.py"],
      "env": {
        "EXA_API_KEY": "your_exa_api_key"
      }
    }
  }
}
```

### With Other MCP Clients
The server follows the standard MCP protocol and can be integrated with any MCP-compatible client.

## 🎯 Use Cases

1. **Civic Engagement**: Help citizens find relevant policies affecting their lives
2. **Policy Research**: Assist researchers in discovering related policies
3. **Legal Analysis**: Support legal professionals in policy research
4. **Journalism**: Help journalists find policy context for stories
5. **Education**: Provide students with real-world policy examples

## 🚨 Error Handling

The server includes comprehensive error handling:
- **API Key Issues**: Graceful degradation when Exa API key is missing
- **Network Errors**: Retry logic for failed requests
- **Invalid Input**: Clear error messages for malformed requests
- **Rate Limiting**: Built-in rate limiting to respect API limits

## 🔄 Future Enhancements

- **Caching**: Implement result caching for improved performance
- **More Government Levels**: Expand beyond California/San Francisco
- **Policy Tracking**: Track policy changes over time
- **Sentiment Analysis**: Analyze stakeholder sentiment toward policies
- **Impact Prediction**: Predict policy impacts using historical data

## 📝 License

This MCP server is part of the CivicAI project and follows the same licensing terms.

## 🤝 Contributing

Contributions are welcome! Please see the main CivicAI project for contribution guidelines. 