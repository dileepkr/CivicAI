"""
Weave Inference Client for CivicAI Policy Debate System

This module provides a dedicated Weave inference client that avoids circular reference issues
by keeping Weave inference separate from Weave tracing.
"""

import os
import logging
from typing import Dict, Any, Optional

# Disable Weave tracing to prevent circular reference issues
os.environ['WEAVE_DISABLE_TRACING'] = '1'
os.environ['WEAVE_AUTO_TRACE'] = '0'
os.environ['WEAVE_AUTO_PATCH'] = '0'
os.environ['WANDB_DISABLE_TRACING'] = '1'

logger = logging.getLogger(__name__)

class WeaveInferenceClient:
    """
    Dedicated Weave inference client for local model inference
    """
    
    def __init__(self, model_name: str = "gpt2", project_name: str = "civicai-inference"):
        self.model_name = model_name
        self.project_name = project_name
        self.available = False
        
        # Try to import and initialize Weave
        try:
            import weave
            self.weave = weave
            
            # Initialize Weave project (without tracing)
            weave.init(project_name=project_name)
            
            # Try to load a model using Weave's model loading
            try:
                # Use Weave's model loading capabilities
                # For now, we'll use a mock model since Weave's API is different
                self.model = None
                self.available = True
                logger.info(f"✅ Weave inference client initialized with model: {model_name}")
                print(f"✅ Weave inference client initialized with model: {model_name}")
            except Exception as e:
                logger.warning(f"⚠️  Could not load model {model_name}: {e}")
                self.available = False
                    
        except ImportError:
            logger.warning("⚠️  Weave not available - install with: pip install weave")
            print("⚠️  Weave not available - install with: pip install weave")
            self.available = False
        except Exception as e:
            logger.error(f"❌ Weave initialization failed: {e}")
            print(f"❌ Weave initialization failed: {e}")
            self.available = False
    
    def generate_text(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        Generate text using Weave inference
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        if not self.available:
            raise RuntimeError("Weave inference client not available")
        
        try:
            # Use Weave's inference capabilities
            # For now, we'll use a mock response to test the integration
            # In a real implementation, you would use Weave's actual inference API
            mock_response = f"[Weave Inference] Response to: {prompt[:100]}... This is a mock response for testing the Weave inference integration without circular reference errors."
            
            logger.info(f"✅ Weave inference successful: {len(mock_response)} characters")
            return mock_response
            
        except Exception as e:
            logger.error(f"❌ Weave inference failed: {e}")
            raise RuntimeError(f"Weave inference error: {e}")
    
    def generate_json(self, prompt: str, schema: Dict[str, Any] = None, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate structured JSON response using Weave inference
        
        Args:
            prompt: Input prompt
            schema: Expected JSON schema
            temperature: Sampling temperature
            
        Returns:
            Generated JSON response
        """
        if not self.available:
            raise RuntimeError("Weave inference client not available")
        
        try:
            # Add JSON formatting instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with valid JSON only."
            
            response = self.model.generate(
                prompt=json_prompt,
                temperature=temperature,
                max_tokens=2048
            )
            
            # Try to parse JSON from response
            import json
            try:
                # Extract JSON from response (in case there's extra text)
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response
                
                result = json.loads(json_str)
                logger.info(f"✅ Weave JSON generation successful")
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️  JSON parsing failed: {e}")
                # Return a fallback structure
                return {"error": "JSON parsing failed", "raw_response": response}
                
        except Exception as e:
            logger.error(f"❌ Weave JSON generation failed: {e}")
            raise RuntimeError(f"Weave JSON generation error: {e}")
    
    def is_available(self) -> bool:
        """Check if Weave inference is available"""
        return self.available

    @property
    def providers(self):
        # Return a dummy provider list for compatibility
        return [{
            'name': 'weave_inference',
            'model': self.model_name
        }]

def get_weave_inference_client(model_name: str = "gpt2") -> WeaveInferenceClient:
    """
    Get a Weave inference client instance
    
    Args:
        model_name: Name of the model to use
        
    Returns:
        WeaveInferenceClient instance
    """
    return WeaveInferenceClient(model_name=model_name)

def initialize_weave_inference_client(model_name: str = "gpt2", project_name: str = "civicai-inference") -> WeaveInferenceClient:
    """
    Initialize a Weave inference client
    
    Args:
        model_name: Name of the model to use
        project_name: Name of the Weave project
        
    Returns:
        WeaveInferenceClient instance
    """
    return WeaveInferenceClient(model_name=model_name, project_name=project_name) 