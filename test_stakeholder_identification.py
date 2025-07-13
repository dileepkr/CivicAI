#!/usr/bin/env python3
"""
Test stakeholder identification with full policy text
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_stakeholder_identification():
    """Test stakeholder identification with full policy text"""
    print("🔍 Testing Stakeholder Identification with Full Policy Text...")
    
    try:
        # Add the src directory to the path
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from dynamic_crew.tools.custom_tool import StakeholderIdentifier
        
        # Create stakeholder identifier
        stakeholder_identifier = StakeholderIdentifier()
        print("✅ StakeholderIdentifier created successfully")
        
        # Sample policy text (this should be the full policy content)
        sample_policy_text = """
        POLICY: Rent Control and Tenant Protection Act
        
        Section 1: Purpose
        This policy aims to protect tenants from excessive rent increases and provide stability in the housing market.
        
        Section 2: Rent Control Provisions
        2.1 Annual rent increases shall be limited to 3% or the rate of inflation, whichever is lower.
        2.2 Landlords must provide 60 days notice for any rent increase above 5%.
        2.3 No-fault evictions are prohibited except for owner move-in or substantial renovations.
        
        Section 3: Tenant Rights
        3.1 Tenants have the right to organize and form tenant associations.
        3.2 Landlords must provide written notice of all rent increases.
        3.3 Tenants may withhold rent if essential services are not provided.
        
        Section 4: Landlord Obligations
        4.1 Landlords must maintain habitable living conditions.
        4.2 Landlords must provide 30 days notice for non-payment evictions.
        4.3 Landlords must register all rental units with the housing authority.
        
        Section 5: Enforcement
        5.1 The housing authority shall enforce these provisions.
        5.2 Violations may result in fines up to $10,000 per violation.
        5.3 Tenants may file complaints with the housing authority.
        """
        
        print(f"📄 Sample policy text length: {len(sample_policy_text)} characters")
        print(f"📄 Policy text preview: {sample_policy_text[:200]}...")
        
        # Test stakeholder identification
        print("\n🧪 Running stakeholder identification...")
        result = stakeholder_identifier._run(sample_policy_text)
        
        print(f"📝 Stakeholder identification result: {result}")
        
        if result.startswith("Error"):
            print("❌ Stakeholder identification failed!")
            return False
        
        try:
            # Parse the result
            stakeholder_data = json.loads(result)
            print("✅ Result is valid JSON")
            
            if 'stakeholders' in stakeholder_data:
                stakeholders = stakeholder_data['stakeholders']
                print(f"✅ Found {len(stakeholders)} stakeholders:")
                
                for i, stakeholder in enumerate(stakeholders, 1):
                    name = stakeholder.get('name', 'Unknown')
                    stakeholder_type = stakeholder.get('type', 'unknown')
                    likely_stance = stakeholder.get('likely_stance', 'unknown')
                    interests = stakeholder.get('interests', [])
                    key_concerns = stakeholder.get('key_concerns', [])
                    
                    print(f"   {i}. {name} ({stakeholder_type})")
                    print(f"      Stance: {likely_stance}")
                    print(f"      Interests: {', '.join(interests[:3])}")
                    if key_concerns:
                        print(f"      Key Concerns: {', '.join(key_concerns[:2])}")
                
                # Check if we have real stakeholders (not just "Unknown")
                real_stakeholders = [s for s in stakeholders if s.get('name', '').lower() != 'unknown']
                if real_stakeholders:
                    print(f"✅ Found {len(real_stakeholders)} real stakeholders (not 'Unknown')")
                    return True
                else:
                    print("❌ All stakeholders are 'Unknown' - identification may have failed")
                    return False
            else:
                print("❌ No 'stakeholders' key in result")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON result: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Stakeholder identification test failed: {e}")
        return False

def test_crew_stakeholder_identification():
    """Test stakeholder identification through the crew system"""
    print("\n🔍 Testing Stakeholder Identification through Crew System...")
    
    try:
        # Add the src directory to the path
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
        
        # Create crew instance
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        print("✅ Crew instance created successfully")
        
        # Sample policy text
        sample_policy_text = """
        POLICY: Rent Control and Tenant Protection Act
        
        Section 1: Purpose
        This policy aims to protect tenants from excessive rent increases and provide stability in the housing market.
        
        Section 2: Rent Control Provisions
        2.1 Annual rent increases shall be limited to 3% or the rate of inflation, whichever is lower.
        2.2 Landlords must provide 60 days notice for any rent increase above 5%.
        2.3 No-fault evictions are prohibited except for owner move-in or substantial renovations.
        
        Section 3: Tenant Rights
        3.1 Tenants have the right to organize and form tenant associations.
        3.2 Landlords must provide written notice of all rent increases.
        3.3 Tenants may withhold rent if essential services are not provided.
        
        Section 4: Landlord Obligations
        4.1 Landlords must maintain habitable living conditions.
        4.2 Landlords must provide 30 days notice for non-payment evictions.
        4.3 Landlords must register all rental units with the housing authority.
        
        Section 5: Enforcement
        5.1 The housing authority shall enforce these provisions.
        5.2 Violations may result in fines up to $10,000 per violation.
        5.3 Tenants may file complaints with the housing authority.
        """
        
        print(f"📄 Sample policy text length: {len(sample_policy_text)} characters")
        
        # Test stakeholder identification through the tool
        print("\n🧪 Running stakeholder identification through crew tool...")
        result = crew_instance.stakeholder_identifier._run(sample_policy_text)
        
        print(f"📝 Crew stakeholder identification result: {result}")
        
        if result.startswith("Error"):
            print("❌ Crew stakeholder identification failed!")
            return False
        
        try:
            # Parse the result
            stakeholder_data = json.loads(result)
            print("✅ Crew result is valid JSON")
            
            if 'stakeholders' in stakeholder_data:
                stakeholders = stakeholder_data['stakeholders']
                print(f"✅ Crew found {len(stakeholders)} stakeholders:")
                
                for i, stakeholder in enumerate(stakeholders, 1):
                    name = stakeholder.get('name', 'Unknown')
                    stakeholder_type = stakeholder.get('type', 'unknown')
                    likely_stance = stakeholder.get('likely_stance', 'unknown')
                    
                    print(f"   {i}. {name} ({stakeholder_type}) - Stance: {likely_stance}")
                
                # Check if we have real stakeholders (not just "Unknown")
                real_stakeholders = [s for s in stakeholders if s.get('name', '').lower() != 'unknown']
                if real_stakeholders:
                    print(f"✅ Crew found {len(real_stakeholders)} real stakeholders (not 'Unknown')")
                    return True
                else:
                    print("❌ Crew found only 'Unknown' stakeholders - identification may have failed")
                    return False
            else:
                print("❌ No 'stakeholders' key in crew result")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse crew JSON result: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Crew stakeholder identification test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Stakeholder Identification Tests...\n")
    
    # Test direct stakeholder identification
    direct_success = test_stakeholder_identification()
    
    # Test crew stakeholder identification
    crew_success = test_crew_stakeholder_identification()
    
    print(f"\n🏁 Test Results:")
    print(f"   Direct Stakeholder Identification: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"   Crew Stakeholder Identification: {'✅ PASSED' if crew_success else '❌ FAILED'}")
    
    if direct_success and crew_success:
        print("\n🎉 All tests passed! Stakeholder identification is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.") 