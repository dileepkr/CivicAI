#!/usr/bin/env python3
"""
Simple test to diagnose LLM issues
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_crew_initialization():
    """Test crew initialization with fallback LLM"""
    print("🧪 Testing Crew Initialization")
    print("=" * 50)
    
    try:
        # Test importing the crew module
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        print("✅ Successfully imported DynamicCrewAutomationForPolicyAnalysisAndDebateCrew")
        
        # Test creating an instance
        print("🔄 Creating crew instance...")
        crew = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        print("✅ Crew instance created successfully")
        
        # Test LLM configuration
        if hasattr(crew, 'llm') and crew.llm:
            print(f"✅ LLM configured: {type(crew.llm).__name__}")
            if hasattr(crew.llm, 'model'):
                print(f"   Model: {crew.llm.model}")
            if hasattr(crew.llm, 'api_base'):
                print(f"   API Base: {crew.llm.api_base}")
        else:
            print("❌ LLM not properly configured")
            return False
        
        # Test health check
        print("🔄 Running health check...")
        health_errors = crew.preflight_health_check()
        if health_errors:
            print(f"❌ Health check failed: {health_errors}")
            return False
        else:
            print("✅ Health check passed")
        
        # Test creating a simple agent
        print("🔄 Testing agent creation...")
        try:
            coordinator = crew.coordinator_agent()
            print("✅ Coordinator agent created successfully")
        except Exception as e:
            print(f"❌ Agent creation failed: {e}")
            return False
        
        print("\n🎉 All tests passed! Crew system is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_llm_call():
    """Test a simple LLM call"""
    print("\n🧪 Testing Simple LLM Call")
    print("=" * 50)
    
    try:
        from crewai import LLM
        
        # Get API keys
        groq_api_key = os.getenv('GROQ_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if groq_api_key:
            print("🔄 Testing Groq LLM...")
            llm = LLM(
                model="llama3-8b-8192",
                api_base="https://api.groq.com/openai/v1",
                api_key=groq_api_key,
            )
            
            test_prompt = "Hello! Please respond with a brief greeting."
            print(f"🔄 Testing LLM call with prompt: '{test_prompt}'")
            
            response = llm.call(test_prompt)
            print(f"✅ LLM Response: {response[:200]}...")
            return True
            
        elif openai_api_key:
            print("🔄 Testing OpenAI LLM...")
            llm = LLM(
                model="gpt-3.5-turbo",
                api_key=openai_api_key,
            )
            
            test_prompt = "Hello! Please respond with a brief greeting."
            print(f"🔄 Testing LLM call with prompt: '{test_prompt}'")
            
            response = llm.call(test_prompt)
            print(f"✅ LLM Response: {response[:200]}...")
            return True
        else:
            print("❌ No API keys found")
            return False
        
    except Exception as e:
        print(f"❌ Simple LLM call test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting LLM Fix Tests")
    print("=" * 60)
    
    # Test 1: Crew initialization
    crew_success = test_crew_initialization()
    
    # Test 2: Simple LLM call
    llm_success = test_simple_llm_call()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Crew Test: {'✅ PASSED' if crew_success else '❌ FAILED'}")
    print(f"LLM Call Test: {'✅ PASSED' if llm_success else '❌ FAILED'}")
    
    if crew_success and llm_success:
        print("\n🎉 All tests passed! The LLM issues are fixed.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        sys.exit(1) 