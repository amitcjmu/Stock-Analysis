"""
Flow State Manager - Status Command Operations
Handles all status and phase update operations for master and child flows
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class FlowStateStatusCommands:
    """Handles status and phase update operations for flows"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    async def update_master_flow_status(
        self, flow_id: str, new_status: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update master flow status (lifecycle management)

        ADR-012: Master flow manages high-level lifecycle:
        - initialized, running, paused, completed, failed, deleted
        """
        try:
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            master_repo = CrewAIFlowStateExtensionsRepository(
                self.db,
                self.context.client_account_id,
                self.context.engagement_id,
                self.context.user_id,
            )
            master_flow = await master_repo.get_by_flow_id(flow_id)

            if not master_flow:
                raise ValueError(f"Master flow not found: {flow_id}")

            # Update status
            previous_status = master_flow.flow_status
            master_flow.flow_status = new_status
            master_flow.updated_at = datetime.now(timezone.utc)

            # Store metadata if provided
            if metadata:
                if "lifecycle_events" not in master_flow.flow_persistence_data:
                    master_flow.flow_persistence_data["lifecycle_events"] = []

                master_flow.flow_persistence_data["lifecycle_events"].append(
                    {
                        "event": "status_change",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "previous_status": previous_status,
                        "new_status": new_status,
                        "metadata": metadata,
                        "user_id": self.context.user_id,
                    }
                )

            await self.db.commit()

            logger.info(
                f"✅ [ADR-012] Master flow status updated: {flow_id} "
                f"{previous_status} -> {new_status}"
            )

            return {
                "flow_id": flow_id,
                "previous_status": previous_status,
                "new_status": new_status,
                "updated_at": master_flow.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to update master flow status for {flow_id}: {e}")
            raise

    async def update_child_flow_status(
        self, flow_id: str, new_status: str, flow_type: str = "discovery"
    ) -> Dict[str, Any]:
        """
        Update child flow status (operational decisions)

        ADR-012: Child flow manages operational state for:
        - Field mapping, data cleansing, agent decisions, user approvals
        """
        try:
            if flow_type == "discovery":
                from app.repositories.discovery_flow_repository import (
                    DiscoveryFlowRepository,
                )

                child_repo = DiscoveryFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            elif flow_type == "collection":
                from app.repositories.collection_flow_repository import (
                    CollectionFlowRepository,
                )

                child_repo = CollectionFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            else:
                raise ValueError(f"Unsupported flow type: {flow_type}")

            child_flow = await child_repo.get_by_flow_id(flow_id)
            if not child_flow:
                raise ValueError(f"Child flow not found: {flow_id}")

            # Update status
            previous_status = child_flow.status
            child_flow.status = new_status
            child_flow.updated_at = datetime.now(timezone.utc)

            await self.db.commit()

            logger.info(
                f"✅ [ADR-012] Child flow status updated: {flow_id} "
                f"{previous_status} -> {new_status}"
            )

            return {
                "flow_id": flow_id,
                "previous_status": previous_status,
                "new_status": new_status,
                "updated_at": child_flow.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to update child flow status for {flow_id}: {e}")
            raise

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
        try:
            logger.info(
                f"🔄 [ADR-012] Atomic status update: {flow_id} "
                f"master={master_status}, child={child_status}"
            )

            async with self.db.begin():
                # Update master flow
                master_result = await self.update_master_flow_status(
                    flow_id, master_status, metadata
                )

                # Update child flow
                child_result = await self.update_child_flow_status(
                    flow_id, child_status, flow_type
                )

            logger.info(f"✅ [ADR-012] Atomic status update completed: {flow_id}")

            return {
                "flow_id": flow_id,
                "master_status": master_result,
                "child_status": child_result,
                "atomic": True,
            }

        except Exception as e:
            logger.error(f"❌ Atomic status update failed for {flow_id}: {e}")
            raise

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
        try:
            logger.info(
                f"🔄 Updating child flow phase: {flow_id} -> {new_phase} "
                f"(type={flow_type})"
            )

            if flow_type == "discovery":
                from app.repositories.discovery_flow_repository import (
                    DiscoveryFlowRepository,
                )

                child_repo = DiscoveryFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            elif flow_type == "collection":
                from app.repositories.collection_flow_repository import (
                    CollectionFlowRepository,
                )

                child_repo = CollectionFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            else:
                raise ValueError(f"Unsupported flow type: {flow_type}")

            child_flow = await child_repo.get_by_flow_id(flow_id)
            if not child_flow:
                raise ValueError(f"Child flow not found: {flow_id}")

            # Store previous phase
            previous_phase = child_flow.current_phase

            # Update phase
            child_flow.current_phase = new_phase
            child_flow.updated_at = datetime.now(timezone.utc)

            # Update status if provided
            if set_status:
                child_flow.status = set_status

            # Apply extra updates
            if extra_updates:
                for field, value in extra_updates.items():
                    if hasattr(child_flow, field):
                        setattr(child_flow, field, value)
                    else:
                        logger.warning(f"Unknown field '{field}' in extra_updates")

            # Update progress percentage if available
            if hasattr(child_flow, "update_progress"):
                child_flow.update_progress()

            await self.db.commit()

            logger.info(
                f"✅ Child flow phase updated: {flow_id} {previous_phase} -> {new_phase}"
            )

            return {
                "flow_id": flow_id,
                "previous_phase": previous_phase,
                "new_phase": new_phase,
                "status": child_flow.status if hasattr(child_flow, "status") else None,
                "updated_at": child_flow.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to update child flow phase for {flow_id}: {e}")
            raise
