"""Flow Commands

Write operations for discovery flows.
Backward compatibility facade for modularized flow commands.
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from .flow_base import FlowCommandsBase
from .flow_creation import FlowCreationCommands
from .flow_phase_management import FlowPhaseManagementCommands
from .flow_status_management import FlowStatusManagementCommands
from .flow_completion import FlowCompletionCommands
from .flow_deletion import FlowDeletionCommands
from .flow_maintenance import FlowMaintenanceCommands


class FlowCommands(FlowCommandsBase):
    """Unified flow commands class maintaining backward compatibility"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        super().__init__(db, client_account_id, engagement_id)

        # Initialize command modules as attributes
        self._creation = FlowCreationCommands(db, client_account_id, engagement_id)
        self._phase_mgmt = FlowPhaseManagementCommands(
            db, client_account_id, engagement_id
        )
        self._status_mgmt = FlowStatusManagementCommands(
            db, client_account_id, engagement_id
        )
        self._completion = FlowCompletionCommands(db, client_account_id, engagement_id)
        self._deletion = FlowDeletionCommands(db, client_account_id, engagement_id)
        self._maintenance = FlowMaintenanceCommands(
            db, client_account_id, engagement_id
        )

    # Flow creation methods
    async def create_discovery_flow(self, *args, **kwargs):
        """Create new discovery flow using CrewAI Flow ID"""
        return await self._creation.create_discovery_flow(*args, **kwargs)

    # Phase management methods
    async def update_phase_completion(self, *args, **kwargs):
        """Update phase completion status and data"""
        return await self._phase_mgmt.update_phase_completion(*args, **kwargs)

    # Status management methods
    async def update_flow_status(self, *args, **kwargs):
        """Update discovery flow status"""
        return await self._status_mgmt.update_flow_status(*args, **kwargs)

    # Completion methods
    async def mark_flow_complete(self, *args, **kwargs):
        """Mark flow as complete"""
        return await self._completion.mark_flow_complete(*args, **kwargs)

    async def complete_discovery_flow(self, *args, **kwargs):
        """Complete discovery flow and prepare for assessment handoff"""
        return await self._completion.complete_discovery_flow(*args, **kwargs)

    # Deletion methods
    async def delete_flow(self, *args, **kwargs):
        """Delete discovery flow"""
        return await self._deletion.delete_flow(*args, **kwargs)

    # Maintenance methods
    async def cleanup_stuck_flows(self, *args, **kwargs):
        """Clean up flows that have been stuck for more than the threshold"""
        return await self._maintenance.cleanup_stuck_flows(*args, **kwargs)

    async def update_master_flow_reference(self, *args, **kwargs):
        """Update the master_flow_id for existing flows where it's NULL.
        CRITICAL: This method fixes NULL master_flow_id issues for production data integrity.
        """
        return await self._maintenance.update_master_flow_reference(*args, **kwargs)
