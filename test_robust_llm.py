#!/usr/bin/env python3
"""
Test script for the robust LLM client
"""

import os
import sys
import time

# Add the src directory to the path
sys.path.append('src/dynamic_crew')

def test_robust_llm_client():
    """Test the robust LLM client"""
    print("🧪 Testing Robust LLM Client...")
    
    try:
        from weave_client import get_weave_client
        
        # Initialize client
        client = get_weave_client()
        
        if not client.is_available():
            print("❌ No LLM providers available")
            return False
        
        # Log available providers
        provider_names = [p['name'] for p in client.providers]
        print(f"✅ Available providers: {', '.join(provider_names)}")
        
        # Test simple text generation
        test_prompt = "Say 'Hello, this is a test' and nothing else."
        print(f"📝 Testing with prompt: {test_prompt}")
        
        start_time = time.time()
        response = client.generate_text(test_prompt, temperature=0.1)
        end_time = time.time()
        
        print(f"⏱️  Response time: {end_time - start_time:.2f}s")
        print(f"📝 Response: '{response}'")
        print(f"📏 Response length: {len(response) if response else 0}")
        
        if not response or response.strip() == "":
            print("❌ Client returned empty response!")
            return False
        
        # Test JSON generation
        print("\n🧪 Testing JSON generation...")
        json_prompt = "Return a simple JSON object with a 'message' field containing 'Hello World'"
        
        start_time = time.time()
        json_response = client.generate_json(json_prompt, temperature=0.1)
        end_time = time.time()
        
        print(f"⏱️  JSON response time: {end_time - start_time:.2f}s")
        print(f"📝 JSON response: {json_response}")
        
        if "error" in json_response:
            print("❌ JSON generation failed!")
            return False
        
        # Test policy analysis
        print("\n🧪 Testing policy analysis...")
        policy_text = "All buildings must have fire sprinklers installed within 6 months."
        
        start_time = time.time()
        analysis = client.analyze_policy(
            policy_text=policy_text,
            analysis_type="stakeholder_identification"
        )
        end_time = time.time()
        
        print(f"⏱️  Analysis time: {end_time - start_time:.2f}s")
        print(f"📝 Analysis result: {analysis}")
        
        if "error" in analysis:
            print("❌ Policy analysis failed!")
            return False
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiting():
    """Test rate limiting behavior"""
    print("\n🧪 Testing rate limiting behavior...")
    
    try:
        from weave_client import get_weave_client
        
        client = get_weave_client()
        
        if not client.is_available():
            print("❌ No providers available for rate limit test")
            return False
        
        # Make multiple rapid requests to test rate limiting
        print("📡 Making multiple rapid requests...")
        
        for i in range(5):
            start_time = time.time()
            response = client.generate_text(f"Test request {i+1}", temperature=0.1)
            end_time = time.time()
            
            print(f"Request {i+1}: {end_time - start_time:.2f}s - '{response[:50]}...'")
            
            # Small delay between requests
            time.sleep(0.5)
        
        print("✅ Rate limiting test completed")
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Robust LLM Client Tests")
    print("=" * 50)
    
    # Check environment
    print("🔍 Environment Check:")
    print(f"GROQ_API_KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'NOT SET'}")
    print(f"OPENAI_API_KEY: {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    print(f"WEAVE_DISABLE_TRACING: {os.getenv('WEAVE_DISABLE_TRACING', 'NOT SET')}")
    print()
    
    # Run tests
    success = True
    
    if not test_robust_llm_client():
        success = False
    
    if not test_rate_limiting():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! The robust LLM client is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return success

if __name__ == "__main__":
    main() 