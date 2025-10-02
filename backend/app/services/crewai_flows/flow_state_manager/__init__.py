"""
Flow State Manager - Modular Implementation
Manages CrewAI flow state with PostgreSQL as single source of truth

This module has been modularized for maintainability:
- queries.py: Read operations
- commands.py: Write/update operations
- transitions.py: State transition logic
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator

from ..persistence.postgres_store import PostgresFlowStateStore
from ..persistence.secure_checkpoint_manager import SecureCheckpointManager
from ..persistence.state_recovery import FlowStateRecovery
from ..flow_lifecycle_operations import FlowLifecycleOperations

from .queries import FlowStateQueries, get_flow_summary
from .basic_commands import FlowStateBasicCommands
from .status_commands import FlowStateStatusCommands
from .transitions import FlowStateTransitions, InvalidTransitionError

logger = logging.getLogger(__name__)


class FlowStateManager:
    """
    Manages CrewAI flow state with PostgreSQL as single source of truth

    This class composes the modular components:
    - FlowStateQueries: Read operations
    - FlowStateCommands: Write/update operations
    - FlowStateTransitions: State transition logic
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
        self.recovery = FlowStateRecovery(db, context)
        # Use secure checkpoint manager instead of insecure one
        self.secure_checkpoint_manager = SecureCheckpointManager(context)
        # Use lifecycle operations for complex operations
        self.lifecycle = FlowLifecycleOperations(db, context)

        # Initialize modular components
        self._queries = FlowStateQueries(db, context)
        self._basic_commands = FlowStateBasicCommands(db, context)
        self._status_commands = FlowStateStatusCommands(db, context)
        self._transitions = FlowStateTransitions(db, context)

    # ========== Query Operations ==========
    async def get_flow_state(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current flow state for agent analysis

        ADR-012: Uses child flow data for operational decisions, not master flow
        """
        return await self._queries.get_flow_state(flow_id)

    async def get_flow_history(self, flow_id: str) -> Dict[str, Any]:
        """Get complete history for a flow"""
        return await self._queries.get_flow_history(flow_id)

    # ========== Command Operations ==========
    async def create_flow_state(
        self, flow_id: str, initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new flow state"""
        return await self._basic_commands.create_flow_state(flow_id, initial_data)

    async def update_flow_state(
        self, flow_id: str, state_updates: Dict[str, Any], version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update flow state with validation"""
        return await self._basic_commands.update_flow_state(
            flow_id, state_updates, version
        )

    async def complete_phase(
        self, flow_id: str, phase: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mark a phase as completed with results"""
        return await self._basic_commands.complete_phase(flow_id, phase, results)

    async def handle_flow_error(
        self,
        flow_id: str,
        error: str,
        phase: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle flow errors with automatic recovery attempts"""
        return await self._basic_commands.handle_flow_error(
            flow_id, error, phase, details
        )

    async def cleanup_flow_state(
        self, flow_id: str, archive: bool = True
    ) -> Dict[str, Any]:
        """Clean up flow state with optional archiving"""
        return await self._basic_commands.cleanup_flow_state(flow_id, archive)

    async def update_master_flow_status(
        self, flow_id: str, new_status: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update master flow status (lifecycle management)

        ADR-012: Master flow manages high-level lifecycle:
        - initialized, running, paused, completed, failed, deleted
        """
        return await self._status_commands.update_master_flow_status(
            flow_id, new_status, metadata
        )

    async def update_child_flow_status(
        self, flow_id: str, new_status: str, flow_type: str = "discovery"
    ) -> Dict[str, Any]:
        """
        Update child flow status (operational decisions)

        ADR-012: Child flow manages operational state for:
        - Field mapping, data cleansing, agent decisions, user approvals
        """
        return await self._status_commands.update_child_flow_status(
            flow_id, new_status, flow_type
        )

    async def update_flow_status_atomically(
        self,
        flow_id: str,
        child_status: str,
        master_status: str,
        flow_type: str = "discovery",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update both master and child flow statuses atomically

        ADR-012: For critical state changes (start/pause/resume), update both
        master and child flows in a single atomic transaction.
        """
        return await self._status_commands.update_flow_status_atomically(
            flow_id, child_status, master_status, flow_type, metadata
        )

    async def update_child_flow_phase(
        self,
        flow_id: str,
        new_phase: str,
        flow_type: str = "discovery",
        set_status: Optional[str] = None,
        extra_updates: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update child flow phase with optional status and field updates

        Centralized method for phase transitions that handles:
        - Phase completion flags
        - Progress percentage updates
        - Phase-specific field updates
        - Status updates
        """
        return await self._status_commands.update_child_flow_phase(
            flow_id, new_phase, flow_type, set_status, extra_updates
        )

    # ========== Transition Operations ==========
    async def transition_phase(
        self,
        flow_id: str,
        new_phase: str,
        phase_data: Optional[Dict[str, Any]] = None,
        force_transition: bool = False,
    ) -> Dict[str, Any]:
        """Handle phase transitions with validation"""
        return await self._transitions.transition_phase(
            flow_id, new_phase, phase_data, force_transition
        )

    async def resume_flow_state(
        self, flow_id: str, target_phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resume flow state during flow resumption - uses force transition to handle edge cases
        """
        return await self._transitions.resume_flow_state(flow_id, target_phase)


# Utility functions for flow state management


@asynccontextmanager
async def create_flow_manager(context: RequestContext):
    """
    Create a flow state manager with database session as async context manager.

    FIXED: Converted to async context manager to properly manage database session lifecycle.
    Use with 'async with' pattern:
        async with create_flow_manager(context) as manager:
            await manager.update_flow_state(...)

    Yields:
        FlowStateManager: Configured flow state manager instance
    """
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        yield FlowStateManager(db, context)


# Export all public APIs
__all__ = [
    "FlowStateManager",
    "InvalidTransitionError",
    "create_flow_manager",
    "get_flow_summary",
]
