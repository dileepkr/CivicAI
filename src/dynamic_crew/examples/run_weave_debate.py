#!/usr/bin/env python
"""
Run Weave Debate System
Full tracing integration perfect for hackathon demonstrations
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate.systems.weave import WeaveDebateSystem


def main():
    """Main function for weave debate"""
    
    if len(sys.argv) < 2:
        print("Usage: python run_weave_debate.py <policy_name>")
        print("Example: python run_weave_debate.py policy_1")
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
        # Run weave debate
        debate_system = WeaveDebateSystem()
        results = debate_system.run_debate(policy_name)
        
        print(f"\n📁 Weave debate session completed!")
        print(f"📊 Session ID: {results['session_id']}")
        print(f"🎭 Participants: {len(results['stakeholder_list'])}")
        print(f"🔄 Rounds: {len(results['round_results'])}")
        print(f"📊 Arguments: {len(results['all_arguments'])}")
        print(f"⏱️  Duration: {results['duration']:.1f} seconds")
        
        # Show trace link
        print(f"\n🔗 View full traces at:")
        print(f"   https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon")
        
    except Exception as e:
        print(f"❌ Error running weave debate: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 