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
    
    def log_step(self, step: str, message: str, status: str = "🔄"):
        """Log each step with timestamp - base implementation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] {status} {step}: {message}")
    
    def log_agent_action(self, agent_name: str, action: str, details: str = ""):
        """Log individual agent actions - base implementation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🤖 {agent_name}: {action}")
        if details:
            print(f"    💬 {details}")

    def load_policy(self, policy_name: str) -> Dict[str, Any]:
        """Load policy data from file"""
        try:
            # Ensure the filename has the .json extension
            if not policy_name.endswith('.json'):
                policy_file = f"{policy_name}.json"
            else:
                policy_file = policy_name
            
            policy_result = self.policy_reader._run(policy_file)
            
            if policy_result.startswith("Error"):
                return {"error": policy_result}
            
            policy_data = json.loads(policy_result)
            
            # Handle nested policy structure
            if "policy_document" in policy_data:
                policy_doc = policy_data["policy_document"]
                return {
                    "id": policy_name,
                    "title": policy_doc.get("title", "Unknown Policy"),
                    "text": policy_doc.get("text", ""),
                    "source_url": policy_doc.get("source_url", ""),
                    "summary": policy_doc.get("summary", "No summary available"),
                    "date": policy_data.get("date", "Unknown Date"),
                    "user_profile": policy_data.get("user_profile", {})
                }
            else:
                # Handle flat structure (fallback)
                return {
                    "id": policy_name,
                    "title": policy_data.get("title", "Unknown Policy"),
                    "text": policy_data.get("text", ""),
                    "summary": policy_data.get("summary", "No summary available"),
                    "date": policy_data.get("date", "Unknown Date")
                }
        except Exception as e:
            return {"error": f"Error loading policy: {str(e)}"}
    
    def get_llm_response(self, prompt: str, analysis_type: str = "general") -> Dict[str, Any]:
        """Get LLM response using Claude instead of mock weave client"""
        try:
            # Import here to avoid circular imports
            from crewai import LLM
            import os
            
            # Try to use Claude LLM
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_api_key:
                llm = LLM(
                    model="claude-3-5-sonnet-20241022",
                    api_key=anthropic_api_key,
                    temperature=0.7,
                    max_tokens=4096
                )
                
                # Create analysis-specific prompts
                if analysis_type == "stakeholder_identification":
                    formatted_prompt = f"""
Analyze the following policy text and identify ONLY the main stakeholders who are directly and significantly affected.

Policy Text:
{prompt}

Return ONLY a valid JSON object with this exact structure:
{{
    "stakeholders": [
        {{
            "name": "Stakeholder Name",
            "type": "stakeholder_type",
            "interests": ["interest1", "interest2"],
            "direct_impact": "How they are directly affected",
            "stance": "supportive/opposed/neutral",
            "concerns": ["concern1", "concern2"]
        }}
    ]
}}
"""
                elif analysis_type == "topic_analysis":
                    formatted_prompt = f"""
Analyze this policy and identify key debate topics that would generate discussion.

Policy Text:
{prompt}

Return ONLY a valid JSON object with this structure:
{{
    "debate_topics": [
        {{
            "title": "Topic Title",
            "description": "Topic description",
            "priority": 8,
            "stakeholders_involved": ["stakeholder1", "stakeholder2"],
            "key_questions": ["question1", "question2"]
        }}
    ]
}}
"""
                elif analysis_type == "argument_generation":
                    formatted_prompt = prompt  # For argument generation, the prompt is already formatted
                else:
                    formatted_prompt = prompt
                
                response = llm.call(formatted_prompt)
                
                # Try to parse as JSON
                try:
                    # Clean up response if it has markdown formatting
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()
                    
                    return json.loads(cleaned_response)
                except json.JSONDecodeError:
                    # If not valid JSON, return as text
                    return {"error": f"Failed to parse JSON response: {response}"}
            else:
                return {"error": "No LLM available - ANTHROPIC_API_KEY not found"}
                
        except Exception as e:
            return {"error": f"LLM error: {str(e)}"}

    def identify_stakeholders(self, policy_text: str) -> List[Dict[str, Any]]:
        """Identify stakeholders using proper LLM"""
        try:
            result = self.get_llm_response(policy_text, "stakeholder_identification")
            
            if "error" in result:
                print(f"❌ Error in stakeholder identification: {result['error']}")
                # Return fallback stakeholders
                return [
                    {"name": "Tenants", "type": "residents", "interests": ["affordable_housing"], "likely_stance": "supportive"},
                    {"name": "Landlords", "type": "property_owners", "interests": ["property_rights"], "likely_stance": "opposed"},
                    {"name": "City Officials", "type": "government", "interests": ["policy_implementation"], "likely_stance": "neutral"}
                ]
            
            stakeholders = result.get("stakeholders", [])
            print(f"✅ Found {len(stakeholders)} stakeholders")
            for i, stakeholder in enumerate(stakeholders, 1):
                name = stakeholder.get('name', 'Unknown')
                stance = stakeholder.get('stance', stakeholder.get('likely_stance', 'neutral'))
                print(f"   {i}. {name} (Stance: {stance})")
            
            return stakeholders
            
        except Exception as e:
            print(f"❌ Error in stakeholder identification: {str(e)}")
            # Return fallback stakeholders
            return [
                {"name": "Tenants", "type": "residents", "interests": ["affordable_housing"], "likely_stance": "supportive"},
                {"name": "Landlords", "type": "property_owners", "interests": ["property_rights"], "likely_stance": "opposed"},
                {"name": "City Officials", "type": "government", "interests": ["policy_implementation"], "likely_stance": "neutral"}
            ]

    def analyze_topics(self, policy_text: str, stakeholders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze topics using proper LLM"""
        try:
            # Prepare stakeholder info for context
            stakeholder_context = f"\nStakeholder Context:\n"
            for stakeholder in stakeholders:
                stakeholder_context += f"- {stakeholder.get('name', 'Unknown')}: {stakeholder.get('likely_stance', 'neutral')} stance\n"
            
            combined_prompt = policy_text + stakeholder_context
            result = self.get_llm_response(combined_prompt, "topic_analysis")
            
            if "error" in result:
                print(f"❌ Error in topic analysis: {result['error']}")
                # Return fallback topics
                return [
                    {
                        "title": "Policy Implementation Timeline",
                        "description": "Discussion of implementation timeline and requirements",
                        "priority": 8,
                        "stakeholders_involved": [s.get('name', 'Unknown') for s in stakeholders[:3]],
                        "key_questions": ["Is the timeline realistic?", "What support is needed?"]
                    }
                ]
            
            topics = result.get("debate_topics", [])
            print(f"✅ Found {len(topics)} debate topics")
            for i, topic in enumerate(topics, 1):
                title = topic.get('title', 'Unknown Topic')
                priority = topic.get('priority', 'N/A')
                print(f"   {i}. {title} (Priority: {priority}/10)")
            
            return topics
            
        except Exception as e:
            print(f"❌ Error in topic analysis: {str(e)}")
            # Return fallback topics
            return [
                {
                    "title": "Policy Implementation Timeline",
                    "description": "Discussion of implementation timeline and requirements",
                    "priority": 8,
                    "stakeholders_involved": [s.get('name', 'Unknown') for s in stakeholders[:3]],
                    "key_questions": ["Is the timeline realistic?", "What support is needed?"]
                }
            ]

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
        """Generate argument for a stakeholder on a topic using proper LLM"""
        try:
            # Create argument prompt
            topic_title = topic.get('title', 'Unknown Topic')
            topic_description = topic.get('description', '')
            
            prompt = f"""
You are representing {stakeholder_name} in a policy debate about "{topic_title}".

Topic: {topic_title}
Description: {topic_description}

Generate a {argument_type} argument from {stakeholder_name}'s perspective. The argument should be:
- Factual and evidence-based
- Relevant to their interests and concerns
- Professional and respectful
- 2-3 sentences long

Return ONLY a valid JSON object with this structure:
{{
    "stakeholder_name": "{stakeholder_name}",
    "argument_type": "{argument_type}",
    "content": "The actual argument content here",
    "strength": 7,
    "evidence": ["Supporting evidence 1", "Supporting evidence 2"]
}}
"""
            
            result = self.get_llm_response(prompt, "argument_generation")
            
            if "error" in result:
                # Return fallback argument
                fallback_content = f"As {stakeholder_name}, I believe this policy requires careful consideration of all stakeholder impacts and proper implementation planning."
                return json.dumps({
                    "stakeholder_name": stakeholder_name,
                    "argument_type": argument_type,
                    "content": fallback_content,
                    "strength": 6,
                    "evidence": ["Stakeholder analysis", "Policy review"]
                })
            
            # Return the LLM result as JSON string
            return json.dumps(result)
            
        except Exception as e:
            # Return fallback argument on error
            fallback_content = f"As {stakeholder_name}, I have important concerns about this policy that need to be addressed."
            return json.dumps({
                "stakeholder_name": stakeholder_name,
                "argument_type": argument_type,
                "content": fallback_content,
                "strength": 5,
                "evidence": ["Policy analysis"]
            })
    
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