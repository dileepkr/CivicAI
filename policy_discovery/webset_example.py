"""
Example usage of the Hybrid Policy Discovery Agent with Websets

This example demonstrates how to use the enhanced PolicyDiscoveryAgent
with both Webset collection and real-time search capabilities.
"""

import asyncio
import os
import json

from dotenv import load_dotenv

from policy_discovery import (
    GovernmentLevel,
    PolicyDiscoveryAgent,
    PolicyDomain,
    RegulationTiming,
    UserContext,
)

# Load environment variables
load_dotenv()


async def main():
    """
    Example demonstrating the hybrid Webset + Search approach
    """

    # Initialize the agent
    agent = PolicyDiscoveryAgent(exa_api_key=os.getenv("EXA_API_KEY"))

    print("=== Hybrid Policy Discovery with Websets ===\n")

    # Example 1: Initialize websets (one-time setup)
    print("=== Step 1: Initialize Policy Websets ===")
    try:
        webset_ids = await agent.initialize_websets()
        print(f"Initialized {len(webset_ids)} websets:")
        for name, webset_id in webset_ids.items():
            print(f"  - {name}: {webset_id}")
    except Exception as e:
        print(f"Failed to initialize websets: {e}")
        print("Continuing with search-only mode...")

    print("\n=== Step 2: Set up Policy Monitoring ===")
    try:
        monitor_ids = await agent.setup_policy_monitoring()
        print(f"Set up {len(monitor_ids)} monitors for automated policy collection:")
        for name, monitor_id in monitor_ids.items():
            print(f"  - {name}: {monitor_id}")
    except Exception as e:
        print(f"Failed to set up monitoring: {e}")

    print("\n=== Step 3: Check Webset Status ===")
    try:
        status = await agent.get_webset_status()
        print("Webset Status:")
        for name, info in status.items():
            if "error" in info:
                print(f"  - {name}: ERROR - {info['error']}")
            else:
                print(f"  - {name}: {info['item_count']} items, status: {info.get('status', 'unknown')}")
    except Exception as e:
        print(f"Failed to get webset status: {e}")

    # Example 2: Hybrid policy discovery
    print("\n=== Step 4: Hybrid Policy Discovery ===")

    renter_context = UserContext(
        location="San Francisco, CA",
        stakeholder_roles=["renter", "tenant"],
        interests=["rent control", "tenant protection", "housing affordability"],
        regulation_timing=RegulationTiming.ALL,
    )

    print("Searching for housing policies using hybrid approach...")
    results = await agent.discover_policies(
        user_context=renter_context,
        domains=[PolicyDomain.HOUSING],
        government_levels=[GovernmentLevel.STATE, GovernmentLevel.LOCAL],
        use_websets=True  # Enable hybrid mode
    )

    print(f"\n=== Results Summary ===")
    print(f"Total policies found: {results.total_found}")
    print(f"Search time: {results.search_time:.2f} seconds")
    print(f"Webset policies: {results.search_metadata.get('webset_policies_count', 0)}")
    print(f"Live search policies: {results.search_metadata.get('search_policies_count', 0)}")
    print(f"Hybrid mode: {results.search_metadata.get('hybrid_mode', False)}")

    # Display AI-powered policy analysis if available
    if results.search_metadata.get("policy_analysis"):
        analysis = results.search_metadata["policy_analysis"]
        print(f"\n=== AI Policy Analysis ===")
        print(f"Answer: {analysis['answer']}")
        if analysis.get('citations'):
            print(f"\nBased on {len(analysis['citations'])} sources:")
            for i, citation in enumerate(analysis['citations'][:3], 1):  # Show top 3 citations
                print(f"  {i}. {citation['title']} - {citation['url']}")

    # Display top policies with source indication
    print(f"\n=== Top 5 Relevant Policies ===")
    for i, policy in enumerate(results.priority_ranking[:5], 1):
        # Determine source (webset vs search)
        webset_count = results.search_metadata.get('webset_policies_count', 0)
        search_count = results.search_metadata.get('search_policies_count', 0)
        
        # Simple heuristic: higher confidence scores likely from websets
        source = "Webset" if policy.confidence_score > 0.7 else "Live Search"
        
        print(f"\n{i}. {policy.title}")
        print(f"   Source: {source}")
        print(f"   Level: {policy.government_level.value.title()}")
        print(f"   Domain: {policy.domain.value.title()}")
        print(f"   Status: {policy.status.value.title()}")
        print(f"   Confidence: {policy.confidence_score:.2f}")
        print(f"   URL: {policy.url}")
        print(f"   Summary: {policy.summary[:150]}...")

    # Example 3: Compare with search-only mode
    print("\n\n=== Step 5: Compare with Search-Only Mode ===")
    
    print("Searching for the same policies using search-only mode...")
    search_only_results = await agent.discover_policies(
        user_context=renter_context,
        domains=[PolicyDomain.HOUSING],
        government_levels=[GovernmentLevel.STATE, GovernmentLevel.LOCAL],
        use_websets=False  # Disable websets for comparison
    )

    print(f"\nComparison:")
    print(f"Hybrid mode: {results.total_found} policies in {results.search_time:.2f}s")
    print(f"Search-only: {search_only_results.total_found} policies in {search_only_results.search_time:.2f}s")
    
    # Show unique policies from each approach
    hybrid_urls = {p.url for p in results.priority_ranking}
    search_only_urls = {p.url for p in search_only_results.priority_ranking}
    
    unique_to_hybrid = hybrid_urls - search_only_urls
    unique_to_search = search_only_urls - hybrid_urls
    
    print(f"Policies unique to hybrid mode: {len(unique_to_hybrid)}")
    print(f"Policies unique to search-only: {len(unique_to_search)}")

    # Example 4: Format response for the top policy
    if results.priority_ranking:
        print(f"\n=== Step 6: Formatted Response Example ===")
        top_policy = results.priority_ranking[0]
        formatted_response = await agent.format_policy_response(
            user_context=renter_context,
            policy_result=top_policy,
            request_id="webset_example_001"
        )
        
        # Convert to JSON format
        response_dict = agent.format_response_as_json(formatted_response)
        print("Formatted JSON Response:")
        print(json.dumps(response_dict, indent=2))

    # Example 5: Business owner scenario
    print("\n\n=== Step 7: Business Owner Labor Policy Discovery ===")
    
    business_context = UserContext(
        location="San Francisco, CA",
        stakeholder_roles=["business_owner", "employer"],
        interests=["minimum wage", "worker classification", "employment law"],
        regulation_timing=RegulationTiming.FUTURE,  # Focus on upcoming changes
    )

    business_results = await agent.discover_policies(
        user_context=business_context,
        domains=[PolicyDomain.LABOR],
        use_websets=True
    )

    print(f"Business-relevant policies found: {business_results.total_found}")
    print(f"Top upcoming labor policies for business owners:")
    
    for i, policy in enumerate(business_results.priority_ranking[:3], 1):
        print(f"\n{i}. {policy.title}")
        print(f"   Status: {policy.status.value.title()}")
        print(f"   Level: {policy.government_level.value.title()}")
        print(f"   Summary: {policy.summary[:100]}...")

    print("\n=== Hybrid Policy Discovery Complete ===")
    print("Benefits of hybrid approach:")
    print("- Structured collection of policies in websets")
    print("- Automatic monitoring for new policies")
    print("- Real-time search for latest updates")
    print("- Enhanced data enrichment and metadata")
    print("- Improved relevance scoring and deduplication")


if __name__ == "__main__":
    asyncio.run(main())