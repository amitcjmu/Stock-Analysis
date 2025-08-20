"""
Phase-Specific Agent Managers

Managers for registering and organizing agents by their execution phase.
This module provides imports and compatibility for the modularized agent managers.
"""

import logging

# Import the base manager
from .managers.base import BasePhaseAgentManager

# Import all specific phase managers
from .managers.discovery import DiscoveryAgentManager
from .managers.assessment import AssessmentAgentManager
from .managers.planning import PlanningAgentManager
from .managers.migration import MigrationAgentManager
from .managers.modernization import ModernizationAgentManager
from .managers.decommission import DecommissionAgentManager
from .managers.finops import FinOpsAgentManager
from .managers.learning import LearningContextAgentManager
from .managers.observability import ObservabilityAgentManager

logger = logging.getLogger(__name__)

# Export all managers for backward compatibility
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
