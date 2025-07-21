"""
Intelligent Flow Agent Package

A modular implementation of the Intelligent Flow Processing Agent using CrewAI.
This package provides intelligent flow continuation and routing for discovery flows.

Backward compatibility is maintained through re-exports of all public interfaces.
"""

from .models import FlowIntelligenceResult
from .agent import IntelligentFlowAgent
from .tools import (
    FlowContextTool,
    FlowStatusTool,
    PhaseValidationTool,
    NavigationDecisionTool
)

__all__ = [
    "FlowIntelligenceResult",
    "IntelligentFlowAgent",
    "FlowContextTool",
    "FlowStatusTool", 
    "PhaseValidationTool",
    "NavigationDecisionTool"
]