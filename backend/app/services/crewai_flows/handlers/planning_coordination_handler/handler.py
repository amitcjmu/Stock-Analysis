"""
Main Planning Coordination Handler class.

This module contains the main PlanningCoordinationHandler class that
combines all the mixins to provide complete planning coordination functionality.
"""

import logging
from .base import PlanningCoordinationHandlerBase
from .crew_planning import CrewPlanningMixin
from .adaptive_workflow import AdaptiveWorkflowMixin
from .planning_intelligence import PlanningIntelligenceMixin
from .resource_allocation import ResourceAllocationMixin
from .optimization_components import OptimizationComponentsMixin

logger = logging.getLogger(__name__)


class PlanningCoordinationHandler(
    PlanningCoordinationHandlerBase,
    CrewPlanningMixin,
    AdaptiveWorkflowMixin,
    PlanningIntelligenceMixin,
    ResourceAllocationMixin,
    OptimizationComponentsMixin,
):
    """Handles all planning, coordination, optimization and AI intelligence functionality"""

    def __init__(self, crewai_service=None):
        super().__init__(crewai_service)
        logger.info(
            "🎯 PlanningCoordinationHandler initialized with full functionality"
        )

    def get_handler_status(self) -> dict:
        """Get comprehensive status of the planning coordination handler"""
        return {
            "handler_initialized": True,
            "components_status": {
                "planning_coordination": self.planning_coordination is not None,
                "adaptive_workflow": self.adaptive_workflow is not None,
                "planning_intelligence": self.planning_intelligence is not None,
                "resource_allocation": self.resource_allocation is not None,
                "storage_optimization": self.storage_optimization is not None,
                "network_optimization": self.network_optimization is not None,
                "data_lifecycle_management": self.data_lifecycle_management is not None,
                "data_encryption": self.data_encryption is not None,
            },
            "capabilities": [
                "crew_planning_coordination",
                "adaptive_workflow_management",
                "ai_planning_intelligence",
                "resource_allocation_optimization",
                "storage_optimization",
                "network_optimization",
                "data_lifecycle_management",
                "data_encryption",
            ],
            "ready_for_execution": all(
                [
                    hasattr(self, "crewai_service"),
                    callable(getattr(self, "setup_planning_components", None)),
                ]
            ),
        }
