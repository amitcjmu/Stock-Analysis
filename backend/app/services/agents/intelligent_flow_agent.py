"""
Intelligent Flow Agent - Backward Compatibility Module

This module maintains backward compatibility for the original intelligent_flow_agent.py
while the implementation has been modularized into separate components.

All public interfaces are re-exported from the modular implementation.
Use the modular imports for new code:
- from app.services.agents.intelligent_flow_agent import IntelligentFlowAgent, FlowIntelligenceResult
"""

# Re-export all public interfaces from the modular implementation
from .intelligent_flow_agent import (
    FlowIntelligenceResult,
    IntelligentFlowAgent,
    FlowContextTool,
    FlowStatusTool,
    PhaseValidationTool,
    NavigationDecisionTool
)

# Maintain backward compatibility
__all__ = [
    "FlowIntelligenceResult",
    "IntelligentFlowAgent", 
    "FlowContextTool",
    "FlowStatusTool",
    "PhaseValidationTool",
    "NavigationDecisionTool"
] 