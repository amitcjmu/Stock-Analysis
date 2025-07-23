"""
Agent Registry - Modular Structure

This package provides modular agent registry functionality for managing
all agents across all phases with detailed metadata and observability support.

Generated with CC for modular backend architecture.
"""

# Core registry components
from .base import AgentPhase, AgentRegistration, AgentStatus
from .lifecycle_manager import AgentLifecycleManager

# Phase-specific agent groups
from .phase_agents import (
    AssessmentAgentManager,
    DecommissionAgentManager,
    DiscoveryAgentManager,
    FinOpsAgentManager,
    LearningContextAgentManager,
    MigrationAgentManager,
    ModernizationAgentManager,
    ObservabilityAgentManager,
    PlanningAgentManager,
)

# Main registry class
from .registry import AgentRegistry
from .registry_core import AgentRegistryCore

# Global registry instance - maintaining backward compatibility
try:
    agent_registry = AgentRegistry()
except Exception as e:
    # Log the error but don't fail the import
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize agent_registry: {e}")
    # Create a placeholder that will be initialized later
    agent_registry = None


def get_agent_registry():
    """
    Get or create the agent registry instance.
    This helps avoid circular import issues during initialization.
    """
    global agent_registry
    if agent_registry is None:
        try:
            agent_registry = AgentRegistry()
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create agent_registry: {e}")
            raise
    return agent_registry


__all__ = [
    "AgentPhase",
    "AgentStatus",
    "AgentRegistration",
    "AgentRegistryCore",
    "AgentLifecycleManager",
    "DiscoveryAgentManager",
    "AssessmentAgentManager",
    "PlanningAgentManager",
    "MigrationAgentManager",
    "ModernizationAgentManager",
    "DecommissionAgentManager",
    "FinOpsAgentManager",
    "LearningContextAgentManager",
    "ObservabilityAgentManager",
    "AgentRegistry",
    "agent_registry",  # Include the instance in exports
    "get_agent_registry",  # Include the getter function
]
