"""
A2A Protocol Integration for CivicAI Agent Communication

This module provides Agent-to-Agent (A2A) protocol support for standardized
communication between agents in the CivicAI multi-agent system.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from a2a_sdk import A2AServer, A2AMessage, A2AAgent
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False
    # Define mock classes for development when A2A SDK is not available
    class A2AServer:
        def __init__(self, *args, **kwargs):
            pass
    
    class A2AMessage:
        def __init__(self, *args, **kwargs):
            pass
    
    class A2AAgent:
        def __init__(self, *args, **kwargs):
            pass

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    """Standardized message format for agent communication"""
    agent_id: str
    agent_type: str
    content: str
    message_type: str
    timestamp: str
    session_id: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentInfo:
    """Information about an agent in the system"""
    agent_id: str
    agent_type: str
    role: str
    capabilities: List[str]
    status: str
    created_at: str


class CivicAIA2AAgent:
    """
    CivicAI Agent wrapper that implements A2A protocol for standardized communication
    """
    
    def __init__(self, agent_id: str, agent_type: str, role: str, capabilities: List[str] = None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.role = role
        self.capabilities = capabilities or []
        self.status = "active"
        self.created_at = datetime.now().isoformat()
        self.message_handlers: Dict[str, Callable] = {}
        self.websocket_connections: List[WebSocket] = []
        
        # Initialize A2A agent if available
        if A2A_AVAILABLE:
            try:
                self.a2a_agent = A2AAgent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    capabilities=capabilities
                )
                logger.info(f"✅ A2A agent initialized for {agent_id}")
            except Exception as e:
                logger.error(f"⚠️ Failed to initialize A2A agent for {agent_id}: {e}")
                self.a2a_agent = None
        else:
            self.a2a_agent = None
            logger.warning(f"⚠️ A2A SDK not available, using fallback communication for {agent_id}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register a handler for specific message types"""
        self.message_handlers[message_type] = handler
    
    def add_websocket(self, websocket: WebSocket):
        """Add WebSocket connection for real-time communication"""
        self.websocket_connections.append(websocket)
    
    def remove_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
    
    async def send_message(self, recipient_id: str, content: str, message_type: str = "general", 
                          session_id: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Send message to another agent using A2A protocol"""
        message = AgentMessage(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            content=content,
            message_type=message_type,
            timestamp=datetime.now().isoformat(),
            session_id=session_id or "default",
            metadata=metadata or {}
        )
        
        success = False
        
        # Try A2A protocol first
        if self.a2a_agent:
            try:
                a2a_message = A2AMessage(
                    sender_id=self.agent_id,
                    recipient_id=recipient_id,
                    content=json.dumps(message.to_dict()),
                    message_type=message_type
                )
                await self.a2a_agent.send_message(a2a_message)
                success = True
                logger.info(f"📨 A2A message sent from {self.agent_id} to {recipient_id}")
            except Exception as e:
                logger.error(f"❌ A2A message failed from {self.agent_id} to {recipient_id}: {e}")
        
        # Fallback to WebSocket broadcast
        if not success:
            await self._broadcast_via_websocket(message)
            success = True
        
        return success
    
    async def receive_message(self, message: Dict[str, Any]) -> bool:
        """Process incoming message from another agent"""
        try:
            agent_message = AgentMessage(**message)
            
            # Find appropriate handler
            handler = self.message_handlers.get(agent_message.message_type)
            if handler:
                await handler(agent_message)
            else:
                # Default handler - just log
                logger.info(f"📥 {self.agent_id} received {agent_message.message_type} from {agent_message.agent_id}: {agent_message.content}")
            
            # Broadcast to WebSocket connections
            await self._broadcast_via_websocket(agent_message)
            
            return True
        except Exception as e:
            logger.error(f"❌ Error processing message in {self.agent_id}: {e}")
            return False
    
    async def _broadcast_via_websocket(self, message: AgentMessage):
        """Broadcast message to all connected WebSockets"""
        if not self.websocket_connections:
            return
        
        message_data = {
            "type": "agent_message",
            "data": message.to_dict()
        }
        
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(json.dumps(message_data))
            except Exception as e:
                logger.error(f"❌ WebSocket send failed: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for ws in disconnected:
            self.remove_websocket(ws)
    
    def get_info(self) -> AgentInfo:
        """Get agent information"""
        return AgentInfo(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            role=self.role,
            capabilities=self.capabilities,
            status=self.status,
            created_at=self.created_at
        )


class A2ACoordinator:
    """
    Coordinates A2A communication between multiple agents in a debate session
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.agents: Dict[str, CivicAIA2AAgent] = {}
        self.message_history: List[AgentMessage] = []
        self.websocket_connections: List[WebSocket] = []
        
        # Initialize A2A server if available
        if A2A_AVAILABLE:
            try:
                self.a2a_server = A2AServer(
                    server_id=f"civicai_session_{session_id}",
                    port=8001  # Use different port from main API
                )
                logger.info(f"✅ A2A server initialized for session {session_id}")
            except Exception as e:
                logger.error(f"⚠️ Failed to initialize A2A server for session {session_id}: {e}")
                self.a2a_server = None
        else:
            self.a2a_server = None
    
    def register_agent(self, agent: CivicAIA2AAgent):
        """Register an agent in this coordination session"""
        self.agents[agent.agent_id] = agent
        logger.info(f"🤖 Registered agent {agent.agent_id} ({agent.agent_type}) in session {self.session_id}")
    
    def unregister_agent(self, agent_id: str):
        """Unregister an agent from this session"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"🚫 Unregistered agent {agent_id} from session {self.session_id}")
    
    async def broadcast_message(self, sender_id: str, content: str, message_type: str = "broadcast", 
                              metadata: Dict[str, Any] = None):
        """Broadcast message from one agent to all others in the session"""
        if sender_id not in self.agents:
            logger.error(f"❌ Sender {sender_id} not found in session {self.session_id}")
            return False
        
        sender = self.agents[sender_id]
        success_count = 0
        
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:  # Don't send to self
                success = await sender.send_message(
                    recipient_id=agent_id,
                    content=content,
                    message_type=message_type,
                    session_id=self.session_id,
                    metadata=metadata
                )
                if success:
                    success_count += 1
        
        logger.info(f"📡 Broadcast from {sender_id} delivered to {success_count}/{len(self.agents)-1} agents")
        return success_count > 0
    
    async def send_direct_message(self, sender_id: str, recipient_id: str, content: str, 
                                 message_type: str = "direct", metadata: Dict[str, Any] = None):
        """Send direct message between two specific agents"""
        if sender_id not in self.agents:
            logger.error(f"❌ Sender {sender_id} not found in session {self.session_id}")
            return False
        
        if recipient_id not in self.agents:
            logger.error(f"❌ Recipient {recipient_id} not found in session {self.session_id}")
            return False
        
        sender = self.agents[sender_id]
        return await sender.send_message(
            recipient_id=recipient_id,
            content=content,
            message_type=message_type,
            session_id=self.session_id,
            metadata=metadata
        )
    
    def add_websocket(self, websocket: WebSocket):
        """Add WebSocket connection to receive all session communications"""
        self.websocket_connections.append(websocket)
        # Also add to all agents
        for agent in self.agents.values():
            agent.add_websocket(websocket)
    
    def remove_websocket(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        # Also remove from all agents
        for agent in self.agents.values():
            agent.remove_websocket(websocket)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session"""
        return {
            "session_id": self.session_id,
            "agent_count": len(self.agents),
            "agents": [agent.get_info() for agent in self.agents.values()],
            "message_count": len(self.message_history),
            "a2a_enabled": A2A_AVAILABLE and self.a2a_server is not None
        }
    
    async def facilitate_debate_round(self, round_number: int, topic: str, 
                                    moderator_id: str = None) -> List[AgentMessage]:
        """Facilitate a structured debate round using A2A protocol"""
        round_messages = []
        
        # Announce round start
        announcement = f"🎯 Debate Round {round_number}: {topic}"
        await self.broadcast_message(
            sender_id=moderator_id or "system",
            content=announcement,
            message_type="round_start",
            metadata={"round_number": round_number, "topic": topic}
        )
        
        # Allow each agent to speak in order
        for agent_id, agent in self.agents.items():
            if agent_id == moderator_id:
                continue  # Skip moderator
            
            # Signal agent to speak
            speak_message = f"🎤 {agent_id}, please present your position on: {topic}"
            await self.send_direct_message(
                sender_id=moderator_id or "system",
                recipient_id=agent_id,
                content=speak_message,
                message_type="speak_turn",
                metadata={"round_number": round_number, "topic": topic}
            )
            
            # Wait for response (in real implementation, this would be handled by agent responses)
            await asyncio.sleep(1)  # Simulate thinking time
        
        # Announce round end
        await self.broadcast_message(
            sender_id=moderator_id or "system",
            content=f"✅ Round {round_number} completed",
            message_type="round_end",
            metadata={"round_number": round_number}
        )
        
        return round_messages


# Global coordinator registry for managing multiple sessions
_coordinators: Dict[str, A2ACoordinator] = {}


def get_coordinator(session_id: str) -> A2ACoordinator:
    """Get or create A2A coordinator for a session"""
    if session_id not in _coordinators:
        _coordinators[session_id] = A2ACoordinator(session_id)
    return _coordinators[session_id]


def cleanup_coordinator(session_id: str):
    """Clean up coordinator for a completed session"""
    if session_id in _coordinators:
        del _coordinators[session_id]
        logger.info(f"🧹 Cleaned up A2A coordinator for session {session_id}")


def is_a2a_available() -> bool:
    """Check if A2A SDK is available"""
    return A2A_AVAILABLE