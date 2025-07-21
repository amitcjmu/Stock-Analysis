"""
Agent Registry - Modular Structure

This package provides modular agent registry functionality for managing
all agents across all phases with detailed metadata and observability support.

Generated with CC for modular backend architecture.
"""

# Core registry components
from .base import AgentPhase, AgentStatus, AgentRegistration
from .registry_core import AgentRegistryCore
from .lifecycle_manager import AgentLifecycleManager

# Phase-specific agent groups
from .phase_agents import (
    DiscoveryAgentManager,
    AssessmentAgentManager,
    PlanningAgentManager,
    MigrationAgentManager,
    ModernizationAgentManager,
    DecommissionAgentManager,
    FinOpsAgentManager,
    LearningContextAgentManager,
    ObservabilityAgentManager
)

# Main registry class
from .registry import AgentRegistry

__all__ = [
    'AgentPhase',
    'AgentStatus', 
    'AgentRegistration',
    'AgentRegistryCore',
    'AgentLifecycleManager',
    'DiscoveryAgentManager',
    'AssessmentAgentManager',
    'PlanningAgentManager',
    'MigrationAgentManager',
    'ModernizationAgentManager',
    'DecommissionAgentManager',
    'FinOpsAgentManager',
    'LearningContextAgentManager',
    'ObservabilityAgentManager',
    'AgentRegistry'
]