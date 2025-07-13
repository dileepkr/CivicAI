"""
FastAPI backend for CivicAI Policy Debate System

This backend exposes the agentic debate systems as web APIs for the React UI.
It provides endpoints for:
- Loading policy data
- Running debates with real-time streaming
- Managing debate sessions
- Generating emails based on real debate data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import json
import uuid
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate.systems.debug import DebugDebateSystem
from src.dynamic_crew.debate.systems.weave import WeaveDebateSystem
from src.dynamic_crew.debate.systems.human import HumanDebateSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CivicAI Policy Debate API",
    description="Backend API for the CivicAI Policy Debate System",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global debate session manager
class DebateSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    def create_session(self, session_id: str, system_type: str) -> Dict[str, Any]:
        """Create a new debate session"""
        session_data = {
            "session_id": session_id,
            "system_type": system_type,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "debate_system": None,
            "policy_data": None,
            "stakeholders": [],
            "messages": [],
            "current_round": 0
        }
        self.active_sessions[session_id] = session_data
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return self.active_sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]):
        """Update session data"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update(updates)
    
    def add_websocket(self, session_id: str, websocket: WebSocket):
        """Add WebSocket connection for session"""
        self.websocket_connections[session_id] = websocket
    
    def remove_websocket(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast message to session WebSocket"""
        if session_id in self.websocket_connections:
            try:
                await self.websocket_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                self.remove_websocket(session_id)

# Initialize session manager
session_manager = DebateSessionManager()

# Pydantic models
class PolicyResponse(BaseModel):
    id: str
    title: str
    date: str
    summary: str
    relevance: str
    text: str

class StartDebateRequest(BaseModel):
    policy_name: str
    system_type: str  # "debug", "weave", or "human"

class DebateMessage(BaseModel):
    id: str
    sender: str
    content: str
    timestamp: str
    message_type: str = "message"
    metadata: Dict[str, Any] = {}

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "CivicAI Policy Debate API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/policies", response_model=List[PolicyResponse])
async def get_policies():
    """Get all available policies"""
    policies = []
    test_data_dir = project_root / "test_data"
    
    try:
        for policy_file in test_data_dir.glob("*.json"):
            try:
                with open(policy_file, 'r') as f:
                    policy_data = json.load(f)
                
                # Extract policy information
                policy_id = policy_file.stem
                title = policy_data.get('title', 'Unknown Policy')
                date = policy_data.get('date', datetime.now().strftime('%Y-%m-%d'))
                summary = policy_data.get('summary', 'No summary available')
                text = policy_data.get('text', '')
                
                # Simple relevance scoring (can be enhanced)
                relevance = "high" if len(text) > 1000 else "medium"
                
                policies.append(PolicyResponse(
                    id=policy_id,
                    title=title,
                    date=date,
                    summary=summary,
                    relevance=relevance,
                    text=text
                ))
            except Exception as e:
                logger.error(f"Error loading policy {policy_file}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error reading policies directory: {e}")
        raise HTTPException(status_code=500, detail="Error loading policies")
    
    return policies

@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str):
    """Get a specific policy by ID"""
    policy_file = project_root / "test_data" / f"{policy_id}.json"
    
    if not policy_file.exists():
        raise HTTPException(status_code=404, detail="Policy not found")
    
    try:
        with open(policy_file, 'r') as f:
            policy_data = json.load(f)
        
        return PolicyResponse(
            id=policy_id,
            title=policy_data.get('title', 'Unknown Policy'),
            date=policy_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            summary=policy_data.get('summary', 'No summary available'),
            relevance="high",  # Default relevance
            text=policy_data.get('text', '')
        )
    except Exception as e:
        logger.error(f"Error loading policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail="Error loading policy")

@app.post("/debates/start")
async def start_debate(request: StartDebateRequest):
    """Start a new debate session"""
    session_id = f"debate_{uuid.uuid4().hex[:8]}"
    
    # Validate system type
    if request.system_type not in ["debug", "weave", "human"]:
        raise HTTPException(status_code=400, detail="Invalid system type")
    
    # Validate policy exists
    policy_file = project_root / "test_data" / f"{request.policy_name}.json"
    if not policy_file.exists():
        raise HTTPException(status_code=404, detail="Policy not found")
    
    try:
        # Create session
        session_data = session_manager.create_session(session_id, request.system_type)
        
        # Initialize debate system
        if request.system_type == "debug":
            debate_system = DebugDebateSystem()
        elif request.system_type == "weave":
            debate_system = WeaveDebateSystem()
        else:  # human
            debate_system = HumanDebateSystem()
        
        # Store in session
        session_manager.update_session(session_id, {
            "debate_system": debate_system,
            "policy_name": request.policy_name,
            "status": "initialized"
        })
        
        return {
            "session_id": session_id,
            "status": "initialized",
            "policy_name": request.policy_name,
            "system_type": request.system_type
        }
        
    except Exception as e:
        logger.error(f"Error starting debate: {e}")
        raise HTTPException(status_code=500, detail="Error starting debate")

@app.get("/debates/{session_id}/status")
async def get_debate_status(session_id: str):
    """Get debate session status"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.get("status", "unknown"),
        "current_round": session.get("current_round", 0),
        "message_count": len(session.get("messages", [])),
        "stakeholder_count": len(session.get("stakeholders", [])),
        "system_type": session.get("system_type", "unknown")
    }

@app.get("/debates/{session_id}/messages")
async def get_debate_messages(session_id: str):
    """Get all messages from a debate session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": session.get("messages", []),
        "total_count": len(session.get("messages", []))
    }

@app.websocket("/debates/{session_id}/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time debate streaming"""
    await websocket.accept()
    
    try:
        # Add WebSocket to session manager
        session_manager.add_websocket(session_id, websocket)
        
        # Send initial connection message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        session = session_manager.get_session(session_id)
        if not session:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Session not found"
            }))
            return
        
        # Start the debate in the background
        asyncio.create_task(run_debate_with_streaming(session_id, session))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "user_message":
                    await handle_user_message(session_id, message)
                elif message.get("type") == "pause_debate":
                    await handle_pause_debate(session_id)
                elif message.get("type") == "resume_debate":
                    await handle_resume_debate(session_id)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        session_manager.remove_websocket(session_id)

async def run_debate_with_streaming(session_id: str, session: Dict[str, Any]):
    """Run debate with real-time streaming to WebSocket"""
    try:
        debate_system = session["debate_system"]
        policy_name = session["policy_name"]
        
        # Update session status
        session_manager.update_session(session_id, {"status": "running"})
        
        # Send status update
        await session_manager.broadcast_to_session(session_id, {
            "type": "status_update",
            "status": "running",
            "message": f"Starting debate for {policy_name}..."
        })
        
        # Create a custom streaming version of the debate
        await stream_debate_process(session_id, debate_system, policy_name)
        
    except Exception as e:
        logger.error(f"Error in debate streaming: {e}")
        await session_manager.broadcast_to_session(session_id, {
            "type": "error",
            "message": f"Error in debate: {str(e)}"
        })

async def stream_debate_process(session_id: str, debate_system, policy_name: str):
    """Stream the debate process step by step"""
    try:
        # Step 1: Load Policy
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "load_policy",
            "message": "Loading policy data..."
        })
        
        policy_info = debate_system.load_policy(policy_name)
        
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "load_policy_complete",
            "message": f"Policy loaded: {policy_info.get('title', 'Unknown')}",
            "data": policy_info
        })
        
        # Step 2: Identify Stakeholders
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "identify_stakeholders",
            "message": "Identifying stakeholders..."
        })
        
        stakeholders = debate_system.identify_stakeholders(policy_info.get("text", ""))
        
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "identify_stakeholders_complete",
            "message": f"Found {len(stakeholders)} stakeholders",
            "data": stakeholders
        })
        
        # Update session with stakeholders
        session_manager.update_session(session_id, {"stakeholders": stakeholders})
        
        # Step 3: Create Personas
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "create_personas",
            "message": "Creating debate personas..."
        })
        
        personas = debate_system.create_personas(stakeholders)
        
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "create_personas_complete",
            "message": f"Created {len(personas)} personas",
            "data": personas
        })
        
        # Step 4: Start Debate Rounds
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_step",
            "step": "start_rounds",
            "message": "Starting debate rounds..."
        })
        
        # For now, simulate debate messages
        # In a real implementation, you'd integrate with the actual debate system
        await simulate_debate_rounds(session_id, stakeholders)
        
        # Final step
        await session_manager.broadcast_to_session(session_id, {
            "type": "debate_complete",
            "message": "Debate session completed successfully"
        })
        
        session_manager.update_session(session_id, {"status": "completed"})
        
    except Exception as e:
        logger.error(f"Error in debate process: {e}")
        await session_manager.broadcast_to_session(session_id, {
            "type": "error",
            "message": f"Error in debate process: {str(e)}"
        })

async def simulate_debate_rounds(session_id: str, stakeholders: List[Dict[str, Any]]):
    """Simulate debate rounds with realistic timing"""
    # This is a simplified simulation - in the real implementation,
    # you'd integrate with the actual debate system methods
    
    rounds = ["opening", "rebuttal", "closing"]
    
    for round_num, round_type in enumerate(rounds, 1):
        await session_manager.broadcast_to_session(session_id, {
            "type": "round_start",
            "round": round_num,
            "round_type": round_type,
            "message": f"Starting {round_type} round..."
        })
        
        # Simulate each stakeholder speaking
        for stakeholder in stakeholders:
            await asyncio.sleep(2)  # Simulate thinking time
            
            # Simulate argument generation
            message = {
                "type": "debate_message",
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "sender": stakeholder.get("name", "Unknown"),
                "content": f"[{round_type.title()}] This is a simulated argument from {stakeholder.get('name', 'Unknown')} regarding the policy...",
                "timestamp": datetime.now().isoformat(),
                "round": round_num,
                "round_type": round_type
            }
            
            await session_manager.broadcast_to_session(session_id, message)
            
            # Store message in session
            session = session_manager.get_session(session_id)
            if session:
                session["messages"].append(message)
        
        await session_manager.broadcast_to_session(session_id, {
            "type": "round_complete",
            "round": round_num,
            "round_type": round_type,
            "message": f"Round {round_num} ({round_type}) completed"
        })

async def handle_user_message(session_id: str, message: Dict[str, Any]):
    """Handle user message during debate"""
    user_message = {
        "type": "debate_message",
        "id": f"msg_{uuid.uuid4().hex[:8]}",
        "sender": "user",
        "content": message.get("content", ""),
        "timestamp": datetime.now().isoformat(),
        "message_type": "user_input"
    }
    
    # Broadcast to all connections
    await session_manager.broadcast_to_session(session_id, user_message)
    
    # Store in session
    session = session_manager.get_session(session_id)
    if session:
        session["messages"].append(user_message)

async def handle_pause_debate(session_id: str):
    """Handle pause debate request"""
    await session_manager.broadcast_to_session(session_id, {
        "type": "debate_paused",
        "message": "Debate paused by user"
    })
    
    session_manager.update_session(session_id, {"status": "paused"})

async def handle_resume_debate(session_id: str):
    """Handle resume debate request"""
    await session_manager.broadcast_to_session(session_id, {
        "type": "debate_resumed",
        "message": "Debate resumed by user"
    })
    
    session_manager.update_session(session_id, {"status": "running"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)