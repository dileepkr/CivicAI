#!/usr/bin/env python3
"""
Debug script to test crew initialization
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔧 Starting crew initialization debug...")

try:
    print("📦 Importing crew module...")
    from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew
    print("✅ Crew module imported successfully")
    
    print("🚀 Creating crew instance...")
    crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
    print("✅ Crew system initialized successfully!")
    
    print("🔍 Testing crew components...")
    print(f"   - Policy discovery client: {crew_system.policy_discovery_client is not None}")
    print(f"   - LLM configured: {crew_system.llm is not None}")
    print(f"   - Agents config loaded: {len(crew_system.agents_config) if crew_system.agents_config else 0} items")
    print(f"   - Tasks config loaded: {len(crew_system.tasks_config) if crew_system.tasks_config else 0} items")
    
    print("🎉 All tests passed!")
    
except Exception as e:
    print(f"❌ Error during crew initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 