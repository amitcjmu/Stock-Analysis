"""
Status management operations.

Handles flow status updates and state transitions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.sql import text as sa_text
from sqlalchemy import func

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

    async def set_conflict_resolution_pending(
        self,
        flow_id: UUID,
        conflict_count: int,
        data_import_id: Optional[UUID] = None,
    ) -> None:
        """
        Pause discovery flow for conflict resolution.

        Sets phase_state flags per ADR-012 (child flow owns operational state):
        - phase_state.conflict_resolution_pending: true
        - phase_state.conflict_metadata: { conflict_count, data_import_id, paused_at }

        NOTE: status remains 'active' (flow is paused but not completed)

        Args:
            flow_id: Discovery flow UUID
            conflict_count: Number of conflicts detected
            data_import_id: Optional data import UUID for filtering
        """
        conflict_metadata = {
            "conflict_count": conflict_count,
            "data_import_id": str(data_import_id) if data_import_id else None,
            "paused_at": datetime.utcnow().isoformat(),
        }

        # NEW: Coalesce phase_state to empty JSONB before jsonb_set (per GPT-5 feedback)
        # Prevents failure when phase_state is NULL
        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(
                phase_state=func.jsonb_set(
                    func.jsonb_set(
                        func.coalesce(
                            DiscoveryFlow.phase_state, sa_text("'{}'::jsonb")
                        ),
                        sa_text("ARRAY['conflict_resolution_pending']::text[]"),
                        sa_text("'true'::jsonb"),
                    ),
                    sa_text("ARRAY['conflict_metadata']::text[]"),
                    sa_text(f"'{json.dumps(conflict_metadata)}'::jsonb"),
                ),
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(stmt)

        logger.info(
            f"⏸️ Discovery flow {flow_id} paused for conflict resolution "
            f"({conflict_count} conflicts)"
        )

    async def clear_conflict_resolution_pending(self, flow_id: UUID) -> None:
        """
        Resume discovery flow after conflict resolution.

        Clears phase_state.conflict_resolution_pending flag and metadata.

        Args:
            flow_id: Discovery flow UUID
        """
        # NEW: Coalesce phase_state to empty JSONB before jsonb_set (per GPT-5 feedback)
        stmt = (
            update(DiscoveryFlow)
            .where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                )
            )
            .values(
                phase_state=func.jsonb_set(
                    func.jsonb_set(
                        func.coalesce(
                            DiscoveryFlow.phase_state, sa_text("'{}'::jsonb")
                        ),
                        sa_text("ARRAY['conflict_resolution_pending']::text[]"),
                        sa_text("'false'::jsonb"),
                    ),
                    sa_text("ARRAY['conflict_metadata']::text[]"),
                    sa_text("'{}'::jsonb"),
                ),
                updated_at=datetime.utcnow(),
            )
        )

        await self.db.execute(stmt)

        logger.info(f"▶️ Discovery flow {flow_id} resumed after conflict resolution")

    async def get_conflict_resolution_status(self, flow_id: UUID) -> Optional[Dict]:
        """
        Check if flow is paused for conflict resolution.

        Returns:
            Dict with { pending: bool, conflict_count: int, data_import_id: str } or None
        """
        stmt = select(DiscoveryFlow.phase_state).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == self.client_account_id,
                DiscoveryFlow.engagement_id == self.engagement_id,
            )
        )
        result = await self.db.execute(stmt)
        phase_state = result.scalar_one_or_none()

        if not phase_state:
            return None

        is_pending = phase_state.get("conflict_resolution_pending", False)
        conflict_metadata = phase_state.get("conflict_metadata", {})

        return {
            "pending": is_pending,
            "conflict_count": conflict_metadata.get("conflict_count", 0),
            "data_import_id": conflict_metadata.get("data_import_id"),
            "paused_at": conflict_metadata.get("paused_at"),
        }
