"""
Weave-Integrated Real-Time Policy Debate System
Perfect for hackathon demonstrations with full tracing capabilities
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    print("⚠️  Weave not available - install with: pip install weave")

from ..base import BaseDebateSystem


class WeaveDebateSystem(BaseDebateSystem):
    """
    Real-time debate system with comprehensive Weave tracing for hackathon demos
    """
    
    def __init__(self):
        super().__init__("weave_debate")
        
        if WEAVE_AVAILABLE:
            # Initialize Weave with project name
            weave.init(project_name="civicai-hackathon")
            print(f"🔗 Weave Tracing Active - Session: {self.session_id}")
            print(f"📊 View traces at: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon")
        else:
            print("⚠️  Weave tracing disabled - functionality will work without tracing")
    
    def _weave_op(self, func):
        """Decorator wrapper for weave operations"""
        if WEAVE_AVAILABLE:
            return weave.op()(func)
        return func
    
    def _weave_attributes(self, attrs):
        """Context manager wrapper for weave attributes"""
        if WEAVE_AVAILABLE:
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
        """Create simple personas for weave tracking"""
        personas = {}
        
        for stakeholder in stakeholder_list:
            name = stakeholder.get('name', 'Unknown')
            persona = {
                'name': name,
                'stakeholder_group': name,
                'stance': stakeholder.get('likely_stance', 'unknown'),
                'interests': stakeholder.get('interests', []),
                'concerns': stakeholder.get('key_concerns', [])
            }
            personas[name] = persona
        
        return personas
    
    def load_policy_with_tracing(self, policy_name: str) -> Dict[str, Any]:
        """Load policy with weave tracing"""
        print(f"\n📄 Loading Policy: {policy_name}")
        
        with self._weave_attributes({
            "policy_name": policy_name,
            "session_id": self.session_id,
            "step": "load_policy"
        }):
            policy_info = self.load_policy(policy_name)
            
            print(f"✅ Policy loaded: {policy_info.get('title', 'Unknown Title')}")
            print(f"📊 Policy text length: {len(policy_info.get('text', ''))} characters")
            
            return policy_info
    
    def identify_stakeholders_with_tracing(self, policy_text: str) -> List[Dict[str, Any]]:
        """Identify stakeholders with weave tracing"""
        print(f"\n🎯 Identifying Stakeholders...")
        
        with self._weave_attributes({
            "policy_text_length": len(policy_text),
            "session_id": self.session_id,
            "step": "identify_stakeholders"
        }):
            stakeholder_list = self.identify_stakeholders(policy_text)
            
            print(f"✅ Found {len(stakeholder_list)} stakeholders:")
            for i, stakeholder in enumerate(stakeholder_list, 1):
                name = stakeholder.get('name', 'Unknown')
                stakeholder_type = stakeholder.get('type', 'unknown')
                stance = stakeholder.get('likely_stance', 'unknown')
                print(f"   {i}. {name} ({stakeholder_type}) - Stance: {stance}")
            
            return stakeholder_list
    
    def research_stakeholder_perspective(self, stakeholder: Dict[str, Any], policy_text: str) -> Dict[str, Any]:
        """Research stakeholder perspective with Weave tracing"""
        stakeholder_name = stakeholder.get('name', 'Unknown')
        print(f"\n🔍 Researching {stakeholder_name} perspective...")
        
        with self._weave_attributes({
            "stakeholder_name": stakeholder_name,
            "stakeholder_type": stakeholder.get('type', 'unknown'),
            "session_id": self.session_id,
            "step": "research_stakeholder"
        }):
            research_result = self.stakeholder_researcher._run(
                json.dumps(stakeholder), 
                policy_text
            )
            
            if research_result.startswith("Error"):
                print(f"❌ Research failed for {stakeholder_name}: {research_result}")
                return {"error": research_result}
            
            research_data = json.loads(research_result)
            
            print(f"✅ Research completed for {stakeholder_name}")
            print(f"   📊 Confidence: {research_data.get('confidence_level', 'unknown')}")
            print(f"   📋 Summary: {research_data.get('research_summary', '')[:100]}...")
            
            return research_data
    
    def analyze_debate_topics_with_tracing(self, policy_text: str, stakeholder_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze debate topics with Weave tracing"""
        print(f"\n📋 Analyzing debate topics...")
        
        with self._weave_attributes({
            "stakeholder_count": len(stakeholder_data.get('stakeholders', [])),
            "session_id": self.session_id,
            "step": "analyze_topics"
        }):
            topics_list = self.analyze_topics(policy_text, stakeholder_data['stakeholders'])
            
            print(f"✅ Found {len(topics_list)} debate topics:")
            for i, topic in enumerate(topics_list[:3], 1):  # Show top 3
                title = topic.get('title', 'Unknown Topic')
                priority = topic.get('priority', 0)
                print(f"   {i}. {title} (Priority: {priority}/10)")
            
            return topics_list
    
    def generate_argument_with_tracing(self, stakeholder_name: str, topic: Dict[str, Any], argument_type: str) -> Dict[str, Any]:
        """Generate stakeholder argument with Weave tracing"""
        print(f"\n💬 {stakeholder_name} generating {argument_type}...")
        
        with self._weave_attributes({
            "stakeholder_name": stakeholder_name,
            "argument_type": argument_type,
            "topic_title": topic.get('title', 'Unknown'),
            "topic_priority": topic.get('priority', 0),
            "session_id": self.session_id,
            "debate_round": self.debate_round,
            "step": "generate_argument"
        }):
            argument_result = self.generate_argument(stakeholder_name, topic, argument_type)
            
            if argument_result.startswith("Error"):
                print(f"❌ Argument generation failed: {argument_result}")
                return {"error": argument_result}
            
            argument_data = json.loads(argument_result)
            
            print(f"✅ {argument_type.title()} generated")
            print(f"   💪 Strength: {argument_data.get('strength', 'N/A')}/10")
            print(f"   📝 Preview: {argument_data.get('content', '')[:100]}...")
            
            return argument_data
    
    def send_a2a_message_with_tracing(self, sender: str, receiver: str, message_type: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send A2A message with Weave tracing"""
        print(f"\n📧 A2A Message: {sender} → {receiver}")
        
        with self._weave_attributes({
            "sender": sender,
            "receiver": receiver,
            "message_type": message_type,
            "session_id": self.session_id,
            "debate_round": self.debate_round,
            "step": "a2a_message"
        }):
            message_result = self.send_a2a_message(sender, receiver, message_type, content, context)
            
            if message_result.startswith("Error"):
                print(f"❌ A2A message failed: {message_result}")
                return {"error": message_result}
            
            message_data = json.loads(message_result)
            
            print(f"✅ Message sent successfully")
            print(f"   📋 Type: {message_data.get('message_type', 'unknown')}")
            print(f"   🆔 ID: {message_data.get('message_id', 'unknown')}")
            
            return message_data
    
    def run_debate_round_with_tracing(self, stakeholder_list: List[Dict[str, Any]], topics_list: List[Dict[str, Any]], round_type: str) -> Dict[str, Any]:
        """Run debate round with comprehensive tracing"""
        
        self.debate_round += 1
        
        print(f"\n🎭 === ROUND {self.debate_round}: {round_type.upper()} ===")
        
        with self._weave_attributes({
            "round_number": self.debate_round,
            "round_type": round_type,
            "participant_count": len(stakeholder_list),
            "session_id": self.session_id,
            "step": "debate_round"
        }):
            round_results = {
                "round_number": self.debate_round,
                "round_type": round_type,
                "arguments": [],
                "a2a_messages": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Use first topic for debate
            main_topic = topics_list[0] if topics_list else {"title": "Policy Discussion", "priority": 5}
            print(f"📢 Topic: {main_topic.get('title', 'Unknown')}")
            
            # Generate arguments for each stakeholder
            for stakeholder in stakeholder_list:
                stakeholder_name = stakeholder.get('name', 'Unknown')
                
                argument_data = self.generate_argument_with_tracing(stakeholder_name, main_topic, round_type)
                
                if "error" not in argument_data:
                    round_results["arguments"].append({
                        "stakeholder": stakeholder_name,
                        "argument_data": argument_data,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Store in conversation history
                    self.conversation_history.append(argument_data.get('content', ''))
                    
                    # Store in all arguments
                    self.all_arguments.append({
                        "speaker": stakeholder_name,
                        "stakeholder_group": stakeholder_name,
                        "topic": main_topic.get('title', 'Unknown'),
                        "content": argument_data.get('content', ''),
                        "evidence": argument_data.get('evidence', []),
                        "argument_type": round_type,
                        "timestamp": datetime.now().isoformat()
                    })
                
                time.sleep(1)  # Pause between speakers
            
            # A2A messaging after each round
            if len(stakeholder_list) >= 2:
                print(f"\n📡 A2A Messaging Round {self.debate_round}")
                
                for i in range(len(stakeholder_list)):
                    for j in range(i + 1, len(stakeholder_list)):
                        sender = stakeholder_list[i].get('name', 'Unknown')
                        receiver = stakeholder_list[j].get('name', 'Unknown')
                        
                        # Find sender's argument from this round
                        sender_arg = None
                        for arg in round_results["arguments"]:
                            if arg["stakeholder"] == sender:
                                sender_arg = arg["argument_data"]
                                break
                        
                        if sender_arg:
                            message_content = f"Regarding {round_type}: {sender_arg.get('content', '')[:100]}..."
                            context = {
                                "round": self.debate_round,
                                "topic": main_topic.get('title', 'Unknown')
                            }
                            
                            message_data = self.send_a2a_message_with_tracing(
                                sender, receiver, "debate_response", message_content, context
                            )
                            
                            if "error" not in message_data:
                                round_results["a2a_messages"].append({
                                    "sender": sender,
                                    "receiver": receiver,
                                    "message_data": message_data,
                                    "timestamp": datetime.now().isoformat()
                                })
                        
                        time.sleep(0.5)  # Brief pause between messages
            
            print(f"✅ Round {self.debate_round} completed - {len(round_results['arguments'])} arguments, {len(round_results['a2a_messages'])} A2A messages")
            
            return round_results
    
    def run_debate(self, policy_name: str) -> Dict[str, Any]:
        """Run complete debate with full Weave tracing"""
        
        print(f"\n🚀 === WEAVE-TRACED POLICY DEBATE: {policy_name.upper()} ===")
        print(f"🎭 Session ID: {self.session_id}")
        
        start_time = datetime.now()
        
        with self._weave_attributes({
            "policy_name": policy_name,
            "session_id": self.session_id,
            "debate_type": "weave_traced",
            "step": "full_debate"
        }):
            try:
                # Step 1: Load Policy
                policy_info = self.load_policy_with_tracing(policy_name)
                policy_text = policy_info.get("text", "")
                
                # Step 2: Identify Stakeholders
                stakeholder_list = self.identify_stakeholders_with_tracing(policy_text)
                
                # Step 3: Create Personas
                personas = self.create_personas(stakeholder_list)
                
                # Step 4: Research Stakeholder Perspectives
                print(f"\n🔬 === RESEARCH PHASE ===")
                stakeholder_research = {}
                
                for stakeholder in stakeholder_list:
                    research_data = self.research_stakeholder_perspective(stakeholder, policy_text)
                    stakeholder_name = stakeholder.get('name', 'Unknown')
                    
                    if "error" not in research_data:
                        stakeholder_research[stakeholder_name] = research_data
                        
                        # Store in knowledge base
                        kb_result = self.kb_manager._run(stakeholder_name, json.dumps(research_data), "create")
                        print(f"   📚 Stored in KB: {kb_result}")
                
                # Step 5: Analyze Topics
                stakeholder_summary = {"stakeholders": stakeholder_list}
                topics_list = self.analyze_debate_topics_with_tracing(policy_text, stakeholder_summary)
                
                # Step 6: Initialize Debate Session
                print(f"\n🎭 === DEBATE SESSION INITIALIZATION ===")
                session_result = self.create_debate_session(policy_info, stakeholder_list)
                print(f"✅ Session initialized: {session_result}")
                
                # Step 7: Run Debate Rounds
                print(f"\n🗣️ === DEBATE ROUNDS ===")
                round_results = []
                
                # Round 1: Opening Statements
                round1 = self.run_debate_round_with_tracing(stakeholder_list, topics_list, "claim")
                round_results.append(round1)
                
                # Round 2: Rebuttals
                round2 = self.run_debate_round_with_tracing(stakeholder_list, topics_list, "rebuttal")
                round_results.append(round2)
                
                # Round 3: Closing Arguments
                round3 = self.run_debate_round_with_tracing(stakeholder_list, topics_list, "closing")
                round_results.append(round3)
                
                # Step 8: End Session
                print(f"\n🏁 === SESSION CONCLUSION ===")
                end_result = self.end_debate_session()
                print(f"✅ Session ended: {end_result}")
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                # Compile results
                results = {
                    "session_id": self.session_id,
                    "policy_info": policy_info,
                    "stakeholder_list": stakeholder_list,
                    "personas": personas,
                    "stakeholder_research": stakeholder_research,
                    "topics_list": topics_list,
                    "round_results": round_results,
                    "all_arguments": self.all_arguments,
                    "conversation_history": self.conversation_history,
                    "duration": duration,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                }
                
                # Final statistics
                total_arguments = sum(len(r.get('arguments', [])) for r in round_results)
                total_messages = sum(len(r.get('a2a_messages', [])) for r in round_results)
                
                print(f"\n🎉 === WEAVE-TRACED DEBATE COMPLETED ===")
                print(f"📊 Duration: {duration:.1f} seconds")
                print(f"💬 Total arguments: {total_arguments}")
                print(f"📧 Total A2A messages: {total_messages}")
                print(f"🎭 Participants: {len(stakeholder_list)}")
                
                if WEAVE_AVAILABLE:
                    print(f"🔗 View full traces at: https://wandb.ai/aniruddhr04-university-of-cincinnati/civicai-hackathon")
                
                return results
                
            except Exception as e:
                print(f"❌ Error in weave debate: {e}")
                raise 