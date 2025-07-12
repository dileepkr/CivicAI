from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai_tools import ScrapeWebsiteTool

@CrewBase
class DynamicCrewAutomationForPolicyAnalysisAndDebateCrew():
    """DynamicCrewAutomationForPolicyAnalysisAndDebate crew"""

    @agent
    def coordinator_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['coordinator_agent'],
            tools=[],
        )

    @agent
    def policy_discovery_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['policy_discovery_agent'],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
        )

    @agent
    def policy_debate_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['policy_debate_agent'],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
        )

    @agent
    def advocate_sub_agents(self) -> Agent:
        return Agent(
            config=self.agents_config['advocate_sub_agents'],
            tools=[],
        )

    @agent
    def action_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['action_agent'],
            tools=[],
        )


    @task
    def receive_query_task(self) -> Task:
        return Task(
            config=self.tasks_config['receive_query_task'],
            tools=[],
        )

    @task
    def fetch_policy_text_task(self) -> Task:
        return Task(
            config=self.tasks_config['fetch_policy_text_task'],
            tools=[SerperDevTool(), ScrapeWebsiteTool()],
        )

    @task
    def analyze_policy_text_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_policy_text_task'],
            tools=[],
        )

    @task
    def dynamic_sub_agent_creation_task(self) -> Task:
        return Task(
            config=self.tasks_config['dynamic_sub_agent_creation_task'],
            tools=[],
        )

    @task
    def stakeholder_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['stakeholder_analysis_task'],
            tools=[],
        )

    @task
    def synthesize_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config['synthesize_summary_task'],
            tools=[],
        )

    @task
    def draft_email_task(self) -> Task:
        return Task(
            config=self.tasks_config['draft_email_task'],
            tools=[],
        )


    @crew
    def crew(self) -> Crew:
        """Creates the DynamicCrewAutomationForPolicyAnalysisAndDebate crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
