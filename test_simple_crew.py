#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from langchain_google_genai import ChatGoogleGenerativeAI
from src.dynamic_crew.tools.custom_tool import PolicyFileReader
import logging

# Load environment variables
load_dotenv()

# Enable debug logging
logging.basicConfig(level=logging.ERROR)

# Test LLM directly first
print("🧪 Testing LLM directly...")
try:
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",  # Try with full model path
        google_api_key=os.getenv('GEMINI_API_KEY'),
        temperature=0.3
    )
    response = llm.invoke("Hello, this is a test")
    print(f"✅ LLM direct test successful: {response.content[:50]}...")
except Exception as e:
    print(f"❌ LLM direct test failed: {e}")
    exit(1)

# Create simple agent
simple_agent = Agent(
    role="Policy Reader",
    goal="Read policy files from the test_data folder",
    backstory="You are a simple agent that reads policy files",
    tools=[PolicyFileReader()],
    llm=llm,
    verbose=True
)

# Create simple task
simple_task = Task(
    description="Use PolicyFileReader to read the policy file policy_1.json from test_data folder",
    expected_output="Policy file content successfully read and displayed",
    agent=simple_agent
)

# Create minimal crew
crew = Crew(
    agents=[simple_agent],
    tasks=[simple_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    print("🧪 Testing simple crew without weave...")
    
    try:
        # Test the agent directly first
        print("Testing agent execution...")
        task_prompt = "Use PolicyFileReader to read the policy file policy_1.json from test_data folder"
        
        # Try with a more explicit prompt
        simple_task.description = "Read the file policy_1.json from the test_data directory using the PolicyFileReader tool. Return the complete policy content."
        
        result = crew.kickoff()
        print("\n✅ Success! Result:")
        print(result)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Try to get more specific error info
        if hasattr(e, '__cause__') and e.__cause__:
            print(f"Cause: {e.__cause__}")
        
        import traceback
        traceback.print_exc()