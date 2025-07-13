#!/usr/bin/env python3
"""
Test script for W&B Inference integration with CrewAI
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Check if we're in a virtual environment (simpler check)
if 'venv' not in sys.prefix and 'VIRTUAL_ENV' not in os.environ:
    print("⚠️  Not running in a virtual environment")
    print("   Please activate your virtual environment first:")
    print("   source venv/bin/activate")
    print("   Then run this script again.")
    sys.exit(1)

def test_wb_inference_setup():
    """Test the W&B Inference setup"""
    print("🧪 Testing W&B Inference Integration")
    print("=" * 50)
    
    # Check if WANDB_API_KEY is set
    wandb_api_key = os.getenv('WANDB_API_KEY')
    if not wandb_api_key:
        print("❌ WANDB_API_KEY not found in environment variables")
        print("   Please set WANDB_API_KEY with your W&B API key")
        print("   Example: export WANDB_API_KEY='your_api_key_here'")
        return False
    
    print(f"✅ WANDB_API_KEY found: {wandb_api_key[:10]}...")
    
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
        
        print("\n🎉 All tests passed! W&B Inference integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_llm_call():
    """Test a simple LLM call using W&B Inference"""
    print("\n🧪 Testing Simple LLM Call")
    print("=" * 50)
    
    try:
        from crewai import LLM
        
        # Get W&B API key
        wandb_api_key = os.getenv('WANDB_API_KEY')
        if not wandb_api_key:
            print("❌ WANDB_API_KEY not found")
            return False
        
        # Create W&B Inference LLM
        llm = LLM(
            model="openai/meta-llama/Llama-4-Scout-17B-16E-Instruct",
            api_base="https://api.inference.wandb.ai/v1",
            api_key=wandb_api_key,
            extra_headers={"OpenAI-Project": "crewai/pop_smoke"},
        )
        
        print("✅ W&B Inference LLM created")
        
        # Test a simple call
        test_prompt = "Hello! Please respond with a brief greeting."
        print(f"🔄 Testing LLM call with prompt: '{test_prompt}'")
        
        response = llm.call(test_prompt)
        print(f"✅ LLM Response: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple LLM call test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting W&B Inference Integration Tests")
    print("=" * 60)
    
    # Test 1: Setup and configuration
    setup_success = test_wb_inference_setup()
    
    # Test 2: Simple LLM call
    llm_success = test_simple_llm_call()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Setup Test: {'✅ PASSED' if setup_success else '❌ FAILED'}")
    print(f"LLM Call Test: {'✅ PASSED' if llm_success else '❌ FAILED'}")
    
    if setup_success and llm_success:
        print("\n🎉 All tests passed! W&B Inference integration is ready to use.")
        print("\n📝 Next steps:")
        print("   1. Make sure your WANDB_API_KEY is set in your environment")
        print("   2. You can now use the DynamicCrewAutomationForPolicyAnalysisAndDebateCrew")
        print("   3. The system will use W&B Inference for all LLM calls")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        sys.exit(1) 