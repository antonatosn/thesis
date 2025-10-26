import os
import yaml
from crewai import LLM, Agent, Crew, Task
from crewai.process import Process
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import MCPServerAdapter

# --- Configuration ---
BaseURL = os.environ.get("AI_BASE_URL", "https://api.anthropic.com/v1")
AI_api_key = os.environ.get("ANTHROPIC_API_KEY", "your_api_key_here")
Model = os.environ.get("AI_MODEL", "claude-3-haiku-20240307")

# Define the connection parameters for your MCP server
mcp_params = {
    "transport": "streamable-http",
    # Make sure 'mcp_server' is the correct hostname for your container
    "url": "http://mcp_server:6000/mcp",
}


@CrewBase
class AgentCrew:
    """Base class for the Customer Support Representative agent crew."""

    def __init__(self, mcp_tools):
        self.mcp_tools = mcp_tools
        self.llm = LLM(
            model=Model,
            api_key=AI_api_key,
            max_tokens=4096,
            verbose=True,
        )
        with open(os.path.abspath("app/config/agents.yaml"), 'r') as f:
            self.agents_data = yaml.safe_load(f)
        with open(os.path.abspath("app/config/tasks.yaml"), 'r') as f:
            self.tasks_data = yaml.safe_load(f)

    @agent
    def customer_support_agent(self) -> Agent:
        """Create a customer support representative agent."""
        agent_data = self.agents_data['customer_support_agent']
        return Agent(
            **agent_data,
            # Correctly pass the tools from the MCP server
            tools=self.mcp_tools,
            llm=self.llm,
            verbose=True,
        )

    @task
    def customer_support_task(self) -> Task:
        """Creates the main task for the customer support agent."""
        task_data = self.tasks_data['customer_support_task']
        return Task(
            **task_data
        )

    @crew
    def create_crew(self) -> Crew:
        """Assembles the agent and task into a sequential crew."""
        agent = self.customer_support_agent()
        task = self.customer_support_task()
        task.agent = agent
        return Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )


def run_chat(user_message: str) -> str:
    """Run the chat agent with the given user message."""
    print("Attempting to connect to MCP server...")

    # Use the context manager to handle the connection
    # The 'tools' variable will be a list of all tools from the server
    try:
        with MCPServerAdapter(serverparams=mcp_params) as tools:
            print(f"Successfully connected. Discovered tools: {[tool.name for tool in tools]}")

            # Now that we have the tools, we can create our crew
            agent_crew_instance = AgentCrew(mcp_tools=tools)

            # Define the input for the task
            inputs = {"user_message": user_message}

            # Kick off the crew
            result = agent_crew_instance.create_crew().kickoff(inputs=inputs)

            print("\n\nCrew work finished. Here is the result:")
            print(result)
            return result.raw

    except Exception as e:
        print(f"An error occurred: {e}")
        print(
            "Please ensure the FastMCP server is running and accessible at 'http://mcp_server:6000'."
        )
        return f"An error occurred: {e}"