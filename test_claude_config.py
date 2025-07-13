#!/usr/bin/env python3
"""
Test script to verify Claude LLM configuration in CrewAI system
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_claude_configuration():
    """Test that Claude is properly configured as the primary LLM"""
    
    print("🧪 Testing Claude LLM Configuration")
    print("=" * 50)
    
    # Check if ANTHROPIC_API_KEY is set
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEY not found in environment variables")
        print("   Please set your Anthropic API key:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return False
    
    print("✅ ANTHROPIC_API_KEY found")
    
    try:
        # Import the crew system
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        print("🔄 Initializing CrewAI system with Claude...")
        
        # Initialize the crew system
        crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Check if LLM is properly configured
        if hasattr(crew_system, 'llm') and crew_system.llm:
            model_name = getattr(crew_system.llm, 'model', 'Unknown')
            provider = getattr(crew_system.llm, 'provider', 'Unknown')
            
            print(f"✅ LLM configured successfully")
            print(f"   Model: {model_name}")
            print(f"   Provider: {provider}")
            
            # Test if it's actually Claude
            if 'claude' in model_name.lower():
                print("🎉 Claude is successfully configured as the primary LLM!")
                
                # Test a simple call
                try:
                    print("🔄 Testing Claude with a simple prompt...")
                    test_response = crew_system.llm.call("Hello, this is a test. Please respond with 'Claude is working!'")
                    print(f"✅ Claude response: {test_response[:100]}...")
                    return True
                except Exception as e:
                    print(f"❌ Claude test call failed: {e}")
                    return False
            else:
                print(f"⚠️  Expected Claude but got: {model_name}")
                print("   This might indicate a fallback to another provider")
                return False
        else:
            print("❌ LLM not properly configured")
            return False
            
    except Exception as e:
        print(f"❌ Failed to initialize CrewAI system: {e}")
        return False

def test_agent_creation():
    """Test that agents are created with Claude LLM"""
    
    print("\n🧪 Testing Agent Creation with Claude")
    print("=" * 50)
    
    try:
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Test creating a simple agent
        print("🔄 Creating test agent...")
        test_agent = crew_system.coordinator_agent()
        
        if hasattr(test_agent, 'llm') and test_agent.llm:
            model_name = getattr(test_agent.llm, 'model', 'Unknown')
            if 'claude' in model_name.lower():
                print("✅ Agent created successfully with Claude LLM")
                return True
            else:
                print(f"⚠️  Agent created but not using Claude: {model_name}")
                return False
        else:
            print("❌ Agent LLM not properly configured")
            return False
            
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Claude Configuration Test Suite")
    print("=" * 60)
    
    # Test 1: Basic configuration
    config_success = test_claude_configuration()
    
    # Test 2: Agent creation
    agent_success = test_agent_creation()
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 30)
    print(f"Configuration Test: {'✅ PASSED' if config_success else '❌ FAILED'}")
    print(f"Agent Creation Test: {'✅ PASSED' if agent_success else '❌ FAILED'}")
    
    if config_success and agent_success:
        print("\n🎉 All tests passed! Claude is properly configured for all CrewAI agents.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        sys.exit(1) 