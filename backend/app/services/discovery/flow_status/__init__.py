"""
Flow Status Service Package - Modularized for Maintainability

This package provides discovery flow status operations with a clean,
modular architecture that maintains backward compatibility.

Public API:
- get_flow_status: Get detailed status of a discovery flow
- update_flow_status: Update flow status and related metadata
- get_active_flows: Get list of active discovery flows
"""

from .operations import get_flow_status, update_flow_status, get_active_flows

__all__ = ["get_flow_status", "update_flow_status", "get_active_flows"]
