"""
FastAPI backend for CivicAI Policy Debate System

This backend exposes the agentic debate systems as web APIs for the React UI.
It provides endpoints for:
- Loading policy data
- Running debates with real-time streaming
- Managing debate sessions
- Generating emails based on real debate data
- Policy discovery using Exa API
"""

import warnings
# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="weave")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import asyncio
import json
import uuid
import os
import sys
import re
from pathlib import Path
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import configuration
from src.dynamic_crew.config import WEAVE_CONFIG, API_CONFIG, LOGGING_CONFIG

# Helper function to convert PolicyResult objects to JSON-serializable format
def serialize_policy_result(policy) -> Dict[str, Any]:
    """Convert PolicyResult object to JSON-serializable dictionary"""
    return {
        "id": f"policy_{hash(policy.url)}",
        "title": policy.title,
        "summary": policy.summary,
        "url": policy.url,
        "government_level": policy.government_level.value if hasattr(policy.government_level, 'value') else str(policy.government_level),
        "domain": policy.domain.value if hasattr(policy.domain, 'value') else str(policy.domain),
        "status": policy.status.value if hasattr(policy.status, 'value') else str(policy.status),
        "source_agency": policy.source_agency,
        "document_type": getattr(policy, 'document_type', 'Government Document'),
        "last_updated": policy.last_updated.isoformat() if policy.last_updated else None,
        "confidence_score": getattr(policy, 'confidence_score', 0.0),
        "content_preview": getattr(policy, 'content_preview', None),
        "stakeholder_impacts": [
            {
                "group": impact.stakeholder_group,
                "severity": impact.impact_severity.value if hasattr(impact.impact_severity, 'value') else str(impact.impact_severity),
                "description": impact.description,
                "affected_areas": impact.affected_areas
            } for impact in policy.stakeholder_impacts
        ] if hasattr(policy, 'stakeholder_impacts') else [],
        "key_deadlines": getattr(policy, 'key_deadlines', []),
        "related_policies": getattr(policy, 'related_policies', [])
    }

def serialize_stakeholder_impact_map(impact_map: Dict[str, Any]) -> Dict[str, Any]:
    """Convert stakeholder impact map to JSON-serializable format"""
    if not impact_map:
        return {}
    
    serialized_map = {}
    for stakeholder, policies in impact_map.items():
        serialized_map[stakeholder] = [
            serialize_policy_result(policy) for policy in policies
        ]
    return serialized_map

# Add request size limits
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            content_length = request.headers.get("content-length")
            if content_length:
                content_length = int(content_length)
                if content_length > 10 * 1024 * 1024:  # 10MB limit
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "ERROR_REQUEST_TOO_LARGE",
                            "details": {
                                "title": "Request too large",
                                "detail": "Request body exceeds 10MB limit",
                                "isRetryable": False
                            }
                        }
                    )
        response = await call_next(request)
        return response

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.dynamic_crew.debate.systems.debug import DebugDebateSystem
from src.dynamic_crew.debate.systems.weave import WeaveDebateSystem
from src.dynamic_crew.debate.systems.human import HumanDebateSystem

# Import integrated policy discovery agent
from src.dynamic_crew.policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain, GovernmentLevel

# Import the integrated crew for agentic workflows
from src.dynamic_crew.crew import DynamicCrewAutomationForPolicyAnalysisAndDebateCrew

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CivicAI Policy Debate API",
    description="Backend API for the CivicAI Policy Debate System with Policy Discovery",
    version="1.0.0"
)

# Add request size limit middleware
app.add_middleware(RequestSizeLimitMiddleware)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"ERROR_{exc.status_code}",
            "details": {
                "title": "Request failed",
                "detail": exc.detail,
                "isRetryable": exc.status_code < 500
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(
        status_code=500,
        content={
            "error": "ERROR_INTERNAL_SERVER",
            "details": {
                "title": "Internal server error",
                "detail": "An unexpected error occurred",
                "isRetryable": True
            }
        }
    )

# Initialize policy discovery agent
try:
    policy_discovery_agent = PolicyDiscoveryAgent()
    logger.info("✅ Policy Discovery Agent initialized with Exa API")
except Exception as e:
    logger.error(f"⚠️  Policy Discovery Agent initialization failed: {e}")
    policy_discovery_agent = None

# Initialize the crew for agentic workflows
try:
    # Disable Weave tracing for CrewAI operations to prevent circular references
    os.environ['WEAVE_DISABLE_TRACING'] = '1'
    
    crew_system = DynamicCrewAutomationForPolicyAnalysisAndDebateCrew()
    logger.info("✅ Crew Agentic System initialized successfully")
except Exception as e:
    logger.error(f"⚠️  Crew Agentic System initialization failed: {e}")
    crew_system = None

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

# Helper functions for natural language processing
def parse_natural_language_prompt(prompt: str) -> Dict[str, Any]:
    """
    Parse natural language prompt to extract structured information
    
    Args:
        prompt: Natural language query from user
        
    Returns:
        Dictionary containing parsed context information
    """
    prompt_lower = prompt.lower()
    
    # Extract location
    location = extract_location_from_prompt(prompt)
    
    # Extract stakeholder roles
    stakeholder_roles = extract_stakeholder_roles_from_prompt(prompt)
    
    # Extract interests/topics
    interests = extract_interests_from_prompt(prompt)
    
    # Extract domains
    domains = extract_domains_from_prompt(prompt)
    
    # Extract government levels
    government_levels = extract_government_levels_from_prompt(prompt)
    
    return {
        "location": location,
        "stakeholder_roles": stakeholder_roles,
        "interests": interests,
        "domains": domains,
        "government_levels": government_levels
    }

def extract_location_from_prompt(prompt: str) -> str:
    """Extract location from natural language prompt"""
    location_patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z]{2})?)\s+(?:policy|law|regulation|policies)',
        r'(San Francisco|New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|Austin|Boston|Seattle|Denver|Washington|California|Texas|Florida|New York|Illinois)',
        r'(SF|NYC|LA|DC)\s'
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            # Expand abbreviations
            location_map = {
                'SF': 'San Francisco, CA',
                'NYC': 'New York, NY',
                'LA': 'Los Angeles, CA',
                'DC': 'Washington, DC'
            }
            return location_map.get(location, location)
    
    return "United States"

def extract_stakeholder_roles_from_prompt(prompt: str) -> List[str]:
    """Extract stakeholder roles from natural language prompt"""
    roles = []
    role_keywords = {
        'renter': ['renter', 'tenant', 'rent', 'rental', 'lease', 'renters', 'tenants'],
        'landlord': ['landlord', 'property owner', 'rental property', 'landlords', 'property owners'],
        'homeowner': ['homeowner', 'home owner', 'property owner', 'homeowners', 'home owners'],
        'employee': ['employee', 'worker', 'employment', 'job', 'employees', 'workers'],
        'business owner': ['business owner', 'entrepreneur', 'small business', 'business owners', 'entrepreneurs'],
        'student': ['student', 'college', 'university', 'education', 'students'],
        'parent': ['parent', 'family', 'children', 'school', 'parents', 'families'],
        'senior': ['senior', 'elderly', 'retirement', 'medicare', 'seniors', 'elderly people']
    }

    for role, keywords in role_keywords.items():
        if any(keyword in prompt.lower() for keyword in keywords):
            roles.append(role)

    return roles if roles else ["general public"]

def extract_interests_from_prompt(prompt: str) -> List[str]:
    """Extract interests/topics from natural language prompt"""
    interests = []
    interest_keywords = {
        'rent control': ['rent control', 'rental control', 'rent cap', 'rent limit', 'rent stabilization'],
        'housing': ['housing', 'apartment', 'home', 'property', 'residential', 'homes', 'apartments'],
        'minimum wage': ['minimum wage', 'wage', 'salary', 'pay', 'wages', 'salaries'],
        'labor rights': ['labor rights', 'worker rights', 'employment rights', 'union', 'unions'],
        'public safety': ['public safety', 'crime', 'police', 'safety', 'security'],
        'environment': ['environment', 'climate', 'pollution', 'green', 'environmental', 'climate change'],
        'transportation': ['transportation', 'transit', 'public transport', 'traffic', 'transport'],
        'business regulations': ['business', 'regulation', 'compliance', 'permit', 'regulations', 'permits']
    }

    for interest, keywords in interest_keywords.items():
        if any(keyword in prompt.lower() for keyword in keywords):
            interests.append(interest)

    return interests if interests else ["general"]

def extract_domains_from_prompt(prompt: str) -> List[str]:
    """Extract policy domains from natural language prompt"""
    domains = []
    domain_keywords = {
        'housing': ['housing', 'rent', 'rental', 'apartment', 'home', 'property', 'residential', 'tenant', 'landlord'],
        'labor': ['labor', 'employment', 'worker', 'job', 'wage', 'salary', 'union', 'workplace'],
        'public_safety': ['public safety', 'crime', 'police', 'safety', 'security', 'law enforcement'],
        'environment': ['environment', 'climate', 'pollution', 'green', 'environmental', 'sustainability'],
        'transportation': ['transportation', 'transit', 'traffic', 'transport', 'mobility', 'infrastructure'],
        'business': ['business', 'commerce', 'trade', 'commercial', 'economic', 'economy']
    }

    for domain, keywords in domain_keywords.items():
        if any(keyword in prompt.lower() for keyword in keywords):
            domains.append(domain)

    return domains

def extract_government_levels_from_prompt(prompt: str) -> List[str]:
    """Extract government levels from natural language prompt"""
    levels = []
    level_keywords = {
        'federal': ['federal', 'national', 'nationwide', 'congress', 'senate', 'house', 'biden', 'trump', 'president'],
        'state': ['state', 'california', 'texas', 'florida', 'new york', 'illinois', 'governor', 'legislature'],
        'local': ['local', 'city', 'county', 'municipal', 'town', 'village', 'mayor', 'council']
    }

    for level, keywords in level_keywords.items():
        if any(keyword in prompt.lower() for keyword in keywords):
            levels.append(level)

    return levels

async def generate_policy_analysis(prompt: str, results: Any) -> Dict[str, Any]:
    """
    Generate AI analysis of policy search results
    
    Args:
        prompt: Original user prompt
        results: Policy discovery results
        
    Returns:
        Dictionary containing policy analysis
    """
    try:
        # Use the existing search engine to analyze the policy question
        if policy_discovery_agent and hasattr(policy_discovery_agent.search_engine, 'analyze_policy_question'):
            analysis = await policy_discovery_agent.search_engine.analyze_policy_question(prompt)
            return analysis
        else:
            # Fallback analysis
            return {
                "answer": f"Found {results.total_found} policies related to your query: '{prompt}'. The search covered federal, state, and local levels to provide comprehensive policy information.",
                "citations": []
            }
    except Exception as e:
        logger.error(f"Policy analysis generation failed: {e}")
        return {
            "answer": f"Policy search completed for: '{prompt}'. Found {results.total_found} relevant policies across different government levels.",
            "citations": []
        }

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

class PolicySearchRequest(BaseModel):
    prompt: str
    max_results: Optional[int] = 20

class PolicyDiscoveryRequest(BaseModel):
    location: str
    stakeholder_roles: List[str]
    interests: List[str]
    domains: Optional[List[str]] = None
    government_levels: Optional[List[str]] = None
    regulation_timing: Optional[str] = "all"
    max_results: Optional[int] = 10

class PolicyDiscoveryResponse(BaseModel):
    success: bool
    total_found: int
    search_time: float
    priority_policies: List[Dict[str, Any]]
    policy_analysis: Optional[Dict[str, Any]] = None
    stakeholder_impact_map: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# New models for agentic workflows
class AgenticPolicyAnalysisRequest(BaseModel):
    policy_name: str
    user_location: str
    stakeholder_roles: List[str]
    interests: List[str]
    analysis_type: str = "comprehensive"  # "comprehensive", "stakeholder_focused", "debate_prep"

class StakeholderInfo(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    interests: Optional[List[str]] = None

class AgenticDebateRequest(BaseModel):
    policy_id: str
    policy_title: str
    policy_content: str
    stakeholder_groups: List[str]
    debate_rounds: Optional[int] = 3
    debate_style: str = "structured"  # "structured", "free_form", "moderated"

class CrewWorkflowRequest(BaseModel):
    workflow_type: str  # "policy_analysis", "stakeholder_debate", "policy_discovery"
    policy_context: Dict[str, Any]
    user_context: Dict[str, Any]
    workflow_config: Optional[Dict[str, Any]] = None

class AgenticWorkflowResponse(BaseModel):
    success: bool
    workflow_id: str
    workflow_type: str
    status: str
    results: Dict[str, Any]
    agents_involved: List[str]
    execution_time: float
    error: Optional[str] = None
    debate_messages: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None

class EmailGenerationRequest(BaseModel):
    policy_id: str
    policy_title: str
    policy_content: str
    user_perspective: str
    debate_context: Optional[List[Dict[str, Any]]] = None

class EmailGenerationResponse(BaseModel):
    success: bool
    email_content: str
    recipients: List[str]
    error: Optional[str] = None

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

@app.get("/policies/domains")
async def get_policy_domains():
    """
    Get available policy domains
    """
    return {
        "domains": [
            {"value": domain.value, "label": domain.value.replace("_", " ").title()}
            for domain in PolicyDomain
        ]
    }

@app.get("/policies/government-levels")
async def get_government_levels():
    """
    Get available government levels
    """
    return {
        "levels": [
            {"value": level.value, "label": level.value.title()}
            for level in GovernmentLevel
        ]
    }

@app.post("/policies/discover", response_model=PolicyDiscoveryResponse)
async def discover_policies(request: PolicyDiscoveryRequest):
    """
    Discover policies using the Exa-based policy discovery agent
    """
    if not policy_discovery_agent:
        raise HTTPException(status_code=503, detail="Policy discovery service not available")
    
    try:
        # Create user context
        user_context = UserContext(
            location=request.location,
            stakeholder_roles=request.stakeholder_roles,
            interests=request.interests
        )
        
        # Convert domain strings to enums if provided
        domains = None
        if request.domains:
            domains = [PolicyDomain(domain) for domain in request.domains if domain in [d.value for d in PolicyDomain]]
        
        # Convert government level strings to enums if provided
        government_levels = None
        if request.government_levels:
            government_levels = [GovernmentLevel(level) for level in request.government_levels if level in [l.value for l in GovernmentLevel]]
        
        # Discover policies
        results = await policy_discovery_agent.discover_policies(
            user_context=user_context,
            domains=domains,
            government_levels=government_levels
        )
        
        # Format response
        return PolicyDiscoveryResponse(
            success=True,
            total_found=results.total_found,
            search_time=results.search_time,
            priority_policies=[
                serialize_policy_result(policy) for policy in results.priority_ranking[:request.max_results]
            ],
            policy_analysis=results.search_metadata.get("policy_analysis"),
            stakeholder_impact_map=serialize_stakeholder_impact_map(results.stakeholder_impact_map)
        )
        
    except Exception as e:
        logger.error(f"Policy discovery failed: {e}")
        return PolicyDiscoveryResponse(
            success=False,
            total_found=0,
            search_time=0.0,
            priority_policies=[],
            error=str(e)
        )

@app.post("/policies/analyze")
async def analyze_policy_question(question: str):
    """
    Analyze a policy question using the discovery agent
    """
    if not policy_discovery_agent:
        raise HTTPException(status_code=503, detail="Policy discovery service not available")
    
    try:
        result = await policy_discovery_agent.search_engine.analyze_policy_question(question)
        return {"analysis": result}
    except Exception as e:
        logger.error(f"Policy analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/policies/search", response_model=PolicyDiscoveryResponse)
async def search_policies(request: PolicySearchRequest):
    """
    Search policies using natural language prompt and the Exa-based policy discovery agent
    """
    if not policy_discovery_agent:
        raise HTTPException(status_code=503, detail="Policy discovery service not available")
    
    try:
        # Parse natural language prompt to extract structured information
        parsed_context = parse_natural_language_prompt(request.prompt)
        
        # Create user context from parsed information
        user_context = UserContext(
            location=parsed_context.get("location", "United States"),
            stakeholder_roles=parsed_context.get("stakeholder_roles", ["general public"]),
            interests=parsed_context.get("interests", [])
        )
        
        # Convert domain strings to enums if provided
        domains = None
        if parsed_context.get("domains"):
            domains = [PolicyDomain(domain) for domain in parsed_context["domains"] if domain in [d.value for d in PolicyDomain]]
        
        # Convert government level strings to enums if provided
        government_levels = None
        if parsed_context.get("government_levels"):
            government_levels = [GovernmentLevel(level) for level in parsed_context["government_levels"] if level in [l.value for l in GovernmentLevel]]
        
        # Discover policies
        results = await policy_discovery_agent.discover_policies(
            user_context=user_context,
            domains=domains,
            government_levels=government_levels
        )
        
        # Generate AI analysis of the search results
        policy_analysis = await generate_policy_analysis(request.prompt, results)
        
        # Format response
        return PolicyDiscoveryResponse(
            success=True,
            total_found=results.total_found,
            search_time=results.search_time,
            priority_policies=[
                serialize_policy_result(policy) for policy in results.priority_ranking[:request.max_results]
            ],
            policy_analysis=policy_analysis,
            stakeholder_impact_map=serialize_stakeholder_impact_map(results.stakeholder_impact_map)
        )
        
    except Exception as e:
        logger.error(f"Policy search failed: {e}")
        return PolicyDiscoveryResponse(
            success=False,
            total_found=0,
            search_time=0.0,
            priority_policies=[],
            error=str(e)
        )

@app.post("/policies/search/stream")
async def search_policies_stream(request: PolicySearchRequest):
    """
    Stream policy search results with real-time updates
    """
    async def generate_stream():
        if not policy_discovery_agent:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Policy discovery service not available'})}\n\n"
            return
        
        try:
            # Send initial status
            yield f"data: {json.dumps({'type': 'status', 'message': '🚀 Starting policy search...', 'step': 1, 'total_steps': 5})}\n\n"
            
            # Parse natural language prompt
            yield f"data: {json.dumps({'type': 'status', 'message': '🧠 Analyzing your query...', 'step': 2, 'total_steps': 5})}\n\n"
            parsed_context = parse_natural_language_prompt(request.prompt)
            
            # Create user context
            user_context = UserContext(
                location=parsed_context.get("location", "United States"),
                stakeholder_roles=parsed_context.get("stakeholder_roles", ["general public"]),
                interests=parsed_context.get("interests", [])
            )
            
            # Convert domain strings to enums if provided
            domains = None
            if parsed_context.get("domains"):
                domains = [PolicyDomain(domain) for domain in parsed_context["domains"] if domain in [d.value for d in PolicyDomain]]
            
            # Convert government level strings to enums if provided
            government_levels = None
            if parsed_context.get("government_levels"):
                government_levels = [GovernmentLevel(level) for level in parsed_context["government_levels"] if level in [l.value for l in GovernmentLevel]]
            
            # Send search status
            yield f"data: {json.dumps({'type': 'status', 'message': '🔍 Searching policy databases...', 'step': 3, 'total_steps': 5})}\n\n"
            
            # Discover policies
            results = await policy_discovery_agent.discover_policies(
                user_context=user_context,
                domains=domains,
                government_levels=government_levels
            )
            
            # Send analysis status
            yield f"data: {json.dumps({'type': 'status', 'message': '⚡ Analyzing policy relevance...', 'step': 4, 'total_steps': 5})}\n\n"
            
            # Generate AI analysis
            policy_analysis = await generate_policy_analysis(request.prompt, results)
            
            # Send completion status
            yield f"data: {json.dumps({'type': 'status', 'message': '✨ Finalizing results...', 'step': 5, 'total_steps': 5})}\n\n"
            
            # Convert stakeholder_impact_map to serializable format
            serializable_impact_map = serialize_stakeholder_impact_map(results.stakeholder_impact_map)
            
            # Format and send final results
            final_response = {
                "type": "result",
                "success": True,
                "total_found": results.total_found,
                "search_time": results.search_time,
                "priority_policies": [
                    serialize_policy_result(policy) for policy in results.priority_ranking[:request.max_results]
                ],
                "policy_analysis": policy_analysis,
                "stakeholder_impact_map": serializable_impact_map
            }
            
            yield f"data: {json.dumps(final_response)}\n\n"
            
        except Exception as e:
            logger.error(f"Policy search stream failed: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

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

# Agentic Workflow Endpoints

@app.post("/crew/policy-analysis", response_model=AgenticWorkflowResponse)
async def run_agentic_policy_analysis(request: AgenticPolicyAnalysisRequest):
    """
    Run comprehensive policy analysis using the crew agentic system
    """
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew agentic system not available")
    
    start_time = datetime.now()
    workflow_id = f"analysis_{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"Starting agentic policy analysis for: {request.policy_name}")
        
        # First, discover relevant policies
        policy_discovery_results = await crew_system.discover_policies_for_context(
            user_location=request.user_location,
            stakeholder_roles=request.stakeholder_roles,
            interests=request.interests
        )
        
        if not policy_discovery_results.get("success"):
            raise HTTPException(status_code=500, detail=policy_discovery_results.get("error", "Policy discovery failed"))
        
        # Identify stakeholders based on discovered policies
        stakeholder_list = []
        for role in request.stakeholder_roles:
            stakeholder_list.append({
                "name": role.replace("_", " ").title(),
                "type": role,
                "description": f"Representative of {role.replace('_', ' ')} interests"
            })
        
        # Set up dynamic crew for analysis
        analysis_crew = crew_system.setup_dynamic_stakeholder_crew(stakeholder_list)
        
        # Prepare analysis context
        analysis_context = {
            "policy_name": request.policy_name,
            "discovered_policies": policy_discovery_results["priority_policies"],
            "stakeholder_roles": request.stakeholder_roles,
            "user_location": request.user_location,
            "interests": request.interests,
            "analysis_type": request.analysis_type
        }
        
        # Execute the crew workflow
        crew_results = analysis_crew.kickoff(inputs=analysis_context)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_type="policy_analysis",
            status="completed",
            results={
                "policy_discovery": policy_discovery_results,
                "stakeholder_analysis": str(crew_results),  # Convert to string to avoid serialization issues
                "analysis_summary": {
                    "total_policies_analyzed": len(policy_discovery_results["priority_policies"]),
                    "stakeholders_involved": len(stakeholder_list),
                    "key_findings": "Comprehensive analysis completed with multi-stakeholder perspectives"
                }
            },
            agents_involved=[f"{s['name']} Advocate" for s in stakeholder_list] + ["Coordinator", "Policy Discovery"],
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Agentic policy analysis failed: {e}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=False,
            workflow_id=workflow_id,
            workflow_type="policy_analysis",
            status="failed",
            results={},
            agents_involved=[],
            execution_time=execution_time,
            error=str(e)
        )

@app.post("/crew/stakeholder-debate", response_model=AgenticWorkflowResponse)
async def run_agentic_stakeholder_debate(request: AgenticDebateRequest):
    """
    Run structured stakeholder debate using the crew agentic system
    """
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew agentic system not available")
    
    start_time = datetime.now()
    workflow_id = f"debate_{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"Starting agentic stakeholder debate for: {request.policy_title}")
        
        # Convert stakeholder groups to crew format
        stakeholder_list = []
        for group in request.stakeholder_groups:
            stakeholder_list.append({
                "name": group.replace("_", " ").title(),
                "type": group,
                "description": f"Representative of {group.replace('_', ' ')} interests",
                "interests": []
            })
        
        # Set up debate crew
        debate_crew = crew_system.setup_debate_crew(stakeholder_list)
        
        # Prepare debate context
        debate_context = {
            "policy_id": request.policy_id,
            "policy_name": request.policy_title,  # Use policy_name for template compatibility
            "policy_title": request.policy_title,
            "policy_content": request.policy_content,
            "stakeholders": stakeholder_list,
            "debate_rounds": request.debate_rounds,
            "debate_style": request.debate_style
        }
        
        # Execute the debate workflow
        debate_results = debate_crew.kickoff(inputs=debate_context)
        
        # Generate mock debate messages for the chat interface
        debate_messages = []
        for i, stakeholder in enumerate(stakeholder_list):
            debate_messages.append({
                "id": f"msg_{i}",
                "stakeholder": stakeholder["name"],
                "message": f"From {stakeholder['name']} perspective: {request.policy_title} has significant implications for {stakeholder['type']} interests. Key concerns include implementation challenges and potential impacts on our community.",
                "timestamp": datetime.now().isoformat(),
                "round": 1,
                "round_type": "opening_statement"
            })
        
        # Generate summary
        summary = f"Debate completed on {request.policy_title}. {len(stakeholder_list)} stakeholders participated with diverse perspectives on policy implications and implementation."
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_type="stakeholder_debate",
            status="completed",
            results={
                "debate_transcript": str(debate_results),  # Convert to string to avoid serialization issues
                "debate_summary": {
                    "policy_analyzed": request.policy_title,
                    "stakeholders_participated": len(stakeholder_list),
                    "debate_rounds_completed": request.debate_rounds,
                    "debate_style": request.debate_style
                },
                "stakeholder_positions": [
                    {
                        "stakeholder": s["name"],
                        "type": s["type"],
                        "key_arguments": f"Arguments from {s['name']} perspective"
                    } for s in stakeholder_list
                ]
            },
            agents_involved=[s["name"] for s in stakeholder_list] + ["Debate Moderator", "Policy Debate Agent"],
            execution_time=execution_time,
            debate_messages=debate_messages,
            summary=summary
        )
        
    except Exception as e:
        logger.error(f"Agentic stakeholder debate failed: {e}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=False,
            workflow_id=workflow_id,
            workflow_type="stakeholder_debate",
            status="failed",
            results={},
            agents_involved=[],
            execution_time=execution_time,
            error=str(e)
        )

@app.post("/crew/workflow", response_model=AgenticWorkflowResponse)
async def run_custom_crew_workflow(request: CrewWorkflowRequest):
    """
    Run custom crew workflow based on workflow type
    """
    if not crew_system:
        raise HTTPException(status_code=503, detail="Crew agentic system not available")
    
    start_time = datetime.now()
    workflow_id = f"workflow_{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"Starting custom crew workflow: {request.workflow_type}")
        
        if request.workflow_type == "policy_discovery":
            # Policy discovery workflow
            user_context = request.user_context
            results = await crew_system.discover_policies_for_context(
                user_location=user_context.get("location", "San Francisco, CA"),
                stakeholder_roles=user_context.get("stakeholder_roles", []),
                interests=user_context.get("interests", [])
            )
            
            agents_involved = ["Policy Discovery Agent"]
            
        elif request.workflow_type == "comprehensive_analysis":
            # Comprehensive analysis combining discovery and stakeholder analysis
            policy_context = request.policy_context
            user_context = request.user_context
            
            # First discover policies
            discovery_results = await crew_system.discover_policies_for_context(
                user_location=user_context.get("location", "San Francisco, CA"),
                stakeholder_roles=user_context.get("stakeholder_roles", []),
                interests=user_context.get("interests", [])
            )
            
            # Then run stakeholder analysis
            stakeholder_list = [
                {
                    "name": role.replace("_", " ").title(),
                    "type": role,
                    "description": f"Representative of {role.replace('_', ' ')} interests"
                } for role in user_context.get("stakeholder_roles", [])
            ]
            
            analysis_crew = crew_system.setup_dynamic_stakeholder_crew(stakeholder_list)
            analysis_context = {
                **policy_context,
                **user_context,
                "discovered_policies": discovery_results.get("priority_policies", [])
            }
            
            analysis_results = analysis_crew.kickoff(inputs=analysis_context)
            
            results = {
                "policy_discovery": discovery_results,
                "stakeholder_analysis": str(analysis_results)  # Convert to string to avoid serialization issues
            }
            
            agents_involved = ["Policy Discovery Agent"] + [f"{s['name']} Advocate" for s in stakeholder_list]
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow type: {request.workflow_type}")
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=True,
            workflow_id=workflow_id,
            workflow_type=request.workflow_type,
            status="completed",
            results=results,
            agents_involved=agents_involved,
            execution_time=execution_time
        )
        
    except Exception as e:
        logger.error(f"Custom crew workflow failed: {e}")
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return AgenticWorkflowResponse(
            success=False,
            workflow_id=workflow_id,
            workflow_type=request.workflow_type,
            status="failed",
            results={},
            agents_involved=[],
            execution_time=execution_time,
            error=str(e)
        )

@app.get("/crew/workflows")
async def get_available_workflows():
    """
    Get list of available crew workflows
    """
    return {
        "workflows": [
            {
                "type": "policy_analysis",
                "name": "Comprehensive Policy Analysis",
                "description": "Discover and analyze policies with multi-stakeholder perspectives",
                "required_fields": ["policy_name", "user_location", "stakeholder_roles", "interests"]
            },
            {
                "type": "stakeholder_debate",
                "name": "Structured Stakeholder Debate",
                "description": "Conduct moderated debates between different stakeholder groups",
                "required_fields": ["policy_name", "stakeholders"]
            },
            {
                "type": "policy_discovery",
                "name": "AI-Powered Policy Discovery",
                "description": "Discover relevant policies using advanced AI search",
                "required_fields": ["user_context"]
            },
            {
                "type": "comprehensive_analysis",
                "name": "End-to-End Policy Analysis",
                "description": "Complete workflow from discovery to stakeholder analysis",
                "required_fields": ["policy_context", "user_context"]
            }
        ]
    }

@app.get("/crew/status")
async def get_crew_system_status():
    """
    Get status of the crew agentic system
    """
    if not crew_system:
        return {
            "status": "unavailable",
            "message": "Crew agentic system not initialized"
        }
    
    return {
        "status": "available",
        "components": {
            "policy_discovery_agent": crew_system.policy_discovery_client is not None,
            "llm_configured": crew_system.llm is not None,
            "tools_available": {
                "policy_file_reader": crew_system.policy_file_reader is not None,
                "stakeholder_identifier": crew_system.stakeholder_identifier is not None,
                "knowledge_base_manager": crew_system.knowledge_base_manager is not None,
                "debate_moderator": crew_system.debate_moderator is not None
            }
        },
        "message": "Crew agentic system fully operational"
    }

@app.post("/email/generate", response_model=EmailGenerationResponse)
async def generate_email(request: EmailGenerationRequest):
    """
    Generate an advocacy email based on policy analysis and debate context
    """
    try:
        if not crew_system:
            return EmailGenerationResponse(
                success=False,
                email_content="",
                recipients=[],
                error="Crew system not initialized"
            )
        
        # Use the action agent to generate the email
        action_agent = crew_system.action_agent()
        
        # Prepare context for email generation
        email_context = {
            "policy_id": request.policy_id,
            "policy_title": request.policy_title,
            "policy_content": request.policy_content,
            "user_perspective": request.user_perspective,
            "debate_context": request.debate_context or []
        }
        
        # Generate email content using the action agent
        email_prompt = f"""
        Generate a professional advocacy email about the policy: {request.policy_title}
        
        Policy Content: {request.policy_content}
        
        User Perspective: {request.user_perspective}
        
        {"Debate Context: " + str(request.debate_context) if request.debate_context else ""}
        
        Please create a compelling email that:
        1. Clearly states the policy issue
        2. Presents the user's perspective
        3. Includes specific arguments and evidence
        4. Has a clear call to action
        5. Is professional and persuasive
        
        Format the email with appropriate subject line, greeting, body, and closing.
        """
        
        # Create a task for email generation
        from crewai import Task
        email_task = Task(
            description=email_prompt,
            expected_output="A professional advocacy email with subject line, greeting, body, and closing",
            agent=action_agent
        )
        
        # Execute the task
        email_result = email_task.execute()
        
        # Default recipients based on policy level and domain
        recipients = [
            "mayor@sfgov.org",
            "board.of.supervisors@sfgov.org",
            "info@sfgov.org"
        ]
        
        # Add more specific recipients based on policy domain
        if "housing" in request.policy_title.lower() or "housing" in request.policy_content.lower():
            recipients.extend([
                "housing@sfgov.org",
                "planning@sfgov.org"
            ])
        elif "transport" in request.policy_title.lower() or "transport" in request.policy_content.lower():
            recipients.extend([
                "transportation@sfgov.org",
                "sfmta@sfgov.org"
            ])
        elif "business" in request.policy_title.lower() or "business" in request.policy_content.lower():
            recipients.extend([
                "business@sfgov.org",
                "economic.development@sfgov.org"
            ])
        
        return EmailGenerationResponse(
            success=True,
            email_content=str(email_result),
            recipients=list(set(recipients))  # Remove duplicates
        )
        
    except Exception as e:
        logger.error(f"Email generation failed: {str(e)}")
        return EmailGenerationResponse(
            success=False,
            email_content="",
            recipients=[],
            error=f"Email generation failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)