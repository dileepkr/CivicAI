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

# Import policy discovery agent
from policy_discovery.agent import PolicyDiscoveryAgent
from policy_discovery.models import UserContext, RegulationTiming, PolicyDiscoveryResponse

# Import A2A protocol integration
from api.a2a_integration import (
    CivicAIA2AAgent, A2ACoordinator, get_coordinator, 
    cleanup_coordinator, is_a2a_available
)

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

# Initialize policy discovery agent
try:
    policy_discovery_agent = PolicyDiscoveryAgent()
    logger.info("✅ Policy discovery agent initialized successfully")
except Exception as e:
    logger.error(f"⚠️  Policy discovery agent initialization failed: {e}")
    policy_discovery_agent = None

async def discover_policy_data(query: str, user_context: UserContext = None) -> Dict[str, Any]:
    """Discover policy data using the policy discovery agent"""
    if not policy_discovery_agent:
        # Fallback to loading from test_data if agent not available
        return load_policy_data_fallback(query)
    
    try:
        # If no user context provided, create a focused one based on query
        if not user_context:
            user_context = UserContext(
                location="San Francisco, CA",
                stakeholder_roles=["citizen"],  # Generic role
                interests=[query],  # Use exact query
                regulation_timing=RegulationTiming.ALL
            )
        
        # Use direct search with user's exact query to avoid predefined keywords
        search_engine = policy_discovery_agent.search_engine
        
        # Search with the exact user query
        search_results = await search_engine.search_policies(
            query=query,
            domains=[],  # Let Exa find the best sources
            max_results=10
        )
        
        # Create a simple result structure
        if search_results:
            top_result = search_results[0]
            # Create a policy result manually - determine level from URL
            from policy_discovery.models import GovernmentLevel
            
            url = top_result.get("url", "")
            if any(domain in url for domain in ["congress.gov", "regulations.gov", "federalregister.gov"]):
                level = GovernmentLevel.FEDERAL
            elif any(domain in url for domain in ["ca.gov", "calmatters"]):
                level = GovernmentLevel.STATE  
            elif any(domain in url for domain in ["sf.gov", "sfplanning"]):
                level = GovernmentLevel.LOCAL
            else:
                level = GovernmentLevel.FEDERAL  # Default
                
            policy_result = policy_discovery_agent._create_policy_result(top_result, level)
            
            if policy_result:
                discovery_result = type('MockResult', (), {
                    'priority_ranking': [policy_result],
                    'total_found': len(search_results)
                })()
            else:
                raise ValueError("Could not create policy result")
        else:
            raise ValueError("No search results found")
        
        # Get the top priority policy
        if discovery_result.priority_ranking:
            top_policy = discovery_result.priority_ranking[0]
            
            # Format the response using the agent's formatting method
            policy_response = await policy_discovery_agent.format_policy_response(
                user_context, top_policy
            )
            
            return {
                "id": top_policy.url.split("/")[-1] or query,
                "title": policy_response.policy_document.title,
                "date": top_policy.last_updated.isoformat() if top_policy.last_updated else "Unknown Date",
                "summary": top_policy.summary,
                "relevance": "high",
                "text": policy_response.policy_document.text,
                "url": top_policy.url,
                "government_level": top_policy.government_level.value,
                "domain": top_policy.domain.value,
                "confidence_score": top_policy.confidence_score
            }
        else:
            raise ValueError("No policies found")
            
    except Exception as e:
        logger.error(f"Policy discovery failed: {e}")
        # Fallback to test data
        return load_policy_data_fallback(query)

def load_policy_data_fallback(policy_name: str) -> Dict[str, Any]:
    """Fallback method to load policy data from test_data directory"""
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
    """Get available policies using policy discovery"""
    try:
        policies = []
        
        # Try to use policy discovery agent first
        if policy_discovery_agent:
            try:
                # Create a minimal user context for general policy discovery
                user_context = UserContext(
                    location="San Francisco, CA",
                    stakeholder_roles=["citizen"],
                    interests=["policy"],  # Very generic interest
                    regulation_timing=RegulationTiming.ALL
                )
                
                # Use a simple general search instead of full discovery to avoid keyword expansion
                search_engine = policy_discovery_agent.search_engine
                search_results = await search_engine.search_policies(
                    query="government policy regulations",
                    domains=[],
                    max_results=10
                )
                
                # Create mock discovery result
                from policy_discovery.models import GovernmentLevel
                discovery_result = type('MockResult', (), {'priority_ranking': []})()
                
                for item in search_results:
                    url = item.get("url", "")
                    if any(domain in url for domain in ["congress.gov", "regulations.gov"]):
                        level = GovernmentLevel.FEDERAL
                    elif any(domain in url for domain in ["ca.gov", "calmatters"]):
                        level = GovernmentLevel.STATE  
                    elif any(domain in url for domain in ["sf.gov", "sfplanning"]):
                        level = GovernmentLevel.LOCAL
                    else:
                        level = GovernmentLevel.FEDERAL
                        
                    policy = policy_discovery_agent._create_policy_result(item, level)
                    if policy:
                        discovery_result.priority_ranking.append(policy)
                
                # Convert discovered policies to API format
                for policy_result in discovery_result.priority_ranking[:10]:  # Limit to top 10
                    policy_data = {
                        "id": policy_result.url.split("/")[-1] or f"policy_{len(policies)}",
                        "title": policy_result.title,
                        "date": policy_result.last_updated.isoformat() if policy_result.last_updated else "Unknown Date",
                        "summary": policy_result.summary,
                        "relevance": "high" if policy_result.confidence_score > 0.7 else "medium",
                        "text": policy_result.content_preview or policy_result.summary
                    }
                    policies.append(PolicyResponse(**policy_data))
                    
                if policies:
                    return policies
                    
            except Exception as e:
                logger.error(f"Policy discovery failed, falling back to test data: {e}")
        
        # Fallback to test data if policy discovery fails or no agent available
        test_data_dir = project_root / "test_data"
        if test_data_dir.exists():
            for file in test_data_dir.glob("*.json"):
                policy_name = file.stem
                try:
                    policy_data = load_policy_data_fallback(policy_name)
                    policies.append(PolicyResponse(**policy_data))
                except Exception as e:
                    logger.error(f"Error loading policy {policy_name}: {e}")
        
        return policies
    except Exception as e:
        logger.error(f"Error getting policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/policies/{policy_id}", response_model=PolicyResponse)
async def get_policy(policy_id: str):
    """Get specific policy by ID using policy discovery"""
    try:
        # Try to discover policy using the ID as search query
        policy_data = await discover_policy_data(policy_id)
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
            policy_data = await discover_policy_data(request.policy_name)
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

async def run_debate_with_streaming(session_id: str, session: Dict[str, Any], websocket: WebSocket):
    """Run debate with real-time streaming using A2A protocol"""
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
        
        # Clean up A2A coordinator
        cleanup_coordinator(session_id)
        
    except Exception as e:
        logger.error(f"Error running debate for session {session_id}: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Debate failed: {str(e)}"
        }))
        session_manager.update_session(session_id, {"status": "error"})
        
        # Clean up A2A coordinator on error too
        cleanup_coordinator(session_id)

async def stream_debate_process(session_id: str, debate_system, policy_name: str, websocket: WebSocket):
    """Stream the debate process with real-time updates using A2A protocol"""
    
    # Initialize A2A coordinator for this session
    coordinator = get_coordinator(session_id)
    coordinator.add_websocket(websocket)
    
    # Create A2A agents for the debate
    moderator_agent = CivicAIA2AAgent(
        agent_id="moderator",
        agent_type="moderator",
        role="Debate Moderator",
        capabilities=["facilitate_debate", "manage_turns", "summarize"]
    )
    
    policy_agent = CivicAIA2AAgent(
        agent_id="policy_analyst",
        agent_type="analyst",
        role="Policy Analyst",
        capabilities=["analyze_policy", "provide_context", "fact_check"]
    )
    
    # Register agents with coordinator
    coordinator.register_agent(moderator_agent)
    coordinator.register_agent(policy_agent)
    
    # Custom message handler for streaming with A2A
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
        
        # Send via A2A protocol if available, otherwise WebSocket
        if sender in ["moderator", "policy_analyst"]:
            await coordinator.broadcast_message(
                sender_id=sender,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
        else:
            # Send via WebSocket for non-agent messages
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
        
        # Load policy data using discovery agent
        user_context = UserContext(
            location=user_location,
            stakeholder_roles=stakeholder_roles,
            interests=interests,
            regulation_timing=RegulationTiming.ALL
        )
        policy_data = await discover_policy_data(policy_name, user_context)
        
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
                # Parse keywords from prompt at the beginning
                keywords = [kw.strip().lower() for kw in prompt.lower().split() if len(kw.strip()) > 1]
                
                # Send initial status
                yield f"data: {json.dumps({'type': 'status', 'message': 'Initializing policy search...', 'step': 1, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 1: Search local policies
                yield f"data: {json.dumps({'type': 'status', 'message': 'Searching local policy database...', 'step': 2, 'total_steps': 4})}\n\n"
                await asyncio.sleep(0.1)
                
                local_policies = []
                
                # Try to use policy discovery agent for search
                if policy_discovery_agent:
                    try:
                        # Create focused user context based only on search prompt
                        user_context = UserContext(
                            location="San Francisco, CA",
                            stakeholder_roles=["citizen"],  # Generic role
                            interests=[prompt],  # Use the exact search prompt, not keywords
                            regulation_timing=RegulationTiming.ALL
                        )
                        
                        # Use direct search with exact prompt to avoid keyword expansion
                        search_engine = policy_discovery_agent.search_engine
                        search_results = await search_engine.search_policies(
                            query=prompt,
                            domains=[],  # Let Exa find relevant sources
                            max_results=max_results
                        )
                        
                        # Convert search results to policy format
                        from policy_discovery.models import GovernmentLevel
                        discovery_result = type('MockResult', (), {'priority_ranking': []})()
                        
                        for item in search_results:
                            url = item.get("url", "")
                            if any(domain in url for domain in ["congress.gov", "regulations.gov"]):
                                level = GovernmentLevel.FEDERAL
                            elif any(domain in url for domain in ["ca.gov", "calmatters"]):
                                level = GovernmentLevel.STATE  
                            elif any(domain in url for domain in ["sf.gov", "sfplanning"]):
                                level = GovernmentLevel.LOCAL
                            else:
                                level = GovernmentLevel.FEDERAL
                                
                            policy = policy_discovery_agent._create_policy_result(item, level)
                            if policy:
                                discovery_result.priority_ranking.append(policy)
                        
                        for policy_result in discovery_result.priority_ranking[:max_results]:
                            local_policies.append({
                                "id": policy_result.url.split("/")[-1] or f"discovered_{len(local_policies)}",
                                "title": policy_result.title,
                                "summary": policy_result.summary,
                                "date": policy_result.last_updated.isoformat() if policy_result.last_updated else "Unknown",
                                "url": policy_result.url,
                                "government_level": policy_result.government_level.value,
                                "domain": policy_result.domain.value,
                                "relevance_score": policy_result.confidence_score,
                                "matched_keywords": keywords
                            })
                        
                        if local_policies:
                            # Skip fallback if we found policies via discovery
                            yield f"data: {json.dumps({'type': 'status', 'message': f'Found {len(local_policies)} policies via discovery', 'step': 3, 'total_steps': 4})}\n\n"
                            await asyncio.sleep(0.1)
                        
                    except Exception as e:
                        logger.error(f"Policy discovery search failed: {e}")
                
                # Fallback to test data if discovery didn't find anything or failed
                if not local_policies:
                    test_data_dir = project_root / "test_data"
                    if test_data_dir.exists():
                        for file in test_data_dir.glob("*.json"):
                            policy_name = file.stem
                            try:
                                policy_data = load_policy_data_fallback(policy_name)
                                
                                # Enhanced search logic - search in title, summary, and policy text
                                search_text = f"{policy_data['title']} {policy_data['summary']} {policy_data['text'][:2000]}".lower()
                                
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
                if not local_policies:
                    test_data_dir = project_root / "test_data"
                    if test_data_dir.exists():
                        for file in test_data_dir.glob("*.json"):
                            policy_name = file.stem
                            try:
                                policy_data = load_policy_data_fallback(policy_name)
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
                "human_system": human_system is not None,
                "policy_discovery_agent": policy_discovery_agent is not None,
                "a2a_protocol": is_a2a_available()
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

@app.get("/debates/{session_id}/a2a-info")
async def get_a2a_session_info(session_id: str):
    """Get A2A protocol session information"""
    try:
        coordinator = get_coordinator(session_id)
        session_info = coordinator.get_session_info()
        return {
            "success": True,
            "session_info": session_info,
            "a2a_available": is_a2a_available()
        }
    except Exception as e:
        logger.error(f"Error getting A2A session info for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/debates/{session_id}/a2a-message")
async def send_a2a_message(session_id: str, request: Dict[str, Any]):
    """Send message via A2A protocol"""
    try:
        sender_id = request.get("sender_id")
        recipient_id = request.get("recipient_id")
        content = request.get("content")
        message_type = request.get("message_type", "direct")
        metadata = request.get("metadata", {})
        
        if not all([sender_id, content]):
            raise HTTPException(status_code=400, detail="sender_id and content are required")
        
        coordinator = get_coordinator(session_id)
        
        if recipient_id:
            # Direct message
            success = await coordinator.send_direct_message(
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
        else:
            # Broadcast message
            success = await coordinator.broadcast_message(
                sender_id=sender_id,
                content=content,
                message_type=message_type,
                metadata=metadata
            )
        
        return {
            "success": success,
            "message": "Message sent successfully" if success else "Failed to send message"
        }
        
    except Exception as e:
        logger.error(f"Error sending A2A message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)