"""This module contains the definition of the Customer Support Representative agent."""
import os

from crewai import LLM, Agent, Crew, Task
from crewai.process import Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import FileReadTool, MCPServerAdapter

import app
from app.ai_tools.database import UnsafeDatabaseQueryTool
from app.ai_tools.db_tool import DatabaseTool

BaseURL = os.environ.get('AI_BASE_URL', 'https://www.google.com')
AI_api_key = os.environ.get('AI_API_KEY', 'your_api_key_here')
Model= os.environ.get('AI_MODEL', 'anthropic/claude-3-7-sonnet-20250219')
FileRead = FileReadTool(file_path='/app/app/personal_data.txt')
Database = DatabaseTool()
Raw_Database = UnsafeDatabaseQueryTool(
    db=app.db,
    app=app.create_app(),
)  # type: ignore

@CrewBase
class AgentCrew:
    """Base class for the Customer Support Representative agent crew."""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    llm = LLM(
        model=Model,
        api_base=BaseURL,
        api_key=AI_api_key,
    )

    @agent
    def customer_support_agent(self) -> Agent:
        """Create a customer support representative agent."""
        return Agent(
            config=self.agents_config['customer_support_agent'],
            tools=[FileRead, Database, Raw_Database],
            llm=self.llm,
            verbose=True
        )  # type: ignore

    @task
    def customer_support_task(self) -> Task:
        """
        Creates the main task for the customer support agent.
        The task's description and expected output are loaded from the tasks.yaml file.
        The {user_message} placeholder will be filled in at runtime.
        """
        return Task(
            config=self.tasks_config['customer_support_task'],
            agent=self.customer_support_agent()
        )  # type: ignore

    @crew
    def create_crew(self) -> Crew:
        """
        Assembles the agent and task into a sequential crew.
        The @crew decorator automatically collects the defined agents and tasks.
        """
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            # Set to a higher level for more detailed crew-wide logging.
            verbose=True
        )
