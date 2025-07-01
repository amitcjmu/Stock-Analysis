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
from .unified_discovery_flow.base_flow import (
    UnifiedDiscoveryFlow,
    create_unified_discovery_flow,
    CREWAI_FLOW_AVAILABLE
)

from .unified_discovery_flow.flow_config import (
    FlowConfig,
    PhaseNames,
    ASSET_TYPE_KEYWORDS,
    PHASE_ORDER,
    USER_APPROVAL_PHASES
)

from .unified_discovery_flow.state_management import StateManager
from .unified_discovery_flow.crew_coordination import CrewCoordinator
from .unified_discovery_flow.flow_management import FlowManager
from .unified_discovery_flow.flow_initialization import FlowInitializer
from .unified_discovery_flow.flow_finalization import FlowFinalizer

# Export phase implementations if needed
from .unified_discovery_flow.phases import (
    DataValidationPhase,
    FieldMappingPhase,
    DataCleansingPhase,
    AssetInventoryPhase,
    DependencyAnalysisPhase,
    TechDebtAssessmentPhase
)

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
    'DataValidationPhase',
    'FieldMappingPhase',
    'DataCleansingPhase',
    'AssetInventoryPhase',
    'DependencyAnalysisPhase',
    'TechDebtAssessmentPhase',
]