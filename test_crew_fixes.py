#!/usr/bin/env python3
"""
Test script to verify the TopicAnalyzer tool fixes work properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.dynamic_crew.tools.custom_tool import TopicAnalyzer

def test_topic_analyzer():
    """Test the TopicAnalyzer tool with various inputs"""
    print("🧪 Testing TopicAnalyzer tool fixes...")
    
    topic_analyzer = TopicAnalyzer()
    
    # Test 1: Empty stakeholder list
    print("\n📋 Test 1: Empty stakeholder list")
    try:
        result1 = topic_analyzer._run("Test policy content", "")
        print(f"✅ Result: {result1[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: None stakeholder list
    print("\n📋 Test 2: None stakeholder list")
    try:
        result2 = topic_analyzer._run("Test policy content", None)
        print(f"✅ Result: {result2[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Valid stakeholder list
    print("\n📋 Test 3: Valid stakeholder list")
    try:
        stakeholders = {
            "stakeholders": [
                {"name": "Tenants", "type": "residents"},
                {"name": "Landlords", "type": "property_owners"}
            ]
        }
        result3 = topic_analyzer._run("Test policy content", stakeholders)
        print(f"✅ Result: {result3[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: List stakeholder list
    print("\n📋 Test 4: List stakeholder list")
    try:
        stakeholders_list = [
            {"name": "Tenants", "type": "residents"},
            {"name": "Landlords", "type": "property_owners"}
        ]
        result4 = topic_analyzer._run("Test policy content", stakeholders_list)
        print(f"✅ Result: {result4[:200]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n✅ TopicAnalyzer tests completed!")

if __name__ == "__main__":
    test_topic_analyzer() 