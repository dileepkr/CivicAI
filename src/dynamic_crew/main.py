#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv
from dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
import weave

# Load environment variables
load_dotenv()

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

weave.init(project_name="civicAI")

def run():
    """
    Run the crew with local policy analysis.
    """
    # Check if policy file is provided as argument
    if len(sys.argv) > 2:
        policy_file = sys.argv[2]
        # Remove .json extension if provided
        if policy_file.endswith('.json'):
            policy_file = policy_file[:-5]
        policy_name = policy_file
    else:
        # Default to policy_1 if no argument provided
        policy_name = 'policy_1'
    
    inputs = {
        'policy_name': policy_name
    }
    
    print(f"🚀 Starting policy analysis for: {policy_name}")
    print(f"📁 Looking for policy file: test_data/{policy_name}.json")
    
    # Check if policy file exists
    policy_file_path = os.path.join("test_data", f"{policy_name}.json")
    if not os.path.exists(policy_file_path):
        print(f"❌ Error: Policy file not found at {policy_file_path}")
        print("Available policy files:")
        try:
            for file in os.listdir("test_data"):
                if file.endswith('.json'):
                    print(f"  - {file}")
        except FileNotFoundError:
            print("  No test_data directory found")
        return
    
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        result = crew_instance.crew().kickoff(inputs=inputs)
        
        print("\n🎉 Policy analysis completed successfully!")
        print("📊 Results:")
        print(str(result))
        
        # Check if knowledge base was created
        kb_path = os.path.join("knowledge", "stakeholders")
        if os.path.exists(kb_path):
            print(f"\n📚 Knowledge base created at: {kb_path}")
            print("Stakeholder knowledge files:")
            for file in os.listdir(kb_path):
                if file.endswith('.json'):
                    print(f"  - {file}")
        
    except Exception as e:
        print(f"❌ Error during policy analysis: {e}")
        raise

def run_with_dynamic_agents():
    """
    Run the crew with dynamic stakeholder agent creation.
    """
    if len(sys.argv) > 2:
        policy_file = sys.argv[2]
        if policy_file.endswith('.json'):
            policy_file = policy_file[:-5]
        policy_name = policy_file
    else:
        policy_name = 'policy_1'
    
    inputs = {
        'policy_name': policy_name
    }
    
    print(f"🚀 Starting enhanced policy analysis with dynamic agents for: {policy_name}")
    
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # First, identify stakeholders
        print("🔍 Step 1: Identifying stakeholders...")
        from dynamic_crew.tools.custom_tool import PolicyFileReader, StakeholderIdentifier
        
        policy_reader = PolicyFileReader()
        stakeholder_identifier = StakeholderIdentifier()
        
        # Read policy file
        policy_data = policy_reader._run(f"{policy_name}.json")
        
        # Check if policy reading was successful
        if policy_data.startswith("Error"):
            print(f"❌ {policy_data}")
            return
        
        # Extract policy text from the structured output
        import json
        policy_info = json.loads(policy_data)
        policy_text = policy_info.get("text", "")
        
        if not policy_text:
            print("❌ No policy text found in the file")
            return
        
        # Identify stakeholders
        print("🎯 Analyzing policy text to identify stakeholders...")
        stakeholder_result = stakeholder_identifier._run(policy_text)
        
        # Check if stakeholder identification was successful
        if stakeholder_result.startswith("Error"):
            print(f"❌ {stakeholder_result}")
            return
        
        print("✅ Stakeholder identification completed")
        
        # Parse the validated stakeholder data
        try:
            stakeholder_data = json.loads(stakeholder_result)
            
            # The new format includes a 'stakeholders' array and metadata
            if 'stakeholders' in stakeholder_data:
                stakeholder_list = stakeholder_data['stakeholders']
                total_count = stakeholder_data.get('total_count', len(stakeholder_list))
                analysis_summary = stakeholder_data.get('analysis_summary', '')
                
                print(f"👥 Found {total_count} stakeholders")
                print(f"📋 Analysis: {analysis_summary}")
                
                # Display stakeholder summary
                print("\n🏷️  Identified Stakeholders:")
                for i, stakeholder in enumerate(stakeholder_list, 1):
                    name = stakeholder.get('name', 'Unknown')
                    stakeholder_type = stakeholder.get('type', 'unknown')
                    likely_stance = stakeholder.get('likely_stance', 'unknown')
                    print(f"  {i}. {name} ({stakeholder_type}) - Stance: {likely_stance}")
                
                # Create dynamic crew with stakeholder agents
                print("\n🎭 Step 2: Creating dynamic stakeholder agents...")
                dynamic_crew = crew_instance.setup_dynamic_stakeholder_crew(stakeholder_list)
                
                print("🔄 Step 3: Running analysis with dynamic stakeholder agents...")
                result = dynamic_crew.kickoff(inputs=inputs)
                
                print("\n🎉 Enhanced policy analysis completed!")
                print("📊 Results:")
                print(str(result))
                
                # Show knowledge base information
                kb_path = os.path.join("knowledge", "stakeholders")
                if os.path.exists(kb_path):
                    print(f"\n📚 Knowledge base created at: {kb_path}")
                    print("📁 Stakeholder research files:")
                    for file in os.listdir(kb_path):
                        if file.endswith('.json'):
                            print(f"  - {file}")
                            
                            # Show a preview of the knowledge base content
                            try:
                                with open(os.path.join(kb_path, file), 'r') as f:
                                    kb_data = json.load(f)
                                    stakeholder_name = kb_data.get('stakeholder_name', 'Unknown')
                                    version = kb_data.get('version', 1)
                                    print(f"    📄 {stakeholder_name} - Version {version}")
                            except:
                                pass
                
            else:
                print("❌ Invalid stakeholder data format - missing 'stakeholders' array")
                return
                
        except json.JSONDecodeError as e:
            print(f"❌ Could not parse stakeholder data as JSON: {e}")
            print(f"Raw response: {stakeholder_result}")
            return
        
    except Exception as e:
        print(f"❌ Error during enhanced policy analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

def run_structured_debate():
    """
    Run a structured debate between stakeholder agents with A2A protocols.
    """
    if len(sys.argv) > 2:
        policy_file = sys.argv[2]
        if policy_file.endswith('.json'):
            policy_file = policy_file[:-5]
        policy_name = policy_file
    else:
        policy_name = 'policy_1'
    
    inputs = {
        'policy_name': policy_name
    }
    
    print(f"🎭 Starting structured policy debate with A2A protocols for: {policy_name}")
    
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        
        # First, identify stakeholders
        print("🔍 Step 1: Identifying stakeholders...")
        from dynamic_crew.tools.custom_tool import PolicyFileReader, StakeholderIdentifier
        
        policy_reader = PolicyFileReader()
        stakeholder_identifier = StakeholderIdentifier()
        
        # Read policy file
        policy_data = policy_reader._run(f"{policy_name}.json")
        
        # Check if policy reading was successful
        if policy_data.startswith("Error"):
            print(f"❌ {policy_data}")
            return
        
        # Extract policy text from the structured output
        import json
        policy_info = json.loads(policy_data)
        policy_text = policy_info.get("text", "")
        
        if not policy_text:
            print("❌ No policy text found in the file")
            return
        
        # Identify stakeholders
        print("🎯 Analyzing policy text to identify stakeholders...")
        stakeholder_result = stakeholder_identifier._run(policy_text)
        
        # Check if stakeholder identification was successful
        if stakeholder_result.startswith("Error"):
            print(f"❌ {stakeholder_result}")
            return
        
        print("✅ Stakeholder identification completed")
        
        # Parse the validated stakeholder data
        try:
            stakeholder_data = json.loads(stakeholder_result)
            
            # The new format includes a 'stakeholders' array and metadata
            if 'stakeholders' in stakeholder_data:
                stakeholder_list = stakeholder_data['stakeholders']
                total_count = stakeholder_data.get('total_count', len(stakeholder_list))
                
                print(f"👥 Found {total_count} stakeholders for debate")
                
                # Display stakeholder summary
                print("\n🏷️  Debate Participants:")
                for i, stakeholder in enumerate(stakeholder_list, 1):
                    name = stakeholder.get('name', 'Unknown')
                    stakeholder_type = stakeholder.get('type', 'unknown')
                    likely_stance = stakeholder.get('likely_stance', 'unknown')
                    print(f"  {i}. {name} ({stakeholder_type}) - Initial Stance: {likely_stance}")
                
                # Create debate crew with stakeholder agents
                print("\n🎭 Step 2: Setting up debate framework...")
                debate_crew = crew_instance.setup_debate_crew(stakeholder_list)
                
                print("🔄 Step 3: Conducting structured policy debate...")
                print("   📋 Debate will follow A2A protocols with:")
                print("   - Topic analysis and prioritization")
                print("   - Structured argumentation rounds")
                print("   - Evidence-based arguments from knowledge bases")
                print("   - Moderated discussion flow")
                print("   - Comprehensive debate summary")
                
                result = debate_crew.kickoff(inputs=inputs)
                
                print("\n🎉 Structured policy debate completed!")
                print("📊 Debate Results:")
                print(str(result))
                
                # Show debate session information
                debate_sessions_path = os.path.join("knowledge", "debates", "sessions")
                if os.path.exists(debate_sessions_path):
                    print(f"\n📚 Debate sessions stored at: {debate_sessions_path}")
                    for file in os.listdir(debate_sessions_path):
                        if file.endswith('.json'):
                            print(f"  - {file}")
                
                # Show A2A messages
                debate_messages_path = os.path.join("knowledge", "debates", "messages")
                if os.path.exists(debate_messages_path):
                    print(f"\n💬 A2A Messages stored at: {debate_messages_path}")
                    message_count = len([f for f in os.listdir(debate_messages_path) if f.endswith('.json')])
                    print(f"   📧 {message_count} messages exchanged during debate")
                
            else:
                print("❌ Invalid stakeholder data format - missing 'stakeholders' array")
                return
                
        except json.JSONDecodeError as e:
            print(f"❌ Could not parse stakeholder data as JSON: {e}")
            print(f"Raw response: {stakeholder_result}")
            return
        
    except Exception as e:
        print(f"❌ Error during structured debate: {e}")
        import traceback
        traceback.print_exc()
        raise

def train():
    """
    Train the crew for a given number of iterations.
    """
    policy_name = 'policy_1'
    if len(sys.argv) > 3:
        policy_name = sys.argv[3]
    
    inputs = {
        'policy_name': policy_name
    }
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        crew_instance.crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)
        print(f"✅ Training completed for {policy_name}")

    except Exception as e:
        print(f"❌ Error during training: {e}")
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        crew_instance.crew().replay(task_id=sys.argv[1])
        print(f"✅ Replay completed for task: {sys.argv[1]}")

    except Exception as e:
        print(f"❌ Error during replay: {e}")
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    policy_name = 'policy_1'
    if len(sys.argv) > 3:
        policy_name = sys.argv[3]
    
    inputs = {
        'policy_name': policy_name
    }
    try:
        crew_instance = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
        result = crew_instance.crew().test(n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs)
        print(f"✅ Test completed for {policy_name}")
        print(f"📊 Results: {result}")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        raise Exception(f"An error occurred while testing the crew: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: main.py <command> [<policy_file>] [<args>]")
        print("Commands:")
        print("  run [policy_file] - Run policy analysis")
        print("  dynamic [policy_file] - Run with dynamic stakeholder agents")
        print("  debate [policy_file] - Run structured debate with A2A protocols")
        print("  train <iterations> <filename> [policy_file] - Train the crew")
        print("  replay <task_id> - Replay specific task")
        print("  test <iterations> <model_name> [policy_file] - Test the crew")
        print("\nExample:")
        print("  python main.py run policy_1")
        print("  python main.py dynamic policy_1")
        print("  python main.py debate policy_1")
        sys.exit(1)

    command = sys.argv[1]
    if command == "run":
        run()
    elif command == "dynamic":
        run_with_dynamic_agents()
    elif command == "debate":
        run_structured_debate()
    elif command == "train":
        train()
    elif command == "replay":
        replay()
    elif command == "test":
        test()
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: run, dynamic, debate, train, replay, test")
        sys.exit(1)
