"""
Debate System Implementations

This module contains the various debate system implementations:
- DebugDebateSystem: Real-time debug version with live agent actions
- WeaveDebateSystem: Full Weave integration with comprehensive tracing
- HumanDebateSystem: Human-like conversational system with personas
"""

from .debug import DebugDebateSystem
from .weave import WeaveDebateSystem
from .human import HumanDebateSystem

__all__ = [
    'DebugDebateSystem',
    'WeaveDebateSystem',
    'HumanDebateSystem'
] 