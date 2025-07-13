import json
import os
import uuid
from typing import Type, List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ValidationError
from crewai.tools import BaseTool
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Mock pandas for timestamp functionality
class pd:
    class Timestamp:
        @staticmethod
        def now():
            return datetime.now()
        
        @staticmethod
        def now_iso():
            return datetime.now().isoformat()

# =============================================================================
# OUTPUT MODELS - Pydantic models for ensuring proper JSON format and types
# =============================================================================

class UserProfile(BaseModel):
    """Model for user profile information."""
    name: Optional[str] = None
    location: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            # Add custom encoders if needed
        }

class PolicyInfo(BaseModel):
    """Model for policy information output."""
    title: str = Field(..., description="Policy title")
    text: str = Field(..., description="Policy text content")
    source_url: str = Field(default="", description="Source URL of the policy")
    user_profile: Optional[UserProfile] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Stakeholder(BaseModel):
    """Model for individual stakeholder information."""
    name: str = Field(..., description="Stakeholder name or type")
    type: str = Field(..., description="Category or type of stakeholder")
    interests: List[str] = Field(default=[], description="List of stakeholder interests")
    impact: str = Field(..., description="Description of how policy affects them")
    likely_stance: str = Field(..., description="Likely stance: supportive/opposed/neutral")
    key_concerns: List[str] = Field(default=[], description="List of key concerns")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Property Owners",
                "type": "business_stakeholder",
                "interests": ["property_value", "compliance_costs"],
                "impact": "Required to invest in seismic retrofitting",
                "likely_stance": "opposed",
                "key_concerns": ["financial_burden", "implementation_timeline"]
            }
        }

class StakeholderList(BaseModel):
    """Model for list of stakeholders."""
    stakeholders: List[Stakeholder] = Field(..., description="List of identified stakeholders")
    total_count: int = Field(..., description="Total number of stakeholders identified")
    analysis_summary: str = Field(default="", description="Summary of stakeholder analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "stakeholders": [
                    {
                        "name": "Property Owners",
                        "type": "business_stakeholder",
                        "interests": ["property_value", "compliance_costs"],
                        "impact": "Required to invest in seismic retrofitting",
                        "likely_stance": "opposed",
                        "key_concerns": ["financial_burden", "implementation_timeline"]
                    }
                ],
                "total_count": 1,
                "analysis_summary": "Multiple stakeholders identified with varying interests"
            }
        }

class KnowledgeBase(BaseModel):
    """Model for knowledge base entries."""
    stakeholder_name: str = Field(..., description="Name of the stakeholder")
    research_data: str = Field(..., description="Research findings and analysis")
    timestamp: str = Field(..., description="When the data was created/updated")
    version: int = Field(default=1, description="Version number of the knowledge base")
    previous_research: Optional[str] = Field(default=None, description="Previous research data if updating")
    
    class Config:
        schema_extra = {
            "example": {
                "stakeholder_name": "Property Owners",
                "research_data": "Detailed analysis of policy impacts...",
                "timestamp": "2024-01-01T10:00:00",
                "version": 1,
                "previous_research": None
            }
        }

class PolicyImpact(BaseModel):
    """Model for policy impact analysis."""
    direct_impacts: List[str] = Field(..., description="Direct impacts on stakeholder")
    economic_implications: List[str] = Field(..., description="Economic consequences")
    legal_changes: List[str] = Field(..., description="Legal/regulatory changes")
    benefits: List[str] = Field(..., description="Potential benefits")
    risks: List[str] = Field(..., description="Potential risks")
    short_term_consequences: List[str] = Field(..., description="Short-term effects")
    long_term_consequences: List[str] = Field(..., description="Long-term effects")

class StakeholderResearch(BaseModel):
    """Model for stakeholder research output."""
    stakeholder_name: str = Field(..., description="Name of the stakeholder")
    stakeholder_type: str = Field(..., description="Type of stakeholder")
    policy_impact: PolicyImpact = Field(..., description="Detailed policy impact analysis")
    recommended_actions: List[str] = Field(..., description="Recommended actions for stakeholder")
    debate_arguments: List[str] = Field(..., description="Key arguments for policy debates")
    research_summary: str = Field(..., description="Executive summary of research findings")
    confidence_level: str = Field(default="medium", description="Confidence level: low/medium/high")
    
    class Config:
        schema_extra = {
            "example": {
                "stakeholder_name": "Property Owners",
                "stakeholder_type": "business_stakeholder",
                "policy_impact": {
                    "direct_impacts": ["Required seismic retrofitting"],
                    "economic_implications": ["Significant upfront costs"],
                    "legal_changes": ["New compliance requirements"],
                    "benefits": ["Increased property safety"],
                    "risks": ["Financial burden"],
                    "short_term_consequences": ["Immediate compliance costs"],
                    "long_term_consequences": ["Improved property values"]
                },
                "recommended_actions": ["Seek financial assistance programs"],
                "debate_arguments": ["Need for implementation timeline flexibility"],
                "research_summary": "Property owners face significant financial burden but gain safety benefits",
                "confidence_level": "high"
            }
        }

# =============================================================================
# DEBATE MODELS - Pydantic models for structured debate system
# =============================================================================

class DebateTopic(BaseModel):
    """Model for individual debate topics."""
    topic_id: str = Field(..., description="Unique identifier for the topic")
    title: str = Field(..., description="Title of the debate topic")
    description: str = Field(..., description="Detailed description of the topic")
    priority: int = Field(..., description="Priority level (1-10, higher is more important)")
    stakeholders_involved: List[str] = Field(..., description="List of stakeholder names involved in this topic")
    key_questions: List[str] = Field(default=[], description="Key questions to be addressed")
    
    class Config:
        schema_extra = {
            "example": {
                "topic_id": "implementation_timeline",
                "title": "Implementation Timeline",
                "description": "Discussion about the feasibility of the proposed implementation timeline",
                "priority": 8,
                "stakeholders_involved": ["Property Owners", "City Officials", "Contractors"],
                "key_questions": ["Is the timeline realistic?", "What are the major bottlenecks?"]
            }
        }

class DebateTopicList(BaseModel):
    """Model for collection of debate topics."""
    topics: List[DebateTopic] = Field(..., description="List of debate topics")
    total_count: int = Field(..., description="Total number of topics")
    analysis_summary: str = Field(default="", description="Summary of topic analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "topics": [
                    {
                        "topic_id": "implementation_timeline",
                        "title": "Implementation Timeline",
                        "description": "Discussion about the feasibility of the proposed implementation timeline",
                        "priority": 8,
                        "stakeholders_involved": ["Property Owners", "City Officials", "Contractors"],
                        "key_questions": ["Is the timeline realistic?", "What are the major bottlenecks?"]
                    }
                ],
                "total_count": 1,
                "analysis_summary": "Key debate topics identified with stakeholder involvement"
            }
        }

class Argument(BaseModel):
    """Model for individual debate arguments."""
    argument_id: str = Field(..., description="Unique identifier for the argument")
    stakeholder_name: str = Field(..., description="Name of the stakeholder making the argument")
    argument_type: str = Field(..., description="Type of argument: claim, evidence, rebuttal, counter-claim")
    content: str = Field(..., description="The actual argument content")
    evidence: List[str] = Field(default=[], description="Supporting evidence or sources")
    references_argument_id: Optional[str] = Field(default=None, description="ID of argument this responds to")
    strength: int = Field(default=5, description="Argument strength (1-10)")
    timestamp: str = Field(..., description="When the argument was made")
    
    class Config:
        schema_extra = {
            "example": {
                "argument_id": "arg_001",
                "stakeholder_name": "Property Owners",
                "argument_type": "claim",
                "content": "The implementation timeline is unrealistic for small property owners",
                "evidence": ["Industry standards", "Financial analysis"],
                "references_argument_id": None,
                "strength": 8,
                "timestamp": "2024-01-01T10:00:00"
            }
        }

class DebateRound(BaseModel):
    """Model for a single debate round."""
    round_id: str = Field(..., description="Unique identifier for the round")
    topic: DebateTopic = Field(..., description="Topic being debated in this round")
    round_number: int = Field(..., description="Round number in the debate")
    round_type: str = Field(..., description="Type of round: opening, argument, rebuttal, closing")
    arguments: List[Argument] = Field(default=[], description="Arguments made in this round")
    duration_minutes: int = Field(default=10, description="Duration of the round in minutes")
    status: str = Field(default="pending", description="Status: pending, active, completed")
    
    class Config:
        schema_extra = {
            "example": {
                "round_id": "round_001",
                "topic": {
                    "topic_id": "implementation_timeline",
                    "title": "Implementation Timeline",
                    "description": "Discussion about the feasibility of the proposed implementation timeline",
                    "priority": 8,
                    "stakeholders_involved": ["Property Owners", "City Officials", "Contractors"],
                    "key_questions": ["Is the timeline realistic?", "What are the major bottlenecks?"]
                },
                "round_number": 1,
                "round_type": "opening",
                "arguments": [],
                "duration_minutes": 10,
                "status": "pending"
            }
        }

class DebateSession(BaseModel):
    """Model for a complete debate session."""
    session_id: str = Field(..., description="Unique identifier for the debate session")
    policy_name: str = Field(..., description="Name of the policy being debated")
    moderator: str = Field(..., description="Name of the moderator agent")
    participants: List[str] = Field(..., description="List of participating stakeholder names")
    topics: List[DebateTopic] = Field(..., description="Topics to be debated")
    rounds: List[DebateRound] = Field(default=[], description="Debate rounds")
    start_time: str = Field(..., description="When the debate session started")
    end_time: Optional[str] = Field(default=None, description="When the debate session ended")
    status: str = Field(default="preparing", description="Status: preparing, active, completed, cancelled")
    summary: str = Field(default="", description="Summary of the debate session")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "debate_001",
                "policy_name": "Seismic Retrofit Policy",
                "moderator": "AI Moderator",
                "participants": ["Property Owners", "City Officials", "Contractors"],
                "topics": [],
                "rounds": [],
                "start_time": "2024-01-01T10:00:00",
                "end_time": None,
                "status": "preparing",
                "summary": ""
            }
        }

class A2AMessage(BaseModel):
    """Model for Agent-to-Agent communication messages."""
    message_id: str = Field(..., description="Unique identifier for the message")
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(..., description="Name of the receiving agent")
    message_type: str = Field(..., description="Type: request, response, argument, query, clarification")
    content: str = Field(..., description="The message content")
    context: Dict[str, Any] = Field(default={}, description="Additional context for the message")
    timestamp: str = Field(..., description="When the message was sent")
    requires_response: bool = Field(default=False, description="Whether this message requires a response")
    
    class Config:
        schema_extra = {
            "example": {
                "message_id": "msg_001",
                "sender": "Property Owner Agent",
                "receiver": "City Official Agent",
                "message_type": "request",
                "content": "Can you clarify the implementation timeline?",
                "context": {"topic": "implementation_timeline"},
                "timestamp": "2024-01-01T10:00:00",
                "requires_response": True
            }
        }

class A2AProtocol(BaseModel):
    """Model for A2A protocol configuration."""
    protocol_id: str = Field(..., description="Unique identifier for the protocol")
    protocol_name: str = Field(..., description="Name of the protocol")
    description: str = Field(..., description="Description of the protocol")
    rules: List[str] = Field(..., description="Rules governing the protocol")
    message_flow: List[str] = Field(..., description="Expected message flow pattern")
    timeout_seconds: int = Field(default=300, description="Timeout for responses")
    
    class Config:
        schema_extra = {
            "example": {
                "protocol_id": "protocol_001",
                "protocol_name": "Debate Protocol",
                "description": "Protocol for structured policy debates",
                "rules": ["Respect time limits", "Stay on topic"],
                "message_flow": ["opening", "argument", "rebuttal", "closing"],
                "timeout_seconds": 300
            }
        }

# =============================================================================
# INPUT MODELS - Pydantic models for tool input validation
# =============================================================================

class PolicyFileReaderInput(BaseModel):
    """Input schema for PolicyFileReader."""
    file_path: str = Field(..., description="Path to the policy file to read")

class StakeholderIdentifierInput(BaseModel):
    """Input schema for StakeholderIdentifier."""
    policy_text: Union[str, Dict[str, Any]] = Field(..., description="The policy text to analyze for stakeholders")

class KnowledgeBaseManagerInput(BaseModel):
    """Input schema for KnowledgeBaseManager."""
    stakeholder_name: str = Field(..., description="Name of the stakeholder")
    research_data: Union[str, Dict[str, Any]] = Field(..., description="Research data to store")
    action: str = Field(..., description="Action to perform: 'create', 'update', 'retrieve'")

class StakeholderResearcherInput(BaseModel):
    """Input schema for StakeholderResearcher."""
    stakeholder_info: Union[str, Dict[str, Any]] = Field(..., description="JSON string containing stakeholder information or stakeholder object")
    policy_text: Union[str, Dict[str, Any]] = Field(..., description="The policy text to analyze or policy object")

# =============================================================================
# INPUT MODELS FOR DEBATE TOOLS
# =============================================================================

class TopicAnalyzerInput(BaseModel):
    """Input schema for TopicAnalyzer."""
    policy_text: Union[str, Dict[str, Any]] = Field(..., description="The policy text to analyze for debate topics or policy object")
    stakeholder_list: Union[str, Dict[str, Any], None] = Field(default=None, description="JSON string of stakeholder information or stakeholder object")

class DebateModeratorInput(BaseModel):
    """Input schema for DebateModerator."""
    session_id: str = Field(..., description="ID of the debate session")
    action: str = Field(..., description="Action: start, moderate, summarize, end")
    context: Union[str, Dict[str, Any]] = Field(default="", description="Additional context for the action or context object")

class ArgumentGeneratorInput(BaseModel):
    """Input schema for ArgumentGenerator."""
    stakeholder_name: str = Field(..., description="Name of the stakeholder")
    topic: Union[str, Dict[str, Any]] = Field(..., description="JSON string of the debate topic or topic object")
    argument_type: str = Field(..., description="Type of argument to generate")
    responding_to: str = Field(default="", description="ID of argument being responded to")

class A2AMessengerInput(BaseModel):
    """Input schema for A2AMessenger."""
    sender: str = Field(..., description="Name of the sending agent")
    receiver: str = Field(..., description="Name of the receiving agent")
    message_type: str = Field(..., description="Type of message")
    content: str = Field(..., description="Message content")
    context: Union[str, Dict[str, Any]] = Field(default="{}", description="JSON string of additional context or context object")

# =============================================================================
# ENHANCED TOOLS WITH PYDANTIC OUTPUT VALIDATION
# =============================================================================

class PolicyFileReader(BaseTool):
    name: str = "PolicyFileReader"
    description: str = (
        "Reads policy documents from local files. Supports JSON format with policy text content."
    )
    args_schema: Type[BaseModel] = PolicyFileReaderInput

    def _run(self, file_path: str) -> str:
        try:
            # Default to test_data if not absolute path
            if not os.path.isabs(file_path):
                file_path = os.path.join("test_data", file_path)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            # Extract and validate policy information using Pydantic
            user_profile_data = data.get("user_profile", {})
            user_profile = UserProfile(
                name=user_profile_data.get("name"),
                location=user_profile_data.get("location"),
                preferences=user_profile_data.get("preferences")
            ) if user_profile_data else None
            
            policy_info = PolicyInfo(
                title=data.get("policy_document", {}).get("title", "Unknown Policy"),
                text=data.get("policy_document", {}).get("text", ""),
                source_url=data.get("policy_document", {}).get("source_url", ""),
                user_profile=user_profile
            )
            
            return policy_info.model_dump_json(indent=2)
            
        except ValidationError as e:
            return f"Error: Invalid policy data format - {str(e)}"
        except Exception as e:
            return f"Error reading policy file: {str(e)}"

class StakeholderIdentifier(BaseTool):
    name: str = "StakeholderIdentifier"
    description: str = (
        "Analyzes policy text to identify ONLY direct and main stakeholders who are immediately and significantly affected by the policy. Excludes secondary, indirect, or tangentially affected parties."
    )
    args_schema: Type[BaseModel] = StakeholderIdentifierInput

    def _run(self, policy_text: Union[str, Dict[str, Any]]) -> str:
        try:
            # Handle both string and dictionary inputs
            if isinstance(policy_text, dict):
                policy_text_str = policy_text.get("text", "") or policy_text.get("content", "") or str(policy_text)
            else:
                policy_text_str = str(policy_text)
            
            # Get Weave client
            weave_client = get_weave_client()
            if not weave_client.is_available():
                return "Error: Weave client not available - WNB_API_KEY required"
            
            # Use the specialized policy analysis method
            result = weave_client.analyze_policy(
                policy_text=policy_text_str,
                analysis_type="stakeholder_identification"
            )
            
            # Check if there was an error
            if "error" in result:
                return f"Error in stakeholder identification: {result['error']}"
            
            # Validate and format the response
            try:
                stakeholder_data = result.get("stakeholders", [])
                
                # Validate each stakeholder using Pydantic
                validated_stakeholders = []
                for stakeholder in stakeholder_data:
                    # Map the Weave response to expected format
                    stakeholder_mapped = {
                        "name": stakeholder.get("name", "Unknown"),
                        "type": stakeholder.get("type", "unknown"),
                        "interests": stakeholder.get("interests", []),
                        "impact": stakeholder.get("direct_impact", ""),
                        "likely_stance": stakeholder.get("stance", "neutral"),
                        "key_concerns": stakeholder.get("concerns", [])
                    }
                    validated_stakeholder = Stakeholder(**stakeholder_mapped)
                    validated_stakeholders.append(validated_stakeholder)
                
                # Create the final stakeholder list
                stakeholder_list = StakeholderList(
                    stakeholders=validated_stakeholders,
                    total_count=len(validated_stakeholders),
                    analysis_summary=f"Identified {len(validated_stakeholders)} key stakeholders affected by the policy"
                )
                
                return stakeholder_list.model_dump_json(indent=2)
                
            except ValidationError as e:
                return f"Error: Response validation failed: {str(e)}"
            
        except Exception as e:
            return f"Error identifying stakeholders: {str(e)}"

class KnowledgeBaseManager(BaseTool):
    name: str = "KnowledgeBaseManager"
    description: str = (
        "Manages knowledge base for each stakeholder agent, storing and retrieving research data."
    )
    args_schema: Type[BaseModel] = KnowledgeBaseManagerInput

    def _run(self, stakeholder_name: str, research_data: Union[str, Dict[str, Any]], action: str) -> str:
        try:
            # Handle both string and dictionary inputs for research_data
            if isinstance(research_data, dict):
                research_data_str = json.dumps(research_data)
            else:
                research_data_str = str(research_data)
            
            # Create knowledge directory if it doesn't exist
            knowledge_dir = os.path.join("knowledge", "stakeholders")
            os.makedirs(knowledge_dir, exist_ok=True)
            
            file_path = os.path.join(knowledge_dir, f"{stakeholder_name.lower().replace(' ', '_')}.json")
            
            if action == "create" or action == "update":
                # Create knowledge base entry using Pydantic
                knowledge_data = KnowledgeBase(
                    stakeholder_name=stakeholder_name,
                    research_data=research_data_str,
                    timestamp=pd.Timestamp.now_iso(),
                    version=1
                )
                
                # If updating, load existing data and increment version
                if action == "update" and os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        existing_data = json.load(f)
                    knowledge_data.version = existing_data.get("version", 1) + 1
                    knowledge_data.previous_research = existing_data.get("research_data", "")
                
                # Save validated data
                with open(file_path, 'w') as f:
                    f.write(knowledge_data.model_dump_json(indent=2))
                
                return f"Knowledge base {action}d for {stakeholder_name}. Version: {knowledge_data.version}"
                
            elif action == "retrieve":
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Validate existing data
                    try:
                        knowledge_base = KnowledgeBase(**data)
                        return knowledge_base.model_dump_json(indent=2)
                    except ValidationError:
                        # Return raw data if validation fails (for backwards compatibility)
                        return json.dumps(data, indent=2)
                else:
                    return f"No knowledge base found for {stakeholder_name}"
                    
        except ValidationError as e:
            return f"Error: Invalid knowledge base data format - {str(e)}"
        except Exception as e:
            return f"Error managing knowledge base: {str(e)}"

class StakeholderResearcher(BaseTool):
    name: str = "StakeholderResearcher"
    description: str = (
        "Conducts detailed research on how a policy affects a specific stakeholder, from their perspective."
    )
    args_schema: Type[BaseModel] = StakeholderResearcherInput

    def _run(self, stakeholder_info: Union[str, Dict[str, Any]], policy_text: Union[str, Dict[str, Any]]) -> str:
        try:
            # Get Weave client
            weave_client = get_weave_client()
            if not weave_client.is_available():
                return "Error: Weave client not available - WNB_API_KEY required"
            
            # Handle both string and dictionary inputs from CrewAI
            if isinstance(stakeholder_info, dict):
                stakeholder_data = stakeholder_info
            else:
                try:
                    stakeholder_data = json.loads(stakeholder_info)
                except (json.JSONDecodeError, TypeError):
                    # If it's not valid JSON, treat it as a simple string
                    stakeholder_data = {"name": str(stakeholder_info), "type": "unknown"}
            
            # Handle both string and dictionary inputs for policy_text
            if isinstance(policy_text, dict):
                # Extract text from policy object
                policy_text_str = policy_text.get("text", "") or policy_text.get("content", "") or str(policy_text)
            else:
                policy_text_str = str(policy_text)
            
            stakeholder_name = stakeholder_data.get("name", "Unknown Stakeholder")
            stakeholder_type = stakeholder_data.get("type", "unknown")
            
            # Use the specialized policy analysis method
            result = weave_client.analyze_policy(
                policy_text=policy_text_str,
                analysis_type="stakeholder_research",
                context={"stakeholder_name": stakeholder_name}
            )
            
            # Check if there was an error
            if "error" in result:
                return f"Error in stakeholder research: {result['error']}"
            
            # Map the Weave response to the expected format
            try:
                research_data = {
                    "stakeholder_name": result.get("stakeholder_name", stakeholder_name),
                    "stakeholder_type": stakeholder_type,
                    "policy_impact": {
                        "direct_impacts": result.get("direct_impacts", []),
                        "economic_implications": [result.get("financial_implications", "")],
                        "legal_changes": [],  # Can be extracted from operational_changes
                        "benefits": result.get("benefits", []),
                        "risks": result.get("risks", []),
                        "short_term_consequences": [],  # Can be derived from impacts
                        "long_term_consequences": []   # Can be derived from impacts
                    },
                    "recommended_actions": result.get("recommended_actions", []),
                    "debate_arguments": result.get("key_concerns", []),  # Map concerns to arguments
                    "research_summary": result.get("research_summary", ""),
                    "confidence_level": result.get("confidence_level", "medium")
                }
                
                # Validate using Pydantic
                validated_research = StakeholderResearch(**research_data)
                
                return validated_research.model_dump_json(indent=2)
                
            except ValidationError as e:
                return f"Error: Response validation failed: {str(e)}"
            
        except Exception as e:
            error_msg = f"Error conducting stakeholder research: {str(e)}"
            logger.error(error_msg)
            return error_msg

# =============================================================================
# DEBATE TOOLS - Tools for structured debate system with A2A protocols
# =============================================================================

class TopicAnalyzer(BaseTool):
    name: str = "TopicAnalyzer"
    description: str = (
        "Analyzes policy text and stakeholder information to identify key debate topics and areas of contention."
    )
    args_schema: Type[BaseModel] = TopicAnalyzerInput

    def _run(self, policy_text: Union[str, Dict[str, Any]], stakeholder_list: Union[str, Dict[str, Any], None] = None) -> str:
        try:
            # Debug: Log input parameters
            logger.info(f"TopicAnalyzer input - policy_text type: {type(policy_text)}")
            logger.info(f"TopicAnalyzer input - stakeholder_list type: {type(stakeholder_list)}")
            logger.info(f"TopicAnalyzer input - stakeholder_list value: {stakeholder_list}")
            
            # Get Weave client
            weave_client = get_weave_client()
            if not weave_client.is_available():
                return "Error: Weave client not available - API key required"
            
            # Handle both string and dictionary inputs
            if isinstance(policy_text, dict):
                policy_text_str = policy_text.get("text", "") or policy_text.get("content", "") or str(policy_text)
            else:
                policy_text_str = str(policy_text)
            
            # Handle stakeholder_list input with better error handling
            stakeholders = []
            if stakeholder_list is None or stakeholder_list == "" or stakeholder_list == "null":
                # If no stakeholders provided, create default ones based on policy content
                stakeholders = [
                    {"name": "Policy Makers", "type": "government"},
                    {"name": "Affected Citizens", "type": "public"},
                    {"name": "Business Community", "type": "business"}
                ]
            elif isinstance(stakeholder_list, dict):
                if "stakeholders" in stakeholder_list:
                    stakeholders = stakeholder_list["stakeholders"]
                else:
                    stakeholders = [stakeholder_list]
            elif isinstance(stakeholder_list, list):
                stakeholders = stakeholder_list
            else:
                try:
                    # Handle string input that might be "null" or empty
                    if stakeholder_list in ["null", "None", ""]:
                        stakeholder_data = {"stakeholders": []}
                    else:
                        stakeholder_data = json.loads(stakeholder_list) if stakeholder_list else {"stakeholders": []}
                    
                    if "stakeholders" in stakeholder_data:
                        stakeholders = stakeholder_data["stakeholders"]
                    elif isinstance(stakeholder_data, list):
                        stakeholders = stakeholder_data
                    else:
                        stakeholders = [{"name": str(stakeholder_list), "type": "unknown"}]
                except (json.JSONDecodeError, TypeError):
                    stakeholders = [{"name": "General Public", "type": "public"}]
            
            # Ensure we have at least some stakeholders
            if not stakeholders:
                stakeholders = [{"name": "General Public", "type": "public"}]
            
            # Use the correct analysis type for topic analysis
            result = weave_client.analyze_policy(
                policy_text=policy_text_str,
                analysis_type="topic_analysis",
                context={"stakeholder_list": stakeholders}
            )
            
            # Check if there was an error
            if "error" in result:
                return f"Error in topic analysis: {result['error']}"
            
            # Map the Weave response to the expected format
            try:
                # Debug: Check what type of result we got
                logger.info(f"TopicAnalyzer result type: {type(result)}")
                logger.info(f"TopicAnalyzer result: {result}")
                
                # Handle case where result might be a list or string
                if isinstance(result, list):
                    debate_topics_data = result
                elif isinstance(result, str):
                    try:
                        result_dict = json.loads(result)
                        debate_topics_data = result_dict.get("debate_topics", [])
                    except (json.JSONDecodeError, TypeError):
                        debate_topics_data = []
                else:
                    debate_topics_data = result.get("debate_topics", []) if isinstance(result, dict) else []
                
                # If no topics found, create default ones
                if not debate_topics_data:
                    debate_topics_data = [
                        {
                            "topic": "Policy Implementation and Impact",
                            "description": "Discussion about how the policy will be implemented and its overall impact",
                            "stakeholder_positions": {s.get("name", "Unknown"): "neutral" for s in stakeholders},
                            "contention_level": "medium",
                            "key_questions": ["How will this policy be implemented?", "What are the expected outcomes?"]
                        },
                        {
                            "topic": "Cost and Resource Allocation",
                            "description": "Discussion about the costs and resource requirements of the policy",
                            "stakeholder_positions": {s.get("name", "Unknown"): "neutral" for s in stakeholders},
                            "contention_level": "high",
                            "key_questions": ["What are the costs involved?", "Who will bear these costs?"]
                        }
                    ]
                
                # Validate each topic using Pydantic
                validated_topics = []
                for topic in debate_topics_data:
                    # Map the response structure to our DebateTopic model
                    stakeholder_positions = topic.get("stakeholder_positions", {})
                    stakeholders_involved = list(stakeholder_positions.keys()) if stakeholder_positions else []
                    
                    topic_mapped = {
                        "topic_id": f"topic_{uuid.uuid4().hex[:8]}",
                        "title": topic.get("topic", "Unknown Topic"),
                        "description": topic.get("description", ""),
                        "priority": 5 if topic.get("contention_level") == "high" else 3 if topic.get("contention_level") == "medium" else 1,
                        "stakeholders_involved": stakeholders_involved,
                        "key_questions": topic.get("key_questions", [])
                    }
                    
                    validated_topic = DebateTopic(**topic_mapped)
                    validated_topics.append(validated_topic)
                
                # Create the final topic list
                topic_list = DebateTopicList(
                    topics=validated_topics,
                    total_count=len(validated_topics),
                    analysis_summary=f"Identified {len(validated_topics)} key debate topics from policy analysis"
                )
                
                return topic_list.model_dump_json(indent=2)
                
            except ValidationError as e:
                logger.error(f"Response validation failed: {str(e)}")
                return f"Error: Response validation failed: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error analyzing debate topics: {str(e)}")
            return f"Error analyzing debate topics: {str(e)}"

class ArgumentGenerator(BaseTool):
    name: str = "ArgumentGenerator"
    description: str = (
        "Generates structured arguments for stakeholders based on their knowledge base and the debate topic."
    )
    args_schema: Type[BaseModel] = ArgumentGeneratorInput

    def _run(self, stakeholder_name: str, topic: Union[str, Dict[str, Any]], argument_type: str, responding_to: str = "") -> str:
        try:
            # Get Weave client
            weave_client = get_weave_client()
            if not weave_client.is_available():
                return "Error: Weave client not available - WNB_API_KEY required"
            
            # Handle both string and dictionary inputs for topic
            if isinstance(topic, dict):
                topic_data = topic
            else:
                try:
                    topic_data = json.loads(topic)
                except (json.JSONDecodeError, TypeError):
                    topic_data = {"title": str(topic), "description": ""}
            
            # Load stakeholder knowledge base
            knowledge_dir = os.path.join("knowledge", "stakeholders")
            file_path = os.path.join(knowledge_dir, f"{stakeholder_name.lower().replace(' ', '_')}.json")
            
            stakeholder_context = ""
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    kb_data = json.load(f)
                    stakeholder_context = kb_data.get("research_data", "")
            
            # Use the specialized policy analysis method
            result = weave_client.analyze_policy(
                policy_text=f"Topic: {topic_data.get('title', '')}\nDescription: {topic_data.get('description', '')}\nStakeholder Context: {stakeholder_context}",
                analysis_type="argument_generation",
                context={
                    "stakeholder_name": stakeholder_name,
                    "argument_type": argument_type,
                    "responding_to": responding_to
                }
            )
            
            # Check if there was an error
            if "error" in result:
                return f"Error in argument generation: {result['error']}"
            
            # Map the Weave response to the expected format
            try:
                argument_data = {
                    "argument_id": result.get("argument_id", f"arg_{uuid.uuid4().hex[:8]}"),
                    "stakeholder_name": stakeholder_name,
                    "argument_type": argument_type,
                    "content": result.get("content", ""),
                    "evidence": result.get("evidence", []),
                    "references_argument_id": responding_to if responding_to else None,
                    "strength": result.get("strength", 5),
                    "timestamp": pd.Timestamp.now_iso()
                }
                
                # Validate using Pydantic
                validated_argument = Argument(**argument_data)
                
                return validated_argument.model_dump_json(indent=2)
                
            except ValidationError as e:
                return f"Error: Response validation failed: {str(e)}"
            
        except Exception as e:
            return f"Error generating argument: {str(e)}"

class A2AMessenger(BaseTool):
    name: str = "A2AMessenger"
    description: str = (
        "Facilitates Agent-to-Agent communication with structured messaging protocols."
    )
    args_schema: Type[BaseModel] = A2AMessengerInput

    def _run(self, sender: str, receiver: str, message_type: str, content: str, context: Union[str, Dict[str, Any]] = "{}") -> str:
        try:
            # Handle both string and dictionary inputs for context
            if isinstance(context, dict):
                context_data = context
            else:
                try:
                    context_data = json.loads(context)
                except (json.JSONDecodeError, TypeError):
                    context_data = {}
            
            # Create message using Pydantic
            message = A2AMessage(
                message_id=f"msg_{uuid.uuid4().hex[:8]}",
                sender=sender,
                receiver=receiver,
                message_type=message_type,
                content=content,
                context=context_data,
                timestamp=pd.Timestamp.now_iso(),
                requires_response=message_type in ["request", "query"]
            )
            
            # Store message in debate session directory
            debate_dir = os.path.join("knowledge", "debates", "messages")
            os.makedirs(debate_dir, exist_ok=True)
            
            file_path = os.path.join(debate_dir, f"{message.message_id}.json")
            with open(file_path, 'w') as f:
                f.write(message.model_dump_json(indent=2))
            
            return f"Message sent from {sender} to {receiver}. Message ID: {message.message_id}"
            
        except ValidationError as e:
            return f"Error: Invalid message format - {str(e)}"
        except Exception as e:
            return f"Error sending message: {str(e)}"

class DebateModerator(BaseTool):
    name: str = "DebateModerator"
    description: str = (
        "Moderates policy debates by managing topics, rounds, and ensuring structured argumentation."
    )
    args_schema: Type[BaseModel] = DebateModeratorInput

    def _run(self, session_id: str, action: str, context: Union[str, Dict[str, Any]] = "") -> str:
        try:
            # Handle both string and dictionary inputs for context
            if isinstance(context, dict):
                context_data = context
            else:
                try:
                    context_data = json.loads(context) if context else {}
                except (json.JSONDecodeError, TypeError):
                    context_data = {}
            
            # Create debate session directory
            debate_dir = os.path.join("knowledge", "debates", "sessions")
            os.makedirs(debate_dir, exist_ok=True)
            
            file_path = os.path.join(debate_dir, f"{session_id}.json")
            
            if action == "start":
                # Create new debate session
                session = DebateSession(
                    session_id=session_id,
                    policy_name=context_data.get("policy_name", "Unknown Policy"),
                    moderator=context_data.get("moderator", "AI Moderator"),
                    participants=context_data.get("participants", []),
                    topics=[],
                    rounds=[],
                    start_time=pd.Timestamp.now_iso(),
                    status="preparing"
                )
                
                with open(file_path, 'w') as f:
                    f.write(session.model_dump_json(indent=2))
                
                return f"Debate session {session_id} started. Status: {session.status}"
                
            elif action == "moderate":
                # Load existing session and add round
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                    
                    session = DebateSession(**session_data)
                    
                    # Create new round
                    round_data = context_data.get("round", {})
                    debate_round = DebateRound(
                        round_id=f"round_{len(session.rounds) + 1}",
                        topic=DebateTopic(**round_data.get("topic", {})),
                        round_number=len(session.rounds) + 1,
                        round_type=round_data.get("round_type", "argument"),
                        arguments=[],
                        duration_minutes=round_data.get("duration_minutes", 10),
                        status="active"
                    )
                    
                    session.rounds.append(debate_round)
                    session.status = "active"
                    
                    with open(file_path, 'w') as f:
                        f.write(session.model_dump_json(indent=2))
                    
                    return f"Round {debate_round.round_number} started in session {session_id}"
                else:
                    return f"Debate session {session_id} not found"
                    
            elif action == "summarize":
                # Generate debate summary
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                    
                    session = DebateSession(**session_data)
                    
                    # Generate summary using Weave client
                    weave_client = get_weave_client()
                    if weave_client.is_available():
                        summary_result = weave_client.analyze_policy(
                            policy_text=f"Debate session {session_id} with {len(session.participants)} participants",
                            analysis_type="debate_summary",
                            context={"session_data": session_data}
                        )
                        
                        if "error" not in summary_result:
                            session.summary = summary_result.get("summary", "Debate summary generated")
                    
                    session.status = "completed"
                    session.end_time = pd.Timestamp.now_iso()
                    
                    with open(file_path, 'w') as f:
                        f.write(session.model_dump_json(indent=2))
                    
                    return f"Debate session {session_id} summarized and completed"
                else:
                    return f"Debate session {session_id} not found"
                    
            elif action == "end":
                # End debate session
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                    
                    session = DebateSession(**session_data)
                    session.status = "completed"
                    session.end_time = pd.Timestamp.now_iso()
                    
                    with open(file_path, 'w') as f:
                        f.write(session.model_dump_json(indent=2))
                    
                    return f"Debate session {session_id} ended"
                else:
                    return f"Debate session {session_id} not found"
                    
            else:
                return f"Unknown action: {action}"
                
        except ValidationError as e:
            return f"Error: Invalid debate session format - {str(e)}"
        except Exception as e:
            return f"Error moderating debate: {str(e)}"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_weave_client():
    """Get Weave client instance."""
    try:
        from ..weave_client import get_weave_client
        return get_weave_client()
    except ImportError:
        logger.error("WeaveClient not available")
        return None
