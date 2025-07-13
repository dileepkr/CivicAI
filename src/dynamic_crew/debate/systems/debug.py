"""
Debug Real-Time Policy Debate System
Shows live agent interactions without complex logging that causes hangs
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any

from ..base import BaseDebateSystem


class DebugDebateSystem(BaseDebateSystem):
    """Real-time debug debate system with live agent action logging"""
    
    def __init__(self):
        super().__init__("debug_debate")
        print("🐛 Debug Mode: Shows live agent interactions without complex logging")
    
    def log_step(self, step: str, message: str, status: str = "🔄"):
        """Log each step with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {status} {step}: {message}")
    
    def log_agent_action(self, agent_name: str, action: str, details: str = ""):
        """Log individual agent actions"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🤖 {agent_name}: {action}")
        if details:
            print(f"    💬 {details}")
    
    def create_personas(self, stakeholder_list: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Create simple personas for debug mode"""
        personas = {}
        
        print(f"\n👥 DEBATE PARTICIPANTS:")
        for i, stakeholder in enumerate(stakeholder_list, 1):
            name = stakeholder.get('name', 'Unknown')
            stance = stakeholder.get('likely_stance', 'unknown')
            
            # Create simple persona
            persona = {
                'name': name,
                'stakeholder_group': name,
                'stance': stance,
                'interests': stakeholder.get('interests', []),
                'concerns': stakeholder.get('key_concerns', [])
            }
            
            personas[name] = persona
            print(f"   {i}. {name} (Initial stance: {stance})")
        
        return personas
    
    def run_debate_round(self, stakeholders: List[Dict[str, Any]], topics: List[Dict[str, Any]], round_type: str, round_num: int) -> List[Dict[str, Any]]:
        """Run a debate round with live logging"""
        
        if not topics:
            return []
        
        debate_topic = topics[0]
        results = []
        
        print(f"\n🔴 ROUND {round_num}: {round_type.upper()}")
        print("-" * 40)
        
        if round_num == 1:
            print(f"\n🎯 DEBATING: {debate_topic.get('title', 'Unknown Topic')}")
            print(f"📝 Description: {debate_topic.get('description', 'No description')}")
            print("\n" + "="*60)
        
        for i, stakeholder in enumerate(stakeholders):
            name = stakeholder.get('name', 'Unknown')
            self.log_agent_action(f"{name} Agent", f"Preparing {round_type}...")
            
            time.sleep(1)  # Simulate thinking time
            
            argument_result = self.generate_argument(name, debate_topic, round_type)
            
            if not argument_result.startswith("Error"):
                try:
                    argument = json.loads(argument_result)
                    content = argument.get('content', 'No content available')
                    strength = argument.get('strength', 'N/A')
                    
                    print(f"\n💬 {name}:")
                    print(f"   {content}")
                    print(f"   (Argument strength: {strength}/10)")
                    
                    self.log_agent_action(f"{name} Agent", "✅ Statement delivered")
                    
                    results.append({
                        'speaker': name,
                        'content': content,
                        'strength': strength,
                        'round': round_num,
                        'type': round_type
                    })
                    
                except json.JSONDecodeError:
                    print(f"\n💬 {name}: [Argument parsing failed]")
                    self.log_agent_action(f"{name} Agent", "❌ Argument parsing failed")
            else:
                print(f"\n💬 {name}: [Failed to generate argument]")
                self.log_agent_action(f"{name} Agent", "❌ Failed to generate argument")
        
        return results
    
    def simulate_a2a_messaging(self, stakeholders: List[Dict[str, Any]], round_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulate agent-to-agent messaging"""
        
        if len(stakeholders) < 2:
            return []
        
        print(f"\n📡 A2A MESSAGING")
        print("-" * 20)
        
        messages = []
        
        # Simulate cross-stakeholder messaging
        for i in range(len(stakeholders)):
            for j in range(i + 1, len(stakeholders)):
                sender = stakeholders[i].get('name', 'Unknown')
                receiver = stakeholders[j].get('name', 'Unknown')
                
                self.log_agent_action(f"{sender} Agent", f"Sending message to {receiver}...")
                
                # Find sender's last argument
                sender_arg = None
                for result in reversed(round_results):
                    if result['speaker'] == sender:
                        sender_arg = result
                        break
                
                if sender_arg:
                    message_content = f"Regarding {sender_arg.get('type', 'argument')}: {sender_arg.get('content', '')[:100]}..."
                    
                    message_result = self.send_a2a_message(
                        sender,
                        receiver,
                        "debate_point",
                        message_content,
                        {'round': sender_arg.get('round', 1)}
                    )
                    
                    if not message_result.startswith("Error"):
                        try:
                            message = json.loads(message_result)
                            print(f"   📧 {sender} → {receiver}: {message.get('message_type', 'unknown')}")
                            messages.append(message)
                            self.log_agent_action(f"{sender} Agent", f"✅ Message sent to {receiver}")
                        except json.JSONDecodeError:
                            self.log_agent_action(f"{sender} Agent", f"❌ Message parsing failed")
                    else:
                        self.log_agent_action(f"{sender} Agent", f"❌ Message failed: {message_result}")
                
                time.sleep(0.5)  # Brief pause between messages
        
        return messages
    
    def run_debate(self, policy_name: str) -> Dict[str, Any]:
        """Run complete debug debate with live logging"""
        
        print("🎭 REAL-TIME POLICY DEBATE SYSTEM")
        print("=" * 50)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Load Policy
            self.log_step("STEP 1", "Reading policy file...", "📖")
            policy_info = self.load_policy(policy_name)
            policy_text = policy_info.get("text", "")
            self.log_step("STEP 1", f"✅ Policy loaded: {policy_info.get('title', 'Unknown')}", "✅")
            
            # Step 2: Identify Stakeholders
            self.log_step("STEP 2", "Identifying stakeholders...", "🔍")
            stakeholders = self.identify_stakeholders(policy_text)
            self.log_step("STEP 2", f"✅ Found {len(stakeholders)} stakeholders", "✅")
            
            # Step 3: Create Personas
            personas = self.create_personas(stakeholders)
            
            # Step 4: Research Phase
            self.log_step("STEP 3", "Stakeholder research phase...", "🔬")
            stakeholder_research = {}
            
            for stakeholder in stakeholders:
                name = stakeholder.get('name', 'Unknown')
                self.log_agent_action(f"{name} Research Agent", "Conducting policy analysis...")
                
                research_result = self.stakeholder_researcher._run(json.dumps(stakeholder), policy_text)
                
                if not research_result.startswith("Error"):
                    stakeholder_research[name] = json.loads(research_result)
                    
                    # Store in knowledge base
                    kb_result = self.kb_manager._run(name, research_result, "create")
                    self.log_agent_action(f"{name} Research Agent", f"✅ Analysis complete", kb_result)
                else:
                    self.log_agent_action(f"{name} Research Agent", f"❌ Research failed", research_result)
            
            # Step 5: Topic Analysis
            self.log_step("STEP 4", "Analyzing debate topics...", "📋")
            topics = self.analyze_topics(policy_text, stakeholders)
            
            self.log_agent_action("Topic Analyzer", f"✅ Identified {len(topics)} debate topics")
            
            print("\n📋 DEBATE TOPICS:")
            for i, topic in enumerate(topics[:3], 1):  # Show top 3 topics
                title = topic.get('title', 'Unknown Topic')
                priority = topic.get('priority', 'N/A')
                print(f"   {i}. {title} (Priority: {priority}/10)")
            
            # Step 6: Initialize Debate Session
            self.log_step("STEP 5", "Starting debate session...", "🎭")
            session_result = self.create_debate_session(policy_info, stakeholders)
            self.log_agent_action("Debate Moderator", f"✅ Session {self.session_id} started")
            
            # Step 7: Live Debate Simulation
            self.log_step("STEP 6", "LIVE DEBATE IN PROGRESS", "🗣️")
            
            all_results = []
            all_messages = []
            
            if len(topics) > 0 and len(stakeholders) >= 2:
                # Round 1: Opening Statements
                round1_results = self.run_debate_round(stakeholders, topics, "claim", 1)
                all_results.extend(round1_results)
                self.conversation_history.extend([r['content'] for r in round1_results])
                
                # A2A Messaging after round 1
                messages = self.simulate_a2a_messaging(stakeholders, round1_results)
                all_messages.extend(messages)
                
                # Round 2: Rebuttals
                round2_results = self.run_debate_round(stakeholders, topics, "rebuttal", 2)
                all_results.extend(round2_results)
                self.conversation_history.extend([r['content'] for r in round2_results])
                
                # Round 3: Closing Statements
                round3_results = self.run_debate_round(stakeholders, topics, "closing", 3)
                all_results.extend(round3_results)
                self.conversation_history.extend([r['content'] for r in round3_results])
            
            # Step 8: End Session
            self.log_step("STEP 7", "Ending debate session...", "🏁")
            end_result = self.end_debate_session()
            self.log_agent_action("Debate Moderator", f"✅ Session ended")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Final Results
            results = {
                'session_id': self.session_id,
                'policy_info': policy_info,
                'stakeholders': stakeholders,
                'personas': personas,
                'topics': topics,
                'research': stakeholder_research,
                'debate_rounds': all_results,
                'a2a_messages': all_messages,
                'conversation_history': self.conversation_history,
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
            print(f"\n🎉 === DEBUG DEBATE COMPLETED ===")
            print(f"📊 Duration: {duration:.1f} seconds")
            print(f"💬 Total statements: {len(all_results)}")
            print(f"📧 A2A messages: {len(all_messages)}")
            print(f"🎭 Participants: {len(stakeholders)}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error in debug debate: {e}")
            raise 