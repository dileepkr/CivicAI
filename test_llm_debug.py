#!/usr/bin/env python3
"""
Debug LLM configuration to identify why empty responses are being returned
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_crewai_llm():
    """Test CrewAI LLM configuration"""
    print("🔍 Testing CrewAI LLM configuration...")
    
    try:
        from crewai import LLM
        
        # Test Groq configuration
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            print("✅ Found GROQ_API_KEY")
            try:
                llm = LLM(
                    model="llama3-8b-8192",
                    api_base="https://api.groq.com/openai/v1",
                    api_key=groq_key,
                )
                print("✅ CrewAI LLM with Groq configured successfully")
                
                # Check available methods
                print(f"🔍 Available methods on LLM object: {[method for method in dir(llm) if not method.startswith('_')]}")
                
                # Test a simple prompt
                test_prompt = "Say 'Hello, this is a test' and nothing else."
                print(f"🧪 Testing with prompt: {test_prompt}")
                
                # Try different method names
                try:
                    response = llm.call(test_prompt)
                    print(f"📝 Response (call): '{response}'")
                except Exception as e1:
                    print(f"❌ call failed: {e1}")
                    try:
                        # Try with a more structured approach
                        response = llm.call([{"role": "user", "content": test_prompt}])
                        print(f"📝 Response (call with messages): '{response}'")
                    except Exception as e2:
                        print(f"❌ call with messages failed: {e2}")
                        print("❌ All LLM methods failed!")
                        return
                
                print(f"📏 Response length: {len(response) if response else 0}")
                
                if not response or response.strip() == "":
                    print("❌ LLM returned empty response!")
                else:
                    print("✅ LLM working correctly")
                    
            except Exception as e:
                print(f"❌ Groq LLM test failed: {e}")
        else:
            print("⚠️  No GROQ_API_KEY found")
        
        # Test OpenAI fallback
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            print("\n🔄 Testing OpenAI fallback...")
            try:
                llm = LLM(
                    model="gpt-3.5-turbo",
                    api_key=openai_key,
                )
                print("✅ CrewAI LLM with OpenAI configured successfully")
                
                # Test a simple prompt
                test_prompt = "Say 'Hello, this is a test' and nothing else."
                print(f"🧪 Testing with prompt: {test_prompt}")
                
                response = llm.call(test_prompt)
                print(f"📝 Response: '{response}'")
                print(f"📏 Response length: {len(response) if response else 0}")
                
                if not response or response.strip() == "":
                    print("❌ LLM returned empty response!")
                else:
                    print("✅ LLM working correctly")
                    
            except Exception as e:
                print(f"❌ OpenAI LLM test failed: {e}")
        else:
            print("⚠️  No OPENAI_API_KEY found")
            
    except Exception as e:
        print(f"❌ CrewAI import failed: {e}")

def test_weave_client():
    """Test Weave client LLM"""
    print("\n🔍 Testing Weave client LLM...")
    
    try:
        sys.path.append('src/dynamic_crew')
        from weave_client import get_weave_client
        
        weave_client = get_weave_client()
        if weave_client.is_available():
            print("✅ Weave client is available")
            
            # Test a simple prompt
            test_prompt = "Say 'Hello, this is a test' and nothing else."
            print(f"🧪 Testing with prompt: {test_prompt}")
            
            response = weave_client.generate_text(test_prompt, temperature=0.1)
            print(f"📝 Response: '{response}'")
            print(f"📏 Response length: {len(response) if response else 0}")
            
            if not response or response.strip() == "":
                print("❌ Weave client returned empty response!")
            else:
                print("✅ Weave client working correctly")
        else:
            print("❌ Weave client not available")
            
    except Exception as e:
        print(f"❌ Weave client test failed: {e}")

def test_agent_creation():
    """Test agent creation with LLM"""
    print("\n🔍 Testing agent creation...")
    
    try:
        # Add the src directory to the path
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        print("✅ Crew instance created successfully")
        
        # Test creating a simple agent
        from crewai import Agent
        
        test_agent = Agent(
            role="Test Agent",
            goal="Test the LLM",
            backstory="A test agent",
            llm=crew_instance.llm,
            verbose=True
        )
        print("✅ Test agent created successfully")
        
        # Test agent execution
        test_task = "Say 'Hello from test agent' and nothing else."
        print(f"🧪 Testing agent with task: {test_task}")
        
        # This might not work directly, but let's see what happens
        try:
            # Try to get the agent's response
            response = test_agent.llm.call(test_task)
            print(f"📝 Agent LLM Response: '{response}'")
            print(f"📏 Response length: {len(response) if response else 0}")
        except Exception as e:
            print(f"⚠️  Agent LLM test failed: {e}")
            
    except Exception as e:
        print(f"❌ Agent creation test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting LLM Debug Tests...\n")
    
    test_crewai_llm()
    test_weave_client()
    test_agent_creation()
    
    print("\n🏁 LLM Debug Tests Complete!") 