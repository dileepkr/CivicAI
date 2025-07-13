"""
Dynamic Crew Policy Debate Systems

This module provides various debate systems for policy analysis:
- DebugDebateSystem: Real-time debug system with live agent interactions
- WeaveDebateSystem: Full Weave integration with comprehensive tracing
- HumanDebateSystem: Human-like conversational system with personas and moderator

All systems share common components for stakeholder identification,
topic analysis, and structured debate facilitation.
"""

from .systems.debug import DebugDebateSystem
from .systems.weave import WeaveDebateSystem
from .systems.human import HumanDebateSystem
from .moderator import HumanModerator
from .personas import HumanPersona
from .base import BaseDebateSystem

__all__ = [
    'DebugDebateSystem',
    'WeaveDebateSystem', 
    'HumanDebateSystem',
    'HumanModerator',
    'HumanPersona',
    'BaseDebateSystem'
]

__version__ = '1.0.0' 