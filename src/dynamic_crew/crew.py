from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai_tools import ScrapeWebsiteTool
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dynamic_crew.tools.custom_tool import (
    PolicyFileReader, 
    StakeholderIdentifier, 
    KnowledgeBaseManager, 
    StakeholderResearcher,
    TopicAnalyzer,
    ArgumentGenerator,
    A2AMessenger,
    DebateModerator
)
from typing import List, Dict, Any

@CrewBase
class DynamicCrewAutomationForPolicyAnalysisAndDebateCrew():
    """DynamicCrewAutomationForPolicyAnalysisAndDebate crew"""
    
    def __init__(self):
        super().__init__()
        self.stakeholder_agents = {}
        self.stakeholder_tasks = {}
        self.policy_file_reader = PolicyFileReader()
        self.stakeholder_identifier = StakeholderIdentifier()
        self.knowledge_base_manager = KnowledgeBaseManager()
        self.stakeholder_researcher = StakeholderResearcher()
        self.topic_analyzer = TopicAnalyzer()
        self.argument_generator = ArgumentGenerator()
        self.a2a_messenger = A2AMessenger()
        self.debate_moderator = DebateModerator()
        
        # Configure Gemini LLM for CrewAI
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            # Try GROQ instead as it's more compatible with CrewAI
            from langchain_groq import ChatGroq
            groq_api_key = os.getenv('GROQ_API_KEY')
            if groq_api_key:
                # Check if we should use Weave API instead
                weave_api_key = os.getenv('WEAVE_API_KEY')
                if weave_api_key:
                    from langchain_openai import ChatOpenAI
                    self.llm = ChatOpenAI(
                        model="openai/meta-llama/Llama-4-Scout-17B-16E-Instruct",
                        base_url="https://api.inference.wandb.ai/v1",
                        api_key=weave_api_key,
                        temperature=0.7,
                        default_headers={"OpenAI-Project": "crewai/pop_smoke"}
                    )
                else:
                    self.llm = ChatGroq(
                        model="llama-3.1-70b-versatile",
                        api_key=groq_api_key,
                        temperature=0.7
                    )
            else:
                # Fallback to simpler Gemini configuration
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=gemini_api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True  # This helps with CrewAI compatibility
                )
        else:
            raise ValueError("GEMINI_API_KEY environment variable is required")

    @agent
    def coordinator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['coordinator_agent'],
            tools=[self.policy_file_reader],
            llm=self.llm,
        )

    @agent
    def policy_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['policy_discovery_agent'],
            tools=[self.policy_file_reader, SerperDevTool(), ScrapeWebsiteTool()],
            llm=self.llm,
        )

    @agent
    def policy_debate_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['policy_debate_agent'],
            tools=[
                self.stakeholder_identifier, 
                self.knowledge_base_manager,
                SerperDevTool(), 
                ScrapeWebsiteTool()
            ],
            llm=self.llm,
        )

    @agent
    def advocate_sub_agents(self) -> Agent:
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
        )

    @agent
    def action_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['action_agent'],
            tools=[self.knowledge_base_manager],
            llm=self.llm,
        )

    @agent
    def debate_moderator_agent(self) -> Agent:
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
        )

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
            allow_delegation=agent_config["allow_delegation"],
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
        
        task_config = {
            "description": f"Research and analyze the policy from {stakeholder_name}'s perspective. Use the StakeholderResearcher tool to conduct detailed analysis and store findings in the knowledge base.",
            "expected_output": f"Comprehensive analysis of policy impacts on {stakeholder_name}, including key arguments, concerns, and recommendations.",
            "agent": agent,
            "tools": [self.stakeholder_researcher, self.knowledge_base_manager]
        }
        
        task = Task(
            description=task_config["description"],
            expected_output=task_config["expected_output"],
            agent=task_config["agent"],
            tools=task_config["tools"]
        )
        
        return task

    @task
    def receive_query_task(self) -> Task:
        return Task(
            config=self.tasks_config['receive_query_task'],
            tools=[self.policy_file_reader],
        )

    @task
    def fetch_policy_text_task(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_policy_text_task'],
            tools=[self.policy_file_reader, SerperDevTool(), ScrapeWebsiteTool()],
        )

    @task
    def analyze_policy_text_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_policy_text_task'],
            tools=[self.stakeholder_identifier],
        )

    @task
    def dynamic_sub_agent_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['dynamic_sub_agent_creation_task'],
            tools=[self.stakeholder_identifier, self.knowledge_base_manager],
        )

    @task
    def stakeholder_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['stakeholder_analysis_task'],
            tools=[self.stakeholder_researcher, self.knowledge_base_manager],
        )

    @task
    def synthesize_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['synthesize_summary_task'],
            tools=[self.knowledge_base_manager],
        )

    @task
    def draft_email_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_email_task'],
            tools=[self.knowledge_base_manager],
        )

    @task
    def analyze_debate_topics_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_debate_topics_task'],
            tools=[self.topic_analyzer],
        )

    @task
    def initiate_debate_session_task(self) -> Task:
        return Task(
            config=self.tasks_config['initiate_debate_session_task'],
            tools=[self.debate_moderator, self.knowledge_base_manager],
        )

    @task
    def conduct_stakeholder_debate_task(self) -> Task:
        return Task(
            config=self.tasks_config['conduct_stakeholder_debate_task'],
            tools=[self.argument_generator, self.a2a_messenger, self.knowledge_base_manager],
        )

    @task
    def moderate_debate_flow_task(self) -> Task:
        return Task(
            config=self.tasks_config['moderate_debate_flow_task'],
            tools=[self.debate_moderator, self.a2a_messenger],
        )

    @task
    def summarize_debate_outcomes_task(self) -> Task:
        return Task(
            config=self.tasks_config['summarize_debate_outcomes_task'],
            tools=[self.debate_moderator, self.knowledge_base_manager],
        )

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
        all_agents = self.agents + stakeholder_agents
        all_tasks = self.tasks + stakeholder_tasks
        
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
        
        for stakeholder_info in stakeholder_list:
            agent = self.create_stakeholder_agent(stakeholder_info)
            stakeholder_agents.append(agent)
            
            # Store for later reference
            stakeholder_name = stakeholder_info.get("name", "Unknown")
            self.stakeholder_agents[stakeholder_name] = agent
        
        # Debate-specific agents
        debate_agents = [
            self.debate_moderator_agent(),
            self.coordinator_agent(),
            self.policy_debate_agent(),
        ] + stakeholder_agents
        
        # Debate-specific tasks
        debate_tasks = [
            self.stakeholder_analysis_task(),
            self.analyze_debate_topics_task(),
            self.initiate_debate_session_task(),
            self.conduct_stakeholder_debate_task(),
            self.moderate_debate_flow_task(),
            self.summarize_debate_outcomes_task(),
        ]
        
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
            process=Process.sequential,  # Changed from hierarchical to sequential
            verbose=True,
            # manager_llm=self.llm,  # Commented out since sequential doesn't need manager
        )
