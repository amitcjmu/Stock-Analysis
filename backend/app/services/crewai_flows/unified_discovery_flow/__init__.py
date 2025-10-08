"""
Unified Discovery Flow - Modularized Implementation

This package contains the modularized version of the UnifiedDiscoveryFlow,
split into logical components for better maintainability and testing.

Main components:
- base_flow.py: Base flow class and initialization
- flow_config.py: Configuration and constants
- phases/: Individual phase implementations
- state_management.py: State handling logic
- crew_coordination.py: Crew and agent orchestration
"""

from .base_flow import UnifiedDiscoveryFlow, create_unified_discovery_flow
from .flow_config import FlowConfig, PhaseNames
from ..flow_state_bridge import FlowStateBridge

__all__ = [
    "UnifiedDiscoveryFlow",
    "create_unified_discovery_flow",
    "FlowConfig",
    "PhaseNames",
    "FlowStateBridge",
]
