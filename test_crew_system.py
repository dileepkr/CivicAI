#!/usr/bin/env python3
"""
Test script to verify the crew system delegation fixes work properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_crew_agents():
    """Test that crew agents can be created without delegation issues"""
    print("🧪 Testing crew system delegation fixes...")
    
    try:
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        # Create crew instance
        print("🔧 Creating crew instance...")
        crew = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Test agent creation
        print("🔧 Testing agent creation...")
        
        # Test coordinator agent
        print("  - Testing coordinator_agent...")
        coordinator = crew.coordinator_agent()
        print(f"    ✅ Created: {coordinator.role}")
        
        # Test policy discovery agent
        print("  - Testing policy_discovery_agent...")
        policy_discovery = crew.policy_discovery_agent()
        print(f"    ✅ Created: {policy_discovery.role}")
        
        # Test debate moderator agent
        print("  - Testing debate_moderator_agent...")
        debate_moderator = crew.debate_moderator_agent()
        print(f"    ✅ Created: {debate_moderator.role}")
        
        # Test policy debate agent
        print("  - Testing policy_debate_agent...")
        policy_debate = crew.policy_debate_agent()
        print(f"    ✅ Created: {policy_debate.role}")
        
        # Test advocate sub agents
        print("  - Testing advocate_sub_agents...")
        advocate_sub = crew.advocate_sub_agents()
        print(f"    ✅ Created: {advocate_sub.role}")
        
        # Test action agent
        print("  - Testing action_agent...")
        action_agent = crew.action_agent()
        print(f"    ✅ Created: {action_agent.role}")
        
        print("\n✅ All agents created successfully!")
        
        # Test task creation
        print("\n🔧 Testing task creation...")
        
        # Test a few key tasks
        print("  - Testing analyze_debate_topics_task...")
        analyze_task = crew.analyze_debate_topics_task()
        print(f"    ✅ Created task: {analyze_task.description[:50]}...")
        
        print("  - Testing initiate_debate_session_task...")
        initiate_task = crew.initiate_debate_session_task()
        print(f"    ✅ Created task: {initiate_task.description[:50]}...")
        
        print("\n✅ All tasks created successfully!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crew_agents()
    if success:
        print("\n🎉 All tests passed! Crew system delegation fixes are working.")
    else:
        print("\n💥 Tests failed! There are still issues to fix.") 