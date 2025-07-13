#!/usr/bin/env python3
"""
Test script to verify focused search behavior
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_focused_search(query):
    """Test search with a specific query"""
    print(f"\n🔍 Testing search for: '{query}'")
    
    try:
        payload = {
            "prompt": query,
            "max_results": 5
        }
        
        # Using regular POST request to see the immediate response
        response = requests.post(f"{BASE_URL}/policies/search/stream", json=payload)
        
        if response.status_code == 200:
            # Parse the streaming response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    if data.get('type') == 'result':
                        policies = data.get('priority_policies', [])
                        print(f"✅ Found {len(policies)} policies")
                        for i, policy in enumerate(policies[:3]):  # Show first 3
                            print(f"   {i+1}. {policy.get('title', 'Unknown')}")
                            print(f"      Score: {policy.get('relevance_score', 0):.2f}")
                        return True
                    elif data.get('type') == 'status':
                        print(f"   Status: {data.get('message', 'Processing...')}")
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        
    return False

def main():
    """Test focused search queries"""
    print("🧪 Testing Focused Policy Search\n")
    
    # Wait for server
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    # Test different types of queries
    test_queries = [
        "housing affordability",
        "transportation policy", 
        "climate change regulations",
        "small business licensing"
    ]
    
    results = []
    for query in test_queries:
        results.append(test_focused_search(query))
    
    print(f"\n📊 Search Tests: {sum(results)}/{len(results)} successful")

if __name__ == "__main__":
    main()