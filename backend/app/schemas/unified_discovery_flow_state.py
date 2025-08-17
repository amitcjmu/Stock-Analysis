"""
Unified Discovery Flow State Schema

This module provides schema imports for the UnifiedDiscoveryFlowState model.
It acts as a bridge between the models and services that need schema-style imports.

The actual implementation is in app.models.unified_discovery_flow_state,
but some services prefer to import through the schemas module for consistency.
"""

# Import the actual implementation from models
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState

# Re-export for schema-style imports
__all__ = ["UnifiedDiscoveryFlowState"]
