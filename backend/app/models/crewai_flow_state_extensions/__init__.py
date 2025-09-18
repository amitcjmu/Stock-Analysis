"""
CrewAI Flow State Extensions Package

Modularized implementation of the CrewAI Flow State Extensions model following
established patterns in the codebase. The model is split into focused mixins
for better maintainability while preserving backward compatibility.
"""

from .base_model import CrewAIFlowStateExtensions

__all__ = ["CrewAIFlowStateExtensions"]
