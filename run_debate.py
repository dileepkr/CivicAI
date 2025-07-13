#!/usr/bin/env python
"""
CivicAI Policy Debate System - Unified Entry Point

This script provides a unified interface to run any of the three debate systems:
- debug: Real-time debug system with live agent interactions
- weave: Full Weave integration with comprehensive tracing
- human: Human-like conversational system with personas and moderator

Usage:
    python run_debate.py <system> <policy_name>
    
Examples:
    python run_debate.py debug policy_1
    python run_debate.py weave policy_2
    python run_debate.py human policy_1
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate import DebugDebateSystem, WeaveDebateSystem, HumanDebateSystem


def show_usage():
    """Show usage information"""
    print("""
🎭 CivicAI Policy Debate System - Unified Entry Point

Usage: python run_debate.py <system> <policy_name>

Available Systems:
  debug   - Real-time debug system with live agent interactions
  weave   - Full Weave integration with comprehensive tracing  
  human   - Human-like conversational system with personas and moderator

Available Policies:
  policy_1 - AB 1248: Hiring of real property: fees and charges
  policy_2 - Rent Stabilization Ordinance Amendment

Examples:
  python run_debate.py debug policy_1
  python run_debate.py weave policy_2
  python run_debate.py human policy_1
""")


def main():
    """Main function"""
    
    if len(sys.argv) < 3:
        show_usage()
        return 1
    
    system_type = sys.argv[1].lower()
    policy_name = sys.argv[2]
    
    # Remove .json extension if present
    if policy_name.endswith('.json'):
        policy_name = policy_name[:-5]
    
    # Validate system type
    if system_type not in ['debug', 'weave', 'human']:
        print(f"❌ Error: Unknown system type '{system_type}'")
        print("Available systems: debug, weave, human")
        return 1
    
    # Validate policy file exists
    policy_file_path = os.path.join(project_root, "test_data", f"{policy_name}.json")
    if not os.path.exists(policy_file_path):
        print(f"❌ Error: Policy file not found at {policy_file_path}")
        print("Available policies: policy_1, policy_2")
        return 1
    
    # Create and run the appropriate debate system
    try:
        print(f"🚀 Starting {system_type.upper()} debate system with {policy_name}")
        print("=" * 60)
        
        if system_type == 'debug':
            debate_system = DebugDebateSystem()
        elif system_type == 'weave':
            debate_system = WeaveDebateSystem()
        elif system_type == 'human':
            debate_system = HumanDebateSystem()
        
        # Run the debate
        results = debate_system.run_debate(policy_name)
        
        # Show summary
        print("\n" + "=" * 60)
        print(f"✅ {system_type.upper()} debate completed successfully!")
        print(f"📊 Session ID: {results.get('session_id', 'unknown')}")
        
        # System-specific statistics
        if system_type == 'debug':
            print(f"🎭 Participants: {len(results.get('stakeholders', []))}")
            print(f"🔄 Rounds: {len(results.get('debate_rounds', []))}")
            print(f"📧 A2A Messages: {len(results.get('a2a_messages', []))}")
        elif system_type == 'weave':
            print(f"🎭 Participants: {len(results.get('stakeholder_list', []))}")
            print(f"🔄 Rounds: {len(results.get('round_results', []))}")
            print(f"📊 Arguments: {len(results.get('all_arguments', []))}")
            print(f"🔗 View traces: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon")
        elif system_type == 'human':
            print(f"🎭 Participants: {len(results.get('personas', {}))}")
            print(f"📋 Topics: {len(results.get('topics_discussed', []))}")
            print(f"💬 Exchanges: {len(results.get('conversation_history', []))}")
            print(f"👩‍💼 Moderator: {debate_system.moderator.name}")
        
        duration = results.get('duration', results.get('total_duration', 0))
        print(f"⏱️  Duration: {duration:.1f} seconds")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Debate interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running {system_type} debate: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 