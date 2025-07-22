"""
Unified Discovery Flow - Modularized Implementation

This module now imports from the modularized structure in the unified_discovery_flow package.
The original 1,799-line file has been split into manageable modules:

- flow_config.py: Configuration and constants
- state_management.py: State management logic
- crew_coordination.py: Agent orchestration
- phases/*.py: Individual phase implementations
- base_flow.py: Main flow class

For backward compatibility, all exports are maintained.
"""

# Re-export everything from the modularized structure
from .unified_discovery_flow.base_flow import CREWAI_FLOW_AVAILABLE, UnifiedDiscoveryFlow, create_unified_discovery_flow
from .unified_discovery_flow.crew_coordination import CrewCoordinator
from .unified_discovery_flow.flow_config import (
    ASSET_TYPE_KEYWORDS,
    PHASE_ORDER,
    USER_APPROVAL_PHASES,
    FlowConfig,
    PhaseNames,
)
from .unified_discovery_flow.flow_finalization import FlowFinalizer
from .unified_discovery_flow.flow_initialization import FlowInitializer
from .unified_discovery_flow.flow_management import FlowManager
from .unified_discovery_flow.state_management import StateManager

# Export phase implementations if needed
# Phase modules removed - using Executor pattern instead

# Maintain backward compatibility
__all__ = [
    'UnifiedDiscoveryFlow',
    'create_unified_discovery_flow',
    'CREWAI_FLOW_AVAILABLE',
    'FlowConfig',
    'PhaseNames',
    'StateManager',
    'CrewCoordinator',
    'FlowManager',
    'FlowInitializer',
    'FlowFinalizer',
]