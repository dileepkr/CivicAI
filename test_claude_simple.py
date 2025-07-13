#!/usr/bin/env python3
"""
Simple test script to verify Claude LLM configuration
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_claude_direct():
    """Test Claude directly with anthropic library"""
    try:
        import anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found")
            return False
            
        print("🔄 Testing Claude directly with anthropic library...")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Test with a simple message
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hello! Please respond with 'Claude is working!'"}
            ]
        )
        
        print(f"✅ Claude response: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ Direct Claude test failed: {e}")
        return False

def test_crewai_claude():
    """Test Claude through CrewAI"""
    try:
        from crewai import LLM
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("❌ ANTHROPIC_API_KEY not found")
            return False
            
        print("🔄 Testing Claude through CrewAI...")
        
        llm = LLM(
            model="claude-3-5-sonnet-20241022",
            api_key=api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        response = llm.call("Hello! Please respond with 'Claude is working!'")
        print(f"✅ CrewAI Claude response: {response}")
        return True
        
    except Exception as e:
        print(f"❌ CrewAI Claude test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Claude Test")
    print("=" * 30)
    
    # Test 1: Direct anthropic library
    direct_success = test_claude_direct()
    
    # Test 2: CrewAI wrapper
    crewai_success = test_crewai_claude()
    
    print("\n📊 Results:")
    print(f"Direct Test: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"CrewAI Test: {'✅ PASSED' if crewai_success else '❌ FAILED'}")
    
    if direct_success and crewai_success:
        print("\n🎉 All tests passed! Claude is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.") 