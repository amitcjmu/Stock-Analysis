"""
Flow Status Service for Discovery Flow Operations - Modularized

This service handles status checking and updates for discovery flows.
The implementation has been modularized for better maintainability while
preserving the exact same public API for backward compatibility.

Issue #128 fix: Added phase-based filtering to get_active_flows() to properly
include flows in early phases like "initialization".
"""

# Re-export all public functions to maintain backward compatibility
from .flow_status import get_flow_status, update_flow_status, get_active_flows

__all__ = ["get_flow_status", "update_flow_status", "get_active_flows"]
