#!/usr/bin/env python3
"""
Test script to verify policy loading works correctly after the fix
"""

import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

from dynamic_crew.debate.systems.human import HumanDebateSystem

def test_policy_loading():
    """Test that policy loading works correctly"""
    print("🔍 Testing Policy Loading...")
    
    # Initialize the debate system
    human_system = HumanDebateSystem()
    
    # Test loading policy_1
    print("\n1. Testing policy_1 loading...")
    policy_info = human_system.load_policy("policy_1")
    
    if "error" in policy_info:
        print(f"❌ Error loading policy_1: {policy_info['error']}")
        return False
    else:
        print(f"✅ Policy loaded successfully!")
        print(f"   Title: {policy_info.get('title', 'No title')}")
        print(f"   Text length: {len(policy_info.get('text', ''))} characters")
        print(f"   Has text content: {'Yes' if policy_info.get('text') else 'No'}")
        
        # Test stakeholder identification with the loaded policy
        print("\n2. Testing stakeholder identification...")
        policy_text = policy_info.get('text', '')
        
        if policy_text:
            stakeholder_list = human_system.identify_stakeholders(policy_text)
            if stakeholder_list:
                print(f"✅ Stakeholder identification successful!")
                print(f"   Found {len(stakeholder_list)} stakeholders")
                for i, stakeholder in enumerate(stakeholder_list[:3], 1):
                    print(f"   {i}. {stakeholder.get('name', 'Unknown')}")
            else:
                print("❌ No stakeholders identified")
                return False
        else:
            print("❌ No policy text found")
            return False
    
    return True

if __name__ == "__main__":
    success = test_policy_loading()
    if success:
        print("\n✅ Policy loading test passed!")
    else:
        print("\n❌ Policy loading test failed!") 