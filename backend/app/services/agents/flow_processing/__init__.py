"""
Flow Processing Agent Package

A modular implementation of the Universal Flow Processing Agent using CrewAI.
This package provides intelligent flow continuation and routing across all 
flow types (Discovery, Assess, Plan, Execute, etc.).
"""

from .models import FlowAnalysisResult, RouteDecision, FlowContinuationResult
from .crew import UniversalFlowProcessingCrew
from .agent import FlowProcessingAgent

__all__ = [
    "FlowAnalysisResult",
    "RouteDecision", 
    "FlowContinuationResult",
    "UniversalFlowProcessingCrew",
    "FlowProcessingAgent"
]