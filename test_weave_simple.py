#!/usr/bin/env python3
"""
Simple test script for Weave inference integration
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Disable Weave tracing to prevent circular reference issues
os.environ['WEAVE_DISABLE_TRACING'] = '1'
os.environ['WEAVE_AUTO_TRACE'] = '0'
os.environ['WEAVE_AUTO_PATCH'] = '0'
os.environ['WANDB_DISABLE_TRACING'] = '1'

def test_weave_inference_client():
    """Test the dedicated Weave inference client"""
    print("🧪 Testing Weave inference client...")
    
    try:
        from dynamic_crew.weave_inference_client import WeaveInferenceClient, initialize_weave_inference_client
        print("✅ Weave inference client imports successful")
        
        # Initialize client
        client = initialize_weave_inference_client("gpt2", "test-project")
        print(f"✅ Weave inference client initialized: {client.available}")
        
        if client.available:
            # Test text generation
            test_prompt = "Hello, this is a test of Weave inference."
            print(f"🤖 Testing text generation: {test_prompt}")
            
            response = client.generate_text(test_prompt, temperature=0.7, max_tokens=100)
            print(f"✅ Text generation successful: {response[:100]}...")
            
            return True
        else:
            print("⚠️  Weave inference not available")
            return False
            
    except Exception as e:
        print(f"❌ Weave inference client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crewai_llm_wrapper():
    """Test the CrewAI LLM wrapper with Weave inference"""
    print("\n🧪 Testing CrewAI LLM wrapper...")
    
    try:
        from dynamic_crew.crew import RobustCrewAILLM
        from dynamic_crew.weave_inference_client import initialize_weave_inference_client
        print("✅ CrewAI LLM wrapper imports successful")
        
        # Initialize Weave inference client
        weave_client = initialize_weave_inference_client("gpt2", "test-project")
        
        if weave_client.available:
            # Create CrewAI LLM wrapper
            llm_wrapper = RobustCrewAILLM(weave_client)
            print(f"✅ CrewAI LLM wrapper initialized with provider: {llm_wrapper.provider_name}")
            
            # Test CrewAI LLM call
            test_prompt = "Generate a brief policy analysis summary."
            print(f"🤖 Testing CrewAI LLM call: {test_prompt}")
            
            response = llm_wrapper.call(test_prompt)
            print(f"✅ CrewAI LLM call successful: {response[:100]}...")
            
            return True
        else:
            print("⚠️  Weave inference not available for CrewAI test")
            return False
            
    except Exception as e:
        print(f"❌ CrewAI LLM wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_crew_system_initialization():
    """Test the full crew system initialization"""
    print("\n🧪 Testing crew system initialization...")
    
    try:
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        print("✅ Crew system imports successful")
        
        # Initialize crew system
        crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        print("✅ Crew system initialization successful")
        
        # Check LLM configuration
        if hasattr(crew_system, 'llm'):
            print(f"✅ LLM configured: {type(crew_system.llm).__name__}")
            if hasattr(crew_system.llm, 'provider_name'):
                print(f"   Provider: {crew_system.llm.provider_name}")
            if hasattr(crew_system.llm, 'model_name'):
                print(f"   Model: {crew_system.llm.model_name}")
        else:
            print("⚠️  No LLM configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Crew system initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Weave inference integration tests...")
    print("=" * 60)
    
    # Test 1: Weave inference client
    test1_passed = test_weave_inference_client()
    
    # Test 2: CrewAI LLM wrapper
    test2_passed = test_crewai_llm_wrapper()
    
    # Test 3: Crew system initialization
    test3_passed = test_crew_system_initialization()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Weave inference client: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   CrewAI LLM wrapper: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"   Crew system initialization: {'✅ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\n🎯 Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("\n🎉 Weave inference integration is working correctly without circular reference errors!")
    else:
        print("\n⚠️  Some issues detected. Please check the error messages above.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main()) 