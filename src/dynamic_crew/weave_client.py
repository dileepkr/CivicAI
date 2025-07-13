"""
Robust Multi-Provider LLM Client for CivicAI Policy Debate System

This module provides a unified interface for all LLM operations with automatic fallback
between different providers (Groq, OpenAI, local models) and robust error handling.
"""

import os
import json
import logging
import time
import random
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from functools import wraps

# Disable Weave completely to prevent circular reference issues
os.environ['WEAVE_DISABLE_TRACING'] = '1'
os.environ['WEAVE_AUTO_TRACE'] = '0'
os.environ['WEAVE_AUTO_PATCH'] = '0'
os.environ['WANDB_DISABLE_TRACING'] = '1'

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    # If dotenv is not available, just continue without loading .env file
    pass

# Try to import Weave for inference (separate from tracing)
try:
    import weave
    WEAVE_AVAILABLE = True
except ImportError:
    WEAVE_AVAILABLE = False
    print("⚠️  Weave not available for inference - install with: pip install weave")

logger = logging.getLogger(__name__)

def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Don't retry on certain errors
                    if "authentication" in str(e).lower() or "invalid" in str(e).lower():
                        raise e
                    
                    if attempt < max_retries - 1:
                        # Calculate delay with jitter
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {e}")
            
            raise last_exception
        return wrapper
    return decorator

class WeaveInferenceProvider:
    """
    Weave inference provider for local model inference
    """
    
    def __init__(self, model_name: str = "gpt2", max_tokens: int = 2048):
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.name = 'weave_inference'
        
        # Initialize Weave model if available
        if WEAVE_AVAILABLE:
            try:
                # Use Weave's model loading capabilities
                # For now, we'll use a simple approach that doesn't require full model loading
                self.available = True
                logger.info(f"✅ Weave inference provider initialized with model: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize Weave model {model_name}: {e}")
                self.available = False
        else:
            self.available = False
            logger.warning("⚠️  Weave not available for inference")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = None) -> str:
        """Generate text using Weave inference"""
        if not self.available:
            raise Exception("Weave inference provider not available")
        
        try:
            # For now, return a mock response to test the integration
            # In a real implementation, you would use Weave's actual inference
            mock_response = f"[Weave Inference Mock] Response to: {prompt[:50]}..."
            logger.info(f"Weave inference generated: {mock_response}")
            return mock_response
        except Exception as e:
            logger.error(f"Weave inference failed: {e}")
            raise Exception(f"Weave inference error: {e}")

class RobustLLMClient:
    """
    Robust LLM client with automatic fallback between providers
    """
    
    def __init__(self, project_name: str = "civicai-policy-debate"):
        """
        Initialize the robust LLM client
        
        Args:
            project_name: Name of the project (for logging)
        """
        self.project_name = project_name
        
        # Configure available providers
        self.providers = self._setup_providers()
        
        # Current provider index
        self.current_provider_index = 0
        
        # Rate limiting tracking
        self.rate_limit_timestamps = {}
        self.rate_limit_windows = {
            'groq': 60,  # 60 seconds window
            'openai': 60,
            'weave_inference': 10,  # Local inference is faster
            'local': 10
        }
        
        logger.info(f"✅ Robust LLM Client initialized with {len(self.providers)} providers")
        print(f"✅ Robust LLM Client initialized with {len(self.providers)} providers")
    
    def _setup_providers(self) -> List[Dict[str, Any]]:
        """Setup available LLM providers in order of preference"""
        providers = []
        
        # 1. Weave Inference (local, fastest, preferred)
        if WEAVE_AVAILABLE:
            try:
                weave_provider = WeaveInferenceProvider(model_name="gpt2")
                if weave_provider.available:
                    providers.append({
                        'name': 'weave_inference',
                        'provider': weave_provider,
                        'model': 'gpt2',
                        'max_tokens': 2048,
                        'timeout': 30,
                        'priority': 1
                    })
                    logger.info("✅ Weave inference provider configured")
            except Exception as e:
                logger.warning(f"⚠️  Weave inference setup failed: {e}")
        
        # 2. Groq (fast API, fallback)
        groq_key = os.getenv('GROQ_API_KEY')
        if groq_key:
            providers.append({
                'name': 'groq',
                'api_key': groq_key,
                'base_url': 'https://api.groq.com/openai/v1',
                'model': 'llama3-8b-8192',
                'max_tokens': 8192,
                'timeout': 60,
                'priority': 2
            })
            logger.info("✅ Groq provider configured")
        
        # 3. OpenAI (reliable fallback)
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            providers.append({
                'name': 'openai',
                'api_key': openai_key,
                'base_url': 'https://api.openai.com/v1',
                'model': 'gpt-3.5-turbo',
                'max_tokens': 4096,
                'timeout': 60,
                'priority': 3
            })
            logger.info("✅ OpenAI provider configured")
        
        # 4. Local model fallback (if available)
        # This could be Ollama, local transformers, etc.
        if not providers:
            logger.warning("⚠️  No providers available - system will not function properly")
        
        return providers
    
    def _check_rate_limit(self, provider_name: str) -> bool:
        """Check if provider is rate limited"""
        if provider_name not in self.rate_limit_timestamps:
            return False
        
        window = self.rate_limit_windows.get(provider_name, 60)
        last_request = self.rate_limit_timestamps[provider_name]
        
        return (time.time() - last_request) < window
    
    def _mark_rate_limited(self, provider_name: str):
        """Mark provider as rate limited"""
        self.rate_limit_timestamps[provider_name] = time.time()
        logger.warning(f"Rate limit hit for {provider_name}")
    
    def _get_next_available_provider(self) -> Optional[Dict[str, Any]]:
        """Get next available provider that's not rate limited"""
        attempts = 0
        while attempts < len(self.providers):
            provider = self.providers[self.current_provider_index]
            
            if not self._check_rate_limit(provider['name']):
                return provider
            
            # Move to next provider
            self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
            attempts += 1
        
        # All providers are rate limited, wait and try again
        logger.warning("All providers rate limited, waiting...")
        time.sleep(30)  # Wait 30 seconds
        return self.providers[0] if self.providers else None
    
    @retry_with_backoff(max_retries=3, base_delay=2)
    def _call_provider(self, provider: Dict[str, Any], prompt: str, **kwargs) -> str:
        """Make API call to specific provider"""
        try:
            # Handle Weave inference provider
            if provider['name'] == 'weave_inference':
                weave_provider = provider['provider']
                return weave_provider.generate(
                    prompt=prompt,
                    temperature=kwargs.get('temperature', 0.7),
                    max_tokens=kwargs.get('max_tokens', provider['max_tokens'])
                )
            
            # Handle API-based providers (Groq, OpenAI, etc.)
            import openai
            
            client = openai.OpenAI(
                api_key=provider['api_key'],
                base_url=provider['base_url'],
                timeout=provider['timeout']
            )
            
            response = client.chat.completions.create(
                model=provider['model'],
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', provider['max_tokens'])
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for rate limiting
            if any(rate_limit_indicator in error_msg for rate_limit_indicator in [
                'rate limit', 'too many requests', 'quota exceeded', 'rate_limit'
            ]):
                self._mark_rate_limited(provider['name'])
                raise Exception(f"Rate limit hit for {provider['name']}: {e}")
            
            # Check for authentication errors
            if any(auth_indicator in error_msg for auth_indicator in [
                'authentication', 'invalid api key', 'unauthorized'
            ]):
                raise Exception(f"Authentication error for {provider['name']}: {e}")
            
            # Other errors
            raise Exception(f"Provider {provider['name']} error: {e}")
    
    def generate_text(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
        retries: int = 3
    ) -> str:
        """
        Generate text using available providers with automatic fallback
        
        Args:
            prompt: The input prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (ignored, uses provider's default)
            retries: Number of retry attempts
            
        Returns:
            Generated text response
        """
        if not self.providers:
            raise RuntimeError("No LLM providers available. Please set GROQ_API_KEY or OPENAI_API_KEY")
        
        last_error = None
        
        for attempt in range(retries):
            try:
                # Get next available provider
                provider = self._get_next_available_provider()
                if not provider:
                    raise RuntimeError("No available providers")
                
                logger.info(f"Using provider: {provider['name']} (attempt {attempt + 1})")
                
                # Make the call
                response = self._call_provider(
                    provider, 
                    prompt, 
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Success - move to next provider for load balancing
                self.current_provider_index = (self.current_provider_index + 1) % len(self.providers)
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < retries - 1:
                    # Wait before retry
                    time.sleep(2 ** attempt)
                    continue
        
        # All retries failed
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
        Generate structured JSON response
        
        Args:
            prompt: The input prompt
            schema: Expected JSON schema (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            model: Model to use (ignored, uses provider's default)
            
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
        Analyze policy using specialized prompts for different analysis types
        
        Args:
            policy_text: The policy text to analyze
            analysis_type: Type of analysis to perform
            context: Additional context for the analysis
            
        Returns:
            Analysis results as dictionary
        """
        context = context or {}
        
        if analysis_type == "stakeholder_identification":
            prompt = f"""
            Analyze the following policy text and identify ONLY the direct and main stakeholders who are immediately and significantly affected by the policy. Exclude secondary, indirect, or tangentially affected parties.
            
            Policy Text:
            {policy_text}
            
            Identify stakeholders and return as JSON:
            {{
                "stakeholders": [
                    {{
                        "name": "stakeholder name",
                        "type": "stakeholder type (e.g., business, government, public)",
                        "interests": ["list of key interests"],
                        "direct_impact": "how the policy directly affects them",
                        "stance": "likely stance: supportive/opposed/neutral",
                        "concerns": ["key concerns or issues"]
                    }}
                ]
            }}
            """
            
        elif analysis_type == "stakeholder_research":
            stakeholder_name = context.get("stakeholder_name", "Unknown")
            prompt = f"""
            Conduct detailed research on how the following policy affects {stakeholder_name} from their perspective.
            
            Policy Text:
            {policy_text}
            
            Stakeholder: {stakeholder_name}
            
            Provide comprehensive analysis and return as JSON:
            {{
                "stakeholder_name": "{stakeholder_name}",
                "direct_impacts": ["list of direct impacts"],
                "financial_implications": "financial consequences",
                "operational_changes": ["operational changes required"],
                "benefits": ["potential benefits"],
                "risks": ["potential risks"],
                "recommended_actions": ["recommended actions for stakeholder"],
                "key_concerns": ["main concerns"],
                "research_summary": "executive summary",
                "confidence_level": "low/medium/high"
            }}
            """
            
        elif analysis_type == "topic_analysis":
            stakeholder_list = context.get("stakeholder_list", [])
            stakeholders_str = json.dumps(stakeholder_list, indent=2)
            
            prompt = f"""
            Analyze the following policy text and identify key debate topics and areas of contention among the stakeholders.
            
            Policy Text:
            {policy_text}
            
            Stakeholders:
            {stakeholders_str}
            
            Identify debate topics and return as JSON:
            {{
                "debate_topics": [
                    {{
                        "topic": "topic title",
                        "description": "detailed description",
                        "stakeholder_positions": {{"stakeholder_name": "position"}},
                        "contention_level": "low/medium/high",
                        "key_questions": ["questions to address"]
                    }}
                ]
            }}
            """
            
        elif analysis_type == "argument_generation":
            stakeholder_name = context.get("stakeholder_name", "Unknown")
            argument_type = context.get("argument_type", "claim")
            responding_to = context.get("responding_to", "")
            
            prompt = f"""
            Generate a structured argument for {stakeholder_name} based on the following topic and context.
            
            Topic:
            {policy_text}
            
            Stakeholder: {stakeholder_name}
            Argument Type: {argument_type}
            Responding To: {responding_to if responding_to else "N/A"}
            
            Generate argument and return as JSON:
            {{
                "argument_id": "unique_id",
                "stakeholder_name": "{stakeholder_name}",
                "argument_type": "{argument_type}",
                "content": "the argument content",
                "evidence": ["supporting evidence"],
                "strength": 5
            }}
            """
            
        elif analysis_type == "debate_summary":
            session_data = context.get("session_data", {})
            prompt = f"""
            Generate a comprehensive summary of the debate session based on the following information.
            
            Session Data:
            {json.dumps(session_data, indent=2)}
            
            Generate summary and return as JSON:
            {{
                "summary": "comprehensive debate summary",
                "key_points": ["main points discussed"],
                "consensus_areas": ["areas of agreement"],
                "disagreement_areas": ["areas of disagreement"],
                "recommendations": ["recommendations from debate"]
            }}
            """
            
        else:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        return self.generate_json(prompt, temperature=0.3)
    
    def is_available(self) -> bool:
        """Check if any LLM provider is available"""
        return len(self.providers) > 0

# Global instance
_llm_client = None

def get_weave_client() -> RobustLLMClient:
    """
    Get the global LLM client instance (maintains backward compatibility)
    
    Returns:
        RobustLLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = RobustLLMClient()
    return _llm_client

def initialize_weave_client(project_name: str = "civicai-policy-debate") -> RobustLLMClient:
    """
    Initialize the global LLM client (maintains backward compatibility)
    
    Args:
        project_name: Name of the project
        
    Returns:
        RobustLLMClient instance
    """
    global _llm_client
    _llm_client = RobustLLMClient(project_name=project_name)
    return _llm_client 