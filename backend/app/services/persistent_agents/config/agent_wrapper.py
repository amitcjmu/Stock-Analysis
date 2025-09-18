"""
Agent Wrapper Module

Provides the AgentWrapper class for CrewAI agent compatibility.
"""

import asyncio
import logging
from typing import Any, Dict

try:
    from crewai import Agent

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            pass


logger = logging.getLogger(__name__)


class AgentWrapper:
    """
    Wrapper to add execution methods to CrewAI agents without field modification.
    This solves Pydantic v2 compatibility issues where dynamic field assignment is not allowed.
    """

    def __init__(self, agent: Agent, agent_type: str):
        """Initialize the wrapper with the CrewAI agent and its type."""
        self._agent = agent
        self._agent_type = agent_type
        logger.info(f"✅ Created AgentWrapper for {agent_type}")

    def __getattr__(self, name):
        """Delegate all other attributes to the wrapped agent."""
        return getattr(self._agent, name)

    def execute(self, task: str = None, **kwargs) -> Any:
        """
        Execute a task using this agent in a single-agent crew.
        This provides synchronous execution compatibility.
        """
        try:
            from crewai import Crew, Task

            # Create a task for the agent
            agent_task = Task(
                description=task or "Execute assigned task",
                agent=self._agent,
                expected_output="Structured analysis and recommendations based on the given task",
            )

            # Create a single-agent crew
            crew = Crew(agents=[self._agent], tasks=[agent_task], verbose=False)

            # Execute the crew
            result = crew.kickoff()
            return result

        except Exception as e:
            logger.error(f"Agent {self._agent_type} execute method failed: {e}")
            return {"status": "error", "error": str(e), "agent_type": self._agent_type}

    async def execute_async(
        self, inputs: Dict[str, Any] = None, **kwargs
    ) -> Dict[str, Any]:
        """
        Async execution method using agent tools.
        Provides asynchronous execution compatibility.
        """
        task = kwargs.get("task", "Execute agent task")

        # Extract task from inputs if provided
        if inputs and "task" in inputs:
            task = inputs["task"]

        # Run synchronous execute in thread pool
        try:
            result = await asyncio.to_thread(self.execute, task, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent {self._agent_type} async execute failed: {e}")
            return {"status": "error", "error": str(e), "agent_type": self._agent_type}

    async def process(self, data: Any) -> Dict[str, Any]:
        """
        Adapter method to make CrewAI agents compatible with executor expectations.
        Converts process() calls to execute_task() calls with structured data.

        This is the critical interface method that executors expect.
        """
        try:
            from crewai import Task

            # Create a task description based on data type and agent role
            data_summary = self._create_data_summary(data)
            task_description = (
                f"Process and analyze the provided data for {self._agent_type} "
                f"operations.\n\n{data_summary}"
            )

            # Create a task for the agent to process the data
            task = Task(
                description=task_description,
                agent=self._agent,
                expected_output="Structured analysis with processed data, insights, and classifications in JSON format",
            )

            # Store data in agent context for tools to access
            if hasattr(self._agent, "context"):
                self._agent.context.update({"data": data})
            else:
                self._agent.context = {"data": data}

            # Execute the task using crew
            from crewai import Crew

            crew = Crew(agents=[self._agent], tasks=[task], verbose=False)
            result = crew.kickoff()

            # Return structured response
            return {
                "status": "success",
                "processed_data": data,
                "agent_output": str(result),
                "agent_type": self._agent_type,
                "insights": getattr(self._agent, "insights", []),
                "classifications": getattr(self._agent, "classifications", {}),
                "execution_method": "process_adapter",
            }

        except Exception as e:
            logger.error(f"Agent {self._agent_type} process method failed: {e}")
            # Return fallback response that maintains the expected structure
            return {
                "status": "error",
                "error": str(e),
                "agent_type": self._agent_type,
                "processed_data": data,
                "execution_method": "process_adapter_fallback",
            }

    def _create_data_summary(self, data: Any) -> str:
        """Create a concise summary of the data for task description."""
        try:
            if isinstance(data, list):
                if not data:
                    return "Empty data list provided."

                data_type = type(data[0]).__name__ if data else "unknown"
                sample_keys = []

                if isinstance(data[0], dict):
                    sample_keys = list(data[0].keys())[:5]  # First 5 keys
                    sample_str = f"Sample keys: {sample_keys}"
                    if len(data[0].keys()) > 5:
                        sample_str += f" (and {len(data[0].keys()) - 5} more)"
                else:
                    sample_str = f"Sample value: {str(data[0])[:100]}..."

                return f"Data: {len(data)} {data_type} records. {sample_str}"

            elif isinstance(data, dict):
                keys = list(data.keys())[:5]
                key_str = f"Keys: {keys}"
                if len(data.keys()) > 5:
                    key_str += f" (and {len(data.keys()) - 5} more)"
                return f"Data: Dictionary with {len(data)} items. {key_str}"

            else:
                return f"Data: {type(data).__name__} - {str(data)[:100]}..."

        except Exception as e:
            logger.warning(f"Failed to create data summary: {e}")
            return f"Data provided for processing (summary generation failed: {e})"
