"""
Inventory Building Crew - Main Crew Class

This module contains the InventoryBuildingCrew class and factory function.
It handles crew initialization, shared memory setup, knowledge base setup,
and crew creation with the appropriate process type.

DEPRECATED WARNING:
This file is DEPRECATED as of September 2025. Asset inventory now uses
persistent agents via TenantScopedAgentPool. This implementation is kept
for backward compatibility but should not be used for new deployments.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from crewai import Crew, Process

from app.services.crewai_flows.config.crew_factory import create_crew
from app.services.crewai_flows.crews.inventory_building_crew_original.agents import (
    CREWAI_ADVANCED_AVAILABLE,
    create_inventory_agents,
)
from app.services.crewai_flows.crews.inventory_building_crew_original.tasks import (
    create_inventory_tasks,
)

# Import advanced CrewAI features with fallbacks
try:
    from crewai.knowledge import Knowledge, LocalKnowledgeBase
    from crewai.memory import LongTermMemory
except ImportError:
    # Fallback classes
    class LongTermMemory:
        def __init__(self, **kwargs):
            pass

    class Knowledge:
        def __init__(self, **kwargs):
            pass

    class LocalKnowledgeBase:
        def __init__(self, **kwargs):
            pass


logger = logging.getLogger(__name__)


class InventoryBuildingCrew:
    """Enhanced Inventory Building Crew with multi-domain classification"""

    def __init__(self, crewai_service, shared_memory=None, knowledge_base=None):
        """
        Initialize the Inventory Building Crew.

        Args:
            crewai_service: CrewAI service instance
            shared_memory: Optional pre-configured shared memory
            knowledge_base: Optional pre-configured knowledge base
        """
        self.crewai_service = crewai_service

        # Get proper LLM configuration from our LLM config service
        try:
            from app.services.llm_config import get_crewai_llm

            self.llm_model = get_crewai_llm()
            logger.info("✅ Inventory Building Crew using configured DeepInfra LLM")
        except Exception as e:
            logger.warning(f"Failed to get configured LLM, using fallback: {e}")
            self.llm_model = getattr(crewai_service, "llm", None)

        # Setup shared memory and knowledge base
        self.shared_memory = shared_memory or self._setup_shared_memory()
        self.knowledge_base = knowledge_base or self._setup_knowledge_base()

        logger.info(
            "✅ Inventory Building Crew initialized with multi-domain classification"
        )

    def _setup_shared_memory(self) -> Optional[LongTermMemory]:
        """Setup shared memory for cross-domain classification insights"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Shared memory not available - using fallback")
            return None

        try:
            # Use LocalKnowledgeBase for file-based knowledge
            kb = LocalKnowledgeBase(
                collection_name="inventory_building_insights",
                storage_path="./data/memory",
            )
            # LongTermMemory now uses a knowledge_base parameter
            memory = LongTermMemory(knowledge_base=kb)
            logger.info("✅ Shared memory initialized with LocalKnowledgeBase")
            return memory
        except Exception as e:
            logger.warning(f"Failed to setup shared memory: {e}")
            return None

    def _setup_knowledge_base(self) -> Optional[Knowledge]:
        """Setup knowledge base for asset classification rules"""
        if not CREWAI_ADVANCED_AVAILABLE:
            logger.warning("Knowledge base not available - using fallback")
            return None

        try:
            # Use LocalKnowledgeBase for file-based knowledge
            return LocalKnowledgeBase(
                collection_name="asset_classification_rules",
                file_path="backend/app/knowledge_bases/asset_classification_rules.json",
            )
        except Exception as e:
            logger.warning(f"Failed to setup knowledge base: {e}")
            return None

    def create_agents(self):
        """
        Create agents with hierarchical management and domain expertise.

        Returns:
            List of agent instances: [manager, server_expert, app_expert, device_expert]
        """
        return create_inventory_agents(
            llm_model=self.llm_model,
            shared_memory=self.shared_memory,
            knowledge_base=self.knowledge_base,
        )

    def create_tasks(
        self, agents, cleaned_data: List[Dict[str, Any]], field_mappings: Dict[str, Any]
    ):
        """
        Create tasks for inventory building.

        Args:
            agents: List of agent instances
            cleaned_data: List of cleaned asset records to classify
            field_mappings: Field mapping configuration

        Returns:
            List of task instances
        """
        return create_inventory_tasks(agents, cleaned_data, field_mappings)

    def create_crew(
        self,
        cleaned_data: List[Dict[str, Any]],
        field_mappings: Dict[str, Any],
        context_info: Dict[str, Any] = None,
    ):
        """
        Create the inventory building crew with agents and tasks.

        Args:
            cleaned_data: List of cleaned asset records to classify
            field_mappings: Field mapping configuration
            context_info: Optional context information (flow_id, client_account_id, etc.)

        Returns:
            Configured Crew instance
        """
        agents = self.create_agents()

        # Add task completion tools to the inventory manager
        if context_info:
            from app.services.crewai_flows.tools.task_completion_tools import (
                create_task_completion_tools,
            )

            completion_tools = create_task_completion_tools(context_info)
            # Add tools to the inventory manager (first agent)
            if agents and hasattr(agents[0], "tools"):
                agents[0].tools.extend(completion_tools)
            else:
                agents[0].tools = completion_tools

        tasks = self.create_tasks(agents, cleaned_data, field_mappings)

        # Use hierarchical process if advanced features available
        process = (
            Process.hierarchical if CREWAI_ADVANCED_AVAILABLE else Process.sequential
        )

        crew_config = {
            "agents": agents,
            "tasks": tasks,
            "process": process,
            "verbose": True,
        }

        # Add advanced features if available
        if CREWAI_ADVANCED_AVAILABLE:
            # Ensure manager_llm uses our configured LLM and not gpt-4o-mini
            crew_config.update(
                {
                    "manager_llm": self.llm_model,  # Critical: Use our DeepInfra LLM
                    "planning": False,  # DISABLED: Causing loops
                    "planning_llm": self.llm_model,  # Force planning to use our LLM too
                    "memory": False,  # DISABLED: Causing APIStatusError loops
                    "knowledge": None,  # DISABLED: Causing API errors
                    "share_crew": False,  # DISABLED: Causing complexity
                    "collaboration": True,  # Re-enabled for proper agent coordination
                }
            )

            # Additional environment override to prevent any gpt-4o-mini fallback
            os.environ["OPENAI_MODEL_NAME"] = (
                str(self.llm_model)
                if isinstance(self.llm_model, str)
                else "deepinfra/meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8"
            )

        process_name = process.name if hasattr(process, "name") else "sequential"
        logger.info(f"Creating Inventory Building Crew with {process_name} process")
        logger.info(
            f"Using LLM: {self.llm_model if isinstance(self.llm_model, str) else 'Unknown'}"
        )
        return create_crew(**crew_config)


def create_inventory_building_crew(
    crewai_service,
    cleaned_data: List[Dict[str, Any]],
    field_mappings: Dict[str, Any],
    shared_memory=None,
    knowledge_base=None,
    context_info: Dict[str, Any] = None,
) -> Crew:
    """
    Factory function to create enhanced Inventory Building Crew.

    Args:
        crewai_service: CrewAI service instance
        cleaned_data: List of cleaned asset records to classify
        field_mappings: Field mapping configuration
        shared_memory: Optional pre-configured shared memory
        knowledge_base: Optional pre-configured knowledge base
        context_info: Optional context information (flow_id, client_account_id, etc.)

    Returns:
        Configured Crew instance ready for execution
    """
    crew_instance = InventoryBuildingCrew(crewai_service, shared_memory, knowledge_base)
    return crew_instance.create_crew(cleaned_data, field_mappings, context_info)


__all__ = ["InventoryBuildingCrew", "create_inventory_building_crew"]
