"""
App-Server Dependency Crew - Main Class Implementation

This module contains the main AppServerDependencyCrew class which provides
a high-level interface for creating and managing the app-server dependency
analysis crew with all its agents, tasks, and tools.

The class follows the enterprise pattern of:
- Graceful degradation with fallback support
- Shared memory integration for cross-crew collaboration
- Knowledge base integration for dependency patterns
- Hierarchical management with delegation capabilities
"""

import logging
from typing import Any, Dict, Optional

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import create_crew

logger = logging.getLogger(__name__)

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge.knowledge import Knowledge
    from crewai.memory import LongTermMemory

    CREWAI_ADVANCED_AVAILABLE = True
except ImportError:
    CREWAI_ADVANCED_AVAILABLE = False

    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass

    class Knowledge:
        def __init__(self, **kwargs):
            pass


class AppServerDependencyCrew:
    """Enhanced App-Server Dependency Crew for hosting relationship mapping"""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        """
        Initialize the App-Server Dependency Crew.

        Args:
            crewai_service: Service providing LLM configuration
            shared_memory: Optional shared memory for cross-crew collaboration
            knowledge_base: Optional knowledge base for dependency patterns
        """
        self.crewai_service = crewai_service

        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ App-Server Dependency Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()

        logger.info("✅ App-Server Dependency Crew initialized with hosting analysis")

    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for dependency pattern insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None

        try:
            return LongTermMemory(
                storage_type="vector",
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None

    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for dependency analysis patterns"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None

        try:
            return Knowledge(
                sources=[
                    "backend/app/knowledge_bases/dependency_analysis_patterns.json"
                ],
                embedder_config={
                    "provider": "openai",
                    "model": "text-embedding-3-small",
                },
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None

    def create_agents(self, asset_inventory: Dict[str, Any]):
        """
        Create agents with hierarchical management for dependency analysis.

        Args:
            asset_inventory: Dictionary containing servers and applications

        Returns:
            List of configured agents
        """
        from app.services.crewai_flows.crews.app_server_dependency_crew.agents import (
            create_app_server_dependency_agents,
        )

        return create_app_server_dependency_agents(
            llm_model=self.llm_model,
            shared_memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
            asset_inventory=asset_inventory,
            tools_available=True,
        )

    def create_tasks(self, agents, asset_inventory: Dict[str, Any]):
        """
        Create hierarchical tasks for app-server dependency analysis.

        Args:
            agents: List of agents for task assignment
            asset_inventory: Dictionary containing servers and applications

        Returns:
            List of configured tasks
        """
        from app.services.crewai_flows.crews.app_server_dependency_crew.tasks import (
            create_app_server_dependency_tasks,
        )

        return create_app_server_dependency_tasks(agents, asset_inventory)

    def create_crew(self, asset_inventory: Dict[str, Any]) -> Crew:
        """
        Create hierarchical crew for app-server dependency analysis.

        Args:
            asset_inventory: Dictionary containing servers and applications

        Returns:
            Configured Crew instance ready for execution
        """
        agents = self.create_agents(asset_inventory)
        tasks = self.create_tasks(agents, asset_inventory)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
            "max_iterations": 10,  # Limit total crew iterations
            "step_callback": lambda step: logger.info(f"Crew step {step}"),
        }

        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update(
                {
                    "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                    "planning": True,
                    "planning_llm": self.llm_model,  # Force planning to use our LLM too
                    "memory": True,
                    "knowledge": self.knowledge_base,
                    "share_crew": True,
                    "collaboration": True,
                }
            )

            # Additional environment override to prevent any gpt-4o-mini fallback
            import os

            os.environ["OPENAI_MODEL_NAME"] = (
                str(self.llm_model)
                if isinstance(self.llm_model, str)
                else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            )

        logger.info(
            f"Creating App-Server Dependency Crew with "
            f"{process.name if hasattr(process, 'name') else 'sequential'} process"
        )
        logger.info(
            f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}"
        )
        return create_crew(**crew_config)


# Export main class for backward compatibility
__all__ = ["AppServerDependencyCrew"]
