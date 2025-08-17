"""
CrewAI Flow Service - Backward Compatibility Shim

This file provides backward compatibility for the modularized CrewAI Flow Service.
All functionality has been moved to the crewai_flows.crewai_flow_service package.

IMPORTANT: This file imports from the modularized implementation to ensure
zero breaking changes for existing code that imports from this path.
"""

# Import all public components from the modularized package
from app.services.crewai_flows.crewai_flow_service import (
    CrewAIFlowService,
    get_crewai_flow_service,
    CREWAI_FLOWS_AVAILABLE,
    CrewAIExecutionError,
    InvalidFlowStateError,
    CrewAIFlowServiceBase,
    FlowExecutionMixin,
    FlowMonitoringMixin,
    FlowStateManagerMixin,
    FlowTaskManagerMixin,
    FlowValidationMixin,
)

# Re-export everything for backward compatibility
__all__ = [
    "CrewAIFlowService",
    "get_crewai_flow_service",
    "CREWAI_FLOWS_AVAILABLE",
    "CrewAIExecutionError",
    "InvalidFlowStateError",
    "CrewAIFlowServiceBase",
    "FlowExecutionMixin",
    "FlowMonitoringMixin",
    "FlowStateManagerMixin",
    "FlowTaskManagerMixin",
    "FlowValidationMixin",
]
