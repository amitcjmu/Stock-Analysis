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
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# For backward compatibility - re-export all classes
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Import modular components
from .decision import (
    AgentDecision,
    BaseDecisionAgent,
    ConfidenceCalculator,
    DecisionUtils,
    FieldMappingDecisionAgent,
    PhaseAction,
    PhaseTransitionAgent,
)

logger = logging.getLogger(__name__)


# Backward compatibility: Keep existing classes available but delegate to modular components
# This allows existing imports to continue working while enabling modular structure

# All classes are now imported from the modular structure above
# Existing code can continue to use:
# from decision_agents import PhaseTransitionAgent, FieldMappingDecisionAgent
# from decision_agents import PhaseAction, AgentDecision