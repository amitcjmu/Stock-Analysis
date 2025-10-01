"""
CrewAI Factory Pattern Implementation

Provides factory classes for creating CrewAI agents, crews, and tasks
with explicit configuration instead of global monkey patches.

References:
- docs/code-reviews/2025-10-01_discovery_flow_over_abstraction_review.md
"""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    from crewai import Agent, Crew, Process, Task  # type: ignore[import-not-found]

    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # Provide stubs for type hints
    Agent = Any  # type: ignore[misc]
    Crew = Any  # type: ignore[misc]
    Task = Any  # type: ignore[misc]

    # Create a mock Process enum for type hints
    class Process:  # type: ignore[no-redef]
        sequential = "sequential"
        hierarchical = "hierarchical"


from app.services.crewai_flows.config.crew_factory.config import CrewConfig
from app.services.crewai_flows.config.embedder_config import EmbedderConfig

logger = logging.getLogger(__name__)


class CrewFactory:
    """
    Factory for creating CrewAI agents and crews with explicit configuration.

    This factory applies sensible defaults while allowing full customization
    at the point of creation, avoiding global monkey patches.
    """

    def __init__(
        self,
        enable_memory: bool = True,
        default_timeout: Optional[int] = None,
        verbose: bool = False,
    ):
        """
        Initialize the factory with global settings.

        Args:
            enable_memory: Enable memory for all agents/crews by default
            default_timeout: Default timeout for crew execution
            verbose: Enable verbose logging by default
        """
        self.enable_memory = enable_memory
        self.default_timeout = default_timeout or CrewConfig.get_default_timeout()
        self.verbose = verbose

        logger.info(
            f"CrewFactory initialized: memory={enable_memory}, "
            f"timeout={self.default_timeout}s, verbose={verbose}"
        )

    def create_agent(
        self,
        role: str,
        goal: str,
        backstory: str,
        llm: Optional[Any] = None,
        tools: Optional[List[Any]] = None,
        allow_delegation: bool = False,
        max_iter: int = 1,
        verbose: Optional[bool] = None,
        memory: Optional[bool] = None,
        **kwargs,
    ) -> Agent:
        """
        Create an agent with factory defaults and explicit overrides.

        Args:
            role: Agent role/name
            goal: Agent goal
            backstory: Agent backstory/context
            llm: Language model to use
            tools: List of tools for the agent
            allow_delegation: Whether agent can delegate tasks
            max_iter: Maximum iterations per task
            verbose: Enable verbose logging
            memory: Enable memory for this agent
            **kwargs: Additional agent parameters

        Returns:
            Configured Agent instance
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI is not available")

        # Start with defaults
        config = CrewConfig.get_agent_defaults(
            allow_delegation=allow_delegation,
            max_iter=max_iter,
            verbose=verbose if verbose is not None else self.verbose,
            memory=memory if memory is not None else self.enable_memory,
        )

        # Set required fields
        config["role"] = role
        config["goal"] = goal
        config["backstory"] = backstory

        if llm is not None:
            config["llm"] = llm

        if tools is not None:
            config["tools"] = tools

        # Apply additional kwargs (allows full customization)
        config.update(kwargs)

        # Apply embedder configuration if memory is enabled
        if config.get("memory", False):
            embedder = EmbedderConfig.get_embedder_for_crew(memory_enabled=True)
            if embedder:
                config["embedder"] = embedder

        logger.debug(
            f"Creating agent: {role} (delegation={config['allow_delegation']}, memory={config.get('memory', False)})"
        )

        return Agent(**config)

    def create_crew(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.sequential,
        max_execution_time: Optional[int] = None,
        max_iterations: int = 1,
        verbose: Optional[bool] = None,
        memory: Optional[bool] = None,
        manager_llm: Optional[Any] = None,
        **kwargs,
    ) -> Crew:
        """
        Create a crew with factory defaults and explicit overrides.

        Args:
            agents: List of agents in the crew
            tasks: List of tasks for the crew
            process: Crew process type (sequential/hierarchical)
            max_execution_time: Timeout in seconds
            max_iterations: Maximum crew iterations
            verbose: Enable verbose logging
            memory: Enable memory for this crew
            manager_llm: LLM for hierarchical manager (if process is hierarchical)
            **kwargs: Additional crew parameters

        Returns:
            Configured Crew instance
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI is not available")

        # Start with defaults
        config = CrewConfig.get_crew_defaults(
            max_execution_time=max_execution_time or self.default_timeout,
            max_iterations=max_iterations,
            verbose=verbose if verbose is not None else self.verbose,
            memory=memory if memory is not None else self.enable_memory,
            process=process,
        )

        # Set required fields
        config["agents"] = agents
        config["tasks"] = tasks

        # Hierarchical process requires manager
        if process == Process.hierarchical and manager_llm is not None:
            config["manager_llm"] = manager_llm

        # Apply additional kwargs (allows full customization)
        config.update(kwargs)

        # Apply embedder configuration if memory is enabled
        if config.get("memory", False):
            embedder = EmbedderConfig.get_embedder_for_crew(memory_enabled=True)
            if embedder:
                config["embedder"] = embedder
                # Also set memory_config for compatibility
                config["memory_config"] = {
                    "provider": embedder["provider"],
                    "config": embedder["config"].copy(),
                }
        else:
            # If memory is disabled, ensure embedder is None
            config["embedder"] = None

        logger.debug(
            f"Creating crew: {len(agents)} agents, {len(tasks)} tasks, "
            f"process={process}, timeout={config['max_execution_time']}s"
        )

        return Crew(**config)

    def create_task(
        self,
        description: str,
        agent: Agent,
        expected_output: str,
        async_execution: bool = False,
        context: Optional[List[Task]] = None,
        **kwargs,
    ) -> Task:
        """
        Create a task with sensible defaults.

        Args:
            description: Task description
            agent: Agent assigned to this task
            expected_output: Expected output description
            async_execution: Enable async execution
            context: List of context tasks
            **kwargs: Additional task parameters

        Returns:
            Configured Task instance
        """
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI is not available")

        config = {
            "description": description,
            "agent": agent,
            "expected_output": expected_output,
            "async_execution": async_execution,
        }

        if context:
            config["context"] = context

        # Apply additional kwargs
        config.update(kwargs)

        return Task(**config)


class CrewMemoryManager:
    """
    Manager for crew memory configuration.

    This provides a centralized way to manage memory settings
    for agents and crews, separate from the embedder configuration.
    """

    @staticmethod
    def is_memory_enabled() -> bool:
        """
        Check if memory is globally enabled.

        Returns:
            True if memory should be enabled by default
        """
        # Memory is enabled by default unless explicitly disabled
        return os.getenv("CREWAI_DISABLE_MEMORY", "false").lower() != "true"

    @staticmethod
    def get_memory_config(
        long_term: bool = True,
        short_term: bool = True,
        entity: bool = False,
    ) -> Dict[str, Any]:
        """
        Get memory configuration for a crew.

        Args:
            long_term: Enable long-term memory
            short_term: Enable short-term memory
            entity: Enable entity memory

        Returns:
            Memory configuration dictionary
        """
        if not CrewMemoryManager.is_memory_enabled():
            return {"memory": False}

        config = {
            "memory": True,
            "long_term_memory": long_term,
            "short_term_memory": short_term,
            "entity_memory": entity,
        }

        # Add embedder configuration
        embedder = EmbedderConfig.get_embedder_for_crew(memory_enabled=True)
        if embedder:
            config["embedder"] = embedder  # type: ignore[assignment]

        return config


# Global factory instance for convenience
default_factory = CrewFactory(
    enable_memory=CrewMemoryManager.is_memory_enabled(),
    verbose=os.getenv("CREWAI_VERBOSE", "false").lower() == "true",
)
