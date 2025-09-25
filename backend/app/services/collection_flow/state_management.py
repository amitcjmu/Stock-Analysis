# flake8: noqa: F401
"""
Collection Flow State Management Service

This file maintains backward compatibility while the actual implementation
has been modularized into the state_management/ subdirectory.
"""

from .state_management import CollectionFlowStateService, CollectionPhase

__all__ = ["CollectionFlowStateService", "CollectionPhase"]
