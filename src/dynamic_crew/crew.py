from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool

# Mock tools to replace missing crewai_tools
class SerperDevTool(BaseTool):
    name: str = "SerperDevTool"
    description: str = "Mock search tool for web research"
    
    def _run(self, query: str) -> str:
        return f"Mock search results for: {query}"

class ScrapeWebsiteTool(BaseTool):
    name: str = "ScrapeWebsiteTool"
    description: str = "Mock web scraping tool"
    
    def _run(self, url: str) -> str:
        return f"Mock scraped content from: {url}"
import os
import logging
import yaml
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Import the integrated policy discovery agent
from .policy_discovery import PolicyDiscoveryAgent, UserContext, PolicyDomain, GovernmentLevel

# Import the robust LLM client (renamed from weave_client)
from .weave_client import get_weave_client, initialize_weave_client
# Import the dedicated Weave inference client
from .weave_inference_client import get_weave_inference_client, initialize_weave_inference_client

# CrewAI LLM wrapper for robust client
class RobustCrewAILLM:
    """
    Wrapper class to make robust LLM client compatible with CrewAI's expected LLM interface
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        # Use the first available provider's model
        if llm_client.providers:
            first_provider = llm_client.providers[0]
            self.model_name = first_provider.get('model', 'gpt-3.5-turbo')
            self.provider_name = first_provider.get('name', 'unknown')
        else:
            self.model_name = "gpt-3.5-turbo"
            self.provider_name = "unknown"
        self.temperature = 0.7
        
        print(f"✅ CrewAI LLM wrapper initialized with provider: {self.provider_name}, model: {self.model_name}")
    
    def call(self, prompt: str, **kwargs) -> str:
        """CrewAI compatible call method - this is the main method CrewAI uses"""
        try:
            # Check if this is a Weave inference client
            if hasattr(self.llm_client, 'generate_text'):
                return self.llm_client.generate_text(
                    prompt=prompt,
                    temperature=kwargs.get('temperature', self.temperature),
                    max_tokens=kwargs.get('max_tokens', 2048)
                )
            else:
                # Fallback for other client types
                return self.llm_client.generate_text(
                    prompt=prompt,
                    temperature=kwargs.get('temperature', self.temperature),
                    max_tokens=kwargs.get('max_tokens', 2048),
                    model=kwargs.get('model', self.model_name)
                )
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            # Return a fallback response to prevent system crashes
            return f"LLM Error: {str(e)}. Please check your provider configuration."
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """CrewAI compatible invoke method - fallback"""
        return self.call(prompt, **kwargs)
    
    def predict(self, prompt: str, **kwargs) -> str:
        """Alternative predict method for compatibility"""
        return self.call(prompt, **kwargs)
    
    def generate_content(self, prompt: str, **kwargs) -> str:
        """Gemini-style interface compatibility"""
        return self.call(prompt, **kwargs)

from .tools.custom_tool import (
    PolicyFileReader,
    StakeholderIdentifier,
    KnowledgeBaseManager,
    StakeholderResearcher,
    TopicAnalyzer,
    ArgumentGenerator,
    A2AMessenger,
    DebateModerator
)

def load_yaml_config(config_file: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    config_path = Path(__file__).parent / "config" / config_file
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            print(f"✅ Loaded {config_file}: {len(config)} items")
            return config
    except Exception as e:
        print(f"⚠️  Failed to load {config_file}: {e}")
        print(f"   Config path: {config_path}")
        return {}

@CrewBase
class DynamicCrewAutomationForPolicyAnalysisAndDebateCrew():
    """
    Dynamic CrewAI system for policy analysis and debate with robust LLM integration
    """
    
    def __init__(self):
        # Load configurations before calling super().__init__()
        
        # Disable Weave completely to prevent circular reference issues
        os.environ['WEAVE_DISABLE_TRACING'] = '1'
        os.environ['WEAVE_AUTO_TRACE'] = '0'
        os.environ['WEAVE_AUTO_PATCH'] = '0'
        os.environ['WANDB_DISABLE_TRACING'] = '1'
        
        # Load configurations
        self.agents_config = self._load_config('agents.yaml')
        self.tasks_config = self._load_config('tasks.yaml')
        
        # Initialize LLM with Claude as primary, with robust fallback
        try:
            # Try Claude first (Anthropic's most capable model)
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_api_key:
                print("🔄 Attempting Claude LLM configuration...")
                try:
                    # Configure Claude LLM
                    self.llm = LLM(
                        model="claude-3-5-sonnet-20241022",
                        api_key=anthropic_api_key,
                        temperature=0.7,
                        max_tokens=4096
                    )
                    
                    print("✅ Claude LLM configured successfully")
                    print(f"🤖 Using Claude model: claude-3-5-sonnet-20241022")
                    print(f"📡 Provider: Anthropic")
                    
                    # Test the LLM with a simple call
                    test_response = self.llm.call("Hello")
                    if test_response and len(test_response.strip()) > 0:
                        print("✅ Claude LLM test successful")
                        self.llm_client = None  # Use Claude LLM directly
                    else:
                        raise ValueError("Claude LLM returned empty response")
                        
                except Exception as claude_error:
                    print(f"⚠️  Claude configuration failed: {claude_error}")
                    print("   Falling back to other providers")
                    raise claude_error
            else:
                print("⚠️  ANTHROPIC_API_KEY not found, using fallback providers")
                raise ValueError("ANTHROPIC_API_KEY not found")
                
        except Exception as e:
            print(f"🔄 Claude not available, configuring fallback providers...")
            
            # Try Gemini as first fallback
            gemini_api_key = os.getenv('GOOGLE_API_KEY')
            if gemini_api_key:
                try:
                    print("🔄 Configuring Gemini LLM...")
                    self.llm = LLM(
                        model="gemini-1.5-flash",
                        api_key=gemini_api_key,
                        provider="google"
                    )
                    print("✅ Gemini LLM configured successfully")
                    print(f"🤖 Using Gemini model: gemini-1.5-flash")
                    
                    # Test the LLM
                    test_response = self.llm.call("Hello")
                    if test_response and len(test_response.strip()) > 0:
                        print("✅ Gemini LLM test successful")
                        self.llm_client = None
                    else:
                        raise ValueError("Gemini LLM returned empty response")
                        
                except Exception as gemini_error:
                    print(f"⚠️  Gemini configuration failed: {gemini_error}")
                    raise gemini_error
            
            # Try OpenAI as second fallback
            else:
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if openai_api_key:
                    try:
                        print("🔄 Configuring OpenAI LLM...")
                        self.llm = LLM(
                            model="gpt-3.5-turbo",
                            api_key=openai_api_key,
                        )
                        print("✅ OpenAI LLM configured successfully")
                        print(f"🤖 Using OpenAI model: gpt-3.5-turbo")
                        
                        # Test the LLM
                        test_response = self.llm.call("Hello")
                        if test_response and len(test_response.strip()) > 0:
                            print("✅ OpenAI LLM test successful")
                            self.llm_client = None
                        else:
                            raise ValueError("OpenAI LLM returned empty response")
                            
                    except Exception as openai_error:
                        print(f"⚠️  OpenAI configuration failed: {openai_error}")
                        raise openai_error
                
                # Try Groq as third fallback
                else:
                    groq_api_key = os.getenv('GROQ_API_KEY')
                    if groq_api_key:
                        try:
                            print("🔄 Configuring Groq LLM...")
                            self.llm = LLM(
                                model="llama3-8b-8192",
                                api_base="https://api.groq.com/openai/v1",
                                api_key=groq_api_key,
                            )
                            print("✅ Groq LLM configured successfully")
                            print(f"🤖 Using Groq model: llama3-8b-8192")
                            
                            # Test the LLM
                            test_response = self.llm.call("Hello")
                            if test_response and len(test_response.strip()) > 0:
                                print("✅ Groq LLM test successful")
                                self.llm_client = None
                            else:
                                raise ValueError("Groq LLM returned empty response")
                                
                        except Exception as groq_error:
                            print(f"⚠️  Groq configuration failed: {groq_error}")
                            raise groq_error
                    else:
                        # Last resort: try robust multi-provider client
                        try:
                            print("🔄 Attempting robust multi-provider client...")
                            self.llm_client = initialize_weave_client("civicai-policy-debate")
                            
                            if self.llm_client.is_available():
                                self.llm = RobustCrewAILLM(self.llm_client)
                                print("✅ CrewAI LLM configured with robust multi-provider client")
                                
                                # Log available providers
                                provider_names = [p['name'] for p in self.llm_client.providers]
                                print(f"📡 Available providers: {', '.join(provider_names)}")
                            else:
                                raise ValueError("No LLM providers available in robust client")
                        except Exception as robust_error:
                            print(f"❌ All LLM configurations failed")
                            print(f"   Claude Error: {e}")
                            print(f"   Gemini Error: {gemini_error if 'gemini_error' in locals() else 'Not attempted'}")
                            print(f"   OpenAI Error: {openai_error if 'openai_error' in locals() else 'Not attempted'}")
                            print(f"   Groq Error: {groq_error if 'groq_error' in locals() else 'Not attempted'}")
                            print(f"   Robust Client Error: {robust_error}")
                            raise ValueError("Failed to initialize any LLM client. Please check your API keys.")
        
        # Initialize tools
        self._initialize_tools()
        
        # Initialize stakeholder tracking attributes
        self.stakeholder_agents = {}
        self.stakeholder_tasks = {}
        
        # Call parent constructor
        super().__init__()
        
        print("✅ Dynamic CrewAI system initialized successfully")
    
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "config" / filename
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Failed to load {filename}: {e}")
            return {}
    
    def _initialize_tools(self):
        """Initialize all tools with robust error handling"""
        try:
            from .tools.custom_tool import (
                PolicyFileReader, StakeholderIdentifier, KnowledgeBaseManager,
                StakeholderResearcher, TopicAnalyzer, ArgumentGenerator,
                A2AMessenger, DebateModerator
            )
            
            # Initialize tools
            self.policy_file_reader = PolicyFileReader()
            self.stakeholder_identifier = StakeholderIdentifier()
            self.knowledge_base_manager = KnowledgeBaseManager()
            self.stakeholder_researcher = StakeholderResearcher()
            self.topic_analyzer = TopicAnalyzer()
            self.argument_generator = ArgumentGenerator()
            self.a2a_messenger = A2AMessenger()
            self.debate_moderator = DebateModerator()
            
            print("✅ All tools initialized successfully")
            
        except Exception as e:
            print(f"❌ Tool initialization failed: {e}")
            raise ValueError(f"Failed to initialize tools: {e}")

    @agent
    def coordinator_agent(self) -> Agent:
        print(f"🔍 Creating coordinator_agent with config: {self.agents_config.get('coordinator_agent', 'NOT_FOUND')}")
        try:
            return Agent(
                config=self.agents_config['coordinator_agent'],
                tools=[self.policy_file_reader],
                llm=self.llm,
                allow_delegation=False,  # Prevent delegation, use tools directly
                verbose=True,
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in coordinator_agent: {e}")
            print(f"   agents_config type: {type(self.agents_config)}")
            print(f"   agents_config keys: {list(self.agents_config.keys()) if isinstance(self.agents_config, dict) else 'Not a dict'}")
            raise

    @agent
    def policy_discovery_agent(self) -> Agent:
        """Enhanced policy discovery agent using integrated Exa API for comprehensive policy search"""
        print(f"🔍 Creating policy_discovery_agent")
        try:
            return Agent(
                role="Universal Policy Discovery Specialist",
                goal="Discover and categorize relevant policies across all government levels (Federal, State of California, City of San Francisco) based on user context and stakeholder roles using integrated Exa API",
                backstory="""You are an expert in navigating complex government policy landscapes with deep knowledge of Federal, California State, and San Francisco local governance structures. You excel at identifying policies that impact specific stakeholder groups using advanced AI-powered search capabilities through the integrated Exa API. Your expertise includes real-time policy discovery, stakeholder impact assessment, and translating complex governmental processes into actionable insights for civic engagement.""",
                tools=[self.policy_file_reader, SerperDevTool(), ScrapeWebsiteTool()],
                llm=self.llm,
                verbose=True,
                allow_delegation=False,  # Prevent delegation, use tools directly
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in policy_discovery_agent: {e}")
            raise

    async def discover_policies_for_context(self, user_location: str, stakeholder_roles: List[str], interests: List[str]) -> Dict[str, Any]:
        """
        Use the integrated policy discovery agent to find relevant policies with refined search capabilities
        
        Args:
            user_location: User's location (e.g., "San Francisco, CA")
            stakeholder_roles: List of stakeholder roles (e.g., ["renter", "employee"])
            interests: List of policy interests (e.g., ["rent control", "minimum wage"])
            
        Returns:
            Dictionary containing discovered policies and analysis
        """
        # Check if we have a policy discovery client available
        if not hasattr(self, 'llm_client') or not self.llm_client:
            return {"error": "Policy discovery client not available - using W&B Inference LLM directly"}
        
        try:
            # Create user context for policy discovery with refined parameters
            user_context = UserContext(
                location=user_location,
                stakeholder_roles=stakeholder_roles,
                interests=interests
            )
            
            # Discover policies using the refined integrated agent
            results = await self.llm_client.discover_policies(user_context=user_context)
            
            # Return structured results with enhanced quality metrics
            return {
                "success": True,
                "total_found": results.total_found,
                "search_time": results.search_time,
                "priority_policies": [
                    {
                        "id": f"policy_{i}",
                        "title": policy.title,
                        "url": policy.url,
                        "government_level": policy.government_level.value,
                        "domain": policy.domain.value,
                        "summary": policy.summary,
                        "status": policy.status.value,
                        "source_agency": policy.source_agency,
                        "document_type": policy.document_type,
                        "last_updated": policy.last_updated.isoformat() if policy.last_updated else None,
                        "confidence_score": policy.confidence_score,
                        "content_preview": policy.content_preview,
                        "stakeholder_impacts": [
                            {
                                "group": impact.stakeholder_group,
                                "severity": impact.impact_severity.value,
                                "description": impact.description,
                                "affected_areas": impact.affected_areas
                            } for impact in policy.stakeholder_impacts
                        ]
                    } for i, policy in enumerate(results.priority_ranking[:15])  # Top 15 policies for better coverage
                ],
                "stakeholder_impact_map": {
                    role: [
                        {
                            "id": f"policy_{j}",
                            "title": policy.title,
                            "url": policy.url,
                            "government_level": policy.government_level.value,
                            "domain": policy.domain.value,
                            "summary": policy.summary,
                            "confidence_score": policy.confidence_score,
                            "document_type": policy.document_type,
                            "source_agency": policy.source_agency
                        } for j, policy in enumerate(policies[:5])  # Limit to top 5 per role
                    ] for role, policies in results.stakeholder_impact_map.items()
                },
                "search_metadata": {
                    "domains_searched": results.search_metadata.get("domains_searched", []),
                    "levels_searched": results.search_metadata.get("levels_searched", []),
                    "search_quality_score": sum(p.confidence_score for p in results.priority_ranking[:10]) / min(10, len(results.priority_ranking)) if results.priority_ranking else 0,
                    "recent_policies_count": len([p for p in results.priority_ranking if p.last_updated and (datetime.now() - p.last_updated).days <= 90]),
                    "high_confidence_count": len([p for p in results.priority_ranking if p.confidence_score >= 0.8]),
                    "document_types": {
                        doc_type: len([p for p in results.priority_ranking if p.document_type == doc_type])
                        for doc_type in set(p.document_type for p in results.priority_ranking)
                    },
                    "government_levels": {
                        level.value: len([p for p in results.priority_ranking if p.government_level == level])
                        for level in set(p.government_level for p in results.priority_ranking)
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Policy discovery failed: {str(e)}")
            return {"error": f"Policy discovery failed: {str(e)}"}

    @agent
    def policy_debate_agent(self) -> Agent:
        print(f"🔍 Creating policy_debate_agent with config: {self.agents_config.get('policy_debate_agent', 'NOT_FOUND')}")
        try:
            return Agent(
                config=self.agents_config['policy_debate_agent'],
                tools=[
                    self.stakeholder_identifier, 
                    self.knowledge_base_manager,
                    SerperDevTool(), 
                    ScrapeWebsiteTool()
                ],
                llm=self.llm,
                allow_delegation=False,  # Prevent delegation, use tools directly
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in policy_debate_agent: {e}")
            print(f"   agents_config type: {type(self.agents_config)}")
            print(f"   agents_config keys: {list(self.agents_config.keys()) if isinstance(self.agents_config, dict) else 'Not a dict'}")
            raise

    @agent
    def advocate_sub_agents(self) -> Agent:
        print(f"🔍 Creating advocate_sub_agents with config: {self.agents_config.get('advocate_sub_agents', 'NOT_FOUND')}")
        try:
            return Agent(
                config=self.agents_config['advocate_sub_agents'],
                tools=[
                    self.stakeholder_researcher,
                    self.knowledge_base_manager,
                    self.argument_generator,
                    self.a2a_messenger,
                    SerperDevTool(),
                    ScrapeWebsiteTool()
                ],
                llm=self.llm,
                allow_delegation=False,  # Prevent delegation, use tools directly
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in advocate_sub_agents: {e}")
            print(f"   agents_config type: {type(self.agents_config)}")
            print(f"   agents_config keys: {list(self.agents_config.keys()) if isinstance(self.agents_config, dict) else 'Not a dict'}")
            raise

    @agent
    def action_agent(self) -> Agent:
        print(f"🔍 Creating action_agent with config: {self.agents_config.get('action_agent', 'NOT_FOUND')}")
        try:
            return Agent(
                config=self.agents_config['action_agent'],
                tools=[self.knowledge_base_manager],
                llm=self.llm,
                allow_delegation=False,  # Prevent delegation, use tools directly
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in action_agent: {e}")
            print(f"   agents_config type: {type(self.agents_config)}")
            print(f"   agents_config keys: {list(self.agents_config.keys()) if isinstance(self.agents_config, dict) else 'Not a dict'}")
            raise

    @agent
    def debate_moderator_agent(self) -> Agent:
        print(f"🔍 Creating debate_moderator_agent with config: {self.agents_config.get('debate_moderator_agent', 'NOT_FOUND')}")
        try:
            return Agent(
                config=self.agents_config['debate_moderator_agent'],
                tools=[
                    self.topic_analyzer,
                    self.debate_moderator,
                    self.a2a_messenger,
                    self.knowledge_base_manager,
                    SerperDevTool()
                ],
                llm=self.llm,
                allow_delegation=False,  # Prevent delegation, use tools directly
                verbose=True,
                max_iter=1,  # Limit iterations to prevent loops
            )
        except Exception as e:
            print(f"❌ Error in debate_moderator_agent: {e}")
            print(f"   agents_config type: {type(self.agents_config)}")
            print(f"   agents_config keys: {list(self.agents_config.keys()) if isinstance(self.agents_config, dict) else 'Not a dict'}")
            raise

    def create_stakeholder_agent(self, stakeholder_info: Dict[str, Any]) -> Agent:
        """Create a dynamic agent for a specific stakeholder"""
        stakeholder_name = stakeholder_info.get("name", "Unknown Stakeholder")
        stakeholder_type = stakeholder_info.get("type", "stakeholder")
        
        # Create agent configuration
        agent_config = {
            "role": f"{stakeholder_name} Advocate",
            "goal": f"Analyze policies from the perspective of {stakeholder_name} and advocate for their interests",
            "backstory": f"You are a dedicated advocate for {stakeholder_name}. Your role is to understand how policies affect {stakeholder_name} and present their viewpoint in policy debates. You have deep knowledge of {stakeholder_type} concerns and interests.",
            "verbose": True,
            "allow_delegation": False
        }
        
        agent = Agent(
            role=agent_config["role"],
            goal=agent_config["goal"],
            backstory=agent_config["backstory"],
            verbose=agent_config["verbose"],
            allow_delegation=False,  # Always disable delegation for stakeholder agents
            max_iter=1,  # Limit iterations to prevent loops
            tools=[
                self.stakeholder_researcher,
                self.knowledge_base_manager,
                self.argument_generator,
                self.a2a_messenger,
                SerperDevTool(),
                ScrapeWebsiteTool()
            ],
            llm=self.llm
        )
        
        return agent

    def create_stakeholder_task(self, stakeholder_info: Dict[str, Any], agent: Agent) -> Task:
        """Create a task for a stakeholder agent"""
        stakeholder_name = stakeholder_info.get("name", "Unknown Stakeholder")
        
        # Create task with minimal agent reference to avoid circular references
        # Use agent name instead of full agent object when possible
        task = Task(
            description=f"Research and analyze the policy from {stakeholder_name}'s perspective. Use the StakeholderResearcher tool to conduct detailed analysis and store findings in the knowledge base.",
            expected_output=f"Comprehensive analysis of policy impacts on {stakeholder_name}, including key arguments, concerns, and recommendations.",
            agent=agent,
            tools=[self.stakeholder_researcher, self.knowledge_base_manager]
        )
        
        return task

    def create_task_without_circular_refs(self, description: str, expected_output: str, agent: Agent, tools: List = None) -> Task:
        """Create a task without circular references by using minimal agent information"""
        # Create a simplified task that avoids circular references
        task = Task(
            description=description,
            expected_output=expected_output,
            agent=agent,
            tools=tools or []
        )
        return task

    @task
    def receive_query_task(self) -> Task:
        print(f"🔍 Creating receive_query_task with config: {self.tasks_config.get('receive_query_task', 'NOT_FOUND')}")
        try:
            task_config = self.tasks_config['receive_query_task']
            return Task(
                description=task_config['description'],
                expected_output=task_config['expected_output'],
                agent=self.coordinator_agent(),
                tools=[self.policy_file_reader],
            )
        except Exception as e:
            print(f"❌ Error in receive_query_task: {e}")
            print(f"   tasks_config type: {type(self.tasks_config)}")
            print(f"   tasks_config keys: {list(self.tasks_config.keys()) if isinstance(self.tasks_config, dict) else 'Not a dict'}")
            raise

    @task
    def fetch_policy_text_task(self) -> Task:
        print(f"🔍 Creating fetch_policy_text_task with config: {self.tasks_config.get('fetch_policy_text_task', 'NOT_FOUND')}")
        try:
            task_config = self.tasks_config['fetch_policy_text_task']
            return Task(
                description=task_config['description'],
                expected_output=task_config['expected_output'],
                agent=self.policy_discovery_agent(),
                tools=[self.policy_file_reader, SerperDevTool(), ScrapeWebsiteTool()],
            )
        except Exception as e:
            print(f"❌ Error in fetch_policy_text_task: {e}")
            print(f"   tasks_config type: {type(self.tasks_config)}")
            print(f"   tasks_config keys: {list(self.tasks_config.keys()) if isinstance(self.tasks_config, dict) else 'Not a dict'}")
            raise

    @task
    def analyze_policy_text_task(self) -> Task:
        print(f"🔍 Creating analyze_policy_text_task with config: {self.tasks_config.get('analyze_policy_text_task', 'NOT_FOUND')}")
        try:
            task_config = self.tasks_config['analyze_policy_text_task']
            return Task(
                description=task_config['description'],
                expected_output=task_config['expected_output'],
                agent=self.policy_debate_agent(),
                tools=[self.stakeholder_identifier],
            )
        except Exception as e:
            print(f"❌ Error in analyze_policy_text_task: {e}")
            print(f"   tasks_config type: {type(self.tasks_config)}")
            print(f"   tasks_config keys: {list(self.tasks_config.keys()) if isinstance(self.tasks_config, dict) else 'Not a dict'}")
            raise

    @task
    def dynamic_sub_agent_creation_task(self) -> Task:
        task_config = self.tasks_config['dynamic_sub_agent_creation_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.policy_debate_agent(),
            tools=[self.stakeholder_identifier, self.knowledge_base_manager],
        )

    @task
    def stakeholder_analysis_task(self) -> Task:
        task_config = self.tasks_config['stakeholder_analysis_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.advocate_sub_agents(),
            tools=[self.stakeholder_researcher, self.knowledge_base_manager],
        )

    @task
    def synthesize_summary_task(self) -> Task:
        task_config = self.tasks_config['synthesize_summary_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.action_agent(),
            tools=[self.knowledge_base_manager],
        )

    @task
    def draft_email_task(self) -> Task:
        task_config = self.tasks_config['draft_email_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.action_agent(),
            tools=[self.knowledge_base_manager],
        )

    @task
    def analyze_debate_topics_task(self) -> Task:
        task_config = self.tasks_config['analyze_debate_topics_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.debate_moderator_agent(),
            tools=[self.topic_analyzer],
        )

    @task
    def initiate_debate_session_task(self) -> Task:
        task_config = self.tasks_config['initiate_debate_session_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.debate_moderator_agent(),
            tools=[self.debate_moderator, self.knowledge_base_manager],
        )

    @task
    def conduct_stakeholder_debate_task(self) -> Task:
        task_config = self.tasks_config['conduct_stakeholder_debate_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.advocate_sub_agents(),
            tools=[self.argument_generator, self.a2a_messenger, self.knowledge_base_manager],
        )

    @task
    def moderate_debate_flow_task(self) -> Task:
        task_config = self.tasks_config['moderate_debate_flow_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.debate_moderator_agent(),
            tools=[self.debate_moderator, self.a2a_messenger],
        )

    @task
    def summarize_debate_outcomes_task(self) -> Task:
        task_config = self.tasks_config['summarize_debate_outcomes_task']
        return Task(
            description=task_config['description'],
            expected_output=task_config['expected_output'],
            agent=self.debate_moderator_agent(),
            tools=[self.debate_moderator, self.knowledge_base_manager],
        )

    def preflight_health_check(self):
        """Check LLM and tool availability before running workflow."""
        errors = []
        
        # Check LLM - handle Claude, Gemini, W&B Inference, and fallback clients
        try:
            if hasattr(self, 'llm') and self.llm:
                if hasattr(self.llm, 'model'):  # Claude, Gemini or W&B Inference LLM
                    model_name = getattr(self.llm, 'model', 'Unknown')
                    provider = getattr(self.llm, 'provider', 'Unknown')
                    if 'claude' in model_name.lower():
                        print(f"✅ Claude LLM available: {model_name}")
                    elif 'gemini' in model_name.lower():
                        print(f"✅ Gemini LLM available: {model_name}")
                    elif 'wandb' in str(self.llm).lower() or 'inference' in str(self.llm).lower():
                        print(f"✅ W&B Inference LLM available: {model_name}")
                    else:
                        print(f"✅ LLM available: {model_name} (Provider: {provider})")
                elif hasattr(self.llm, 'llm_client') and self.llm.llm_client:  # Fallback client
                    if self.llm.llm_client.is_available():
                        provider_names = [p['name'] for p in self.llm.llm_client.providers]
                        print(f"✅ Fallback LLM providers available: {', '.join(provider_names)}")
                    else:
                        errors.append("No available LLM providers in fallback client")
                else:
                    errors.append("LLM not properly configured")
            else:
                errors.append("No LLM configured")
        except Exception as e:
            errors.append(f"LLM health check failed: {e}")
        
        # Check tools
        try:
            _ = self.stakeholder_researcher
            _ = self.knowledge_base_manager
            _ = self.argument_generator
            _ = self.a2a_messenger
            _ = self.debate_moderator
            _ = self.policy_file_reader
            _ = self.stakeholder_identifier
            _ = self.topic_analyzer
            print("✅ All tools available")
        except Exception as e:
            errors.append(f"Tool health check failed: {e}")
        
        return errors

    def run_debate_workflow(self, policy_text, stakeholder_list):
        """Run the full debate workflow with robust error handling."""
        # Use local logger only, do not attach to self or pass to Weave
        local_logger = logging.getLogger("debate_orchestration")
        results = {}
        errors = []
        # 1. Preflight health check
        health_errors = self.preflight_health_check()
        if health_errors:
            local_logger.error(f"Preflight health check failed: {health_errors}")
            return {"success": False, "errors": health_errors}
        local_logger.info("Preflight health check passed.")

        # 2. Setup agents (explicit, robust)
        try:
            # Coordinator
            coordinator = self.coordinator_agent()
            # Policy discovery
            policy_discovery = self.policy_discovery_agent()
            # Policy debate
            debate_agent = self.policy_debate_agent()
            # Action agent
            action_agent = self.action_agent()
            # Moderator
            moderator_agent = self.debate_moderator_agent()
            # Stakeholder agents
            stakeholder_agents = [self.create_stakeholder_agent(s) for s in stakeholder_list]
        except Exception as e:
            local_logger.error(f"Agent setup failed: {e}")
            errors.append(f"Agent setup failed: {e}")
            return {"success": False, "errors": errors}

        # 3. Setup tasks (explicit, robust, clear descriptions)
        try:
            # Policy discovery task
            discovery_task = Task(
                description=(
                    "Use the policy discovery tools to find relevant policies for the following context. "
                    f"Policy text: {policy_text}\nStakeholders: {stakeholder_list}\n"
                    "Return a list of relevant policies."
                ),
                expected_output="List of relevant policies.",
                agent=policy_discovery,
            )
            # Stakeholder identification
            stakeholder_id_task = Task(
                description=(
                    "Use the StakeholderIdentifier tool to identify main stakeholders in the following policy. "
                    f"Policy text: {policy_text}\n"
                    "Return a list of stakeholders with their interests and stances."
                ),
                expected_output="List of stakeholders with interests and stances.",
                agent=debate_agent,
            )
            # Stakeholder research (for each stakeholder)
            stakeholder_research_tasks = []
            for s, agent in zip(stakeholder_list, stakeholder_agents):
                stakeholder_research_tasks.append(Task(
                    description=(
                        "Use the StakeholderResearcher tool to analyze the following policy for this stakeholder. "
                        f"Stakeholder: {s}\nPolicy: {policy_text}\n"
                        "Store findings in the knowledge base using KnowledgeBaseManager."
                    ),
                    expected_output=f"Research report for {s.get('name', 'stakeholder')}",
                    agent=agent,
                ))
            # Topic analysis
            topic_task = Task(
                description=(
                    "Use the TopicAnalyzer tool to identify key debate topics and areas of contention for the following policy and stakeholders. "
                    f"Policy: {policy_text}\nStakeholders: {stakeholder_list}\n"
                    "Return a list of debate topics."
                ),
                expected_output="List of debate topics.",
                agent=moderator_agent,
            )
            # Argument generation (for each stakeholder)
            argument_tasks = []
            for s, agent in zip(stakeholder_list, stakeholder_agents):
                argument_tasks.append(Task(
                    description=(
                        "Use the ArgumentGenerator tool to generate an opening argument for this stakeholder on the main debate topic. "
                        f"Stakeholder: {s}\nPolicy: {policy_text}\n"
                        "Return the argument as structured text."
                    ),
                    expected_output=f"Opening argument for {s.get('name', 'stakeholder')}",
                    agent=agent,
                ))
            # Synthesis
            synthesis_task = Task(
                description=(
                    "Use the KnowledgeBaseManager tool to synthesize all stakeholder research into a summary. "
                    f"Stakeholders: {stakeholder_list}\nPolicy: {policy_text}\n"
                    "Return a balanced summary."
                ),
                expected_output="Balanced summary of all stakeholder perspectives.",
                agent=action_agent,
            )
        except Exception as e:
            local_logger.error(f"Task setup failed: {e}")
            errors.append(f"Task setup failed: {e}")
            return {"success": False, "errors": errors}

        # 4. Run workflow step by step, catching errors
        try:
            local_logger.info("Running policy discovery task...")
            results['discovery'] = discovery_task.execute()
        except Exception as e:
            local_logger.error(f"Policy discovery failed: {e}")
            errors.append(f"Policy discovery failed: {e}")
        try:
            local_logger.info("Running stakeholder identification task...")
            results['stakeholder_id'] = stakeholder_id_task.execute()
        except Exception as e:
            local_logger.error(f"Stakeholder identification failed: {e}")
            errors.append(f"Stakeholder identification failed: {e}")
        for i, t in enumerate(stakeholder_research_tasks):
            try:
                local_logger.info(f"Running stakeholder research task {i}...")
                results[f'stakeholder_research_{i}'] = t.execute()
            except Exception as e:
                local_logger.error(f"Stakeholder research {i} failed: {e}")
                errors.append(f"Stakeholder research {i} failed: {e}")
        try:
            local_logger.info("Running topic analysis task...")
            results['topic_analysis'] = topic_task.execute()
        except Exception as e:
            local_logger.error(f"Topic analysis failed: {e}")
            errors.append(f"Topic analysis failed: {e}")
        for i, t in enumerate(argument_tasks):
            try:
                local_logger.info(f"Running argument generation task {i}...")
                results[f'argument_{i}'] = t.execute()
            except Exception as e:
                local_logger.error(f"Argument generation {i} failed: {e}")
                errors.append(f"Argument generation {i} failed: {e}")
        try:
            local_logger.info("Running synthesis task...")
            results['synthesis'] = synthesis_task.execute()
        except Exception as e:
            local_logger.error(f"Synthesis failed: {e}")
            errors.append(f"Synthesis failed: {e}")

        results['errors'] = errors
        results['success'] = len(errors) == 0
        return results

    def setup_dynamic_stakeholder_crew(self, stakeholder_list: List[Dict[str, Any]]) -> Crew:
        """Set up a dynamic crew with stakeholder-specific agents"""
        
        # Create stakeholder agents and tasks
        stakeholder_agents = []
        stakeholder_tasks = []
        
        for stakeholder_info in stakeholder_list:
            agent = self.create_stakeholder_agent(stakeholder_info)
            task = self.create_stakeholder_task(stakeholder_info, agent)
            
            stakeholder_agents.append(agent)
            stakeholder_tasks.append(task)
            
            # Store for later reference
            stakeholder_name = stakeholder_info.get("name", "Unknown")
            self.stakeholder_agents[stakeholder_name] = agent
            self.stakeholder_tasks[stakeholder_name] = task
        
        # Combine all agents and tasks
        # Get agents and tasks from the CrewBase class
        base_agents = [self.coordinator_agent(), self.policy_discovery_agent(), 
                      self.policy_debate_agent(), self.advocate_sub_agents(), 
                      self.action_agent(), self.debate_moderator_agent()]
        base_tasks = [self.receive_query_task(), self.fetch_policy_text_task(),
                     self.analyze_policy_text_task(), self.dynamic_sub_agent_creation_task(),
                     self.stakeholder_analysis_task(), self.synthesize_summary_task(),
                     self.draft_email_task(), self.analyze_debate_topics_task(),
                     self.initiate_debate_session_task(), self.conduct_stakeholder_debate_task(),
                     self.moderate_debate_flow_task(), self.summarize_debate_outcomes_task()]
        
        all_agents = base_agents + stakeholder_agents
        all_tasks = base_tasks + stakeholder_tasks
        
        # Create crew with minimal configuration to avoid circular references
        return Crew(
            agents=all_agents,
            tasks=all_tasks,
            process=Process.sequential,
            verbose=True,
            manager_llm=self.llm,
        )

    def setup_debate_crew(self, stakeholder_list: List[Dict[str, Any]]) -> Crew:
        """Set up a crew specifically for conducting structured debates with A2A protocols"""
        
        # Create stakeholder agents with debate capabilities
        stakeholder_agents = []
        stakeholder_tasks = []
        
        for stakeholder_info in stakeholder_list:
            agent = self.create_stakeholder_agent(stakeholder_info)
            stakeholder_agents.append(agent)
            
            stakeholder_name = stakeholder_info.get("name", "Unknown")
            
            # Create stakeholder-specific research task for this agent
            stakeholder_research_task = Task(
                description=f"IMPORTANT: Use the StakeholderResearcher tool directly to conduct detailed analysis of the policy from {stakeholder_name}'s perspective. Do NOT delegate this task. Use the KnowledgeBaseManager tool to store your findings. Use SerperDevTool for additional research if needed. You must complete this analysis yourself using the available tools.",
                expected_output=f"Comprehensive research report from {stakeholder_name}'s perspective stored in the knowledge base using KnowledgeBaseManager.",
                agent=agent,  # Assign to specific stakeholder agent
                tools=[self.stakeholder_researcher, self.knowledge_base_manager, SerperDevTool()]
            )
            
            # Create stakeholder-specific debate task for this agent
            stakeholder_debate_task = Task(
                description=f"IMPORTANT: Use the ArgumentGenerator tool directly to create evidence-based arguments from {stakeholder_name}'s perspective on the debate topics. Use A2AMessenger for structured communication with other agents. Do NOT delegate this task. You must generate arguments yourself using the available tools.",
                expected_output=f"Evidence-based arguments from {stakeholder_name}'s perspective using ArgumentGenerator, with structured communication via A2AMessenger.",
                agent=agent,  # Assign to specific stakeholder agent
                tools=[self.argument_generator, self.a2a_messenger, self.knowledge_base_manager]
            )
            
            stakeholder_tasks.extend([stakeholder_research_task, stakeholder_debate_task])
            
            # Store for later reference
            self.stakeholder_agents[stakeholder_name] = agent
            self.stakeholder_tasks[stakeholder_name] = stakeholder_research_task
        
        # Debate-specific agents (non-stakeholder agents)
        debate_agents = [
            self.debate_moderator_agent(),
            self.coordinator_agent(),
            self.policy_debate_agent(),
        ] + stakeholder_agents
        
        # Debate-specific tasks (non-stakeholder tasks)
        debate_tasks = [
            self.analyze_debate_topics_task(),
            self.initiate_debate_session_task(),
            self.moderate_debate_flow_task(),
            self.summarize_debate_outcomes_task(),
        ] + stakeholder_tasks  # Add stakeholder-specific tasks
        
        return Crew(
            agents=debate_agents,
            tasks=debate_tasks,
            process=Process.hierarchical,
            verbose=True,
            manager_llm=self.llm,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the DynamicCrewAutomationForPolicyAnalysisAndDebate crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.hierarchical,
            verbose=True,
            manager_llm=self.llm,
        )
