"""
Collection Flow State Management Service

This service manages the lifecycle and state transitions of Collection Flows,
including initialization, phase transitions, and status updates.
"""

from .base import CollectionPhase
from .service import CollectionFlowStateService

__all__ = ["CollectionPhase", "CollectionFlowStateService"]
