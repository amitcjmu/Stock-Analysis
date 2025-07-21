"""
Decision Agent Framework - Modular Structure

This package provides modular decision-making agents that replace hardcoded
business logic with intelligent, context-aware decisions.
"""

# Base classes and utilities
from .base import BaseDecisionAgent, AgentDecision, PhaseAction

# Specialized decision agents
from .phase_transition import PhaseTransitionAgent
from .field_mapping import FieldMappingDecisionAgent

# Utilities
from .utils import DecisionUtils, ConfidenceCalculator

__all__ = [
    'BaseDecisionAgent',
    'AgentDecision', 
    'PhaseAction',
    'PhaseTransitionAgent',
    'FieldMappingDecisionAgent',
    'DecisionUtils',
    'ConfidenceCalculator'
]