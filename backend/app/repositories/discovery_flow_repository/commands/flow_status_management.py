"""
Status management operations.

Handles flow status updates and state transitions.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import and_, update

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase


# 🔧 CC FIX: Import UUID conversion utility for JSON serialization safety
def convert_uuids_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings for JSON serialization.
    🔧 CC FIX: Prevents 'Object of type UUID is not JSON serializable' errors
    """
    import uuid

    if isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuids_to_str(item) for item in obj]
    return obj


logger = logging.getLogger(__name__)


class FlowStatusManagementCommands(FlowCommandsBase):
    """Handles flow status management operations"""

    async def update_flow_status(
        self, flow_id: str, status: str, progress_percentage: Optional[float] = None
    ) -> Optional[DiscoveryFlow]:
        """Update discovery flow status"""

        # Ensure flow_id is UUID
        flow_uuid = self._ensure_uuid(flow_id)

        # Get existing flow to merge state data
        existing_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if not existing_flow:
            logger.error(f"Flow not found for status update: {flow_id}")
            return None

        # Get existing state data
        state_data = existing_flow.crewai_state_data or {}

        # Update status in state data
        state_data["status"] = status

        # Special handling for waiting_for_approval status
        if status == "waiting_for_approval":
            state_data["awaiting_user_approval"] = True
            # Also update current_phase to field_mapping
            update_values = {
                "status": status,
                "current_phase": "field_mapping",
                # 🔧 CC FIX: Convert UUIDs to strings before storing in JSON field
                "crewai_state_data": convert_uuids_to_str(state_data),
            }
        else:
            # 🔧 CC FIX: Convert UUIDs to strings before storing in JSON field
            update_values = {
                "status": status,
                "crewai_state_data": convert_uuids_to_str(state_data),
            }

        # Update progress if provided
        if progress_percentage is not None:
            update_values["progress_percentage"] = progress_percentage

        # Always update timestamp
        update_values["updated_at"] = datetime.utcnow()

        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_uuid,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(**update_values)
        )

        await self.db.execute(stmt)
        await self.db.commit()

        # Invalidate cache after update
        updated_flow = await self.flow_queries.get_by_flow_id(flow_id)
        if updated_flow:
            await self._invalidate_flow_cache(updated_flow)

        return updated_flow
