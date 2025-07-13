#!/usr/bin/env python
"""
Run Debug Debate System
Shows live agent interactions without complex logging
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate.systems.debug import DebugDebateSystem


def main():
    """Main function for debug debate"""
    
    if len(sys.argv) < 2:
        print("Usage: python run_debug_debate.py <policy_name>")
        print("Example: python run_debug_debate.py policy_1")
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
        # Run debug debate
        debate_system = DebugDebateSystem()
        results = debate_system.run_debate(policy_name)
        
        print(f"\n📁 Debug debate session completed!")
        print(f"📊 Session ID: {results['session_id']}")
        print(f"🎭 Participants: {len(results['stakeholders'])}")
        print(f"🔄 Rounds: {len(results['debate_rounds'])}")
        print(f"📧 A2A Messages: {len(results['a2a_messages'])}")
        print(f"⏱️  Duration: {results['duration']:.1f} seconds")
        
    except Exception as e:
        print(f"❌ Error running debug debate: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 