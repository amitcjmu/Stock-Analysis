"""
Planning Coordination Handler for Discovery Flow

Handles all planning, coordination, optimization and AI intelligence functionality.

This module provides comprehensive planning coordination capabilities including:
- Cross-crew planning coordination
- Adaptive workflow strategy management
- AI planning intelligence and optimization
- Resource allocation optimization
- Storage, network, and data optimization
- Data lifecycle management and encryption

Usage:
    from app.services.crewai_flows.handlers.planning_coordination_handler import PlanningCoordinationHandler

    handler = PlanningCoordinationHandler(crewai_service)
    handler.setup_planning_components()

    # Use coordination functionality
    coordination_plan = handler.coordinate_crew_planning(data_complexity)
    adaptation_result = handler.adapt_workflow_strategy(performance_metrics)
    intelligence_result = handler.apply_planning_intelligence(planning_context)
"""

# Import main handler class for backward compatibility
from .handler import PlanningCoordinationHandler

# Import component mixins for advanced usage
from .base import PlanningCoordinationHandlerBase
from .crew_planning import CrewPlanningMixin
from .adaptive_workflow import AdaptiveWorkflowMixin
from .planning_intelligence import PlanningIntelligenceMixin
from .resource_allocation import ResourceAllocationMixin
from .optimization_components import OptimizationComponentsMixin

# Export all public components
__all__ = [
    "PlanningCoordinationHandler",
    "PlanningCoordinationHandlerBase",
    "CrewPlanningMixin",
    "AdaptiveWorkflowMixin",
    "PlanningIntelligenceMixin",
    "ResourceAllocationMixin",
    "OptimizationComponentsMixin",
]
