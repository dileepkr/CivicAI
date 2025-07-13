"""
Centralized Weave LLM Client for CivicAI Policy Debate System

This module provides a unified interface for all LLM operations using Weave inference
with WNB_API_KEY authentication. It replaces all direct Google Gemini API calls
throughout the system.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    print("⚠️  Weave not available - install with: pip install weave")

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class WeaveClient:
    """
    Centralized Weave LLM client for all CivicAI operations
    """
    
    def __init__(self, project_name: str = "civicai-policy-debate"):
        """
        Initialize the Weave client
        
        Args:
            project_name: Name of the Weave project
        """
        self.project_name = project_name
        self.client = None
        
        # Configure model - can be overridden via environment variable
        self.model_name = os.getenv('WEAVE_MODEL_NAME', "openai/meta-llama/Llama-4-Scout-17B-16E-Instruct")
        
        # Get Groq API key (optional, will fallback to OpenAI)
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        if not self.groq_key and not self.openai_key:
            raise ValueError("Either GROQ_API_KEY or OPENAI_API_KEY environment variable is required")
        
        # Groq API configuration
        self.api_base = "https://api.groq.com/openai/v1"
        
        # Project configuration
        project_name = os.getenv('WANDB_PROJECT', 'civicai-policy-debate')
        self.extra_headers = {
            "User-Agent": "CivicAI-PolicyDebate/1.0"
        }
        
        # Initialize Weave if available
        if WEAVE_AVAILABLE:
            try:
                # Set the API key for Weave (use Groq key if available, otherwise OpenAI)
                api_key = self.groq_key or self.openai_key
                if api_key:
                    os.environ['WANDB_API_KEY'] = api_key
                
                # Disable Weave tracing to prevent circular reference issues with CrewAI
                os.environ['WEAVE_DISABLE_TRACING'] = '1'
                os.environ['WEAVE_AUTO_TRACE'] = '0'
                os.environ['WEAVE_AUTO_PATCH'] = '0'
                
                # Initialize Weave with project name
                # Note: Weave doesn't support auto_trace/auto_patch parameters in init()
                # We'll disable tracing through environment variables instead
                weave.init(project_name=self.project_name)
                self.weave_enabled = True
                
                logger.info(f"✅ Weave client initialized for project: {self.project_name}")
                print(f"✅ Weave client initialized for project: {self.project_name}")
                print(f"📊 View traces at: https://wandb.ai/your-username/{self.project_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize Weave: {e}")
                self.weave_enabled = False
                print(f"⚠️  Weave initialization failed: {e}")
                print("⚠️  Continuing without Weave tracing")
        else:
            self.weave_enabled = False
            print("⚠️  Weave not available - continuing without tracing")
    
    def generate_text(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
        retries: int = 3
    ) -> str:
        """
        Generate text using Groq API with retry logic
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (defaults to self.model_name)
            retries: Number of retry attempts
            
        Returns:
            Generated text response
        """
        # Allow text generation even if Weave is disabled
        if not hasattr(self, 'weave_enabled'):
            raise RuntimeError("Weave client not properly initialized")
        
        # Use the model parameter or default
        model_to_use = model or self.model_name
        
        last_error = None
        
        for attempt in range(retries):
            try:
                # First try Groq
                import openai
                
                groq_key = os.getenv('GROQ_API_KEY')
                if groq_key:
                    # Set up OpenAI client with Groq configuration
                    client = openai.OpenAI(
                        api_key=groq_key,
                        base_url="https://api.groq.com/openai/v1",
                        timeout=60.0  # Add timeout
                    )
                    
                    # Use Groq model
                    groq_model = "llama3-8b-8192" if "llama" in model_to_use.lower() else "llama3-8b-8192"
                    
                    # Generate response using Groq
                    response = client.chat.completions.create(
                        model=groq_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # Extract text from response
                    return response.choices[0].message.content
                else:
                    raise RuntimeError("No Groq API key available")
                
            except Exception as groq_error:
                last_error = groq_error
                logger.warning(f"Groq API attempt {attempt + 1} failed: {groq_error}")
                
                # Fallback to regular OpenAI if Groq fails
                try:
                    openai_key = os.getenv('OPENAI_API_KEY')
                    if openai_key:
                        logger.info(f"Falling back to regular OpenAI API (attempt {attempt + 1})")
                        
                        client = openai.OpenAI(
                            api_key=openai_key,
                            timeout=60.0  # Add timeout
                        )
                        
                        # Use a standard OpenAI model for fallback
                        fallback_model = "gpt-3.5-turbo" if "llama" in model_to_use.lower() else model_to_use
                        
                        response = client.chat.completions.create(
                            model=fallback_model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=temperature,
                            max_tokens=max_tokens
                        )
                        
                        return response.choices[0].message.content
                    else:
                        raise RuntimeError("No fallback OpenAI API key available")
                        
                except Exception as openai_error:
                    last_error = openai_error
                    logger.error(f"Both Groq and OpenAI fallback failed on attempt {attempt + 1}: {openai_error}")
                    
                    # If this is not the last attempt, wait before retrying
                    if attempt < retries - 1:
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
        
        # If we get here, all retries failed
        raise RuntimeError(f"Text generation failed after {retries} attempts. Last error: {last_error}")
    
    def generate_json(
        self, 
        prompt: str, 
        schema: Dict[str, Any] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        model: str = None,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate structured JSON response using Weave inference
        
        Args:
            prompt: The input prompt
            schema: Expected JSON schema (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (defaults to self.model_name)
            
        Returns:
            Parsed JSON response
        """
        # Add JSON formatting instructions to prompt
        json_prompt = f"""
{prompt}

Please respond with valid JSON only. Do not include any explanation or markdown formatting.
{f"The response should follow this schema: {json.dumps(schema, indent=2)}" if schema else ""}
"""
        
        try:
            response_text = self.generate_text(
                json_prompt, 
                temperature=temperature,
                max_tokens=max_tokens,
                model=model
            )
            
            # Clean up response (remove markdown formatting if present)
            cleaned_response = response_text.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Parse JSON
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response was: {cleaned_response}")
                
                # Fallback: try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # If all else fails, return a basic structure
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": cleaned_response
                }
                
        except Exception as e:
            logger.error(f"JSON generation failed: {e}")
            return {
                "error": f"JSON generation failed: {str(e)}",
                "raw_response": ""
            }
    
    def analyze_policy(
        self, 
        policy_text: str, 
        analysis_type: str = "stakeholder_identification",
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Specialized policy analysis using Weave inference
        
        Args:
            policy_text: The policy text to analyze
            analysis_type: Type of analysis to perform
            context: Additional context for analysis
            
        Returns:
            Analysis results as structured data
        """
        context = context or {}
        
        if analysis_type == "stakeholder_identification":
            prompt = f"""
            Analyze the following policy text and identify ONLY the direct and main stakeholders who are immediately and significantly affected by this policy.
            
            STRICT CRITERIA - Include ONLY stakeholders who meet ALL of these requirements:
            1. DIRECT IMPACT: The policy directly requires them to take action, comply with requirements, or experience immediate changes
            2. MAIN ACTORS: They are primary parties mentioned in the policy or are the primary target/beneficiary
            3. SIGNIFICANT CONSEQUENCES: They face substantial financial, legal, operational, or personal impacts
            4. IMMEDIATE EFFECT: The policy affects them directly, not through secondary or indirect channels
            
            EXCLUDE:
            - Secondary stakeholders (affected only through others)
            - Indirect beneficiaries or those with minor impacts
            - General groups with tangential interests
            - Professional service providers unless directly regulated
            - Advocacy groups or organizations that aren't directly affected
            - Government agencies unless they are directly regulated (not just implementing)
            
            For each DIRECT and MAIN stakeholder, provide:
            1. Stakeholder name/type
            2. Their primary interests/concerns
            3. How they are DIRECTLY affected (positively or negatively)
            4. Their likely stance on the policy
            
            Policy Text:
            {policy_text}
            
            Return the analysis as JSON with the following structure:
            {{
                "stakeholders": [
                    {{
                        "name": "Stakeholder Name",
                        "type": "stakeholder_type",
                        "interests": ["interest1", "interest2"],
                        "direct_impact": "description of direct impact",
                        "stance": "supportive/opposed/neutral",
                        "concerns": ["concern1", "concern2"]
                    }}
                ]
            }}
            """
            
            schema = {
                "stakeholders": [
                    {
                        "name": "string",
                        "type": "string", 
                        "interests": ["string"],
                        "direct_impact": "string",
                        "stance": "string",
                        "concerns": ["string"]
                    }
                ]
            }
            
            return self.generate_json(prompt, schema=schema, temperature=0.3)
            
        elif analysis_type == "stakeholder_research":
            stakeholder_name = context.get("stakeholder_name", "Unknown")
            prompt = f"""
            Conduct detailed research on how the policy affects the stakeholder "{stakeholder_name}" from their specific perspective.
            
            Policy Text:
            {policy_text}
            
            Stakeholder: {stakeholder_name}
            
            Provide a comprehensive analysis including:
            1. Direct impacts on this stakeholder
            2. Financial implications
            3. Operational changes required
            4. Potential benefits and risks
            5. Recommended actions or responses
            6. Key concerns and priorities
            
            Return as JSON with this structure:
            {{
                "stakeholder_name": "{stakeholder_name}",
                "direct_impacts": ["impact1", "impact2"],
                "financial_implications": "description",
                "operational_changes": "description", 
                "benefits": ["benefit1", "benefit2"],
                "risks": ["risk1", "risk2"],
                "recommended_actions": ["action1", "action2"],
                "key_concerns": ["concern1", "concern2"],
                "confidence_level": "high/medium/low",
                "research_summary": "brief summary of findings"
            }}
            """
            
            return self.generate_json(prompt, temperature=0.3)
            
        elif analysis_type == "topic_analysis":
            stakeholder_list = context.get("stakeholder_list", [])
            prompt = f"""
            Analyze the policy text and stakeholder information to identify key debate topics and areas of contention.
            
            Policy Text:
            {policy_text}
            
            Stakeholders: {json.dumps(stakeholder_list, indent=2)}
            
            Identify the main debate topics that would emerge from discussions between these stakeholders.
            Focus on areas where stakeholders are likely to have different perspectives or conflicting interests.
            
            Return as JSON:
            {{
                "debate_topics": [
                    {{
                        "topic": "Topic Name",
                        "description": "Description of the topic",
                        "stakeholder_positions": {{
                            "stakeholder_name": "expected_position"
                        }},
                        "contention_level": "high/medium/low",
                        "key_questions": ["question1", "question2"]
                    }}
                ]
            }}
            """
            
            return self.generate_json(prompt, temperature=0.3)
            
        elif analysis_type == "argument_generation":
            stakeholder_name = context.get("stakeholder_name", "Unknown")
            topic = context.get("topic", "")
            argument_type = context.get("argument_type", "claim")
            
            prompt = f"""
            Generate a {argument_type} argument for stakeholder "{stakeholder_name}" on the topic: {topic}
            
            Policy Text:
            {policy_text}
            
            Stakeholder: {stakeholder_name}
            Topic: {topic}
            Argument Type: {argument_type}
            
            Generate a compelling argument that reflects this stakeholder's perspective, interests, and concerns.
            The argument should be well-reasoned, factual, and persuasive.
            
            Return as JSON:
            {{
                "stakeholder": "{stakeholder_name}",
                "topic": "{topic}",
                "argument_type": "{argument_type}",
                "argument": "The main argument text",
                "supporting_points": ["point1", "point2", "point3"],
                "evidence": ["evidence1", "evidence2"],
                "counterarguments": ["counter1", "counter2"],
                "strength": "high/medium/low"
            }}
            """
            
            return self.generate_json(prompt, temperature=0.5)
            
        elif analysis_type == "debate_moderation":
            session_context = context.get("session_context", {})
            prompt = f"""
            You are moderating a policy debate. Based on the current session state and context, provide moderation guidance.
            
            Policy Text:
            {policy_text}
            
            Session Context:
            {json.dumps(session_context, indent=2)}
            
            Provide moderation guidance including:
            1. Next steps in the debate
            2. Which stakeholder should speak next
            3. Any procedural notes
            4. Topic transitions if needed
            
            Return as JSON:
            {{
                "next_steps": "description of next steps",
                "next_speaker": "stakeholder name or null",
                "procedural_notes": "any procedural guidance",
                "topic_transition": "suggested topic transition or null",
                "moderation_message": "message to participants"
            }}
            """
            
            return self.generate_json(prompt, temperature=0.3)
            
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    def is_available(self) -> bool:
        """Check if Weave client is available and has API keys"""
        # Check if we have either Groq or OpenAI API keys
        groq_key = os.getenv('GROQ_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if groq_key or openai_key:
            return True
        else:
            return False


# Global instance
_weave_client = None


def get_weave_client() -> WeaveClient:
    """
    Get the global Weave client instance
    
    Returns:
        WeaveClient instance
    """
    global _weave_client
    if _weave_client is None:
        _weave_client = WeaveClient()
    return _weave_client


def initialize_weave_client(project_name: str = "civicai-policy-debate") -> WeaveClient:
    """
    Initialize the global Weave client
    
    Args:
        project_name: Name of the Weave project
        
    Returns:
        WeaveClient instance
    """
    global _weave_client
    _weave_client = WeaveClient(project_name=project_name)
    return _weave_client 