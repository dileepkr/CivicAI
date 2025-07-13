#!/usr/bin/env python
"""
Run Human Debate System
Enhanced human-like conversational system with personas and active moderator
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate.systems.human import HumanDebateSystem


def main():
    """Main function for human debate"""
    
    if len(sys.argv) < 2:
        print("Usage: python run_human_debate.py <policy_name>")
        print("Example: python run_human_debate.py policy_1")
        print("Available policies: policy_1, policy_2")
        return
    
    policy_name = sys.argv[1]
    if policy_name.endswith('.json'):
        policy_name = policy_name[:-5]
    
    policy_file_path = os.path.join(project_root, "test_data", f"{policy_name}.json")
    if not os.path.exists(policy_file_path):
        print(f"❌ Error: Policy file not found at {policy_file_path}")
        return
    
    try:
        # Run human debate
        debate_system = HumanDebateSystem()
        results = debate_system.run_debate(policy_name)
        
        print(f"\n📁 Human debate session completed!")
        print(f"📊 Session ID: {results['session_id']}")
        print(f"🎭 Participants: {len(results['personas'])}")
        print(f"📋 Topics: {len(results['topics_discussed'])}")
        print(f"💬 Exchanges: {len(results['conversation_history'])}")
        print(f"📊 Arguments: {len(results['all_arguments'])}")
        print(f"⏱️  Duration: {results['total_duration']:.1f} seconds")
        
        # Show moderator info
        print(f"\n👩‍💼 Moderator: {debate_system.moderator.name}")
        print(f"🗣️  Speaking balance: {results['speaking_stats']}")
        
        # Show conclusion preview
        conclusion = results.get('moderator_conclusion', '')
        if conclusion:
            print(f"\n📋 Moderator's conclusion preview:")
            print(f"   {conclusion[:200]}...")
        
    except Exception as e:
        print(f"❌ Error running human debate: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 