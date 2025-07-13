"""
Example usage of the Policy Discovery Agent
"""

import asyncio
import os

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
    Example demonstrating policy discovery functionality
    """

    # Initialize the agent
    agent = PolicyDiscoveryAgent(exa_api_key=os.getenv("EXA_API_KEY"))

    # Example 1: Renter looking for housing policies
    print("=== Example 1: Renter Housing Policy Search ===")

    renter_context = UserContext(
        location="San Francisco, CA",
        stakeholder_roles=["renter", "landlord"],
        interests=["rent control"],
        regulation_timing=RegulationTiming.FUTURE,  # Only proposed policies
    )

    results = await agent.discover_policies(
        user_context=renter_context,
        domains=[PolicyDomain.HOUSING],
        government_levels=[GovernmentLevel.STATE],
    )

    print(f"Found {results.total_found} relevant policies")
    print(f"Search completed in {results.search_time:.2f} seconds")
    
    # Display AI-powered policy analysis if available
    if results.search_metadata.get("policy_analysis"):
        analysis = results.search_metadata["policy_analysis"]
        print(f"\n=== AI Policy Analysis ===")
        print(f"Answer: {analysis['answer']}")
        if analysis['citations']:
            print(f"\nBased on {len(analysis['citations'])} sources:")
            for i, citation in enumerate(analysis['citations'][:], 1):  # Show top 2 citations
                print(f"  {i}. {citation['title']} - {citation['url']}")

    # Display top 3 policies in the new format
    print(f"\n=== Formatted Policy Responses ===")
    for i, policy in enumerate(results.priority_ranking[:3], 1):
        print(f"\n--- Policy {i} ---")
        print(f"Title: {policy.title}")
        print(f"Level: {policy.government_level.value.title()}")
        print(f"Domain: {policy.domain.value.title()}")
        print(f"Status: {policy.status.value.title()}")
        print(f"URL: {policy.url}")
        print(f"Summary: {policy.summary[:200]}...")
    
    # Demonstrate the new output format for the top policy
    if results.priority_ranking:
        print(f"\n=== New JSON Output Format (Top Policy) ===")
        top_policy = results.priority_ranking[0]
        formatted_response = await agent.format_policy_response(
            user_context=renter_context,
            policy_result=top_policy,
            request_id="example123-policy456"
        )
        
        # Convert to JSON format using the utility method
        import json
        
        response_dict = agent.format_response_as_json(formatted_response)
        print(json.dumps(response_dict, indent=2))

    # Example 2: Current housing policies for homeowners
    # print("\n\n=== Example 2: Current Housing Policies for Homeowners ===")

    # homeowner_context = UserContext(
    #     location="San Francisco, CA",
    #     stakeholder_roles=["homeowner"],
    #     interests=["zoning", "property tax", "development"],
    #     regulation_timing=RegulationTiming.CURRENT,  # Only current/enacted policies
    # )

    # current_results = await agent.discover_policies(
    #     user_context=homeowner_context,
    #     domains=[PolicyDomain.HOUSING],
    #     government_levels=[GovernmentLevel.LOCAL, GovernmentLevel.STATE],
    # )

    # print(f"Found {current_results.total_found} current policies")
    
    # # Display AI-powered policy analysis if available
    # if current_results.search_metadata.get("policy_analysis"):
    #     analysis = current_results.search_metadata["policy_analysis"]
    #     print(f"\n=== AI Policy Analysis ===")
    #     print(f"Answer: {analysis['answer'][:300]}...")

    # # Display top 2 current policies
    # for i, policy in enumerate(current_results.priority_ranking[:2], 1):
    #     print(f"\n{i}. {policy.title}")
    #     print(f"   Level: {policy.government_level.value.title()}")
    #     print(f"   Status: {policy.status.value.title()}")
    #     print(f"   URL: {policy.url}")

    # # Example 3: Business owner looking for labor policies
    # print("\n\n=== Example 2: Business Owner Labor Policy Search ===")

    # business_context = UserContext(
    #     location="San Francisco, CA",
    #     stakeholder_roles=["business_owner", "employer"],
    #     interests=["minimum wage", "worker classification", "employment law"],
    # )

    # results = await agent.discover_policies(
    #     user_context=business_context,
    #     domains=[PolicyDomain.LABOR, PolicyDomain.BUSINESS],
    # )

    # print(f"Found {results.total_found} relevant policies")

    # # Show stakeholder impact mapping
    # print("\nStakeholder Impact Mapping:")
    # for role, policies in results.stakeholder_impact_map.items():
    #     print(f"  {role.title()}: {len(policies)} relevant policies")

    # # Example 3: Multi-domain search for comprehensive civic engagement
    # print("\n\n=== Example 3: Comprehensive Civic Engagement Search ===")

    # civic_context = UserContext(
    #     location="San Francisco, CA",
    #     stakeholder_roles=["resident", "voter", "parent"],
    #     interests=["public safety", "education", "transportation"],
    # )

    # results = await agent.discover_policies(
    #     user_context=civic_context
    #     # No domain restriction - search all domains
    # )

    # print(f"Found {results.total_found} relevant policies across all domains")

    # # Show distribution by government level
    # print(f"Federal policies: {len(results.federal_policies)}")
    # print(f"State policies: {len(results.state_policies)}")
    # print(f"Local policies: {len(results.local_policies)}")

    # # Show distribution by domain
    # domain_counts = {}
    # all_policies = (
    #     results.federal_policies + results.state_policies + results.local_policies
    # )

    # for policy in all_policies:
    #     domain = policy.domain.value
    #     domain_counts[domain] = domain_counts.get(domain, 0) + 1

    # print("\nPolicies by domain:")
    # for domain, count in sorted(domain_counts.items()):
    #     print(f"  {domain.title()}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
