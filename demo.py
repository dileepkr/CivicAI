#!/usr/bin/env python
"""
CivicAI Policy Analysis Demo
This script demonstrates the enhanced policy analysis system with dynamic stakeholder agents and Serper search.
"""

import os
import json
from dotenv import load_dotenv
from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
from src.dynamic_crew.tools.custom_tool import (
    PolicyFileReader,
    StakeholderIdentifier,
    KnowledgeBaseManager,
    StakeholderResearcher
)

# Load environment variables
load_dotenv()

def demo_policy_analysis():
    """
    Demonstrates the complete policy analysis workflow
    """
    print("🎯 CivicAI Policy Analysis Demo")
    print("=" * 50)
    
    # Check if API keys are configured
    gemini_key = os.getenv('GEMINI_API_KEY')
    serper_key = os.getenv('SERPER_API_KEY')
    
    if not gemini_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables")
        print("Please add your Gemini API key to the .env file")
        return
    
    if not serper_key:
        print("❌ Error: SERPER_API_KEY not found in environment variables")
        print("Please add your Serper API key to the .env file")
        return
    
    print("✅ API keys configured")
    
    # Check if policy file exists
    policy_file = "policy_1.json"
    policy_path = os.path.join("test_data", policy_file)
    
    if not os.path.exists(policy_path):
        print(f"❌ Error: Policy file not found at {policy_path}")
        return
    
    print(f"📁 Reading policy file: {policy_file}")
    
    # Step 1: Read Policy File
    print("\n1️⃣ Reading Policy Document...")
    policy_reader = PolicyFileReader()
    policy_data = policy_reader._run(policy_file)
    
    if policy_data.startswith("Error"):
        print(f"❌ {policy_data}")
        return
    
    policy_info = json.loads(policy_data)
    print(f"✅ Policy loaded: {policy_info.get('title', 'Unknown Title')}")
    
    # Step 2: Identify Stakeholders
    print("\n2️⃣ Identifying Stakeholders...")
    stakeholder_identifier = StakeholderIdentifier()
    stakeholder_result = stakeholder_identifier._run(policy_info['text'])
    print(f"✅ Stakeholder identification completed")
    
    if stakeholder_result.startswith("Error"):
        print(f"❌ {stakeholder_result}")
        return
    
    try:
        # Parse the validated stakeholder data (new Pydantic format)
        stakeholder_data = json.loads(stakeholder_result)
        
        # Check if we have the expected structure
        if 'stakeholders' not in stakeholder_data:
            print("❌ Invalid stakeholder data format - missing 'stakeholders' array")
            return
        
        stakeholder_list = stakeholder_data['stakeholders']
        total_count = stakeholder_data.get('total_count', len(stakeholder_list))
        analysis_summary = stakeholder_data.get('analysis_summary', '')
        
        print(f"✅ Found {total_count} stakeholders")
        print(f"📋 Analysis: {analysis_summary}")
        
        print("\n🏷️  Stakeholder Details:")
        for i, stakeholder in enumerate(stakeholder_list, 1):
            name = stakeholder.get('name', 'Unknown')
            stakeholder_type = stakeholder.get('type', 'unknown')
            likely_stance = stakeholder.get('likely_stance', 'Unknown stance')
            interests = stakeholder.get('interests', [])
            key_concerns = stakeholder.get('key_concerns', [])
            
            print(f"   {i}. {name} ({stakeholder_type})")
            print(f"      Stance: {likely_stance}")
            print(f"      Interests: {', '.join(interests[:3])}")  # Show first 3 interests
            if key_concerns:
                print(f"      Key Concerns: {', '.join(key_concerns[:2])}")  # Show first 2 concerns
        
        # Step 3: Create Dynamic Agents
        print("\n3️⃣ Creating Dynamic Stakeholder Agents...")
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # Create agents for each stakeholder
        for stakeholder in stakeholder_list:
            agent = crew_instance.create_stakeholder_agent(stakeholder)
            print(f"   🤖 Created agent: {agent.role}")
        
        # Step 4: Demonstrate Knowledge Base
        print("\n4️⃣ Demonstrating Knowledge Base System...")
        kb_manager = KnowledgeBaseManager()
        
        # Create sample knowledge base entries
        for stakeholder in stakeholder_list[:2]:  # Just first 2 for demo
            sample_research = f"Sample research data for {stakeholder.get('name', 'Unknown')}"
            result = kb_manager._run(stakeholder.get('name', 'Unknown'), sample_research, 'create')
            print(f"   📚 {result}")
        
        # Step 5: Demonstrate Stakeholder Research
        print("\n5️⃣ Demonstrating Stakeholder Research...")
        researcher = StakeholderResearcher()
        
        # Research from first stakeholder's perspective
        first_stakeholder = stakeholder_list[0]
        research_result = researcher._run(
            json.dumps(first_stakeholder), 
            policy_info['text']
        )
        
        if not research_result.startswith("Error"):
            print(f"✅ Research completed for {first_stakeholder.get('name', 'Unknown')}")
            
            # Parse the structured research result
            try:
                research_data = json.loads(research_result)
                print(f"   📊 Research Summary: {research_data.get('research_summary', 'No summary available')}")
                print(f"   🎯 Confidence Level: {research_data.get('confidence_level', 'Unknown')}")
                
                # Show some key findings
                policy_impact = research_data.get('policy_impact', {})
                if policy_impact:
                    direct_impacts = policy_impact.get('direct_impacts', [])
                    if direct_impacts:
                        print(f"   📌 Direct Impacts: {', '.join(direct_impacts[:2])}")
                    
                    benefits = policy_impact.get('benefits', [])
                    if benefits:
                        print(f"   ✅ Benefits: {', '.join(benefits[:2])}")
                    
                    risks = policy_impact.get('risks', [])
                    if risks:
                        print(f"   ⚠️  Risks: {', '.join(risks[:2])}")
                
            except json.JSONDecodeError:
                print(f"   📄 Research preview: {research_result[:200]}...")
        else:
            print(f"❌ Research failed: {research_result}")
        
        print("\n🎉 Demo completed successfully!")
        print("\n📝 Next Steps:")
        print("   • Run full analysis: python main.py dynamic policy_1")
        print("   • Check knowledge base: ls knowledge/stakeholders/")
        print("   • Try different policies: add more JSON files to test_data/")
        print("   • Agents will use Serper search for comprehensive web research")
        
    except json.JSONDecodeError as e:
        print(f"❌ Could not parse stakeholder data as JSON: {e}")
        print("Raw result:")
        print(stakeholder_result[:500] + "..." if len(stakeholder_result) > 500 else stakeholder_result)

def demo_knowledge_base():
    """
    Demonstrates the knowledge base management system
    """
    print("\n📚 Knowledge Base Demo")
    print("=" * 30)
    
    kb_manager = KnowledgeBaseManager()
    
    # Sample stakeholder data
    stakeholder_data = {
        "name": "Demo Stakeholder",
        "research": "This is sample research data for demonstration purposes.",
        "insights": ["Key insight 1", "Key insight 2", "Key insight 3"],
        "search_results": "Enhanced with Serper search capabilities for comprehensive research"
    }
    
    # Create knowledge base entry
    print("1. Creating knowledge base entry...")
    result = kb_manager._run("Demo Stakeholder", json.dumps(stakeholder_data), "create")
    print(f"   {result}")
    
    # Retrieve knowledge base entry
    print("\n2. Retrieving knowledge base entry...")
    result = kb_manager._run("Demo Stakeholder", "", "retrieve")
    print(f"   Retrieved: {result[:100]}...")
    
    # Update knowledge base entry
    print("\n3. Updating knowledge base entry...")
    updated_data = {
        "name": "Demo Stakeholder",
        "research": "Updated research data with new findings from Serper search.",
        "insights": ["Updated insight 1", "New insight 2", "Additional insight 3"],
        "serper_research": "Comprehensive web research using Serper's search capabilities"
    }
    result = kb_manager._run("Demo Stakeholder", json.dumps(updated_data), "update")
    print(f"   {result}")

def check_setup():
    """
    Checks if the system is properly configured
    """
    print("🔍 System Setup Check")
    print("=" * 25)
    
    # Check environment variables
    print("1. Environment Variables:")
    gemini_key = os.getenv('GEMINI_API_KEY')
    serper_key = os.getenv('SERPER_API_KEY')
    print(f"   GEMINI_API_KEY: {'✅ Set' if gemini_key else '❌ Not set'}")
    print(f"   SERPER_API_KEY: {'✅ Set' if serper_key else '❌ Not set'}")
    
    # Check directories
    print("\n2. Directory Structure:")
    required_dirs = ['test_data', 'knowledge', 'src']
    for dir_name in required_dirs:
        exists = os.path.exists(dir_name)
        print(f"   {dir_name}/: {'✅ Exists' if exists else '❌ Missing'}")
    
    # Check policy files
    print("\n3. Policy Files:")
    if os.path.exists('test_data'):
        policy_files = [f for f in os.listdir('test_data') if f.endswith('.json')]
        if policy_files:
            print(f"   Found {len(policy_files)} policy files:")
            for file in policy_files:
                print(f"     - {file}")
        else:
            print("   ❌ No policy files found")
    
    # Check knowledge base
    print("\n4. Knowledge Base:")
    kb_path = os.path.join('knowledge', 'stakeholders')
    if os.path.exists(kb_path):
        kb_files = [f for f in os.listdir(kb_path) if f.endswith('.json')]
        print(f"   Found {len(kb_files)} knowledge base files:")
        for file in kb_files:
            print(f"     - {file}")
    else:
        print("   📁 Knowledge base directory will be created when needed")

def demo_structured_debate():
    """
    Demonstrates the structured debate system with A2A protocols
    """
    print("\n🎭 Structured Debate Demo")
    print("=" * 35)
    
    # Check if API keys are configured
    gemini_key = os.getenv('GEMINI_API_KEY')
    serper_key = os.getenv('SERPER_API_KEY')
    
    if not gemini_key or not serper_key:
        print("❌ API keys not configured. Skipping debate demo.")
        return
    
    print("✅ API keys configured for debate demo")
    
    # Import debate tools
    from src.dynamic_crew.tools.custom_tool import (
        TopicAnalyzer, ArgumentGenerator, A2AMessenger, DebateModerator
    )
    
    # Sample policy text and stakeholder data
    policy_text = """
    The Mandatory Soft Story Retrofit Program requires property owners to seismically retrofit 
    soft-story buildings within 7 years. The program provides financial assistance but requires 
    compliance with strict building codes and regular inspections.
    """
    
    stakeholder_data = {
        "stakeholders": [
            {
                "name": "Property Owners",
                "type": "business_stakeholder",
                "interests": ["property_value", "compliance_costs"],
                "impact": "Required to invest in seismic retrofitting",
                "likely_stance": "opposed",
                "key_concerns": ["financial_burden", "implementation_timeline"]
            },
            {
                "name": "City Officials",
                "type": "government_stakeholder",
                "interests": ["public_safety", "policy_implementation"],
                "impact": "Responsible for enforcing compliance",
                "likely_stance": "supportive",
                "key_concerns": ["enforcement_challenges", "program_effectiveness"]
            }
        ],
        "total_count": 2,
        "analysis_summary": "Two primary stakeholders with opposing interests"
    }
    
    # Step 1: Analyze debate topics
    print("\n1️⃣ Analyzing debate topics...")
    topic_analyzer = TopicAnalyzer()
    topic_result = topic_analyzer._run(policy_text, json.dumps(stakeholder_data))
    
    if not topic_result.startswith("Error"):
        print("✅ Topic analysis completed")
        try:
            topics = json.loads(topic_result)
            print(f"   📋 Found {topics.get('total_count', 0)} debate topics")
            for topic in topics.get('topics', [])[:2]:  # Show first 2 topics
                print(f"   - {topic.get('title', 'Unknown Topic')} (Priority: {topic.get('priority', 'N/A')})")
        except:
            print("   📄 Topic analysis preview available")
    else:
        print(f"❌ Topic analysis failed: {topic_result}")
        return
    
    # Step 2: Generate sample arguments
    print("\n2️⃣ Generating sample arguments...")
    argument_generator = ArgumentGenerator()
    
    # Create sample topic for argument generation
    sample_topic = {
        "topic_id": "implementation_timeline",
        "title": "Implementation Timeline",
        "description": "Discussion about the feasibility of the 7-year implementation timeline",
        "priority": 8,
        "stakeholders_involved": ["Property Owners", "City Officials"],
        "key_questions": ["Is the timeline realistic?", "What support is needed?"]
    }
    
    # Generate argument for Property Owners
    argument_result = argument_generator._run(
        "Property Owners", 
        json.dumps(sample_topic), 
        "claim"
    )
    
    if not argument_result.startswith("Error"):
        print("✅ Argument generation completed")
        try:
            argument = json.loads(argument_result)
            print(f"   🗣️  Sample argument from {argument.get('stakeholder_name', 'Unknown')}")
            print(f"   📝 Type: {argument.get('argument_type', 'Unknown')}")
            print(f"   💪 Strength: {argument.get('strength', 'N/A')}/10")
        except:
            print("   📄 Argument generation preview available")
    else:
        print(f"❌ Argument generation failed: {argument_result}")
    
    # Step 3: Demonstrate A2A messaging
    print("\n3️⃣ Demonstrating A2A messaging...")
    a2a_messenger = A2AMessenger()
    
    message_result = a2a_messenger._run(
        "Property Owners Agent",
        "City Officials Agent",
        "argument",
        "We need more time for implementation due to financial constraints",
        json.dumps({"topic_id": "implementation_timeline", "argument_type": "claim"})
    )
    
    if not message_result.startswith("Error"):
        print("✅ A2A message sent successfully")
        try:
            message = json.loads(message_result)
            print(f"   📧 Message ID: {message.get('message_id', 'Unknown')}")
            print(f"   🔄 From: {message.get('sender', 'Unknown')} → To: {message.get('receiver', 'Unknown')}")
            print(f"   💬 Type: {message.get('message_type', 'Unknown')}")
        except:
            print("   📄 Message details available")
    else:
        print(f"❌ A2A messaging failed: {message_result}")
    
    # Step 4: Demonstrate debate moderation
    print("\n4️⃣ Demonstrating debate moderation...")
    debate_moderator = DebateModerator()
    
    import uuid
    session_id = f"demo_{uuid.uuid4().hex[:8]}"
    
    # Initialize debate session
    session_context = {
        "policy_name": "Seismic Retrofit Policy",
        "participants": ["Property Owners", "City Officials"],
        "topics": [sample_topic]
    }
    
    moderator_result = debate_moderator._run(
        session_id,
        "start",
        json.dumps(session_context)
    )
    
    if not moderator_result.startswith("Error"):
        print("✅ Debate session initialized")
        print(f"   🎭 Session ID: {session_id}")
        print(f"   📋 Status: {moderator_result}")
        
        # End the demo session
        end_result = debate_moderator._run(session_id, "end")
        if not end_result.startswith("Error"):
            print("✅ Demo debate session ended")
    else:
        print(f"❌ Debate moderation failed: {moderator_result}")
    
    print("\n🎉 Structured Debate Demo completed!")
    print("📝 Key Features Demonstrated:")
    print("   • Topic Analysis - AI identifies key areas of contention")
    print("   • Argument Generation - Evidence-based arguments from stakeholder perspectives")
    print("   • A2A Messaging - Structured communication between agents")
    print("   • Debate Moderation - Neutral facilitation of discussions")
    print("   • Pydantic Validation - Ensures proper JSON format for all debate data")
    print("   • Knowledge Base Integration - Arguments based on stakeholder research")
    print("\n📋 To run a full debate:")
    print("   python main.py debate policy_1")

if __name__ == "__main__":
    print("🚀 CivicAI Enhanced Policy Analysis System with Serper Search")
    print("=" * 68)
    
    # Run setup check
    check_setup()
    
    # Run main demo
    print("\n")
    demo_policy_analysis()
    
    # Run knowledge base demo
    print("\n")
    demo_knowledge_base()
    
    # Run structured debate demo
    print("\n")
    demo_structured_debate()
    
    print("\n" + "=" * 68)
    print("🎯 Demo Complete! Ready to analyze policies with AI agents and structured debates.")
    print("=" * 68) 