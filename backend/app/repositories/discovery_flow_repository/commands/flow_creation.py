"""
Flow creation operations.

Handles creation of new discovery flows with proper initialization.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.discovery_flow import DiscoveryFlow
from .flow_base import FlowCommandsBase

logger = logging.getLogger(__name__)


class FlowCreationCommands(FlowCommandsBase):
    """Handles flow creation operations"""

    async def create_discovery_flow(
        self,
        flow_id: str,
        master_flow_id: Optional[str] = None,
        flow_type: str = "primary",
        description: Optional[str] = None,
        initial_state_data: Optional[Dict[str, Any]] = None,
        data_import_id: Optional[str] = None,
        user_id: Optional[str] = None,
        raw_data: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_commit: bool = True,  # 🔧 CC FIX: Add auto_commit parameter
    ) -> DiscoveryFlow:
        """Create new discovery flow using CrewAI Flow ID"""

        # Parse flow_id as UUID
        parsed_flow_id = self._ensure_uuid(flow_id)

        # Parse optional UUIDs
        master_uuid = self._ensure_uuid(master_flow_id) if master_flow_id else None

        # Prepare initial state data including raw_data and metadata
        state_data = initial_state_data or {}
        if raw_data:
            state_data["raw_data"] = raw_data
        if metadata:
            state_data["metadata"] = metadata

        # Add timeout to metadata (24 hours from creation)
        if "metadata" not in state_data:
            state_data["metadata"] = {}
        state_data["metadata"]["timeout_at"] = (
            datetime.utcnow() + timedelta(hours=24)
        ).isoformat()
        state_data["metadata"]["created_at"] = datetime.utcnow().isoformat()

        # Set status and current phase
        status = state_data.get("status", "initialized")
        current_phase = state_data.get("current_phase", "initialization")
        progress = state_data.get("progress_percentage", 0.0)

        # Create flow object
        flow = DiscoveryFlow(
            id=uuid.uuid4(),
            flow_id=parsed_flow_id,
            master_flow_id=master_uuid,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            user_id=user_id or str(uuid.uuid4()),
            flow_name=description or f"Discovery Flow {str(parsed_flow_id)[:8]}",
            status=status,
            current_phase=current_phase,
            progress_percentage=progress,
            crewai_state_data=state_data,
            data_import_id=(
                self._ensure_uuid(data_import_id) if data_import_id else None
            ),
            learning_scope="engagement",
            memory_isolation_level="strict",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.db.add(flow)

        # 🔧 CC FIX: Handle commit vs flush based on auto_commit parameter
        if auto_commit:
            await self.db.commit()
            await self.db.refresh(flow)
            logger.info(
                f"✅ Created discovery flow with commit: {flow.flow_id} with timeout at "
                f"{state_data['metadata']['timeout_at']}"
            )
        else:
            await self.db.flush()
            await self.db.refresh(flow)
            logger.info(
                f"✅ Created discovery flow with flush: {flow.flow_id} with timeout at "
                f"{state_data['metadata']['timeout_at']}"
            )

        return flow
