#!/usr/bin/env python3
"""
Quick test script to verify API endpoints are working
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_crew_status():
    """Test crew status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/crew/status")
        data = response.json()
        print(f"✅ Crew status: {response.status_code}")
        print(f"   - Policy Discovery Agent: {data['components'].get('policy_discovery_agent', False)}")
        print(f"   - A2A Protocol: {data['components'].get('a2a_protocol', False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Crew status failed: {e}")
        return False

def test_policies():
    """Test policies endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/policies")
        data = response.json()
        print(f"✅ Policies: {response.status_code} - Found {len(data)} policies")
        if data:
            print(f"   - First policy: {data[0].get('title', 'Unknown')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Policies test failed: {e}")
        return False

def test_debate_start():
    """Test starting a debate"""
    try:
        payload = {
            "policy_name": "housing",
            "system_type": "debug"
        }
        response = requests.post(f"{BASE_URL}/debates/start", json=payload)
        data = response.json()
        print(f"✅ Debate start: {response.status_code}")
        if response.status_code == 200:
            session_id = data.get("session_id")
            print(f"   - Session ID: {session_id}")
            return session_id
        return None
    except Exception as e:
        print(f"❌ Debate start failed: {e}")
        return None

def test_a2a_info(session_id):
    """Test A2A session info"""
    try:
        response = requests.get(f"{BASE_URL}/debates/{session_id}/a2a-info")
        data = response.json()
        print(f"✅ A2A Info: {response.status_code}")
        if response.status_code == 200:
            print(f"   - A2A Available: {data.get('a2a_available', False)}")
            print(f"   - Agent Count: {data['session_info'].get('agent_count', 0)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ A2A info failed: {e}")
        return False

def main():
    """Run endpoint tests"""
    print("🧪 Testing CivicAI API Endpoints\n")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    results = []
    
    # Test basic endpoints
    results.append(test_health())
    results.append(test_crew_status())
    results.append(test_policies())
    
    # Test debate functionality
    session_id = test_debate_start()
    if session_id:
        results.append(True)
        results.append(test_a2a_info(session_id))
    else:
        results.extend([False, False])
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All endpoint tests passed!")
    else:
        print("⚠️  Some tests failed. Check server logs for details.")

if __name__ == "__main__":
    main()