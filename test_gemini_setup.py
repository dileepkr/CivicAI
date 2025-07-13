#!/usr/bin/env python3
"""
Test script for Gemini LLM integration with CrewAI
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_gemini_setup():
    """Test the Gemini LLM setup"""
    print("🧪 Testing Gemini LLM Integration")
    print("=" * 50)
    
    # Check if GOOGLE_API_KEY is set
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("   Please set GOOGLE_API_KEY with your Google API key")
        print("   Example: export GOOGLE_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ GOOGLE_API_KEY found: {google_api_key[:10]}...")
    
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
            if hasattr(crew.llm, 'provider'):
                print(f"   Provider: {crew.llm.provider}")
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
        
        print("\n🎉 All tests passed! Gemini LLM integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_gemini_call():
    """Test a simple Gemini LLM call"""
    print("\n🧪 Testing Simple Gemini LLM Call")
    print("=" * 50)
    
    try:
        from crewai import LLM
        
        # Get Google API key
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            print("❌ GOOGLE_API_KEY not found")
            return False
        
        # Create Gemini LLM
        llm = LLM(
            model="gemini-1.5-flash",
            api_key=google_api_key,
            provider="google"
        )
        
        print("✅ Gemini LLM created")
        
        # Test a simple call
        test_prompt = "Hello! Please respond with a brief greeting."
        print(f"🔄 Testing LLM call with prompt: '{test_prompt}'")
        
        response = llm.call(test_prompt)
        print(f"✅ LLM Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple Gemini LLM call test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_providers():
    """Test fallback providers if Gemini is not available"""
    print("\n🧪 Testing Fallback Providers")
    print("=" * 50)
    
    try:
        from crewai import LLM
        
        # Test Groq fallback
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            print("🔄 Testing Groq fallback...")
            llm = LLM(
                model="llama3-8b-8192",
                api_base="https://api.groq.com/openai/v1",
                api_key=groq_api_key,
            )
            
            test_prompt = "Hello! Please respond with a brief greeting."
            response = llm.call(test_prompt)
            print(f"✅ Groq Response: {response[:200]}...")
            return True
        
        # Test OpenAI fallback
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            print("🔄 Testing OpenAI fallback...")
            llm = LLM(
                model="gpt-3.5-turbo",
                api_key=openai_api_key,
            )
            
            test_prompt = "Hello! Please respond with a brief greeting."
            response = llm.call(test_prompt)
            print(f"✅ OpenAI Response: {response[:200]}...")
            return True
        
        print("❌ No fallback API keys found")
        return False
        
    except Exception as e:
        print(f"❌ Fallback provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Gemini LLM Integration Tests")
    print("=" * 60)
    
    # Test 1: Gemini setup
    gemini_success = test_gemini_setup()
    
    # Test 2: Simple Gemini call
    gemini_call_success = test_simple_gemini_call()
    
    # Test 3: Fallback providers
    fallback_success = test_fallback_providers()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Gemini Setup Test: {'✅ PASSED' if gemini_success else '❌ FAILED'}")
    print(f"Gemini Call Test: {'✅ PASSED' if gemini_call_success else '❌ FAILED'}")
    print(f"Fallback Test: {'✅ PASSED' if fallback_success else '❌ FAILED'}")
    
    if gemini_success and gemini_call_success:
        print("\n🎉 All Gemini tests passed! Gemini LLM integration is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Make sure your GOOGLE_API_KEY is set in your environment")
        print("   2. You can now use the DynamicCrewAutomationForPolicyAnalysisAndDebateCrew")
        print("   3. The system will use Gemini for all LLM calls")
    elif fallback_success:
        print("\n⚠️  Gemini not available, but fallback providers are working.")
        print("   The system will use fallback LLM providers.")
    else:
        print("\n❌ All tests failed. Please check the error messages above.")
        sys.exit(1) 