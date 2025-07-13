#!/usr/bin/env python
"""
Simple test script to verify the API endpoints are working
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_policies():
    """Test policies endpoint"""
    print("\n🔍 Testing policies endpoint...")
    try:
        response = requests.get(f"{API_BASE}/policies")
        if response.status_code == 200:
            policies = response.json()
            print(f"✅ Found {len(policies)} policies")
            for policy in policies:
                print(f"   - {policy['id']}: {policy['title']}")
            return True
        else:
            print(f"❌ Policies failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Policies error: {e}")
        return False

def test_start_debate():
    """Test starting a debate"""
    print("\n🔍 Testing debate start...")
    try:
        data = {
            "policy_name": "policy_1",
            "system_type": "debug"
        }
        response = requests.post(f"{API_BASE}/debates/start", json=data)
        if response.status_code == 200:
            session = response.json()
            print(f"✅ Debate session created: {session['session_id']}")
            return session['session_id']
        else:
            print(f"❌ Debate start failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Debate start error: {e}")
        return None

def test_crew_status():
    """Test crew system status"""
    print("\n🔍 Testing crew system status...")
    try:
        response = requests.get(f"{API_BASE}/crew/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Crew status: {status['status']}")
            print(f"   Message: {status['message']}")
            print(f"   Components: {status['components']}")
            return True
        else:
            print(f"❌ Crew status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Crew status error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing CivicAI Policy Debate API")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ API is not running or not accessible")
        return
    
    # Test policies
    if not test_policies():
        print("\n❌ Policies endpoint failed")
        return
    
    # Test crew status
    test_crew_status()
    
    # Test debate start
    session_id = test_start_debate()
    if session_id:
        print(f"\n✅ All basic tests passed!")
        print(f"   Session ID: {session_id}")
        print(f"   You can now test WebSocket streaming with session: {session_id}")
    else:
        print("\n❌ Debate start failed")

if __name__ == "__main__":
    main() 