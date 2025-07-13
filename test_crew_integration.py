#!/usr/bin/env python3
"""
Test script for CrewAI integration with robust LLM client
"""

import os
import sys

# Add the src directory to the path
sys.path.append('src/dynamic_crew')

def test_crew_integration():
    """Test the CrewAI integration"""
    print("🧪 Testing CrewAI Integration...")
    
    try:
        from crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        # Initialize the crew
        print("🔧 Initializing CrewAI system...")
        crew = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Run health check
        print("🏥 Running health check...")
        errors = crew.preflight_health_check()
        
        if errors:
            print("❌ Health check failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("✅ Health check passed!")
        
        # Test basic functionality
        print("🧪 Testing basic functionality...")
        
        # Check if tools are available
        tools = [
            crew.policy_file_reader,
            crew.stakeholder_identifier,
            crew.knowledge_base_manager,
            crew.stakeholder_researcher,
            crew.topic_analyzer,
            crew.argument_generator,
            crew.a2a_messenger,
            crew.debate_moderator
        ]
        
        for tool in tools:
            print(f"  ✅ {tool.name}: {tool.description[:50]}...")
        
        print("✅ All tools available!")
        
        # Test LLM client
        print("🧪 Testing LLM client...")
        if crew.llm_client.is_available():
            provider_names = [p['name'] for p in crew.llm_client.providers]
            print(f"  ✅ LLM providers: {', '.join(provider_names)}")
        else:
            print("  ❌ No LLM providers available")
            return False
        
        print("✅ CrewAI integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ CrewAI integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_workflow():
    """Test a simple workflow"""
    print("\n🧪 Testing Simple Workflow...")
    
    try:
        from crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        # Initialize the crew
        crew = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Test stakeholder identification
        print("📋 Testing stakeholder identification...")
        policy_text = "All buildings must have fire sprinklers installed within 6 months."
        
        result = crew.stakeholder_identifier._run(policy_text)
        print(f"  📝 Result: {result[:200]}...")
        
        if "error" in result.lower():
            print("  ❌ Stakeholder identification failed")
            return False
        
        print("  ✅ Stakeholder identification successful")
        
        # Test topic analysis
        print("📋 Testing topic analysis...")
        result = crew.topic_analyzer._run(policy_text)
        print(f"  📝 Result: {result[:200]}...")
        
        if "error" in result.lower():
            print("  ❌ Topic analysis failed")
            return False
        
        print("  ✅ Topic analysis successful")
        
        print("✅ Simple workflow test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Simple workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🚀 Starting CrewAI Integration Tests")
    print("=" * 50)
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print(f"WEAVE_DISABLE_TRACING: {os.getenv('WEAVE_DISABLE_TRACING', 'NOT SET')}")
    print()
    
    # Run tests
    success = True
    
    if not test_crew_integration():
        success = False
    
    if not test_simple_workflow():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The CrewAI integration is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    main() 