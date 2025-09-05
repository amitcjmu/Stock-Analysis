"""
Unified Discovery Flow State Model - Facade for Backward Compatibility
Single source of truth for Discovery Flow state following CrewAI Flow documentation patterns.
Consolidates all competing state model implementations into one unified model.

This file now serves as a facade, re-exporting the modularized implementation for backward compatibility.
"""

# Re-export everything from the modularized package
from .unified_discovery_flow_state import (
    UnifiedDiscoveryFlowState,
    UUIDEncoder,
    safe_uuid_to_str,
)

__all__ = ["UnifiedDiscoveryFlowState", "UUIDEncoder", "safe_uuid_to_str"]
