#!/usr/bin/env python3
"""
Test the API to ensure policy information is being passed correctly
"""

import requests
import json
import time

def test_policy_information_flow():
    """Test that policy information flows correctly through the API"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Policy Information Flow...")
    
    # Wait for API to start
    time.sleep(3)
    
    try:
        # Test 1: Create a debate session
        print("\n1. Creating debate session...")
        response = requests.post(
            f"{base_url}/debates/start",
            json={
                "policy_name": "policy_1",
                "system_type": "human"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create debate session: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        session_data = response.json()
        session_id = session_data["session_id"]
        print(f"✅ Created debate session: {session_id}")
        
        # Test 2: Wait for debate to process and check messages
        print("\n2. Waiting for debate to process...")
        time.sleep(10)  # Give time for debate to run
        
        # Check messages to see if policy content is being processed
        response = requests.get(f"{base_url}/debates/{session_id}/messages")
        if response.status_code == 200:
            messages_data = response.json()
            messages = messages_data.get("messages", [])
            
            print(f"📨 Found {len(messages)} messages")
            
            # Look for messages that indicate policy content was loaded
            policy_loaded = False
            stakeholder_found = False
            
            for msg in messages:
                content = msg.get("content", "")
                if "Policy:" in content and "AB 1248" in content:
                    policy_loaded = True
                    print(f"✅ Policy content found in message: {content[:100]}...")
                
                if "Created" in content and any(word in content for word in ["Tenant", "Landlord", "Property"]):
                    stakeholder_found = True
                    print(f"✅ Stakeholder creation found: {content[:100]}...")
            
            # Check if we found evidence that policy content was processed
            if policy_loaded:
                print("✅ Policy content is being loaded and processed correctly!")
                return True
            elif stakeholder_found:
                print("✅ Stakeholder creation suggests policy content was processed!")
                return True
            else:
                print("⚠️  No clear evidence of policy content processing")
                # Show some messages for debugging
                print("\nRecent messages:")
                for i, msg in enumerate(messages[-5:], 1):
                    print(f"   {i}. [{msg.get('sender', 'unknown')}] {msg.get('content', '')[:80]}...")
                return False
        else:
            print(f"❌ Could not retrieve messages: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

if __name__ == "__main__":
    success = test_policy_information_flow()
    if success:
        print("\n✅ Policy information flow test passed!")
    else:
        print("\n❌ Policy information flow test failed!") 