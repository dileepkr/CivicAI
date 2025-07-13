"""
Enhanced Human-Like Policy Debate System with Active Moderator
Real stakeholders debating like actual people with personalities, emotions, and guided discussions
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False

from ..base import BaseDebateSystem
from ..moderator import HumanModerator
from ..personas import HumanPersona


class HumanDebateSystem(BaseDebateSystem):
    """
    Enhanced human-like debate system with active moderator and natural conversation flow
    """
    
    def __init__(self):
        super().__init__("human_debate")
        
        # Check if Weave tracing is disabled via environment variable
        import os
        weave_tracing_disabled = os.getenv('WEAVE_DISABLE_TRACING', '0') == '1'
        
        # Initialize Weave if available and tracing is not disabled
        if WEAVE_AVAILABLE and not weave_tracing_disabled:
            weave.init(project_name="civicai-human-debate")
            self.weave_enabled = True
        else:
            # Disable Weave tracing to prevent circular reference issues
            os.environ['WEAVE_DISABLE_TRACING'] = '1'
            os.environ['WEAVE_AUTO_TRACE'] = '0'
            os.environ['WEAVE_AUTO_PATCH'] = '0'
            self.weave_enabled = False
        
        # Enhanced session tracking
        self.current_topic = 0
        self.moderator = HumanModerator()
        self.speaking_time = {}  # Track who's been speaking
        
        print(f"🎭 Enhanced Human-Like Debate System Active - Session: {self.session_id}")
        print(f"👩‍💼 Moderator: {self.moderator.name}")
        if self.weave_enabled:
            print(f"📊 View traces at: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-human-debate")
    
    def _weave_op(self, func):
        """Decorator wrapper for weave operations"""
        if hasattr(self, 'weave_enabled') and self.weave_enabled:
            return weave.op()(func)
        return func
    
    def _weave_attributes(self, attrs):
        """Context manager wrapper for weave attributes"""
        if hasattr(self, 'weave_enabled') and self.weave_enabled:
            return weave.attributes(attrs)
        else:
            # Return a dummy context manager
            class DummyContext:
                def __enter__(self):
                    return self
                def __exit__(self, *args):
                    pass
            return DummyContext()
    
    def create_personas(self, stakeholder_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create human personas for all stakeholders"""
        print(f"\n👥 Creating Human Personas...")
        
        with self._weave_attributes({
            "stakeholder_count": len(stakeholder_list),
            "session_id": self.session_id,
            "step": "create_personas"
        }):
            personas = {}
            
            for stakeholder in stakeholder_list:
                stakeholder_name = stakeholder.get('name', 'Unknown')
                persona = HumanPersona.create_persona(stakeholder_name, stakeholder)
                personas[stakeholder_name] = persona
                
                # Initialize speaking time tracking
                self.speaking_time[stakeholder_name] = 0
                
                print(f"   🎭 {persona['name']} ({stakeholder_name})")
                print(f"      Age: {persona['age']}, Background: {persona['background'][:60]}...")
                print(f"      Style: {persona['speech_style']}")
                print(f"      Response Style: {persona['response_style']}")
            
            self.personas = personas
            return personas
    
    def generate_human_argument(self, persona: Dict[str, Any], topic: Dict[str, Any], argument_type: str, context: str = "") -> str:
        """Generate human-like argument based on persona and context"""
        
        stakeholder_name = persona['stakeholder_group']
        person_name = persona['name']
        
        print(f"\n🗣️  {person_name} ({stakeholder_name}) speaking...")
        
        # Track speaking time
        self.speaking_time[stakeholder_name] += 1
        
        with self._weave_attributes({
            "speaker_name": person_name,
            "stakeholder_group": stakeholder_name,
            "argument_type": argument_type,
            "topic": topic.get('title', 'Unknown'),
            "context": context,
            "session_id": self.session_id,
            "debate_round": self.debate_round,
            "step": "human_argument"
        }):
            # Use the argument generator with enhanced context
            argument_result = self.generate_argument(stakeholder_name, topic, argument_type)
            
            if argument_result.startswith("Error"):
                return f"*{person_name} struggles to find words* I... this is difficult to articulate, but..."
            
            # Convert structured response to natural speech
            try:
                structured_data = json.loads(argument_result)
                content = structured_data.get('content', '')
                evidence = structured_data.get('evidence', [])
                
                # Make it more conversational and contextual
                human_speech = HumanPersona.humanize_argument(persona, content, evidence, argument_type, context)
                
                # Store for later synthesis
                self.all_arguments.append({
                    "speaker": person_name,
                    "stakeholder_group": stakeholder_name,
                    "topic": topic.get('title', 'Unknown'),
                    "content": content,
                    "evidence": evidence,
                    "argument_type": argument_type,
                    "timestamp": datetime.now().isoformat()
                })
                
                return human_speech
                
            except json.JSONDecodeError:
                return f"*{person_name} speaks passionately* Look, the bottom line is..."
    
    def facilitate_natural_exchange(self, personas: Dict[str, Dict[str, Any]], topic: Dict[str, Any], exchange_type: str) -> List[str]:
        """Facilitate natural back-and-forth exchange on a topic"""
        
        print(f"\n💬 Natural Exchange: {topic.get('title', 'Discussion')}")
        
        exchanges = []
        persona_list = list(personas.values())
        
        with self._weave_attributes({
            "topic": topic.get('title', 'Unknown'),
            "exchange_type": exchange_type,
            "participants": len(persona_list),
            "session_id": self.session_id,
            "step": "natural_exchange"
        }):
            # First speaker introduces the topic
            first_speaker = persona_list[0]
            first_statement = self.generate_human_argument(first_speaker, topic, "claim")
            exchanges.append(first_statement)
            print(f"\n{first_statement}")
            time.sleep(1)
            
            # Other speakers respond in turn
            for i in range(1, len(persona_list)):
                responder = persona_list[i]
                previous_speaker = persona_list[i-1]['name']
                
                # Context-aware response
                context = f"responding to {previous_speaker}'s points about {topic.get('title', 'this issue')}"
                response = self.generate_human_argument(responder, topic, "rebuttal", context)
                exchanges.append(response)
                print(f"\n{response}")
                time.sleep(1)
                
                # Moderator might interject
                if i == len(persona_list) - 1 and len(persona_list) > 2:
                    moderator_interjection = self.moderator.facilitate_exchange(
                        persona_list[0]['name'], 
                        responder['name'], 
                        topic.get('title', 'this topic')
                    )
                    exchanges.append(moderator_interjection)
                    print(f"\n{moderator_interjection}")
                    time.sleep(1)
                    
                    # First speaker responds to final point
                    final_context = f"responding to {responder['name']}'s challenge"
                    final_response = self.generate_human_argument(first_speaker, topic, "rebuttal", final_context)
                    exchanges.append(final_response)
                    print(f"\n{final_response}")
            
            # Add to conversation history
            self.conversation_history.extend(exchanges)
            
            return exchanges
    
    def run_multi_topic_debate(self, personas: Dict[str, Dict[str, Any]], topics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run debate across multiple topics with moderator guidance"""
        
        print(f"\n🎭 === MULTI-TOPIC DEBATE SESSION ===")
        
        debate_results = {
            "session_id": self.session_id,
            "topics_discussed": [],
            "moderator_transitions": [],
            "natural_exchanges": [],
            "speaking_stats": self.speaking_time.copy()
        }
        
        with self._weave_attributes({
            "total_topics": len(topics_list),
            "participants": len(personas),
            "session_id": self.session_id,
            "step": "multi_topic_debate"
        }):
            # Discuss each topic
            for topic_num, topic in enumerate(topics_list, 1):
                print(f"\n📋 Topic {topic_num}/{len(topics_list)}: {topic.get('title', 'Unknown')}")
                
                # Moderator introduces topic
                if topic_num > 1:
                    transition = self.moderator.transition_to_topic(
                        topic.get('title', 'Unknown'), 
                        topic_num, 
                        len(topics_list)
                    )
                    debate_results["moderator_transitions"].append(transition)
                    print(f"\n{transition}")
                    time.sleep(1)
                
                # Natural exchange on this topic
                exchanges = self.facilitate_natural_exchange(personas, topic, "discussion")
                
                # Check for balance - if someone hasn't spoken much, moderator intervenes
                self._check_speaking_balance(personas)
                
                topic_result = {
                    "topic_number": topic_num,
                    "topic_title": topic.get('title', 'Unknown'),
                    "exchanges": exchanges,
                    "timestamp": datetime.now().isoformat()
                }
                
                debate_results["topics_discussed"].append(topic_result)
                debate_results["natural_exchanges"].extend(exchanges)
                
                # Moderator wraps up topic
                if topic_num < len(topics_list):
                    key_points = [f"disagreement about {topic.get('title', 'this issue')}"]
                    wrap_up = self.moderator.wrap_up_topic(topic.get('title', 'Unknown'), key_points)
                    print(f"\n{wrap_up}")
                    time.sleep(1)
                
                print(f"\n✅ Topic {topic_num} complete")
                time.sleep(2)
        
        return debate_results
    
    def _check_speaking_balance(self, personas: Dict[str, Dict[str, Any]]):
        """Check if speaking time is balanced, have moderator intervene if needed"""
        
        total_speaking = sum(self.speaking_time.values())
        if total_speaking < 2:
            return
        
        # Find who's spoken the most and least
        most_spoken = max(self.speaking_time, key=self.speaking_time.get)
        least_spoken = min(self.speaking_time, key=self.speaking_time.get)
        
        # If imbalance is significant, moderator intervenes
        if self.speaking_time[most_spoken] > self.speaking_time[least_spoken] + 2:
            quiet_speakers = [name for name, count in self.speaking_time.items() 
                            if count < self.speaking_time[most_spoken] - 1]
            
            if quiet_speakers:
                interruption = self.moderator.interrupt_for_balance(
                    personas[most_spoken]['name'], 
                    [personas[name]['name'] for name in quiet_speakers]
                )
                print(f"\n{interruption}")
                time.sleep(1)
    
    def synthesize_unbiased_conclusion(self, policy_info: Dict[str, Any], personas: Dict[str, Dict[str, Any]]) -> str:
        """Generate unbiased conclusion based on all arguments presented"""
        
        print(f"\n📊 Synthesizing Unbiased Conclusion...")
        
        with self._weave_attributes({
            "total_arguments": len(self.all_arguments),
            "participants": len(personas),
            "session_id": self.session_id,
            "step": "unbiased_conclusion"
        }):
            participant_names = [persona['name'] for persona in personas.values()]
            policy_title = policy_info.get('title', 'This Policy')
            
            # Create comprehensive conclusion
            conclusion = self.moderator.synthesize_conclusion(
                policy_title,
                self.all_arguments,
                participant_names
            )
            
            return conclusion
    
    def run_debate(self, policy_name: str) -> Dict[str, Any]:
        """Run complete enhanced human-like debate session with active moderator"""
        
        print(f"\n🚀 === ENHANCED HUMAN-LIKE POLICY DEBATE: {policy_name.upper()} ===")
        print(f"🎭 Session ID: {self.session_id}")
        
        start_time = datetime.now()
        
        with self._weave_attributes({
            "policy_name": policy_name,
            "session_id": self.session_id,
            "debate_type": "enhanced_human_conversational",
            "step": "enhanced_full_debate"
        }):
            try:
                # Step 1: Load Policy
                print(f"\n📄 Loading Policy...")
                policy_info = self.load_policy(policy_name)
                policy_text = policy_info.get("text", "")
                
                print(f"✅ Policy: {policy_info.get('title', 'Unknown')}")
                
                # Step 2: Identify Stakeholders
                print(f"\n🎯 Identifying Stakeholders...")
                stakeholder_list = self.identify_stakeholders(policy_text)
                
                # Step 3: Create Human Personas
                personas = self.create_personas(stakeholder_list)
                
                # Step 4: Analyze Multiple Debate Topics
                print(f"\n📋 Analyzing Debate Topics...")
                topics_list = self.analyze_topics(policy_text, stakeholder_list)
                
                print(f"✅ Found {len(topics_list)} debate topics")
                for i, topic in enumerate(topics_list, 1):
                    print(f"   {i}. {topic.get('title', 'Unknown')} (Priority: {topic.get('priority', 'N/A')})")
                
                # Step 5: Moderator Introduction
                participant_names = [persona['name'] for persona in personas.values()]
                topic_titles = [topic.get('title', 'Unknown') for topic in topics_list]
                
                introduction = self.moderator.introduce_debate(
                    policy_info.get('title', 'This Policy'),
                    participant_names,
                    topic_titles
                )
                print(f"\n{introduction}")
                time.sleep(2)
                
                # Step 6: Enhanced Multi-Topic Debate
                debate_results = self.run_multi_topic_debate(personas, topics_list)
                
                # Step 7: Unbiased Conclusion
                print(f"\n🎯 === MODERATOR'S UNBIASED CONCLUSION ===")
                conclusion = self.synthesize_unbiased_conclusion(policy_info, personas)
                print(f"\n{conclusion}")
                
                # Compile final results
                end_time = datetime.now()
                final_results = {
                    "session_id": self.session_id,
                    "policy_info": policy_info,
                    "personas": personas,
                    "topics_discussed": topics_list,
                    "debate_results": debate_results,
                    "moderator_conclusion": conclusion,
                    "all_arguments": self.all_arguments,
                    "conversation_history": self.conversation_history,
                    "speaking_stats": self.speaking_time,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "total_duration": (end_time - start_time).total_seconds()
                }
                
                print(f"\n🎉 === ENHANCED DEBATE SESSION COMPLETED ===")
                print(f"🎭 Participants: {', '.join(participant_names)}")
                print(f"📋 Topics Covered: {len(topics_list)}")
                print(f"📊 Total Arguments: {len(self.all_arguments)}")
                print(f"💬 Conversation Turns: {len(self.conversation_history)}")
                print(f"⏱️  Duration: {final_results['total_duration']:.1f} seconds")
                if self.weave_enabled:
                    print(f"🔗 View traces: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-human-debate")
                
                return final_results
                
            except Exception as e:
                print(f"❌ Error in enhanced human debate: {e}")
                raise 