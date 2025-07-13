#!/usr/bin/env python3
"""
MCP Server for Policy Discovery
Provides AI-powered policy discovery across government levels using Exa API
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
)

# Import the policy discovery components
from src.dynamic_crew.policy_discovery.agent import PolicyDiscoveryAgent
from src.dynamic_crew.policy_discovery.models import (
    UserContext,
    PolicyDomain,
    GovernmentLevel,
    RegulationTiming
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the policy discovery agent
policy_agent = None

def initialize_policy_agent():
    """Initialize the policy discovery agent with Exa API"""
    global policy_agent
    try:
        exa_api_key = os.getenv("EXA_API_KEY")
        if not exa_api_key:
            logger.warning("EXA_API_KEY not found - some features may be limited")
        
        policy_agent = PolicyDiscoveryAgent(exa_api_key=exa_api_key)
        logger.info("✅ Policy Discovery Agent initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Policy Discovery Agent: {e}")
        return False

# Initialize the MCP server
server = Server("policy-discovery")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="discover_policies",
                description="Discover relevant policies across government levels based on user context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "User's location (e.g., 'San Francisco, CA')"
                        },
                        "stakeholder_roles": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of stakeholder roles (e.g., ['renter', 'employee'])"
                        },
                        "interests": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of policy interests (e.g., ['rent control', 'minimum wage'])"
                        },
                        "domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Policy domains to search (e.g., ['housing', 'labor'])"
                        },
                        "government_levels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Government levels to search (e.g., ['federal', 'state', 'local'])"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                    "required": ["location", "stakeholder_roles"]
                }
            ),
            Tool(
                name="search_policies",
                description="Search policies using natural language query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="analyze_policy_question",
                description="Get AI-powered analysis of a policy-related question",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Policy-related question to analyze"
                        }
                    },
                    "required": ["question"]
                }
            ),
            Tool(
                name="get_policy_domains",
                description="Get available policy domains",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            ),
            Tool(
                name="get_government_levels",
                description="Get available government levels",
                inputSchema={
                    "type": "object",
                    "properties": {}
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls"""
    
    if not policy_agent:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="❌ Policy Discovery Agent not initialized. Please check EXA_API_KEY environment variable."
                )
            ]
        )
    
    try:
        if name == "discover_policies":
            return await handle_discover_policies(arguments)
        elif name == "search_policies":
            return await handle_search_policies(arguments)
        elif name == "analyze_policy_question":
            return await handle_analyze_policy_question(arguments)
        elif name == "get_policy_domains":
            return handle_get_policy_domains()
        elif name == "get_government_levels":
            return handle_get_government_levels()
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}"
                    )
                ]
            )
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"❌ Error executing {name}: {str(e)}"
                )
            ]
        )

async def handle_discover_policies(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle policy discovery request"""
    
    # Extract arguments
    location = arguments.get("location", "United States")
    stakeholder_roles = arguments.get("stakeholder_roles", ["general public"])
    interests = arguments.get("interests", [])
    domains = arguments.get("domains", [])
    government_levels = arguments.get("government_levels", [])
    max_results = arguments.get("max_results", 10)
    
    # Create user context
    user_context = UserContext(
        location=location,
        stakeholder_roles=stakeholder_roles,
        interests=interests
    )
    
    # Convert domain strings to enums if provided
    domain_enums = None
    if domains:
        domain_enums = [PolicyDomain(domain) for domain in domains if domain in [d.value for d in PolicyDomain]]
    
    # Convert government level strings to enums if provided
    level_enums = None
    if government_levels:
        level_enums = [GovernmentLevel(level) for level in government_levels if level in [l.value for l in GovernmentLevel]]
    
    # Discover policies
    results = await policy_agent.discover_policies(
        user_context=user_context,
        domains=domain_enums,
        government_levels=level_enums
    )
    
    # Format response
    response_data = {
        "success": True,
        "total_found": results.total_found,
        "search_time": results.search_time,
        "priority_policies": [
            {
                "id": f"policy_{i}",
                "title": policy.title,
                "url": policy.url,
                "government_level": policy.government_level.value,
                "domain": policy.domain.value,
                "summary": policy.summary,
                "status": policy.status.value,
                "source_agency": policy.source_agency,
                "document_type": policy.document_type,
                "last_updated": policy.last_updated.isoformat() if policy.last_updated else None,
                "confidence_score": policy.confidence_score,
                "content_preview": policy.content_preview,
                "stakeholder_impacts": [
                    {
                        "group": impact.stakeholder_group,
                        "severity": impact.impact_severity.value,
                        "description": impact.description,
                        "affected_areas": impact.affected_areas
                    } for impact in policy.stakeholder_impacts
                ]
            } for i, policy in enumerate(results.priority_ranking[:max_results])
        ],
        "search_metadata": {
            "domains_searched": results.search_metadata.get("domains_searched", []),
            "levels_searched": results.search_metadata.get("levels_searched", []),
            "search_quality_score": sum(p.confidence_score for p in results.priority_ranking[:10]) / min(10, len(results.priority_ranking)) if results.priority_ranking else 0,
            "recent_policies_count": len([p for p in results.priority_ranking if p.last_updated and (datetime.now() - p.last_updated).days <= 90]),
            "high_confidence_count": len([p for p in results.priority_ranking if p.confidence_score >= 0.8])
        }
    }
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"✅ Found {results.total_found} policies in {results.search_time:.2f} seconds\n\n" + 
                     json.dumps(response_data, indent=2)
            )
        ]
    )

async def handle_search_policies(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle natural language policy search"""
    
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)
    
    if not query:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="❌ Query is required for policy search"
                )
            ]
        )
    
    # Use the search engine's analyze_policy_question method
    try:
        analysis = await policy_agent.search_engine.analyze_policy_question(query)
        
        response_data = {
            "query": query,
            "answer": analysis.get("answer", ""),
            "citations": analysis.get("citations", []),
            "total_citations": len(analysis.get("citations", []))
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"🔍 Policy Analysis for: {query}\n\n" +
                         f"Answer: {analysis.get('answer', 'No answer available')}\n\n" +
                         f"Based on {len(analysis.get('citations', []))} sources\n\n" +
                         json.dumps(response_data, indent=2)
                )
            ]
        )
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"❌ Error analyzing policy question: {str(e)}"
                )
            ]
        )

async def handle_analyze_policy_question(arguments: Dict[str, Any]) -> CallToolResult:
    """Handle policy question analysis"""
    
    question = arguments.get("question", "")
    
    if not question:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text="❌ Question is required for analysis"
                )
            ]
        )
    
    try:
        analysis = await policy_agent.search_engine.analyze_policy_question(question)
        
        response_data = {
            "question": question,
            "answer": analysis.get("answer", ""),
            "citations": analysis.get("citations", []),
            "total_citations": len(analysis.get("citations", []))
        }
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"🤖 AI Policy Analysis\n\n" +
                         f"Question: {question}\n\n" +
                         f"Answer: {analysis.get('answer', 'No answer available')}\n\n" +
                         f"Sources: {len(analysis.get('citations', []))} citations\n\n" +
                         json.dumps(response_data, indent=2)
                )
            ]
        )
    except Exception as e:
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"❌ Error analyzing policy question: {str(e)}"
                )
            ]
        )

def handle_get_policy_domains() -> CallToolResult:
    """Get available policy domains"""
    
    domains = [
        {"value": domain.value, "description": domain.value.replace("_", " ").title()}
        for domain in PolicyDomain
    ]
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"📋 Available Policy Domains:\n\n" + 
                     json.dumps(domains, indent=2)
            )
        ]
    )

def handle_get_government_levels() -> CallToolResult:
    """Get available government levels"""
    
    levels = [
        {"value": level.value, "description": level.value.replace("_", " ").title()}
        for level in GovernmentLevel
    ]
    
    return CallToolResult(
        content=[
            TextContent(
                type="text",
                text=f"🏛️ Available Government Levels:\n\n" + 
                     json.dumps(levels, indent=2)
            )
        ]
    )

async def main():
    """Main entry point"""
    
    # Initialize the policy discovery agent
    if not initialize_policy_agent():
        logger.error("Failed to initialize policy discovery agent")
        return
    
    # Create and run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="policy-discovery",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main()) 