"""
Tenant Scoped Agent Pool - Agent Configuration Module

This module handles agent configuration, setup, and management
for the tenant scoped agent pool system.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from crewai import Agent, Crew

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

    class Agent:
        def __init__(self, **kwargs):
            pass

    class Crew:
        def __init__(self, **kwargs):
            pass


# Import LLM configuration
try:
    from app.services.llm_config import get_crewai_llm

    LLM_CONFIG_AVAILABLE = True
except ImportError:
    LLM_CONFIG_AVAILABLE = False

    def get_crewai_llm():
        return None


from app.services.agentic_memory.three_tier_memory_manager import ThreeTierMemoryManager
from .tool_manager import AgentToolManager

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
        import asyncio

        try:
            result = await asyncio.to_thread(self.execute, task, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Agent {self._agent_type} async execute failed: {e}")
            return {"status": "error", "error": str(e), "agent_type": self._agent_type}


@dataclass
class AgentHealth:
    """Agent health status information."""

    is_healthy: bool
    last_check: datetime
    response_time: float
    memory_usage: float
    error_count: int
    last_error: Optional[str] = None


class AgentConfigManager:
    """Manages agent configuration and creation for the tenant scoped agent pool."""

    @classmethod
    async def create_agent_with_memory(
        cls,
        agent_type: str,
        client_account_id: str,
        engagement_id: str,
        context_info: Dict[str, Any],
    ) -> Agent:
        """Create a new agent with memory capabilities."""
        try:
            if not CREWAI_AVAILABLE:
                logger.warning("CrewAI not available, returning placeholder agent")
                return Agent()

            # Get agent configuration
            config = cls.get_agent_config(agent_type)

            # Initialize memory manager
            try:
                memory_manager = ThreeTierMemoryManager(
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                )
                # Memory manager initializes synchronously in __init__, no async initialize() needed
                logger.info(f"Memory manager initialized for {agent_type}")
            except Exception as e:
                logger.warning(f"Failed to initialize memory manager: {e}")
                memory_manager = None

            # Get LLM for the agent
            llm = get_crewai_llm() if LLM_CONFIG_AVAILABLE else None

            # Get tools for this agent type
            tools = AgentToolManager.get_agent_tools(agent_type, context_info)
            tool_names = [getattr(t, "name", "unnamed") for t in tools]
            logger.info(f"🔧 Agent {agent_type} tools: {tool_names}")

            # Create the agent with configuration
            agent = Agent(
                role=config["role"],
                goal=config["goal"],
                backstory=config["backstory"],
                tools=tools,
                llm=llm,
                memory=memory_manager,
                verbose=config.get("verbose", True),
                allow_delegation=config.get("allow_delegation", False),
                max_iter=config.get("max_iter", 5),
                max_execution_time=config.get("max_execution_time", 300),
            )

            # Wrap agent with execution methods for Pydantic v2 compatibility
            agent_wrapper = cls._add_execute_method(agent, agent_type)

            # Warm up the agent
            await cls.warm_up_agent(agent_wrapper, agent_type)

            logger.info(
                f"Created {agent_type} agent for client {client_account_id}, "
                f"engagement {engagement_id} with {len(tools)} tools"
            )
            return agent_wrapper

        except Exception as e:
            logger.error(f"Failed to create agent {agent_type}: {e}")
            raise

    @classmethod
    async def warm_up_agent(cls, agent: Agent, agent_type: str):
        """Warm up agent by running a simple test to verify functionality."""
        try:
            if not CREWAI_AVAILABLE:
                return

            # Create a simple warm-up task
            warmup_input = {
                "task": f"Verify {agent_type} agent is ready for operation",
                "context": "System initialization",
            }

            # Execute with timeout to prevent hanging - handle different agent types
            if hasattr(agent, "execute_async"):
                await asyncio.wait_for(
                    agent.execute_async(inputs=warmup_input), timeout=30.0
                )
            elif hasattr(agent, "execute"):
                # Fallback to sync execute method if async not available
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: agent.execute(task="System warmup check")
                    ),
                    timeout=30.0,
                )
            else:
                logger.warning(
                    f"{agent_type} agent has no execute method - skipping warmup"
                )
                return

            logger.info(f"{agent_type} agent warmed up successfully")
        except asyncio.TimeoutError:
            logger.warning(f"{agent_type} agent warm-up timed out")
        except Exception as e:
            logger.warning(f"{agent_type} agent warm-up failed: {e}")

    @classmethod
    def _add_execute_method(cls, agent: Agent, agent_type: str) -> AgentWrapper:
        """
        Wrap agent with execution methods for Pydantic v2 compatibility.

        This method returns an AgentWrapper that provides execute methods
        without modifying the original CrewAI Agent object, which would
        violate Pydantic v2's strict field validation.

        Args:
            agent: The CrewAI Agent instance
            agent_type: The type of agent being wrapped

        Returns:
            AgentWrapper: A wrapper providing execute methods
        """
        return AgentWrapper(agent, agent_type)

    @classmethod
    async def check_agent_health(cls, agent: Agent) -> AgentHealth:
        """Check the health status of an agent."""
        start_time = datetime.now()

        try:
            if not CREWAI_AVAILABLE:
                return AgentHealth(
                    is_healthy=False,
                    last_check=start_time,
                    response_time=0.0,
                    memory_usage=0.0,
                    error_count=1,
                    last_error="CrewAI not available",
                )

            # Simple health check task
            health_check_input = {
                "task": "Health check - respond with 'OK'",
                "context": "System health monitoring",
            }

            # Execute health check with timeout - handle different agent types
            if hasattr(agent, "execute_async"):
                response = await asyncio.wait_for(
                    agent.execute_async(inputs=health_check_input), timeout=10.0
                )
            elif hasattr(agent, "execute"):
                # Fallback to sync execute method if async not available
                response = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, lambda: agent.execute(task="Health check")
                    ),
                    timeout=10.0,
                )
            else:
                # Agent has no execute method
                return AgentHealth(
                    is_healthy=False,
                    last_check=datetime.now(),
                    response_time=(datetime.now() - start_time).total_seconds(),
                    memory_usage=0.0,
                    error_count=1,
                    last_error="Agent has no execute method",
                )

            response_time = (datetime.now() - start_time).total_seconds()

            # Check if response is valid
            is_healthy = response is not None and str(response).strip() != ""

            return AgentHealth(
                is_healthy=is_healthy,
                last_check=datetime.now(),
                response_time=response_time,
                memory_usage=0.0,  # Would need memory tracking implementation
                error_count=0 if is_healthy else 1,
                last_error=None if is_healthy else "Empty or invalid response",
            )

        except asyncio.TimeoutError:
            return AgentHealth(
                is_healthy=False,
                last_check=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds(),
                memory_usage=0.0,
                error_count=1,
                last_error="Health check timeout",
            )
        except Exception as e:
            return AgentHealth(
                is_healthy=False,
                last_check=datetime.now(),
                response_time=(datetime.now() - start_time).total_seconds(),
                memory_usage=0.0,
                error_count=1,
                last_error=str(e),
            )

    @classmethod
    def get_agent_config(cls, agent_type: str) -> Dict[str, Any]:
        """Get configuration for the specified agent type."""
        configs = {
            "discovery": {
                "role": "Infrastructure Discovery Agent",
                "goal": "Analyze and categorize infrastructure data for migration planning",
                "backstory": (
                    "You are an expert infrastructure analyst specializing in cloud migration assessments. "
                    "You understand complex infrastructure relationships and can identify migration patterns."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 5,
                "max_execution_time": 300,
            },
            "field_mapper": {
                "role": "Data Field Mapping Specialist",
                "goal": "Create accurate mappings between source data fields and target schema fields",
                "backstory": (
                    "You are a data mapping expert who understands various data formats and can create "
                    "accurate field-to-field mappings for data migration."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 3,
                "max_execution_time": 180,
            },
            "data_cleansing": {
                "role": "Data Quality and Cleansing Agent",
                "goal": "Identify and resolve data quality issues in migration datasets",
                "backstory": (
                    "You are a data quality specialist who can identify inconsistencies, duplicates, and "
                    "quality issues in datasets and recommend cleansing strategies."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 4,
                "max_execution_time": 240,
            },
            "questionnaire_generator": {
                "role": "Business Questionnaire Generation Agent",
                "goal": "Generate targeted questionnaires to gather missing business context",
                "backstory": (
                    "You are a business analyst expert who creates focused questionnaires to gather "
                    "critical missing information for migration planning."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 3,
                "max_execution_time": 150,
            },
            "six_r_analyzer": {
                "role": "6R Migration Strategy Analyst",
                "goal": "Analyze infrastructure and recommend optimal 6R migration strategies",
                "backstory": (
                    "You are a cloud migration strategist expert in the 6R framework (Retire, Retain, Rehost, "
                    "Replat, Refactor, Rearchitect) for making optimal migration recommendations."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 4,
                "max_execution_time": 300,
            },
            "assessment_coordinator": {
                "role": "Assessment Coordination Agent",
                "goal": "Coordinate and orchestrate multi-phase assessment workflows",
                "backstory": (
                    "You are a project coordination specialist who manages complex assessment workflows "
                    "and ensures all phases complete successfully."
                ),
                "verbose": True,
                "allow_delegation": True,
                "max_iter": 6,
                "max_execution_time": 400,
            },
            "asset_inventory": {
                "role": "Asset Inventory Specialist",
                "goal": "Create database asset records efficiently from cleaned CMDB data",
                "backstory": (
                    "You are an expert asset inventory specialist focused on direct execution "
                    "of asset creation tasks. You transform validated CMDB data into database records "
                    "without extensive analysis, ensuring efficient and accurate asset cataloging."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 3,
                "max_execution_time": 180,
            },
            "readiness_assessor": {
                "role": "Collection Readiness Assessment Agent",
                "goal": "Assess readiness for transition from collection to assessment phase",
                "backstory": (
                    "You are an expert business analyst who evaluates data collection completeness "
                    "and quality to determine readiness for migration assessment. You make intelligent "
                    "decisions based on data quality, completeness metrics, and business requirements."
                ),
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 2,
                "max_execution_time": 120,
            },
        }

        # Return configuration or default
        return configs.get(
            agent_type,
            {
                "role": f"{agent_type.title()} Agent",
                "goal": f"Perform {agent_type} operations",
                "backstory": f"You are an expert {agent_type} specialist.",
                "verbose": True,
                "allow_delegation": False,
                "max_iter": 5,
                "max_execution_time": 300,
            },
        )
