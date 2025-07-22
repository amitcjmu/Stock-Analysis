"""
Intelligent Flow Agent Package

A modular implementation of the Intelligent Flow Processing Agent using CrewAI.
This package provides intelligent flow continuation and routing for discovery flows.

Backward compatibility is maintained through re-exports of all public interfaces.
"""

from .agent import IntelligentFlowAgent
from .models import FlowIntelligenceResult
from .tools import FlowContextTool, FlowStatusTool, NavigationDecisionTool, PhaseValidationTool

__all__ = [
    "FlowIntelligenceResult",
    "IntelligentFlowAgent",
    "FlowContextTool",
    "FlowStatusTool", 
    "PhaseValidationTool",
    "NavigationDecisionTool"
]