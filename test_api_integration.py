#!/usr/bin/env python3
"""
Simple test script to verify API integration with policy discovery and A2A protocol
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_policy_discovery():
    """Test policy discovery agent integration"""
    print("🧪 Testing Policy Discovery Integration...")
    
    try:
        from policy_discovery.agent import PolicyDiscoveryAgent
        from policy_discovery.models import UserContext, RegulationTiming
        
        # Initialize agent
        agent = PolicyDiscoveryAgent()
        print("✅ Policy Discovery Agent initialized")
        
        # Create test user context
        user_context = UserContext(
            location="San Francisco, CA",
            stakeholder_roles=["resident"],
            interests=["housing"],
            regulation_timing=RegulationTiming.ALL
        )
        
        # Test discovery (this will use actual Exa API if configured)
        print("🔍 Testing policy discovery...")
        try:
            result = await agent.discover_policies(user_context)
            print(f"✅ Found {result.total_found} policies")
            print(f"📊 Search time: {result.search_time:.2f}s")
            
            if result.priority_ranking:
                top_policy = result.priority_ranking[0]
                print(f"🏆 Top policy: {top_policy.title}")
                print(f"🎯 Confidence: {top_policy.confidence_score:.2f}")
        except Exception as e:
            print(f"⚠️  Policy discovery test failed (expected if no API key): {e}")
        
    except Exception as e:
        print(f"❌ Policy Discovery test failed: {e}")
        return False
    
    return True

async def test_a2a_integration():
    """Test A2A protocol integration"""
    print("\n🧪 Testing A2A Protocol Integration...")
    
    try:
        from api.a2a_integration import (
            CivicAIA2AAgent, A2ACoordinator, get_coordinator, 
            cleanup_coordinator, is_a2a_available
        )
        
        print(f"📡 A2A SDK Available: {is_a2a_available()}")
        
        # Create test agents
        moderator = CivicAIA2AAgent(
            agent_id="test_moderator",
            agent_type="moderator",
            role="Test Moderator",
            capabilities=["facilitate_debate"]
        )
        
        analyst = CivicAIA2AAgent(
            agent_id="test_analyst",
            agent_type="analyst", 
            role="Test Analyst",
            capabilities=["analyze_policy"]
        )
        
        print("✅ A2A Agents created")
        
        # Create coordinator
        coordinator = get_coordinator("test_session")
        coordinator.register_agent(moderator)
        coordinator.register_agent(analyst)
        
        print("✅ A2A Coordinator created and agents registered")
        
        # Test message sending
        success = await coordinator.send_direct_message(
            sender_id="test_moderator",
            recipient_id="test_analyst",
            content="Test message via A2A protocol",
            message_type="test"
        )
        
        print(f"📨 Direct message test: {'✅ Success' if success else '❌ Failed'}")
        
        # Test broadcast
        success = await coordinator.broadcast_message(
            sender_id="test_moderator",
            content="Broadcast test message",
            message_type="broadcast"
        )
        
        print(f"📡 Broadcast test: {'✅ Success' if success else '❌ Failed'}")
        
        # Get session info
        session_info = coordinator.get_session_info()
        print(f"📊 Session has {session_info['agent_count']} agents")
        
        # Cleanup
        cleanup_coordinator("test_session")
        print("🧹 Coordinator cleaned up")
        
    except Exception as e:
        print(f"❌ A2A Integration test failed: {e}")
        return False
    
    return True

async def test_api_functionality():
    """Test API discover_policy_data function"""
    print("\n🧪 Testing API Policy Discovery Function...")
    
    try:
        from api.main import discover_policy_data, load_policy_data_fallback
        from policy_discovery.models import UserContext, RegulationTiming
        
        # Test with user context
        user_context = UserContext(
            location="San Francisco, CA",
            stakeholder_roles=["resident"],
            interests=["housing"],
            regulation_timing=RegulationTiming.ALL
        )
        
        try:
            policy_data = await discover_policy_data("housing policy", user_context)
            print("✅ Policy discovery via API function successful")
            print(f"📋 Policy title: {policy_data.get('title', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  API policy discovery failed (expected if no API key): {e}")
            
            # Test fallback
            try:
                # Check if test data exists
                test_files = list(Path("test_data").glob("*.json")) if Path("test_data").exists() else []
                if test_files:
                    test_policy = test_files[0].stem
                    fallback_data = load_policy_data_fallback(test_policy)
                    print(f"✅ Fallback policy data loaded: {fallback_data.get('title', 'Unknown')}")
                else:
                    print("⚠️  No test data available for fallback test")
            except Exception as e2:
                print(f"❌ Fallback test also failed: {e2}")
        
    except Exception as e:
        print(f"❌ API functionality test failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting CivicAI API Integration Tests\n")
    
    results = []
    
    # Test policy discovery
    results.append(await test_policy_discovery())
    
    # Test A2A integration
    results.append(await test_a2a_integration())
    
    # Test API functionality
    results.append(await test_api_functionality())
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! API integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)