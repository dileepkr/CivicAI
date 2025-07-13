"""
Configuration settings for CivicAI Policy Debate System

This module handles configuration for Weave integration, Pydantic settings,
and other system-wide configurations to prevent deprecation warnings and errors.
"""

import os
import warnings
from typing import Dict, Any

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weave")

# Environment variables for Weave configuration
WEAVE_CONFIG = {
    "project_name": os.getenv("WANDB_PROJECT", "civicai-policy-debate"),
    "api_key": os.getenv("WNB_API_KEY"),
    "model_name": os.getenv("WEAVE_MODEL_NAME", "openai/meta-llama/Llama-4-Scout-17B-16E-Instruct"),
    "api_base": "https://api.inference.wandb.ai/v1",
    "disable_tracing": os.getenv("WEAVE_DISABLE_TRACING", "0") == "1",
}

# CrewAI configuration
CREWAI_CONFIG = {
    "verbose": True,
    "process": "hierarchical",
    "allow_delegation": False,
    "max_iterations": 3,
    "max_rpm": 10,
}

# Policy discovery configuration
POLICY_DISCOVERY_CONFIG = {
    "max_results": 20,
    "search_timeout": 30,
    "confidence_threshold": 0.7,
    "domains": ["housing", "employment", "environment", "healthcare", "education"],
    "government_levels": ["federal", "state", "local"],
}

# Debate system configuration
DEBATE_CONFIG = {
    "max_rounds": 5,
    "timeout_per_round": 60,
    "stakeholder_limit": 6,
    "debate_styles": ["structured", "free_form", "moderated"],
}

# API configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "cors_origins": ["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    "request_size_limit": 10 * 1024 * 1024,  # 10MB
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": ["console"],
}

def get_weave_headers() -> Dict[str, str]:
    """Get Weave API headers"""
    return {
        "OpenAI-Project": f"crewai/{WEAVE_CONFIG['project_name']}",
        "User-Agent": "CivicAI-PolicyDebate/1.0"
    }

def is_weave_available() -> bool:
    """Check if Weave is available and properly configured"""
    try:
        import weave
        return WEAVE_CONFIG["api_key"] is not None
    except ImportError:
        return False

def get_fallback_llm_config() -> Dict[str, Any]:
    """Get fallback LLM configuration"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return {
            "model": "gpt-3.5-turbo",
            "api_key": openai_key,
            "provider": "openai"
        }
    else:
        return {
            "model": "gpt-3.5-turbo",
            "api_key": None,
            "provider": "none"
        } 