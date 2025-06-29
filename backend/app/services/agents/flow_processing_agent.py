"""
Universal Flow Processing Agent - Modular Implementation

This module provides backward compatibility by importing from the new modular
flow_processing package. The actual implementation has been refactored into
smaller, more maintainable modules.

The flow processing functionality is now organized as:
- flow_processing/crewai_imports.py - CrewAI imports and fallbacks
- flow_processing/models.py - Data models
- flow_processing/tools/ - Individual tool implementations
- flow_processing/crew.py - CrewAI crew implementation
- flow_processing/agent.py - Legacy compatibility wrapper
"""

# Import everything from the modular implementation for backward compatibility
from .flow_processing import (
    FlowAnalysisResult,
    RouteDecision,
    FlowContinuationResult,
    UniversalFlowProcessingCrew,
    FlowProcessingAgent
)

# Maintain backward compatibility by exposing the main classes at module level
__all__ = [
    "FlowAnalysisResult",
    "RouteDecision",
    "FlowContinuationResult",
    "UniversalFlowProcessingCrew",
    "FlowProcessingAgent"
]