"""
Phase Agent Managers

Managers for registering and organizing agents by their execution phase.
Each phase manager is responsible for registering agents specific to its phase.
"""

from .base import BasePhaseAgentManager
from .discovery import DiscoveryAgentManager
from .assessment import AssessmentAgentManager
from .planning import PlanningAgentManager
from .migration import MigrationAgentManager
from .modernization import ModernizationAgentManager
from .decommission import DecommissionAgentManager
from .finops import FinOpsAgentManager
from .learning import LearningContextAgentManager
from .observability import ObservabilityAgentManager

__all__ = [
    "BasePhaseAgentManager",
    "DiscoveryAgentManager",
    "AssessmentAgentManager",
    "PlanningAgentManager",
    "MigrationAgentManager",
    "ModernizationAgentManager",
    "DecommissionAgentManager",
    "FinOpsAgentManager",
    "LearningContextAgentManager",
    "ObservabilityAgentManager",
]
