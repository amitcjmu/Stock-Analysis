"""
Flow Processing Agent Package

A modular implementation of the Universal Flow Processing Agent using CrewAI.
This package provides intelligent flow continuation and routing across all 
flow types (Discovery, Assess, Plan, Execute, etc.).
"""

from .agent import FlowProcessingAgent
from .crew import UniversalFlowProcessingCrew
from .models import FlowAnalysisResult, FlowContinuationResult, RouteDecision

__all__ = [
    "FlowAnalysisResult",
    "RouteDecision", 
    "FlowContinuationResult",
    "UniversalFlowProcessingCrew",
    "FlowProcessingAgent"
]