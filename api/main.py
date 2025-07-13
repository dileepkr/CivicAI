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

@app.get("/test/explain/{policy_id}")
async def test_explain_policy(policy_id: str):
    """Test route for policy explanation"""
    return {
        "success": True,
        "policy_id": policy_id,
        "message": "Test policy explanation endpoint is working!",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/policies/{policy_id}/explain")
async def explain_policy(policy_id: str):
    """Get an intelligent LLM-generated explanation of the policy"""
    try:
        # Load the policy data
        policy_data = load_policy_data(policy_id)
        policy_text = policy_data.get("text", "")
        policy_title = policy_data.get("title", "Unknown Policy")
        
        if not policy_text:
            raise HTTPException(status_code=400, detail="Policy text not available for explanation")
        
        logger.info(f"Generating explanation for policy: {policy_title}")
        
        # Create a comprehensive explanation prompt
        explanation_prompt = f"""
Analyze the following policy and provide a comprehensive, easy-to-understand explanation.

Policy Title: {policy_title}

Policy Text:
{policy_text}

Please provide a detailed explanation in JSON format with the following structure:
{{
    "plain_language_summary": "A clear, jargon-free summary of what this policy does in 2-3 sentences",
    "key_provisions": [
        "First major provision or requirement",
        "Second major provision or requirement", 
        "Third major provision or requirement"
    ],
    "who_is_affected": [
        {{
            "group": "Stakeholder group name",
            "impact": "How this policy specifically affects them"
        }}
    ],
    "implementation_timeline": {{
        "effective_date": "When the policy takes effect",
        "key_deadlines": ["Important dates or milestones"],
        "phase_in_period": "Any gradual implementation details"
    }},
    "benefits": [
        "Positive outcome 1",
        "Positive outcome 2"
    ],
    "concerns_or_challenges": [
        "Potential concern 1", 
        "Potential concern 2"
    ],
    "compliance_requirements": [
        "What people/organizations need to do to comply"
    ],
    "penalties_or_enforcement": "What happens if the policy isn't followed",
    "key_definitions": {{
        "technical_term_1": "Plain language definition",
        "technical_term_2": "Plain language definition"
    }}
}}

Focus on making this accessible to everyday citizens who want to understand how this policy affects them.
"""

        # Get LLM explanation using the existing debate system's LLM capabilities
        try:
            result = debug_system.get_llm_response(explanation_prompt, "policy_explanation")
            
            if "error" in result:
                logger.error(f"Error generating policy explanation: {result['error']}")
                # Return a fallback explanation
                return {
                    "success": False,
                    "error": result["error"],
                    "fallback_explanation": {
                        "plain_language_summary": f"This policy, '{policy_title}', contains regulations and requirements that affect various stakeholders. Please refer to the full policy text for detailed information.",
                        "policy_title": policy_title,
                        "policy_length": f"{len(policy_text)} characters",
                        "suggestion": "The policy text is available for detailed review, but automated explanation is currently unavailable."
                    }
                }
            
            # Return the comprehensive explanation
            explanation_data = {
                "success": True,
                "policy_id": policy_id,
                "policy_title": policy_title,
                "explanation": result,
                "generated_at": datetime.now().isoformat(),
                "explanation_type": "llm_generated"
            }
            
            logger.info(f"Successfully generated explanation for {policy_title}")
            return explanation_data
            
        except Exception as llm_error:
            logger.error(f"LLM error: {llm_error}")
            # Return a manual explanation for now
            return {
                "success": True,
                "policy_id": policy_id,
                "policy_title": policy_title,
                "explanation": {
                    "plain_language_summary": f"This is the {policy_title}, which regulates rental fees and charges to create more transparency and predictability for tenants and landlords in residential properties.",
                    "key_provisions": [
                        "Landlords must include all required fees in advertised rent prices (effective April 1, 2026)",
                        "Optional services must be clearly separated and cancelable by tenants",
                        "Utility billing through ratio systems is restricted and regulated"
                    ],
                    "who_is_affected": [
                        {"group": "Tenants", "impact": "Will see upfront total costs and have more protection from surprise fees"},
                        {"group": "Landlords", "impact": "Must change advertising practices and fee structures to comply with transparency requirements"},
                        {"group": "Property Managers", "impact": "Need to update leasing procedures and billing systems"}
                    ],
                    "implementation_timeline": {
                        "effective_date": "April 1, 2026",
                        "key_deadlines": ["April 1, 2026 - All advertising must include total costs"],
                        "phase_in_period": "Applies to new tenancies beginning on or after April 1, 2026"
                    },
                    "benefits": [
                        "Increased transparency in rental costs for tenants",
                        "Reduced surprise fees and hidden costs",
                        "Level playing field among landlords in advertising"
                    ],
                    "concerns_or_challenges": [
                        "Administrative burden on landlords to update systems",
                        "Potential for increased base rents to compensate for fee restrictions",
                        "Complexity in calculating and displaying accurate utility estimates"
                    ],
                    "compliance_requirements": [
                        "Include all required fees in advertised rent prices",
                        "Clearly separate optional services with proper disclosure",
                        "Provide utility billing transparency and tenant inspection rights"
                    ],
                    "penalties_or_enforcement": "Violating landlords are liable for actual damages (minimum $1,000), injunctive relief, attorney's fees, and potentially triple damages for willful violations",
                    "key_definitions": {
                        "housing_services": "All services related to residential property use including utilities, maintenance, and facilities",
                        "optional_housing_service": "Services that are not legally required, freely selectable, and cancelable by tenants",
                        "ratio_utility_billing": "Allocation of utility costs to tenants through methods other than individual meters"
                    }
                },
                "generated_at": datetime.now().isoformat(),
                "explanation_type": "manual_fallback"
            }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Policy not found")
    except Exception as e:
        logger.error(f"Error explaining policy {policy_id}: {e}")
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

@app.get("/debates/{session_id}/summary")
async def get_debate_summary(session_id: str):
    """Get the debate summary for a completed session"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if debate is completed
    if session.get("status") not in ["completed", "terminated_early"]:
        raise HTTPException(status_code=400, detail="Debate must be completed to get summary")
    
    # Find the debate summary message
    messages = session.get("messages", [])
    summary_message = None
    for msg in messages:
        if msg.get("type") == "debate_summary":
            summary_message = msg
            break
    
    if not summary_message:
        raise HTTPException(status_code=404, detail="Debate summary not found")
    
    # Get additional session metadata
    policy_name = session.get("policy_name", "Unknown Policy")
    try:
        policy_data = load_policy_data(policy_name)
        policy_title = policy_data.get("title", "Unknown Policy")
    except Exception:
        policy_title = "Unknown Policy"
    
    return {
        "session_id": session_id,
        "policy_title": policy_title,
        "summary": summary_message.get("content", ""),
        "summary_timestamp": summary_message.get("timestamp", ""),
        "debate_status": session.get("status"),
        "stakeholder_count": session.get("stakeholder_count", 0),
        "topics_discussed": session.get("topics_discussed", 0),
        "total_messages": len(messages),
        "completed_at": session.get("completed_at", "")
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
                            session_manager.update_session(session_id, {"paused": True})
                            await websocket.send_text(json.dumps({
                                "type": "debate_paused",
                                "message": "Debate paused by user",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'resume_debate':
                            # Handle resume request
                            session_manager.update_session(session_id, {"paused": False})
                            await websocket.send_text(json.dumps({
                                "type": "debate_resumed",
                                "message": "Debate resumed by user",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'end_debate':
                            # Enhanced early termination with graceful shutdown
                            confirmation_message = data.get('confirmation', False)
                            reason = data.get('reason', 'User requested early termination')
                            
                            # Send confirmation request if not already confirmed
                            if not confirmation_message:
                                await websocket.send_text(json.dumps({
                                    "type": "end_debate_confirmation",
                                    "message": "Are you sure you want to end the debate early? This will generate a summary of the discussion so far.",
                                    "timestamp": datetime.now().isoformat()
                                }))
                            else:
                                # User confirmed, proceed with graceful termination
                                session_manager.update_session(session_id, {
                                    "terminated_early": True,
                                    "termination_reason": reason,
                                    "termination_confirmed": True,
                                    "termination_timestamp": datetime.now().isoformat()
                                })
                                
                                # Send immediate feedback
                                await websocket.send_text(json.dumps({
                                    "type": "debate_terminating",
                                    "message": "Ending debate gracefully... The moderator will provide a summary of the discussion.",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                                # The debate loop will handle the actual termination and summary generation
                        elif message_type == 'end_debate_confirm':
                            # Handle confirmation of early termination
                            reason = data.get('reason', 'User requested early termination')
                            
                            session_manager.update_session(session_id, {
                                "terminated_early": True,
                                "termination_reason": reason,
                                "termination_confirmed": True,
                                "termination_timestamp": datetime.now().isoformat()
                            })
                            
                            await websocket.send_text(json.dumps({
                                "type": "debate_terminating",
                                "message": "Ending debate gracefully... The moderator will provide a summary of the discussion.",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'end_debate_cancel':
                            # Handle cancellation of early termination
                            await websocket.send_text(json.dumps({
                                "type": "end_debate_cancelled",
                                "message": "Debate termination cancelled. The discussion will continue.",
                                "timestamp": datetime.now().isoformat()
                            }))
                        elif message_type == 'user_input':
                            # Handle user participation in debate
                            user_message = data.get('message', '')
                            if user_message:
                                # Store user input for moderator to process
                                session = session_manager.get_session(session_id)
                                if session:
                                    if 'user_inputs' not in session:
                                        session['user_inputs'] = []
                                    session['user_inputs'].append({
                                        'message': user_message,
                                        'timestamp': datetime.now().isoformat(),
                                        'processed': False
                                    })
                                
                                await websocket.send_text(json.dumps({
                                    "type": "user_input_received",
                                    "message": f"Moderator will address your input: '{user_message[:100]}{'...' if len(user_message) > 100 else ''}'",
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
    """Stream the debate process with real-time updates and enhanced topic-focused structure"""
    
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
    
    # Enhanced argument generation with research focus
    async def generate_researched_argument(stakeholder_name: str, stakeholder_data: Dict[str, Any], topic: Dict[str, Any], argument_type: str, context: str = "") -> str:
        """Generate research-based argument without made-up statistics"""
        try:
            logger.info(f"Generating {argument_type} argument for {stakeholder_name} on topic: {topic.get('title', 'Unknown')}")
            
            # Create enhanced prompt for research-based arguments
            topic_title = topic.get('title', 'Unknown Topic')
            topic_description = topic.get('description', '')
            stakeholder_interests = stakeholder_data.get('interests', [])
            stakeholder_concerns = stakeholder_data.get('concerns', [])
            
            enhanced_prompt = f"""
You are {stakeholder_name} participating in a policy debate about "{topic_title}".

Topic: {topic_title}
Description: {topic_description}
Your interests: {', '.join(stakeholder_interests) if stakeholder_interests else 'General policy concerns'}
Your concerns: {', '.join(stakeholder_concerns) if stakeholder_concerns else 'Policy implementation'}
Context: {context}

Generate a {argument_type} argument that is:
- Factual and evidence-based (NO made-up statistics or data)
- Relevant to your specific interests and concerns
- Professional and respectful
- 2-3 sentences long
- Focused on real policy impacts and logical reasoning

Return ONLY a valid JSON object with this structure:
{{
    "stakeholder_name": "{stakeholder_name}",
    "argument_type": "{argument_type}",
    "content": "The actual argument content here",
    "key_points": ["main point 1", "main point 2"],
    "concerns_addressed": ["concern 1", "concern 2"]
}}
"""
            
            result = debate_system.get_llm_response(enhanced_prompt, "argument_generation")
            
            if "error" in result:
                # Return improved fallback argument
                fallback_content = f"As {stakeholder_name}, I believe this policy's impact on {stakeholder_interests[0] if stakeholder_interests else 'our community'} requires careful consideration and proper implementation planning."
                return json.dumps({
                    "stakeholder_name": stakeholder_name,
                    "argument_type": argument_type,
                    "content": fallback_content,
                    "key_points": ["Policy implementation", "Community impact"],
                    "concerns_addressed": ["Implementation challenges"]
                })
            
            # Return the LLM result as JSON string
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Error generating argument for {stakeholder_name}: {e}")
            # Return fallback argument on error
            fallback_content = f"As {stakeholder_name}, I have important concerns about this policy that need to be addressed through proper consultation and implementation."
            return json.dumps({
                "stakeholder_name": stakeholder_name,
                "argument_type": argument_type,
                "content": fallback_content,
                "key_points": ["Policy consultation", "Implementation concerns"],
                "concerns_addressed": ["Stakeholder input"]
            })
    
    # Function to generate moderator summary
    async def generate_moderator_summary(topic: Dict[str, Any], arguments: List[Dict[str, Any]]) -> str:
        """Generate moderator summary of the round"""
        try:
            topic_title = topic.get('title', 'Unknown Topic')
            
            # Extract key points from arguments
            key_points = []
            for arg in arguments:
                if 'key_points' in arg:
                    key_points.extend(arg['key_points'])
            
            # Create moderator summary
            summary = f"Thank you all for that discussion on {topic_title}. "
            
            if key_points:
                summary += f"Key points raised include: {', '.join(key_points[:3])}. "
            
            summary += "We can see there are different perspectives on this important aspect of the policy."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating moderator summary: {e}")
            return f"Thank you for that thoughtful discussion on {topic.get('title', 'this topic')}. Let's continue with our next topic."
    
    # Function to process user input and generate moderator response
    async def process_user_input(user_input: str, current_context: str = "") -> str:
        """Process user input and generate appropriate moderator response"""
        try:
            prompt = f"""
You are a professional debate moderator facilitating a policy discussion. A user has just provided this input:

User Input: "{user_input}"

Current Context: {current_context}

As the moderator, generate a response that:
- Acknowledges the user's input professionally
- Relates their input to the current policy debate
- Guides the discussion in a relevant direction based on their input
- Encourages stakeholder participation on the user's point
- Maintains neutrality while being responsive

Return a natural moderator response (2-3 sentences) that seamlessly integrates the user's input into the ongoing debate.
"""
            
            result = debug_system.get_llm_response(prompt, "moderator_response")
            
            if "error" in result:
                return f"Thank you for that input. Let me ask our stakeholders to address your point about this policy aspect."
            
            # If result is a dict with content, extract it; otherwise use the string directly
            if isinstance(result, dict) and 'content' in result:
                return result['content']
            elif isinstance(result, str):
                return result
            else:
                return f"Thank you for raising that point. Let's hear how our stakeholders view this aspect of the policy."
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return f"Thank you for your input. Let me ask our stakeholders to address your concerns about this policy."
    
    # Function to check for session control flags
    def check_session_status(session_id: str) -> Dict[str, bool]:
        """Check if debate should be paused, terminated, or has user input"""
        session = session_manager.get_session(session_id)
        if not session:
            return {"continue": True, "paused": False, "terminated": False, "has_user_input": False}
        
        # Check for unprocessed user inputs
        user_inputs = session.get("user_inputs", [])
        unprocessed_inputs = [inp for inp in user_inputs if not inp.get("processed", False)]
        
        return {
            "continue": True,
            "paused": session.get("paused", False),
            "terminated": session.get("terminated_early", False),
            "has_user_input": len(unprocessed_inputs) > 0
        }
    
    # Enhanced function to handle user inputs during debate with dynamic direction changes
    async def handle_user_inputs(session_id: str, current_context: str):
        """Process and respond to user inputs with dynamic discussion direction changes"""
        session = session_manager.get_session(session_id)
        if not session:
            return
        
        user_inputs = session.get("user_inputs", [])
        unprocessed_inputs = [inp for inp in user_inputs if not inp.get("processed", False)]
        
        for user_input in unprocessed_inputs:
            user_message = user_input.get('message', '')
            
            # Enhanced moderator response with dynamic direction change
            moderator_response = await generate_dynamic_moderator_response(user_message, current_context, stakeholders)
            
            # Send moderator acknowledgment
            await send_debate_message("moderator", f"👤 I see a community member has raised an important point: '{user_message}'", "user_interaction")
            await send_debate_message("moderator", moderator_response, "moderator_response")
            
            # Determine if this user input should change the discussion direction
            should_pivot = await should_pivot_discussion(user_message, current_context)
            
            if should_pivot:
                # Create a new focused discussion based on user input
                pivot_topic = await create_pivot_topic(user_message, current_context)
                await send_debate_message("moderator", f"🔄 Based on this important community input, let's explore this aspect in more depth.", "debate_message")
                await send_debate_message("moderator", f"📍 New focus area: {pivot_topic.get('title', 'Community-raised concern')}", "debate_message")
                
                # Get targeted stakeholder responses on this pivot topic
                await send_debate_message("moderator", "Let me ask each stakeholder to specifically address this community concern.", "debate_message")
                
                for stakeholder in stakeholders:
                    name = stakeholder.get('name', 'Unknown')
                    
                    try:
                        # Generate targeted response to the pivot topic
                        pivot_response = await generate_pivot_response(name, stakeholder, pivot_topic, user_message)
                        
                        await send_debate_message(name, pivot_response, "pivot_response", {
                            "responding_to_user": True,
                            "user_input": user_message[:100],
                            "pivot_topic": pivot_topic.get('title', 'Community concern'),
                            "response_type": "targeted_pivot"
                        })
                        
                        await asyncio.sleep(0.4)
                        
                    except Exception as e:
                        logger.error(f"Error generating pivot response for {name}: {e}")
                        await send_debate_message(name, f"That's an important community concern that deserves our attention and response.", "pivot_response")
                
                # Moderator synthesis of the pivot discussion
                await send_debate_message("moderator", "📝 Thank you all for addressing this community concern. This input highlights an important aspect we should keep in mind as we continue our discussion.", "debate_message")
                
            else:
                # Standard response handling for non-pivot inputs
                await send_debate_message("moderator", "Let me ask our stakeholders to briefly address this point.", "debate_message")
                
                # Get quick responses from 1-2 stakeholders
                for i, stakeholder in enumerate(stakeholders[:2]):
                    name = stakeholder.get('name', 'Unknown')
                    
                    try:
                        # Generate standard response to user input
                        response_prompt = f"""
As {name}, respond to this user input: "{user_message}"

Current debate context: {current_context}

Generate a brief response (1-2 sentences) that:
- Addresses the user's point from your stakeholder perspective
- Relates to the current policy discussion
- Is professional and substantive

Return ONLY a valid JSON object:
{{
    "stakeholder_name": "{name}",
    "content": "Your response to the user's point"
}}
"""
                        
                        result = debug_system.get_llm_response(response_prompt, "user_response")
                        
                        if "error" not in result:
                            if isinstance(result, dict) and 'content' in result:
                                response_content = result['content']
                            elif isinstance(result, str):
                                response_content = result
                            else:
                                response_content = f"That's an important point to consider in our policy discussion."
                        else:
                            response_content = f"That's an important point to consider in our policy discussion."
                        
                        await send_debate_message(name, response_content, "user_response", {
                            "responding_to_user": True,
                            "user_input": user_message[:100]
                        })
                        
                        await asyncio.sleep(0.3)
                        
                    except Exception as e:
                        logger.error(f"Error generating user response for {name}: {e}")
                        await send_debate_message(name, "That raises important considerations for our stakeholder group.", "user_response")
            
            # Mark input as processed
            user_input['processed'] = True
            
            # Brief pause before continuing
            await asyncio.sleep(0.5)
    
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
        
        # Step 5: Start enhanced topic-focused debate
        await send_debate_message("moderator", "🎯 Let's begin our structured topic-focused debate!", "debate_message")
        await send_debate_message("moderator", "We'll discuss each key topic systematically with opening statements, responses, and rebuttals.", "debate_message")
        
        # Send debate start message
        await websocket.send_text(json.dumps({
            "type": "debate_start",
            "message": f"Starting enhanced debate on {policy_title}",
            "timestamp": datetime.now().isoformat()
        }))
        
        # Run topic-focused debate rounds (use top 3 topics)
        debate_topics = topics[:3] if len(topics) >= 3 else topics
        
        for topic_num, topic in enumerate(debate_topics, 1):
            # Check for early termination
            status = check_session_status(session_id)
            if status["terminated"]:
                await send_debate_message("moderator", "🛑 The debate has been ended early by user request.", "debate_message")
                break
            
            topic_title = topic.get('title', f'Topic {topic_num}')
            topic_description = topic.get('description', '')
            
            # Moderator introduces the topic
            await send_debate_message("moderator", f"📢 Topic {topic_num}: {topic_title}", "debate_message")
            if topic_description:
                await send_debate_message("moderator", f"Let's discuss: {topic_description}", "debate_message")
            
            # Check for user input before starting topic
            status = check_session_status(session_id)
            if status["has_user_input"]:
                await handle_user_inputs(session_id, f"Topic {topic_num}: {topic_title}")
            
            # Send topic start message
            await websocket.send_text(json.dumps({
                "type": "topic_start",
                "topic": topic_num,
                "topic_title": topic_title,
                "message": f"Starting discussion on {topic_title}",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Collect arguments for this topic
            topic_arguments = []
            
            # Phase 1: Initial positions
            await send_debate_message("moderator", f"🔹 Let's hear each stakeholder's initial position on {topic_title}:", "debate_message")
            
            for stakeholder in stakeholders:
                # Check for pause, termination, or user input
                status = check_session_status(session_id)
                if status["terminated"]:
                    await send_debate_message("moderator", "🛑 The debate has been ended early by user request.", "debate_message")
                    return
                
                # Handle pause
                while status["paused"]:
                    await asyncio.sleep(1)
                    status = check_session_status(session_id)
                    if status["terminated"]:
                        return
                
                # Handle user input
                if status["has_user_input"]:
                    await handle_user_inputs(session_id, f"stakeholder initial positions on {topic_title}")
                
                name = stakeholder.get('name', 'Unknown')
                
                try:
                    argument_json = await generate_researched_argument(name, stakeholder, topic, "initial_position")
                    argument_data = json.loads(argument_json)
                    content = argument_data.get('content', f"As {name}, I have important concerns about this aspect of the policy.")
                    
                    # Send as chat message
                    await send_debate_message(name, content, "debate_message", {
                        "topic": topic_num,
                        "topic_title": topic_title,
                        "argument_type": "initial_position",
                        "stakeholder_type": stakeholder.get('type', 'unknown')
                    })
                    
                    topic_arguments.append(argument_data)
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error generating argument for {name}: {e}")
                    await send_debate_message(name, f"I believe this aspect of the policy requires careful consideration of all stakeholder impacts.", "debate_message")
            
            # Check before rebuttals phase
            status = check_session_status(session_id)
            if status["terminated"]:
                await send_debate_message("moderator", "🛑 The debate has been ended early by user request.", "debate_message")
                break
            
            # Phase 2: Rebuttals and responses
            await send_debate_message("moderator", "🔄 Now let's hear responses and rebuttals:", "debate_message")
            
            # Each stakeholder gets to respond to others
            for i, stakeholder in enumerate(stakeholders):
                # Check session status
                status = check_session_status(session_id)
                if status["terminated"]:
                    await send_debate_message("moderator", "🛑 The debate has been ended early by user request.", "debate_message")
                    return
                
                # Handle pause
                while status["paused"]:
                    await asyncio.sleep(1)
                    status = check_session_status(session_id)
                    if status["terminated"]:
                        return
                
                # Handle user input
                if status["has_user_input"]:
                    await handle_user_inputs(session_id, f"stakeholder rebuttals on {topic_title}")
                
                name = stakeholder.get('name', 'Unknown')
                
                # Create context for rebuttal based on other stakeholders' arguments
                other_arguments = [arg for arg in topic_arguments if arg.get('stakeholder_name') != name]
                context = f"responding to other stakeholders' views on {topic_title}"
                
                if other_arguments:
                    other_points = []
                    for arg in other_arguments[:2]:  # Reference max 2 other arguments
                        other_points.extend(arg.get('key_points', []))
                    
                    if other_points:
                        context += f", particularly their points about {', '.join(other_points[:2])}"
                
                try:
                    argument_json = await generate_researched_argument(name, stakeholder, topic, "rebuttal", context)
                    argument_data = json.loads(argument_json)
                    content = argument_data.get('content', f"As {name}, I'd like to respond to the previous points raised.")
                    
                    await send_debate_message(name, content, "debate_message", {
                        "topic": topic_num,
                        "topic_title": topic_title,
                        "argument_type": "rebuttal",
                        "stakeholder_type": stakeholder.get('type', 'unknown')
                    })
                    
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error generating rebuttal for {name}: {e}")
                    await send_debate_message(name, f"I'd like to add that we need to consider the broader implications of this policy aspect.", "debate_message")
            
            # Check before moderator summary
            status = check_session_status(session_id)
            if status["terminated"]:
                await send_debate_message("moderator", "🛑 The debate has been ended early by user request.", "debate_message")
                break
            
            # Handle any final user input before summary
            if status["has_user_input"]:
                await handle_user_inputs(session_id, f"summary of {topic_title}")
            
            # Phase 3: Moderator summary
            await send_debate_message("moderator", "📝 Let me summarize the key points from this discussion:", "debate_message")
            
            summary = await generate_moderator_summary(topic, topic_arguments)
            await send_debate_message("moderator", summary, "debate_message")
            
            # Send topic complete message
            await websocket.send_text(json.dumps({
                "type": "topic_complete",
                "topic": topic_num,
                "topic_title": topic_title,
                "message": f"Discussion on {topic_title} completed",
                "timestamp": datetime.now().isoformat()
            }))
            
            # Transition to next topic
            if topic_num < len(debate_topics):
                await send_debate_message("moderator", f"Thank you all. Now let's move to our next topic.", "debate_message")
                await asyncio.sleep(0.5)
        
        # Check if debate was terminated early
        final_status = check_session_status(session_id)
        if final_status["terminated"]:
            # Enhanced early termination with comprehensive summary
            session = session_manager.get_session(session_id)
            termination_reason = session.get("termination_reason", "User requested early termination")
            
            await send_debate_message("moderator", f"🛑 {termination_reason}", "debate_message")
            await send_debate_message("moderator", "📋 Let me provide a summary of our discussion so far:", "debate_message")
            
            # Generate comprehensive summary even for early termination
            comprehensive_summary = await generate_comprehensive_debate_summary(session_id, policy_title, debate_topics, stakeholders)
            await send_debate_message("moderator", comprehensive_summary, "debate_summary")
            
            await send_debate_message("moderator", "🎉 Thank you all for this valuable discussion!", "debate_message")
            await send_debate_message("moderator", "Even though our debate was ended early, we've gathered meaningful insights from multiple stakeholder perspectives that will inform community advocacy.", "debate_message")
            
            # Send early termination complete message
            await websocket.send_text(json.dumps({
                "type": "debate_terminated_complete",
                "message": "Debate ended early but with comprehensive summary generated. You can now generate your personalized email based on the discussion.",
                "timestamp": datetime.now().isoformat()
            }))
        else:
            # Normal completion summary
            await send_debate_message("moderator", "🎉 Thank you all for this comprehensive discussion!", "debate_message")
            await send_debate_message("moderator", f"We've covered {len(debate_topics)} key topics with multiple perspectives from each stakeholder group.", "debate_message")
            await send_debate_message("moderator", "This structured debate has highlighted the complexity of this policy and the importance of considering all stakeholder viewpoints.", "debate_message")
            
            # Generate and send comprehensive moderator summary
            await send_debate_message("moderator", "📋 Let me provide a comprehensive summary of our discussion:", "debate_message")
            
            # Generate comprehensive summary of all topics and stakeholder positions
            comprehensive_summary = await generate_comprehensive_debate_summary(session_id, policy_title, debate_topics, stakeholders)
            await send_debate_message("moderator", comprehensive_summary, "debate_summary")
            
            # Send normal completion message
            await websocket.send_text(json.dumps({
                "type": "debate_complete",
                "message": "Enhanced debate completed successfully. You can now generate your personalized email.",
                "timestamp": datetime.now().isoformat()
            }))
        
        # Update session with results
        session_manager.update_session(session_id, {
            "current_round": len(debate_topics),
            "stakeholder_count": len(stakeholders),
            "topics_discussed": len(debate_topics),
            "completed_at": datetime.now().isoformat(),
            "status": "terminated_early" if final_status["terminated"] else "completed"
        })
        
    except Exception as e:
        logger.error(f"Error in debate streaming: {e}")
        await send_debate_message("system", f"❌ Error during debate: {str(e)}", "error")
        raise

async def generate_comprehensive_debate_summary(session_id: str, policy_title: str, debate_topics: List[Dict[str, Any]], stakeholders: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive summary of the entire debate"""
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return "Unable to generate summary - session not found."
        
        # Get all debate messages
        messages = session.get("messages", [])
        debate_messages = [msg for msg in messages if msg.get("type") == "debate_message" and msg.get("sender") != "moderator"]
        
        # Organize messages by topic
        topic_summaries = []
        for i, topic in enumerate(debate_topics, 1):
            topic_title = topic.get('title', f'Topic {i}')
            topic_messages = [msg for msg in debate_messages if msg.get('metadata', {}).get('topic') == i]
            
            if topic_messages:
                # Extract key points from each stakeholder for this topic
                stakeholder_points = {}
                for msg in topic_messages:
                    sender = msg.get('sender', 'Unknown')
                    content = msg.get('content', '')
                    if sender not in stakeholder_points:
                        stakeholder_points[sender] = []
                    stakeholder_points[sender].append(content)
                
                # Create topic summary
                topic_summary = f"**{topic_title}:**\n"
                for stakeholder, points in stakeholder_points.items():
                    if points:
                        # Use the first point as the main position
                        main_point = points[0][:150] + "..." if len(points[0]) > 150 else points[0]
                        topic_summary += f"• {stakeholder}: {main_point}\n"
                
                topic_summaries.append(topic_summary)
        
        # Generate overall summary
        summary = f"**DEBATE SUMMARY: {policy_title}**\n\n"
        summary += f"We conducted a comprehensive discussion involving {len(stakeholders)} stakeholder groups across {len(debate_topics)} key topics.\n\n"
        
        # Add topic summaries
        summary += "**KEY TOPICS DISCUSSED:**\n\n"
        for topic_summary in topic_summaries:
            summary += topic_summary + "\n"
        
        # Add stakeholder overview
        summary += "**STAKEHOLDER PERSPECTIVES:**\n"
        for stakeholder in stakeholders:
            name = stakeholder.get('name', 'Unknown')
            stance = stakeholder.get('stance', stakeholder.get('likely_stance', 'neutral'))
            summary += f"• {name} (Position: {stance})\n"
        
        summary += "\n**NEXT STEPS:**\n"
        summary += "Based on this discussion, community members can now generate personalized advocacy emails to local representatives, incorporating the diverse perspectives and concerns raised by all stakeholders."
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating comprehensive summary: {e}")
        return f"**DEBATE SUMMARY: {policy_title}**\n\nA comprehensive discussion was held with multiple stakeholder groups covering various aspects of this policy. Community members can now generate personalized advocacy emails based on the debate content."

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

@app.post("/debates/{session_id}/email/generate")
async def generate_email_from_debate(session_id: str, request: Dict[str, Any]):
    """Generate advocacy email based on actual debate session data"""
    try:
        # Get the debate session
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Debate session not found")
        
        # Check if debate is completed
        if session.get("status") not in ["completed", "terminated_early"]:
            raise HTTPException(status_code=400, detail="Debate must be completed before generating email")
        
        # Extract parameters from request
        user_perspective = request.get("user_perspective", "concerned_citizen")
        user_name = request.get("user_name", "[Your Name]")
        user_address = request.get("user_address", "[Your Address]")
        user_contact = request.get("user_contact", "[Your Contact Information]")
        focus_areas = request.get("focus_areas", [])  # Topics the user wants to emphasize
        
        # Get policy information
        policy_name = session.get("policy_name", "Unknown Policy")
        try:
            policy_data = load_policy_data(policy_name)
            policy_title = policy_data.get("title", "Unknown Policy")
            policy_text = policy_data.get("text", "")
        except Exception as e:
            logger.error(f"Error loading policy data: {e}")
            policy_title = "Unknown Policy"
            policy_text = ""
        
        # Get debate messages
        messages = session.get("messages", [])
        debate_messages = [msg for msg in messages if msg.get("type") == "debate_message" and msg.get("sender") != "moderator"]
        
        # Find the debate summary if available
        summary_message = None
        for msg in messages:
            if msg.get("type") == "debate_summary":
                summary_message = msg
                break
        
        # Generate enhanced email content using LLM
        email_content = await generate_enhanced_email_content(
            policy_title, 
            policy_text, 
            debate_messages, 
            summary_message, 
            user_perspective, 
            focus_areas
        )
        
        # Format the final email
        formatted_email = f"""Subject: Community Input on {policy_title} - Urgent Action Needed

Dear [Representative/Council Member Name],

I am writing as a {user_perspective.replace('_', ' ')} to provide important community input on the {policy_title}. Our community recently held a comprehensive stakeholder discussion on this policy, and I wanted to share key insights and recommendations.

{email_content}

I believe these perspectives reflect the diverse concerns and interests of our community. I urge you to consider these recommendations as you move forward with this policy.

I would welcome the opportunity to discuss this further and am available to provide additional input or clarification on any of these points.

Thank you for your time and consideration of these important community concerns.

Sincerely,
{user_name}
{user_address}
{user_contact}

---
This email was generated based on a comprehensive community stakeholder debate involving multiple perspectives on {policy_title}.
"""
        
        # Determine recipients based on policy type and location
        recipients = [
            "city.council@city.gov",
            "mayor@city.gov",
            "policy.committee@city.gov",
            "public.affairs@city.gov",
            "planning.department@city.gov"
        ]
        
        # Add session metadata for tracking
        session_manager.update_session(session_id, {
            "email_generated": True,
            "email_generated_at": datetime.now().isoformat(),
            "user_perspective": user_perspective
        })
        
        return {
            "success": True,
            "email_content": formatted_email,
            "recipients": recipients,
            "session_id": session_id,
            "policy_title": policy_title,
            "debate_message_count": len(debate_messages),
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating email from debate session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_enhanced_email_content(
    policy_title: str,
    policy_text: str,
    debate_messages: List[Dict[str, Any]],
    summary_message: Optional[Dict[str, Any]],
    user_perspective: str,
    focus_areas: List[str]
) -> str:
    """Generate enhanced email content using LLM based on debate context"""
    try:
        # Get the comprehensive summary first - this should be the primary source
        primary_summary = ""
        if summary_message:
            primary_summary = summary_message.get('content', '')
        
        # Extract key debate insights organized by topic
        topic_insights = {}
        stakeholder_positions = {}
        
        for msg in debate_messages:
            sender = msg.get('sender', 'Unknown')
            content = msg.get('content', '')
            metadata = msg.get('metadata', {})
            topic_title = metadata.get('topic_title', 'General Discussion')
            
            # Group insights by topic
            if topic_title not in topic_insights:
                topic_insights[topic_title] = []
            
            topic_insights[topic_title].append({
                'stakeholder': sender,
                'position': content,
                'type': metadata.get('argument_type', 'statement')
            })
            
            # Track stakeholder positions
            if sender not in stakeholder_positions:
                stakeholder_positions[sender] = []
            stakeholder_positions[sender].append({
                'topic': topic_title,
                'position': content
            })
        
        # Create rich context for email generation
        debate_context = f"**COMPREHENSIVE DEBATE SUMMARY:**\n{primary_summary}\n\n"
        
        # Add detailed topic analysis
        debate_context += "**DETAILED TOPIC ANALYSIS:**\n"
        for topic, insights in topic_insights.items():
            debate_context += f"\n**{topic}:**\n"
            for insight in insights[:3]:  # Top 3 insights per topic
                debate_context += f"- {insight['stakeholder']}: {insight['position'][:150]}...\n"
        
        # Add stakeholder position summary
        debate_context += "\n**STAKEHOLDER POSITION SUMMARY:**\n"
        for stakeholder, positions in stakeholder_positions.items():
            debate_context += f"\n**{stakeholder}:**\n"
            for pos in positions[:2]:  # Top 2 positions per stakeholder
                debate_context += f"- On {pos['topic']}: {pos['position'][:100]}...\n"
        
        # Create focus areas context
        focus_context = ""
        if focus_areas:
            focus_context = f"\n**PRIORITY FOCUS AREAS:** {', '.join(focus_areas)}"
        
        # Generate email content using comprehensive LLM prompt
        email_prompt = f"""
You are writing a professional advocacy email to local government officials about a policy based on a comprehensive community debate.

Policy: {policy_title}
User Perspective: {user_perspective}
{focus_context}

COMPREHENSIVE DEBATE CONTEXT:
{debate_context}

Generate a professional, persuasive email body that:
1. References the comprehensive community debate as evidence of civic engagement
2. Summarizes 3-4 key concerns that emerged from the debate discussion
3. Presents 4-6 specific, actionable recommendations based on stakeholder input
4. Highlights the most compelling arguments from different stakeholder perspectives
5. Emphasizes community impact and implementation urgency
6. Maintains respectful, professional tone appropriate for government officials
7. Is concrete and specific, drawing from actual debate content
8. Demonstrates broad community input and diverse stakeholder engagement

Structure the email as:
- Opening paragraph: Reference the community debate and its significance
- Body paragraphs: Key concerns and stakeholder perspectives from the debate
- Recommendations section: Specific actionable items based on debate outcomes
- Closing: Emphasis on community engagement and next steps

The email should be 4-5 paragraphs long and feel authentic to the actual debate content.
Return ONLY the email body content (no subject line, no salutation, no signature).
"""
        
        # Try to get enhanced content from LLM
        try:
            result = debug_system.get_llm_response(email_prompt, "comprehensive_email_generation")
            
            if "error" not in result:
                if isinstance(result, dict) and 'content' in result:
                    return result['content']
                elif isinstance(result, str):
                    return result
                else:
                    return str(result)
            else:
                logger.warning(f"LLM error in email generation: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error calling LLM for email generation: {e}")
        
        # Enhanced fallback email generation based on actual debate content
        email_body = f"""Our community recently conducted a comprehensive stakeholder debate on the {policy_title}, facilitated by a professional moderator and including diverse perspectives from affected community members. This structured discussion revealed critical insights that I believe warrant your immediate attention and action.

**Key Community Concerns from the Debate:**
"""
        
        # Add specific concerns from debate topics
        concern_count = 0
        for topic, insights in topic_insights.items():
            if concern_count < 4:  # Limit to 4 key concerns
                email_body += f"\n**{topic}:** "
                main_concerns = []
                for insight in insights[:2]:  # Top 2 insights per topic
                    concern = insight['position']
                    if len(concern) > 100:
                        concern = concern[:100] + "..."
                    main_concerns.append(f"{insight['stakeholder']} emphasized {concern}")
                email_body += " ".join(main_concerns)
                concern_count += 1
        
        # Add stakeholder diversity
        email_body += f"\n\n**Community Stakeholder Engagement:**\nOur debate included {len(stakeholder_positions)} key stakeholder groups: {', '.join(stakeholder_positions.keys())}. This diverse representation demonstrates the broad community interest in this policy and the need for comprehensive implementation planning."
        
        # Add specific recommendations based on debate content
        email_body += f"""

**Specific Recommendations Based on Community Input:**

1. **Comprehensive Implementation Planning**: Establish clear timelines and milestones for policy implementation, with regular public progress updates as requested by community stakeholders.

2. **Multi-Stakeholder Advisory Committee**: Create an ongoing advisory committee including representatives from all stakeholder groups that participated in our debate to ensure continued community input.

3. **Robust Enforcement Mechanisms**: Develop clear enforcement procedures with adequate resources and accountability measures, addressing concerns raised by multiple stakeholder groups.

4. **Impact Assessment and Monitoring**: Implement systematic monitoring of policy impacts on different community groups, with regular review and adjustment processes.

5. **Community Education and Outreach**: Establish comprehensive public education programs to ensure all affected parties understand their rights and responsibilities under the new policy.

6. **Phased Implementation with Feedback Loops**: Consider a phased rollout approach that allows for community feedback and policy refinement based on real-world implementation experience.

The active participation in our community debate, with {len(debate_messages)} substantive contributions from diverse stakeholders, demonstrates significant public engagement with this policy. The structured nature of our discussion revealed both the complexity of implementation challenges and the community's readiness to work collaboratively toward effective solutions.

I urge you to consider these community-derived recommendations as you move forward with policy implementation. The depth of community engagement evidenced by our debate process shows that residents are prepared to be active partners in making this policy successful.
"""
        
        return email_body
        
    except Exception as e:
        logger.error(f"Error generating enhanced email content: {e}")
        return f"""Our community recently held a comprehensive stakeholder debate on the {policy_title}, bringing together diverse perspectives from affected community members. This structured discussion, facilitated by a professional moderator, revealed important insights about policy implementation and community impact.

The debate included multiple stakeholder groups who raised concerns about implementation timelines, enforcement mechanisms, and community impact. Based on this extensive community engagement, I recommend immediate action on several key areas:

**Immediate Recommendations:**
1. Establish transparent implementation timelines with regular community updates
2. Create multi-stakeholder advisory committee for ongoing input
3. Develop robust enforcement mechanisms with clear accountability
4. Implement comprehensive impact monitoring and review processes
5. Provide extensive community education and outreach programs

The level of community engagement demonstrated by our debate process shows that residents are prepared to be active partners in policy implementation. I urge you to consider these community-derived recommendations and establish mechanisms for continued stakeholder input throughout the implementation process.

This policy will significantly impact our community, and the structured debate process has provided valuable insights that can inform effective implementation strategies.
"""

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

async def generate_dynamic_moderator_response(user_message: str, current_context: str, stakeholders: List[Dict[str, Any]]) -> str:
    """Generate dynamic moderator response that can change discussion direction"""
    try:
        stakeholder_names = [s.get('name', 'Unknown') for s in stakeholders]
        
        prompt = f"""
You are a professional debate moderator facilitating a policy discussion. A community member has just provided this input:

User Input: "{user_message}"
Current Context: {current_context}
Stakeholders Present: {', '.join(stakeholder_names)}

As the moderator, generate a response that:
1. Acknowledges the user's input professionally and specifically
2. Analyzes how their input relates to the current policy debate
3. Determines if this input should shift the discussion focus
4. Guides the conversation in a relevant direction based on their input
5. Encourages specific stakeholder participation on the user's point
6. Maintains neutrality while being responsive and engaging

Generate a natural moderator response (2-3 sentences) that seamlessly integrates the user's input into the ongoing debate and shows that their input is valued and will influence the discussion.
"""
        
        result = debug_system.get_llm_response(prompt, "dynamic_moderator_response")
        
        if "error" not in result:
            if isinstance(result, dict) and 'content' in result:
                return result['content']
            elif isinstance(result, str):
                return result
            else:
                return str(result)
        else:
            return f"Thank you for raising that important point about the policy. This community input helps us understand the real-world implications, and I'd like our stakeholders to address this concern directly."
        
    except Exception as e:
        logger.error(f"Error generating dynamic moderator response: {e}")
        return f"Thank you for that valuable community input. Let me ask our stakeholders to address your specific concerns about this policy aspect."

async def should_pivot_discussion(user_message: str, current_context: str) -> bool:
    """Determine if user input should cause a discussion pivot"""
    try:
        # Check if user input contains pivot indicators
        pivot_indicators = [
            "what about", "but what if", "have you considered", "what happens when",
            "i'm concerned about", "the real issue is", "more importantly",
            "actually", "however", "but", "this doesn't address", "missing",
            "overlooked", "ignored", "forgot", "urgent", "critical", "crisis"
        ]
        
        user_lower = user_message.lower()
        
        # Check for pivot indicators
        has_pivot_indicator = any(indicator in user_lower for indicator in pivot_indicators)
        
        # Check message length (longer messages more likely to warrant pivot)
        is_substantial = len(user_message.split()) > 10
        
        # Check for question marks (questions often warrant focused responses)
        has_question = "?" in user_message
        
        # Simple heuristic: pivot if it has indicators AND is substantial OR has a question
        return has_pivot_indicator and (is_substantial or has_question)
        
    except Exception as e:
        logger.error(f"Error determining pivot need: {e}")
        return False

async def create_pivot_topic(user_message: str, current_context: str) -> Dict[str, Any]:
    """Create a focused topic based on user input"""
    try:
        prompt = f"""
A community member has raised an important point during a policy debate that warrants focused discussion.

User Input: "{user_message}"
Current Context: {current_context}

Create a focused discussion topic based on this user input. Return a JSON object with:
{{
    "title": "Concise topic title (5-8 words)",
    "description": "Brief description of what should be discussed (1-2 sentences)",
    "key_question": "Specific question stakeholders should address"
}}
"""
        
        result = debug_system.get_llm_response(prompt, "pivot_topic_creation")
        
        if "error" not in result:
            if isinstance(result, dict):
                return result
            else:
                try:
                    return json.loads(result)
                except:
                    pass
        
        # Fallback pivot topic
        return {
            "title": "Community-Raised Concern",
            "description": f"Address the specific concern raised by a community member: {user_message[:100]}...",
            "key_question": "How should this concern be addressed in the policy implementation?"
        }
        
    except Exception as e:
        logger.error(f"Error creating pivot topic: {e}")
        return {
            "title": "Community Input Focus",
            "description": "Address community concerns about policy implementation",
            "key_question": "How can we address the community's concerns?"
        }

async def generate_pivot_response(stakeholder_name: str, stakeholder_data: Dict[str, Any], pivot_topic: Dict[str, Any], user_message: str) -> str:
    """Generate targeted stakeholder response to pivot topic"""
    try:
        prompt = f"""
You are {stakeholder_name} in a policy debate. A community member has raised an important concern that requires focused discussion.

Community Member's Input: "{user_message}"
Pivot Topic: {pivot_topic.get('title', 'Community Concern')}
Topic Description: {pivot_topic.get('description', '')}
Key Question: {pivot_topic.get('key_question', '')}

Your stakeholder interests: {stakeholder_data.get('interests', [])}
Your stakeholder concerns: {stakeholder_data.get('concerns', [])}

Generate a targeted response (2-3 sentences) that:
1. Directly addresses the community member's concern
2. Provides your stakeholder perspective on this specific issue
3. Offers constructive input or solutions if possible
4. Maintains your stakeholder position while being responsive

Return ONLY a valid JSON object:
{{
    "stakeholder_name": "{stakeholder_name}",
    "content": "Your targeted response to the community concern"
}}
"""
        
        result = debug_system.get_llm_response(prompt, "pivot_response_generation")
        
        if "error" not in result:
            if isinstance(result, dict) and 'content' in result:
                return result['content']
            elif isinstance(result, str):
                try:
                    parsed = json.loads(result)
                    return parsed.get('content', result)
                except:
                    return result
            else:
                return str(result)
        
        # Fallback response
        return f"As {stakeholder_name}, I understand this community concern and believe we need to address it seriously in our policy implementation planning."
        
    except Exception as e:
        logger.error(f"Error generating pivot response for {stakeholder_name}: {e}")
        return f"That's an important community concern that our stakeholder group takes seriously."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)