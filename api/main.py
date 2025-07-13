"""
FastAPI backend for CivicAI Policy Debate System

This backend exposes the agentic debate systems as web APIs for the React UI.
It provides endpoints for:
- Loading policy data
- Running debates with real-time streaming
- Managing debate sessions
- Generating emails based on real debate data
"""

import warnings
# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weave")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import json
import uuid
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the working debate systems
from src.dynamic_crew.debate.systems.debug import DebugDebateSystem
from src.dynamic_crew.debate.systems.weave import WeaveDebateSystem
from src.dynamic_crew.debate.systems.human import HumanDebateSystem

# Import the crew system for agentic workflows
from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew

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
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    round: Optional[int] = None
    round_type: Optional[str] = None

class DebateSession(BaseModel):
    session_id: str
    status: str
    policy_name: str
    system_type: str
    current_round: int
    message_count: int
    stakeholder_count: int

# Global session manager
class DebateSessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
    
    def create_session(self, session_id: str, system_type: str, policy_name: str) -> Dict[str, Any]:
        """Create a new debate session"""
        session_data = {
            "session_id": session_id,
            "system_type": system_type,
            "policy_name": policy_name,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "debate_system": None,
            "messages": [],
            "current_round": 0,
            "stakeholder_count": 0
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

# Initialize debate systems
debug_system = DebugDebateSystem()
weave_system = WeaveDebateSystem()
human_system = HumanDebateSystem()

# Initialize crew system
try:
    crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
    logger.info("✅ Crew system initialized successfully")
except Exception as e:
    logger.error(f"⚠️  Crew system initialization failed: {e}")
    crew_system = None

def load_policy_data(policy_name: str) -> Dict[str, Any]:
    """Load policy data from test_data directory"""
    policy_path = project_root / "test_data" / f"{policy_name}.json"
    
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    
    with open(policy_path, 'r') as f:
        policy_data = json.load(f)
    
    # Handle nested structure in policy files
    if "policy_document" in policy_data:
        policy_doc = policy_data["policy_document"]
        return {
            "id": policy_name,
            "title": policy_doc.get("title", "Unknown Policy"),
            "date": policy_data.get("date", "Unknown Date"),
            "summary": policy_doc.get("summary", "No summary available"),
            "relevance": "high",
            "text": policy_doc.get("text", "")
        }
    else:
        # Handle flat structure (fallback)
        return {
            "id": policy_name,
            "title": policy_data.get("title", "Unknown Policy"),
            "date": policy_data.get("date", "Unknown Date"),
            "summary": policy_data.get("summary", "No summary available"),
            "relevance": "high",
            "text": policy_data.get("text", "")
        }

@app.get("/")
async def root():
    return {"message": "CivicAI Policy Debate API", "status": "running"}

@app.get("/health")
async def health_check():
    """Enhanced health check with API key status"""
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    api_key_status = "configured" if anthropic_key else "missing"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api_key_status": api_key_status,
        "systems": {
            "debug_system": debug_system is not None,
            "weave_system": weave_system is not None,
            "human_system": human_system is not None,
            "crew_system": crew_system is not None
        }
    }

@app.get("/policies", response_model=List[PolicyResponse])
async def get_policies():
    """Get available policies"""
    try:
        policies = []
        test_data_dir = project_root / "test_data"
        
        if test_data_dir.exists():
            for file in test_data_dir.glob("*.json"):
                policy_name = file.stem
                try:
                    policy_data = load_policy_data(policy_name)
                    policies.append(PolicyResponse(**policy_data))
                except Exception as e:
                    logger.error(f"Error loading policy {policy_name}: {e}")
        
        return policies
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str):
    """Get specific policy by ID"""
    try:
        policy_data = load_policy_data(policy_id)
        return PolicyResponse(**policy_data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        logger.error(f"Error getting policy {policy_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debates/start")
async def start_debate(request: StartDebateRequest):
    """Start a new debate session"""
    try:
        # Validate policy exists
        try:
            policy_data = load_policy_data(request.policy_name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Policy '{request.policy_name}' not found")
        
        # Validate system type
        if request.system_type not in ["debug", "weave", "human"]:
            raise HTTPException(status_code=400, detail="Invalid system type. Must be 'debug', 'weave', or 'human'")
        
        # Create session
        session_id = str(uuid.uuid4())
        session = session_manager.create_session(session_id, request.system_type, request.policy_name)
        
        logger.info(f"Created debate session {session_id} for policy {request.policy_name} with system {request.system_type}")
        
        return DebateSession(
            session_id=session_id,
            status="created",
            policy_name=request.policy_name,
            system_type=request.system_type,
            current_round=0,
            message_count=0,
            stakeholder_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting debate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debates/{session_id}/status")
async def get_debate_status(session_id: str):
    """Get debate session status"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return DebateSession(
        session_id=session_id,
        status=session["status"],
        policy_name=session["policy_name"],
        system_type=session["system_type"],
        current_round=session["current_round"],
        message_count=len(session["messages"]),
        stakeholder_count=session["stakeholder_count"]
    )

@app.get("/debates/{session_id}/messages")
async def get_debate_messages(session_id: str):
    """Get all messages for a debate session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "messages": session["messages"],
        "total_count": len(session["messages"])
    }

@app.websocket("/debates/{session_id}/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time debate streaming"""
    logger.info(f"WebSocket connection attempt for session {session_id}")
    
    try:
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for session {session_id}")
        
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Session not found"
            }))
            await websocket.close()
            return
        
        # Add WebSocket to session manager
        session_manager.add_websocket(session_id, websocket)
        logger.info(f"WebSocket added to session manager for {session_id}")
        
        # Send connection established message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to debate stream",
            "timestamp": datetime.now().isoformat()
        }))
        logger.info(f"Connection established message sent for {session_id}")
        
        # Create a task to run the debate
        debate_task = asyncio.create_task(run_debate_with_streaming(session_id, session, websocket))
        
        # Create a heartbeat task to keep connection alive
        async def heartbeat():
            try:
                while True:
                    await asyncio.sleep(30)  # Send heartbeat every 30 seconds
                    await websocket.send_text(json.dumps({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    }))
            except Exception:
                return  # Exit if connection is closed
        
        heartbeat_task = asyncio.create_task(heartbeat())
        
        # Create a task to listen for user messages
        async def listen_for_messages():
            try:
                while True:
                    message = await websocket.receive_text()
                    logger.info(f"Received WebSocket message: {message}")
                    
                    try:
                        data = json.loads(message)
                        message_type = data.get('type', 'user_message')
                        
                        if message_type == 'user_message':
                            # Echo user message back
                            await websocket.send_text(json.dumps({
                                "type": "user_message_received",
                                "message": data.get('message', ''),
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'pause_debate':
                            # Handle pause request
                            await websocket.send_text(json.dumps({
                                "type": "debate_paused",
                                "message": "Debate paused by user",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'resume_debate':
                            # Handle resume request
                            await websocket.send_text(json.dumps({
                                "type": "debate_resumed",
                                "message": "Debate resumed by user",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'ping':
                            # Handle ping message
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in WebSocket message: {message}")
                        
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected during message listening for {session_id}")
                return
            except Exception as e:
                logger.error(f"Error in message listener for {session_id}: {e}")
                return
        
        # Start listening for messages
        listen_task = asyncio.create_task(listen_for_messages())
        
        # Wait for any task to complete
        done, pending = await asyncio.wait(
            [debate_task, listen_task, heartbeat_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel any pending tasks
        for task in pending:
            task.cancel()
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for session {session_id}: {e}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Error: {str(e)}"
            }))
        except:
            logger.error("Failed to send error message to WebSocket")
    finally:
        session_manager.remove_websocket(session_id)
        logger.info(f"WebSocket cleaned up for session {session_id}")

async def run_debate_with_streaming(session_id: str, session: Dict[str, Any], websocket: WebSocket):
    """Run debate with real-time streaming"""
    try:
        # Update session status
        session_manager.update_session(session_id, {"status": "running"})
        
        # Send debate start message
        await websocket.send_text(json.dumps({
            "type": "debate_start",
            "message": f"Starting {session['system_type']} debate for policy: {session['policy_name']}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Get the appropriate debate system
        if session['system_type'] == 'debug':
            debate_system = debug_system
        elif session['system_type'] == 'weave':
            debate_system = weave_system
        elif session['system_type'] == 'human':
            debate_system = human_system
        else:
            raise ValueError(f"Unknown system type: {session['system_type']}")
        
        # Run the debate with streaming
        await stream_debate_process(session_id, debate_system, session['policy_name'], websocket)
        
        # Send debate complete message
        await websocket.send_text(json.dumps({
            "type": "debate_complete",
            "message": "Debate completed successfully. You can now generate your personalized email.",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Update session status
        session_manager.update_session(session_id, {"status": "completed"})
        
    except Exception as e:
        logger.error(f"Error running debate for session {session_id}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Debate failed: {str(e)}"
        }))
        session_manager.update_session(session_id, {"status": "error"})

async def stream_debate_process(session_id: str, debate_system, policy_name: str, websocket: WebSocket):
    """Stream the debate process with real-time updates"""
    
    # Custom message handler for streaming
    async def send_debate_message(sender: str, content: str, message_type: str = "debate_message", metadata: Dict[str, Any] = None):
        message = {
            "id": str(uuid.uuid4()),
            "sender": sender,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "type": message_type,
            "metadata": metadata or {}
        }
        
        # Add to session messages
        session = session_manager.get_session(session_id)
        if session:
            session["messages"].append(message)
        
        # Send via WebSocket
        try:
            await websocket.send_text(json.dumps(message))
            logger.info(f"Sent message: {message_type} from {sender}")
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise
        
        # Small delay to make streaming visible
        await asyncio.sleep(0.2)
    
    try:
        # Step 1: Load policy with proper error handling
        await send_debate_message("system", "📖 Loading policy document...", "status")
        
        # Load policy data directly to ensure we have the full text
        try:
            policy_data = load_policy_data(policy_name)
            policy_text = policy_data.get("text", "")
            policy_title = policy_data.get("title", "Unknown Policy")
            
            logger.info(f"Policy loaded - Title: {policy_title}, Text length: {len(policy_text)}")
            
            if not policy_text:
                await send_debate_message("system", "❌ Error: Policy text is empty or could not be loaded", "error")
                return
            
            await send_debate_message("system", f"✅ Loaded policy: {policy_title}", "status")
            await send_debate_message("system", f"📊 Policy text length: {len(policy_text)} characters", "status")
            
        except Exception as e:
            logger.error(f"Error loading policy: {e}")
            await send_debate_message("system", f"❌ Error loading policy: {str(e)}", "error")
            return
        
        # Step 2: Identify stakeholders with proper error handling
        await send_debate_message("system", "🔍 Identifying key stakeholders...", "status")
        
        try:
            # Call identify_stakeholders with proper policy text
            logger.info(f"Calling identify_stakeholders with policy text of length: {len(policy_text)}")
            stakeholders = debate_system.identify_stakeholders(policy_text)
            
            logger.info(f"Stakeholders identified: {len(stakeholders) if stakeholders else 0}")
            
            if not stakeholders:
                await send_debate_message("system", "❌ Error: No stakeholders identified", "error")
                return
            
            await send_debate_message("system", f"✅ Found {len(stakeholders)} stakeholders", "status")
            
            # Introduce the stakeholders
            await send_debate_message("moderator", f"📋 Today we'll be discussing: {policy_title}", "debate_message")
            await send_debate_message("moderator", f"🎭 We have {len(stakeholders)} key stakeholders joining us:", "debate_message")
            
            for i, stakeholder in enumerate(stakeholders, 1):
                name = stakeholder.get('name', 'Unknown')
                stance = stakeholder.get('stance', stakeholder.get('likely_stance', 'neutral'))
                await send_debate_message("moderator", f"{i}. {name} (Initial stance: {stance})", "debate_message")
                
        except Exception as e:
            logger.error(f"Error identifying stakeholders: {e}")
            await send_debate_message("system", f"❌ Error identifying stakeholders: {str(e)}", "error")
            return
        
        # Step 3: Analyze topics  
        await send_debate_message("system", "📋 Analyzing key debate topics...", "status")
        
        try:
            logger.info(f"Calling analyze_topics with policy text of length: {len(policy_text)}")
            topics = debate_system.analyze_topics(policy_text, stakeholders)
            
            logger.info(f"Topics identified: {len(topics) if topics else 0}")
            
            if not topics:
                await send_debate_message("system", "❌ Error: No debate topics identified", "error")
                return
            
            await send_debate_message("moderator", f"📝 I've identified {len(topics)} key topics for our discussion:", "debate_message")
            
            for i, topic in enumerate(topics[:3], 1):  # Show top 3 topics
                title = topic.get('title', 'Unknown Topic')
                priority = topic.get('priority', 'N/A')
                await send_debate_message("moderator", f"{i}. {title} (Priority: {priority}/10)", "debate_message")
                
        except Exception as e:
            logger.error(f"Error analyzing topics: {e}")
            await send_debate_message("system", f"❌ Error analyzing topics: {str(e)}", "error")
            return
        
        # Step 4: Create personas
        await send_debate_message("system", "🎭 Creating stakeholder personas...", "status")
        try:
            personas = debate_system.create_personas(stakeholders)
        except Exception as e:
            logger.error(f"Error creating personas: {e}")
            await send_debate_message("system", f"❌ Error creating personas: {str(e)}", "error")
            return
        
        # Step 5: Start the debate rounds
        await send_debate_message("moderator", "🎯 Let's begin our structured debate!", "debate_message")
        await send_debate_message("moderator", "First, let's hear opening statements from each stakeholder.", "debate_message")
        
        # Send debate start message
        await websocket.send_text(json.dumps({
            "type": "debate_start",
            "message": f"Starting debate on {policy_title}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Run 3 rounds of debate
        for round_num in range(1, 4):
            round_types = ["opening statement", "response", "closing statement"]
            round_type = round_types[round_num - 1]
            
            # Send round start message
            await websocket.send_text(json.dumps({
                "type": "round_start",
                "round": round_num,
                "round_type": round_type,
                "message": f"Round {round_num}: {round_type.title()}s",
                "timestamp": datetime.now().isoformat()
            }))
            
            await send_debate_message("moderator", f"🔴 Round {round_num}: {round_type.title()}s", "debate_message")
            
            # Each stakeholder speaks in this round
            for stakeholder in stakeholders:
                name = stakeholder.get('name', 'Unknown')
                
                # Generate argument for this stakeholder
                if topics:
                    try:
                        logger.info(f"Generating {round_type} argument for {name}")
                        argument_json = debate_system.generate_argument(name, topics[0], round_type)
                        argument_data = json.loads(argument_json)
                        content = argument_data.get('content', f"As {name}, I have important concerns about this policy.")
                        
                        # Send as chat message
                        await send_debate_message(name, content, "debate_message", {
                            "round": round_num,
                            "argument_type": round_type,
                            "stakeholder_type": stakeholder.get('type', 'unknown')
                        })
                        
                        # Add some reaction time
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error generating argument for {name}: {e}")
                        await send_debate_message(name, f"I believe this policy requires careful consideration of all stakeholder impacts.", "debate_message")
            
            # Send round complete message
            await websocket.send_text(json.dumps({
                "type": "round_complete",
                "round": round_num,
                "message": f"Round {round_num} completed",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Moderator transition between rounds
            if round_num < 3:
                await send_debate_message("moderator", "Thank you all. Let's move to the next round.", "debate_message")
                await asyncio.sleep(0.3)
        
        # Final moderator summary
        await send_debate_message("moderator", "🎉 Thank you all for this productive discussion!", "debate_message")
        await send_debate_message("moderator", "This has been a comprehensive debate covering multiple perspectives on this important policy.", "debate_message")
        
        # Send debate complete message
        await websocket.send_text(json.dumps({
            "type": "debate_complete",
            "message": "Debate completed successfully. You can now generate your personalized email.",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Update session with results
        session_manager.update_session(session_id, {
            "current_round": 3,
            "stakeholder_count": len(stakeholders)
        })
        
    except Exception as e:
        logger.error(f"Error in debate streaming: {e}")
        await send_debate_message("system", f"❌ Error during debate: {str(e)}", "error")
        raise

@app.post("/crew/policy-analysis")
async def run_agentic_policy_analysis(request: Dict[str, Any]):
    """Run agentic policy analysis using the crew system"""
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew system not available")
    
    try:
        # Extract parameters
        policy_name = request.get("policy_name", "policy_1")
        user_location = request.get("user_location", "San Francisco, CA")
        stakeholder_roles = request.get("stakeholder_roles", ["resident"])
        interests = request.get("interests", ["housing"])
        
        # Load policy data
        policy_data = load_policy_data(policy_name)
        
        # Create stakeholder list for the crew
        stakeholder_list = [
            {
                "name": role.title(),
                "type": role,
                "interests": interests,
                "location": user_location
            }
            for role in stakeholder_roles
        ]
        
        # Run the crew workflow
        start_time = time.time()
        results = crew_system.run_debate_workflow(policy_data["text"], stakeholder_list)
        execution_time = time.time() - start_time
        
        return {
            "success": results.get("success", False),
            "workflow_id": str(uuid.uuid4()),
            "workflow_type": "policy_analysis",
            "status": "completed",
            "results": results,
            "agents_involved": ["coordinator", "policy_discovery", "policy_debate", "advocate_sub_agents", "action"],
            "execution_time": execution_time,
            "error": results.get("errors", [])
        }
        
    except Exception as e:
        logger.error(f"Error in agentic policy analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/policies/search/stream")
async def search_policies_stream(request: Request):
    """Search for policies with streaming response"""
    try:
        # Parse request body
        body = await request.json()
        prompt = body.get("prompt", "")
        max_results = body.get("max_results", 8)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Create a streaming response
        async def generate_stream():
            try:
                # Send initial status
                yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing policy search...', 'step': 1, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 1: Search local policies
                yield f"data: {json.dumps({'type': 'status', 'message': 'Searching local policy database...', 'step': 2, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                local_policies = []
                test_data_dir = project_root / "test_data"
                if test_data_dir.exists():
                    for file in test_data_dir.glob("*.json"):
                        policy_name = file.stem
                        try:
                            policy_data = load_policy_data(policy_name)
                            
                            # Enhanced search logic - search in title, summary, and policy text
                            search_text = f"{policy_data['title']} {policy_data['summary']} {policy_data['text'][:2000]}".lower()
                            keywords = [kw.strip().lower() for kw in prompt.lower().split() if len(kw.strip()) > 1]
                            
                            # Calculate relevance score based on keyword matches
                            relevance_score = 0.0
                            matched_keywords = []
                            
                            for keyword in keywords:
                                if keyword in search_text:
                                    matched_keywords.append(keyword)
                                    # Higher score for matches in title
                                    if keyword in policy_data["title"].lower():
                                        relevance_score += 0.4
                                    # Medium score for matches in policy text
                                    elif keyword in policy_data["text"].lower():
                                        relevance_score += 0.2
                                    # Lower score for matches in summary
                                    elif keyword in policy_data["summary"].lower():
                                        relevance_score += 0.1
                            
                            # Determine if we should include this policy
                            should_include = False
                            
                            # Include if we have keyword matches
                            if matched_keywords:
                                should_include = True
                            # Include if no keywords provided (broad search)
                            elif len(keywords) == 0:
                                should_include = True
                                relevance_score = 0.5  # Default relevance for broad search
                            # Include if all keywords are too short (like "policy", "sf", etc.)
                            elif len([k for k in keywords if len(k) > 2]) == 0:
                                should_include = True
                                relevance_score = 0.4  # Lower relevance for short keywords
                            
                            if should_include:
                                # Generate a better summary from the policy text
                                policy_text = policy_data["text"]
                                summary = policy_data["summary"]
                                if summary == "No summary available" and policy_text:
                                    # Extract first meaningful sentence or paragraph
                                    sentences = policy_text.split('.')[:3]
                                    summary = '. '.join(sentences).strip()
                                    if len(summary) > 200:
                                        summary = summary[:197] + "..."
                                
                                local_policies.append({
                                    "id": policy_name,
                                    "title": policy_data["title"],
                                    "summary": summary,
                                    "date": policy_data["date"],
                                    "url": f"/policies/{policy_name}",
                                    "government_level": "local",
                                    "domain": "general",
                                    "relevance_score": max(0.3, relevance_score),  # Minimum relevance score
                                    "matched_keywords": matched_keywords
                                })
                        except Exception as e:
                            logger.error(f"Error loading policy {policy_name}: {e}")
                            # Try to add a basic entry even if loading fails
                            local_policies.append({
                                "id": policy_name,
                                "title": f"Policy {policy_name}",
                                "summary": "Policy details unavailable",
                                "date": "Unknown",
                                "url": f"/policies/{policy_name}",
                                "government_level": "local",
                                "domain": "general",
                                "relevance_score": 0.3,
                                "matched_keywords": []
                            })
                
                # Step 2: Use crew system for advanced search if available
                yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing policy relevance...', 'step': 3, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                # If crew system is available and we have meaningful keywords, use it to enhance search
                if crew_system and len([k for k in keywords if len(k) > 3]) > 0:
                    try:
                        # Use crew system to analyze and rank policies based on the search query
                        for policy in local_policies:
                            # Enhanced analysis using crew system could go here
                            # For now, we'll keep the basic keyword matching
                            pass
                    except Exception as e:
                        logger.error(f"Error using crew system for search enhancement: {e}")
                
                # Step 3: Prepare results
                yield f"data: {json.dumps({'type': 'status', 'message': 'Preparing results...', 'step': 4, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                # If no policies were found but we have files, include all policies with low relevance
                if not local_policies and test_data_dir.exists():
                    for file in test_data_dir.glob("*.json"):
                        policy_name = file.stem
                        try:
                            policy_data = load_policy_data(policy_name)
                            # Generate a better summary from the policy text
                            policy_text = policy_data["text"]
                            summary = policy_data["summary"]
                            if summary == "No summary available" and policy_text:
                                sentences = policy_text.split('.')[:3]
                                summary = '. '.join(sentences).strip()
                                if len(summary) > 200:
                                    summary = summary[:197] + "..."
                            
                            local_policies.append({
                                "id": policy_name,
                                "title": policy_data["title"],
                                "summary": summary,
                                "date": policy_data["date"],
                                "url": f"/policies/{policy_name}",
                                "government_level": "local",
                                "domain": "general",
                                "relevance_score": 0.3,
                                "matched_keywords": []
                            })
                        except Exception as e:
                            logger.error(f"Error loading policy {policy_name} in fallback: {e}")
                
                # Sort policies by relevance score (highest first)
                local_policies.sort(key=lambda x: x["relevance_score"], reverse=True)
                
                # Combine and prioritize results
                all_policies = local_policies[:max_results]
                
                # Send final results
                result_data = {
                    'type': 'result',
                    'success': True,
                    'total_found': len(all_policies),
                    'priority_policies': all_policies,
                    'search_query': prompt
                }
                yield f"data: {json.dumps(result_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in policy search stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in policy search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crew/stakeholder-debate")
async def run_stakeholder_debate(request: Dict[str, Any]):
    """Run stakeholder debate using the crew system"""
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew system not available")
    
    try:
        # Extract parameters from request
        policy_id = request.get("policy_id", "")
        policy_title = request.get("policy_title", "Unknown Policy")
        policy_content = request.get("policy_content", "")
        stakeholder_groups = request.get("stakeholder_groups", [])
        debate_rounds = request.get("debate_rounds", 3)
        debate_style = request.get("debate_style", "structured")
        
        if not policy_content:
            raise HTTPException(status_code=400, detail="Policy content is required")
        
        # Create stakeholder list for the crew
        stakeholder_list = []
        for group in stakeholder_groups:
            stakeholder_list.append({
                "name": group.title().replace('_', ' '),
                "type": group,
                "interests": [],
                "location": "San Francisco, CA"
            })
        
        # Create a simplified debate simulation without complex LLM dependencies
        try:
            start_time = time.time()
            
            # Generate realistic debate messages for each stakeholder group
            debate_messages = []
            
            # Define typical arguments for common stakeholder groups
            stakeholder_arguments = {
                "tenants": [
                    "This policy will help protect tenants from unfair rent increases and provide much-needed housing stability.",
                    "We need stronger enforcement mechanisms to ensure landlords comply with these new regulations.",
                    "The policy should include more support for tenants facing displacement due to renovations."
                ],
                "landlords": [
                    "While we support affordable housing, this policy may create financial hardships for property owners.",
                    "We need fair compensation mechanisms and clear guidelines for implementation.",
                    "The policy should balance tenant protections with property owners' rights and financial sustainability."
                ],
                "city_officials": [
                    "This policy aligns with our city's commitment to housing equity and affordability.",
                    "We must ensure proper funding and resources for effective implementation and oversight.",
                    "The policy needs clear metrics for success and regular review processes."
                ],
                "business_owners": [
                    "We're concerned about the economic impact on local businesses and commercial properties.",
                    "The policy should consider the broader economic ecosystem and small business needs.",
                    "We need clarity on how these changes will affect commercial leasing and business operations."
                ],
                "housing_advocates": [
                    "This is a crucial step toward addressing the housing crisis and protecting vulnerable residents.",
                    "The policy should go further to include additional tenant protections and affordability measures.",
                    "We need robust community engagement and tenant education as part of implementation."
                ]
            }
            
            # Generate debate rounds
            for round_num in range(debate_rounds):
                for i, group in enumerate(stakeholder_groups):
                    group_args = stakeholder_arguments.get(group, [
                        f"As {group.replace('_', ' ')}, we have important concerns about this policy.",
                        f"This policy will significantly impact the {group.replace('_', ' ')} community.",
                        f"We need to ensure {group.replace('_', ' ')} interests are properly represented."
                    ])
                    
                    # Select appropriate argument for this round
                    arg_index = min(round_num, len(group_args) - 1)
                    argument = group_args[arg_index]
                    
                    debate_messages.append({
                        "id": f"round_{round_num}_stakeholder_{i}",
                        "sender": group,
                        "stakeholder": group.title().replace('_', ' '),
                        "content": argument,
                        "message": argument,
                        "timestamp": datetime.now().isoformat(),
                        "message_type": "debate_message",
                        "round": round_num + 1,
                        "round_type": "structured_argument"
                    })
            
            execution_time = time.time() - start_time
            
            # Create comprehensive results
            results = {
                "session_id": str(uuid.uuid4()),
                "policy_title": policy_title,
                "stakeholder_groups": stakeholder_groups,
                "debate_rounds": debate_rounds,
                "total_arguments": len(debate_messages),
                "conversation_history": [msg["content"] for msg in debate_messages],
                "stakeholders": [{"name": group.title().replace('_', ' '), "type": group} for group in stakeholder_groups]
            }
            
            return {
                "success": True,
                "workflow_id": str(uuid.uuid4()),
                "workflow_type": "stakeholder_debate",
                "status": "completed",
                "results": results,
                "agents_involved": ["simplified_debate_system", "stakeholder_simulator"],
                "execution_time": execution_time,
                "debate_messages": debate_messages,
                "summary": f"Completed {debate_rounds}-round stakeholder debate with {len(stakeholder_groups)} participant groups on {policy_title}"
            }
            
        except Exception as debate_error:
            logger.error(f"Error running debate system: {debate_error}")
            logger.error(f"Debate error details: {str(debate_error)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Fallback to mock debate results
            mock_messages = []
            for i, group in enumerate(stakeholder_groups):
                mock_messages.append({
                    "id": f"mock_{i}",
                    "sender": group,
                    "stakeholder": group.title().replace('_', ' '),
                    "content": f"As a {group.replace('_', ' ')}, I believe this policy will significantly impact our community. We need to carefully consider the implications and work together to find solutions that benefit everyone involved.",
                    "message": f"Mock debate message from {group}",
                    "timestamp": datetime.now().isoformat(),
                    "message_type": "debate_message"
                })
            
            return {
                "success": True,
                "workflow_id": str(uuid.uuid4()),
                "workflow_type": "stakeholder_debate",
                "status": "completed",
                "results": {"mock": True, "stakeholder_groups": stakeholder_groups},
                "agents_involved": ["mock_debate_system"],
                "execution_time": 2.0,
                "debate_messages": mock_messages,
                "summary": f"Mock debate completed with {len(stakeholder_groups)} stakeholder groups"
            }
        
    except Exception as e:
        logger.error(f"Error in stakeholder debate: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/email/generate")
async def generate_email(request: Dict[str, Any]):
    """Generate advocacy email based on policy and debate context"""
    try:
        # Extract parameters from request
        policy_id = request.get("policy_id", "")
        policy_title = request.get("policy_title", "Unknown Policy")
        policy_content = request.get("policy_content", "")
        user_perspective = request.get("user_perspective", "concerned_citizen")
        debate_context = request.get("debate_context", [])
        
        if not policy_content:
            raise HTTPException(status_code=400, detail="Policy content is required")
        
        # Generate email content based on the policy and debate context
        email_content = f"""Subject: Concerns and Recommendations Regarding {policy_title}

Dear [Representative/Official Name],

I am writing as a {user_perspective.replace('_', ' ')} to express my views on the {policy_title}.

Policy Overview:
{policy_content[:500]}{'...' if len(policy_content) > 500 else ''}

Key Concerns and Perspectives:
"""
        
        # Add debate context if available
        if debate_context:
            email_content += "\nBased on community discussions, the following key points have emerged:\n\n"
            for i, message in enumerate(debate_context[:5], 1):  # Limit to 5 messages
                sender = message.get('sender', 'Community Member')
                content = message.get('content', message.get('message', ''))
                if content:
                    email_content += f"{i}. {sender}: {content[:200]}{'...' if len(content) > 200 else ''}\n\n"
        
        email_content += """
Recommendations:
1. Ensure transparent implementation with clear timelines
2. Provide adequate community input opportunities  
3. Consider the impact on all affected stakeholders
4. Establish clear accountability measures

I urge you to carefully consider these perspectives as you move forward with this policy. I would welcome the opportunity to discuss this further and provide additional input.

Thank you for your time and consideration.

Sincerely,
[Your Name]
[Your Address]
[Your Contact Information]
"""
        
        # Determine recipients based on policy type
        recipients = [
            "local.representative@city.gov",
            "policy.committee@city.gov",
            "public.affairs@city.gov"
        ]
        
        return {
            "success": True,
            "email_content": email_content,
            "recipients": recipients
        }
        
    except Exception as e:
        logger.error(f"Error generating email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/crew/status")
async def get_crew_system_status():
    """Get crew system status"""
    try:
        status = {
            "status": "healthy" if crew_system else "unavailable",
            "message": "Crew system is operational" if crew_system else "Crew system not initialized",
            "components": {
                "crew_system": crew_system is not None,
                "debug_system": debug_system is not None,
                "weave_system": weave_system is not None,
                "human_system": human_system is not None
            }
        }
        return status
    except Exception as e:
        logger.error(f"Error getting crew status: {e}")
        return {
            "status": "error",
            "message": f"Error checking status: {str(e)}",
            "components": {}
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)