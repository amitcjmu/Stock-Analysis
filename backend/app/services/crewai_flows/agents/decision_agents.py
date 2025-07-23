"""
Agent Decision Framework

This module implements autonomous decision-making agents that replace hardcoded
business logic with intelligent, context-aware decisions.

MODULAR STRUCTURE:
- Base classes and utilities: ./decision/base.py, ./decision/utils.py
- Specialized agents: ./decision/phase_transition.py, ./decision/field_mapping.py

Generated with CC for modular backend architecture.
"""

import logging

# For backward compatibility - re-export all classes
from .decision import (AgentDecision, BaseDecisionAgent,
                       FieldMappingDecisionAgent, PhaseAction,
                       PhaseTransitionAgent)

logger = logging.getLogger(__name__)

# Export all classes for backward compatibility
__all__ = [
    "AgentDecision",
    "BaseDecisionAgent",
    "PhaseAction",
    "PhaseTransitionAgent",
    "FieldMappingDecisionAgent",
]
