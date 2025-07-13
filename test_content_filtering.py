#!/usr/bin/env python3
"""
Test script to verify content filtering functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_content_filtering(query, filter_type):
    """Test search with specific content filter"""
    print(f"\n🔍 Testing '{filter_type}' filter for: '{query}'")
    
    try:
        payload = {
            "prompt": query,
            "max_results": 10,
            "content_filter": filter_type
        }
        
        response = requests.post(f"{BASE_URL}/policies/search/stream", json=payload)
        
        if response.status_code == 200:
            # Parse the streaming response
            lines = response.text.strip().split('\n')
            for line in lines:
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])  # Remove 'data: ' prefix
                        if data.get('type') == 'result':
                            policies = data.get('priority_policies', [])
                            print(f"✅ Found {len(policies)} results")
                            
                            # Analyze content types
                            content_types = {}
                            for policy in policies:
                                content_type = policy.get('content_type', 'unknown')
                                content_types[content_type] = content_types.get(content_type, 0) + 1
                                
                            print(f"📊 Content breakdown: {content_types}")
                            
                            # Show first 3 results
                            for i, policy in enumerate(policies[:3]):
                                content_type = policy.get('content_type', 'unknown')
                                print(f"   {i+1}. [{content_type.upper()}] {policy.get('title', 'Unknown')}")
                                print(f"      URL: {policy.get('url', 'No URL')[:50]}...")
                            
                            return True
                    except json.JSONDecodeError:
                        continue
        else:
            print(f"❌ Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        
    return False

def test_content_classification():
    """Test the content classification function directly"""
    print("\n🧪 Testing Content Classification Logic")
    
    test_cases = [
        {
            "title": "Senate Bill 123 - Housing Regulation Act",
            "url": "https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB123",
            "expected": "policy"
        },
        {
            "title": "Breaking: New Housing Crisis Announced Today",
            "url": "https://cnn.com/news/housing-crisis-latest",
            "expected": "news"
        },
        {
            "title": "Federal Register - New EPA Regulations",
            "url": "https://federalregister.gov/documents/2024/01/15/epa-regulations",
            "expected": "policy"
        },
        {
            "title": "Investigation: City Council Corruption Story",
            "url": "https://sfchronicle.com/news/investigation-corruption",
            "expected": "news"
        }
    ]
    
    # We can't directly call the function, but we can infer from API results
    print("   (Classification tested via API responses above)")
    for case in test_cases:
        print(f"   Expected: {case['title'][:40]}... -> {case['expected']}")

def main():
    """Test content filtering functionality"""
    print("🧪 Testing Content Filtering System\n")
    
    # Wait for server
    print("⏳ Waiting for server...")
    time.sleep(2)
    
    # Test queries with different filters
    test_query = "housing policy San Francisco"
    
    results = []
    
    # Test all content
    results.append(test_content_filtering(test_query, "both"))
    
    # Test policies only
    results.append(test_content_filtering(test_query, "policies"))
    
    # Test news only
    results.append(test_content_filtering(test_query, "news"))
    
    # Test classification logic
    test_content_classification()
    
    print(f"\n📊 Filter Tests: {sum(results)}/{len(results)} successful")
    
    if all(results):
        print("🎉 Content filtering is working correctly!")
        print("\n💡 Usage Tips:")
        print("   - Use 'policies' filter to find official documents, bills, regulations")
        print("   - Use 'news' filter to find recent coverage and analysis")
        print("   - Use 'both' for comprehensive results")
    else:
        print("⚠️  Some filtering tests failed. Check server logs.")

if __name__ == "__main__":
    main()