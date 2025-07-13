"""
Base debate system with common functionality for all debate implementations.
"""

import os
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..tools.custom_tool import (
    PolicyFileReader,
    StakeholderIdentifier,
    KnowledgeBaseManager,
    StakeholderResearcher,
    TopicAnalyzer,
    ArgumentGenerator,
    A2AMessenger,
    DebateModerator
)


class BaseDebateSystem(ABC):
    """
    Base class for all debate systems with common functionality.
    """
    
    def __init__(self, system_name: str):
        """Initialize the base debate system"""
        self.system_name = system_name
        self.session_id = f"{system_name}_{uuid.uuid4().hex[:8]}"
        
        # Initialize tools
        self.policy_reader = PolicyFileReader()
        self.stakeholder_identifier = StakeholderIdentifier()
        self.kb_manager = KnowledgeBaseManager()
        self.stakeholder_researcher = StakeholderResearcher()
        self.topic_analyzer = TopicAnalyzer()
        self.argument_generator = ArgumentGenerator()
        self.a2a_messenger = A2AMessenger()
        self.debate_moderator = DebateModerator()
        
        # Common tracking
        self.debate_round = 0
        self.conversation_history = []
        self.all_arguments = []
        self.personas = {}
        
        print(f"🎭 {system_name} Active - Session: {self.session_id}")
    
    def load_policy(self, policy_name: str) -> Dict[str, Any]:
        """Load and parse policy file"""
        print(f"\n📄 Loading Policy...")
        
        policy_data = self.policy_reader._run(f"{policy_name}.json")
        if policy_data.startswith("Error"):
            raise Exception(f"Policy loading failed: {policy_data}")
        
        policy_info = json.loads(policy_data)
        print(f"✅ Policy: {policy_info.get('title', 'Unknown')}")
        
        return policy_info
    
    def identify_stakeholders(self, policy_text: str) -> List[Dict[str, Any]]:
        """Identify stakeholders from policy text"""
        print(f"\n🎯 Identifying Stakeholders...")
        
        stakeholder_result = self.stakeholder_identifier._run(policy_text)
        if stakeholder_result.startswith("Error"):
            raise Exception(f"Stakeholder identification failed: {stakeholder_result}")
        
        stakeholder_data = json.loads(stakeholder_result)
        stakeholder_list = stakeholder_data.get('stakeholders', [])
        
        print(f"✅ Found {len(stakeholder_list)} stakeholders")
        return stakeholder_list
    
    def analyze_topics(self, policy_text: str, stakeholder_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze debate topics from policy and stakeholders"""
        print(f"\n📋 Analyzing Debate Topics...")
        
        stakeholder_summary = {
            "stakeholders": stakeholder_list,
            "total_count": len(stakeholder_list)
        }
        
        topic_result = self.topic_analyzer._run(policy_text, json.dumps(stakeholder_summary))
        if not topic_result.startswith("Error"):
            topics_data = json.loads(topic_result)
            topics_list = topics_data.get('topics', [])
            # Sort by priority and take top 3
            topics_list = sorted(topics_list, key=lambda x: x.get('priority', 0), reverse=True)[:3]
        else:
            topics_list = [{"title": "Policy Impact and Implementation", "priority": 8}]
        
        print(f"✅ Found {len(topics_list)} debate topics")
        return topics_list

    def research_single_stakeholder(self, stakeholder: Dict[str, Any], policy_text: str) -> Dict[str, Any]:
        """Research a single stakeholder's perspective (for parallel execution)"""
        stakeholder_name = stakeholder.get('name', 'Unknown')
        
        print(f"🔍 Researching {stakeholder_name}'s perspective...")
        
        try:
            research_result = self.stakeholder_researcher._run(json.dumps(stakeholder), policy_text)
            
            if not research_result.startswith("Error"):
                research_data = json.loads(research_result)
                
                # Store in knowledge base
                kb_result = self.kb_manager._run(stakeholder_name, research_result, "create")
                
                print(f"✅ Research complete for {stakeholder_name}")
                return {
                    'name': stakeholder_name,
                    'research_data': research_data,
                    'kb_result': kb_result,
                    'status': 'success'
                }
            else:
                print(f"❌ Research failed for {stakeholder_name}: {research_result}")
                return {
                    'name': stakeholder_name,
                    'error': research_result,
                    'status': 'failed'
                }
        except Exception as e:
            print(f"❌ Research error for {stakeholder_name}: {e}")
            return {
                'name': stakeholder_name,
                'error': str(e),
                'status': 'error'
            }

    def research_stakeholders_parallel(self, stakeholder_list: List[Dict[str, Any]], policy_text: str) -> Dict[str, Any]:
        """Research all stakeholders in parallel to save time"""
        print(f"\n🔬 Starting parallel research for {len(stakeholder_list)} stakeholders...")
        
        start_time = time.time()
        stakeholder_research = {}
        
        # Use ThreadPoolExecutor for parallel research
        with ThreadPoolExecutor(max_workers=min(len(stakeholder_list), 5)) as executor:
            # Submit all research tasks
            future_to_stakeholder = {
                executor.submit(self.research_single_stakeholder, stakeholder, policy_text): stakeholder
                for stakeholder in stakeholder_list
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_stakeholder):
                stakeholder = future_to_stakeholder[future]
                result = future.result()
                
                if result['status'] == 'success':
                    stakeholder_research[result['name']] = result['research_data']
                else:
                    print(f"⚠️ Research issues for {result['name']}: {result.get('error', 'Unknown error')}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Parallel research completed in {duration:.1f} seconds")
        print(f"📊 Successfully researched {len(stakeholder_research)} out of {len(stakeholder_list)} stakeholders")
        
        return stakeholder_research
    
    def generate_argument(self, stakeholder_name: str, topic: Dict[str, Any], argument_type: str) -> str:
        """Generate argument for a stakeholder on a topic"""
        argument_result = self.argument_generator._run(
            stakeholder_name,
            json.dumps(topic),
            argument_type
        )
        
        if argument_result.startswith("Error"):
            return f"Error generating argument: {argument_result}"
        
        return argument_result
    
    def send_a2a_message(self, sender: str, receiver: str, message_type: str, content: str, context: Dict[str, Any]) -> str:
        """Send agent-to-agent message"""
        message_result = self.a2a_messenger._run(
            sender,
            receiver,
            message_type,
            content,
            json.dumps(context)
        )
        
        if message_result.startswith("Error"):
            return f"Error sending message: {message_result}"
        
        return message_result
    
    def create_debate_session(self, policy_info: Dict[str, Any], stakeholders: List[Dict[str, Any]]) -> str:
        """Create a debate session with the moderator"""
        session_context = {
            "policy_name": policy_info.get('title', 'Unknown Policy'),
            "participants": [s.get('name', 'Unknown') for s in stakeholders],
            "session_id": self.session_id,
            "system_type": self.system_name
        }
        
        moderator_result = self.debate_moderator._run(
            self.session_id,
            "start",
            json.dumps(session_context)
        )
        
        if moderator_result.startswith("Error"):
            return f"Error creating debate session: {moderator_result}"
        
        return moderator_result
    
    def end_debate_session(self) -> str:
        """End the debate session"""
        end_result = self.debate_moderator._run(self.session_id, "end")
        
        if end_result.startswith("Error"):
            return f"Error ending debate session: {end_result}"
        
        return end_result
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "system_name": self.system_name,
            "debate_rounds": self.debate_round,
            "total_arguments": len(self.all_arguments),
            "conversation_turns": len(self.conversation_history),
            "participants": len(self.personas)
        }
    
    @abstractmethod
    def run_debate(self, policy_name: str) -> Dict[str, Any]:
        """Run the complete debate process - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def create_personas(self, stakeholder_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create personas for stakeholders - must be implemented by subclasses"""
        pass 