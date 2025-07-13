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

# Initialize weave tracing
try:
    import weave
    weave.init("civicai-api")
    print("✅ Weave tracing initialized for API")
    WEAVE_AVAILABLE = True
except ImportError:
    print("⚠️  Weave not available - install with: pip install weave")
    WEAVE_AVAILABLE = False

# Conditional decorator helper
def weave_op_decorator(func):
    """Apply weave.op decorator only if weave is available"""
    if WEAVE_AVAILABLE:
        return weave.op()(func)
    return func

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

@weave_op_decorator
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
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

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
@weave_op_decorator
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
    await websocket.accept()
    
    session = session_manager.get_session(session_id)
    if not session:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Session not found"
        }))
        await websocket.close()
        return
    
    # Add WebSocket to session manager
    session_manager.add_websocket(session_id, websocket)
    
    try:
        # Send connection established message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to debate stream",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Run the debate
        await run_debate_with_streaming(session_id, session, websocket)
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"Error in WebSocket for session {session_id}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Error: {str(e)}"
        }))
    finally:
        session_manager.remove_websocket(session_id)

@weave_op_decorator
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
        await websocket.send_text(json.dumps(message))
        
        # Small delay to make streaming visible
        await asyncio.sleep(0.1)
    
    # Override the debate system's logging methods to stream messages
    original_log_step = debate_system.log_step
    original_log_agent_action = debate_system.log_agent_action
    
    async def stream_log_step(step: str, message: str, status: str = "🔄"):
        await send_debate_message("moderator", f"{status} {step}: {message}", "debate_step")
        original_log_step(step, message, status)
    
    async def stream_log_agent_action(agent_name: str, action: str, details: str = ""):
        content = f"{agent_name}: {action}"
        if details:
            content += f"\n{details}"
        await send_debate_message(agent_name, content, "agent_action")
        original_log_agent_action(agent_name, action, details)
    
    # Replace logging methods
    debate_system.log_step = lambda step, message, status="🔄": asyncio.create_task(stream_log_step(step, message, status))
    debate_system.log_agent_action = lambda agent_name, action, details="": asyncio.create_task(stream_log_agent_action(agent_name, action, details))
    
    try:
        # Send initial setup messages
        await send_debate_message("moderator", "🎭 Initializing debate system...", "debate_step")
        await send_debate_message("moderator", f"📖 Loading policy: {policy_name}", "debate_step")
        
        # Run the debate
        results = debate_system.run_debate(policy_name)
        
        # Send final summary
        await send_debate_message("moderator", "✅ Debate completed successfully!", "debate_step")
        
        # Update session with results
        session_manager.update_session(session_id, {
            "current_round": len(results.get("debate_rounds", [])),
            "stakeholder_count": len(results.get("stakeholders", []))
        })
        
    except Exception as e:
        await send_debate_message("moderator", f"❌ Error during debate: {str(e)}", "error")
        raise
    finally:
        # Restore original logging methods
        debate_system.log_step = original_log_step
        debate_system.log_agent_action = original_log_agent_action

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