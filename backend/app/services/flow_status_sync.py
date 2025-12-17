"""
Flow Status Synchronization Service

Implements ADR-012: Flow Status Management Separation
Provides atomic updates for critical flow state changes and event-driven synchronization.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowNotFoundError, FlowStateUpdateError

# from app.repositories.assessment_flow_repository import AssessmentFlowRepository  # REMOVED - AssessmentFlow was removed
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository
from app.services.caching.redis_cache import get_redis_cache

logger = logging.getLogger(__name__)


class FlowStatusUpdateType(Enum):
    """Types of flow status updates"""

    CRITICAL_ATOMIC = "critical_atomic"  # Requires atomic transaction
    EVENT_DRIVEN = "event_driven"  # Can use eventual consistency
    SYNC_AGENT = "sync_agent"  # Handled by MFO sync agent


class FlowStatusEvent:
    """Event for flow status changes"""

    def __init__(
        self,
        flow_id: str,
        flow_type: str,
        child_status: str,
        master_status: Optional[str] = None,
        requires_master_sync: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.flow_id = flow_id
        self.flow_type = flow_type
        self.child_status = child_status
        self.master_status = master_status
        self.requires_master_sync = requires_master_sync
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class FlowStatusSyncService:
    """
    Service for synchronizing flow status between master and child flows

    Implements ADR-012 separation of concerns:
    - Master Flow: lifecycle management (initialized, running, paused, completed, failed, deleted)
    - Child Flow: operational decisions (field_mapping, data_cleansing, etc.)
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.master_repo = CrewAIFlowStateExtensionsRepository(
            db, context.client_account_id, context.engagement_id, context.user_id
        )
        self._child_repos = {}
        self._event_queue: List[FlowStatusEvent] = []

    def _get_child_repo(self, flow_type: str):
        """Get appropriate child flow repository"""
        if flow_type not in self._child_repos:
            if flow_type == "discovery":
                self._child_repos[flow_type] = DiscoveryFlowRepository(
                    self.db,
                    self.context.client_account_id,
                    self.context.engagement_id,
                    self.context.user_id,
                )
            elif flow_type == "assessment":
                # REMOVED - AssessmentFlow was removed
                raise ValueError(f"Assessment flow type is no longer supported")
            else:
                raise ValueError(f"Unsupported flow type: {flow_type}")

        return self._child_repos[flow_type]

    async def update_flow_status_atomically(
        self,
        flow_id: str,
        flow_type: str,
        child_status: str,
        master_status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Atomically update both master and child flow status

        Used for critical operations like start/pause/resume where both
        statuses must be updated together or not at all.
        """
        logger.info(
            f"🔄 [FlowStatusSync] Atomic update: {flow_id} -> child:{child_status}, master:{master_status}"
        )

        try:
            # Get Redis cache
            redis_cache = get_redis_cache()

            # Acquire distributed lock for atomic operation
            lock_id = await redis_cache.acquire_lock(f"flow:status:{flow_id}", ttl=30)
            if not lock_id:
                logger.warning(
                    f"Failed to acquire lock for flow {flow_id}, retrying..."
                )
                # Wait and retry once
                await asyncio.sleep(0.5)
                lock_id = await redis_cache.acquire_lock(
                    f"flow:status:{flow_id}", ttl=30
                )
                if not lock_id:
                    raise FlowStateUpdateError(
                        "Could not acquire lock for atomic update"
                    )

            try:
                async with self.db.begin():  # Start transaction
                    # Update master flow
                    master_flow = await self.master_repo.get_by_flow_id(flow_id)
                    if not master_flow:
                        raise FlowNotFoundError(flow_id)

                    await self.master_repo.update_flow_status(
                        flow_id=flow_id, status=master_status, metadata=metadata
                    )

                    # Update child flow
                    child_repo = self._get_child_repo(flow_type)
                    await child_repo.update_flow_status(
                        flow_id=flow_id, status=child_status, metadata=metadata
                    )

                    # Both updates succeed together
                    logger.info(
                        f"✅ [FlowStatusSync] Atomic update successful: {flow_id}"
                    )

                    # Invalidate existing cache before update
                    await redis_cache.invalidate_flow_cache(flow_id)

                    # Update Redis cache with new state
                    flow_state = {
                        "flow_id": flow_id,
                        "flow_type": flow_type,
                        "master_status": master_status,
                        "child_status": child_status,
                        "metadata": metadata,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                    await redis_cache.cache_flow_state(flow_id, flow_state)

                    return {
                        "success": True,
                        "flow_id": flow_id,
                        "master_status": master_status,
                        "child_status": child_status,
                        "update_type": "atomic",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
            finally:
                # Always release the lock
                await redis_cache.release_lock(f"flow:status:{flow_id}", lock_id)

        except SQLAlchemyError as e:
            logger.error(f"❌ [FlowStatusSync] Atomic update failed: {flow_id} - {e}")
            raise FlowStateUpdateError(f"Atomic status update failed: {e}")

    async def publish_status_event(self, event: FlowStatusEvent):
        """
        Publish a flow status event for eventual consistency

        Used for non-critical updates that don't require immediate consistency
        """
        logger.info(
            f"📢 [FlowStatusSync] Publishing event: {event.flow_id} -> {event.child_status}"
        )

        # Add to event queue (in production, this would be a message queue)
        self._event_queue.append(event)

        # Process event immediately for now (in production, this would be async)
        await self._process_status_event(event)

    async def _process_status_event(self, event: FlowStatusEvent):
        """Process a status event"""
        try:
            # Update child flow status
            child_repo = self._get_child_repo(event.flow_type)
            await child_repo.update_flow_status(
                flow_id=event.flow_id,
                status=event.child_status,
                metadata=event.metadata,
            )

            # Update master flow if required
            if event.requires_master_sync and event.master_status:
                await self.master_repo.update_flow_status(
                    flow_id=event.flow_id,
                    status=event.master_status,
                    metadata=event.metadata,
                )

            logger.info(f"✅ [FlowStatusSync] Event processed: {event.flow_id}")

        except Exception as e:
            logger.error(
                f"❌ [FlowStatusSync] Event processing failed: {event.flow_id} - {e}"
            )
            # In production, failed events would be retried

    async def start_flow(self, flow_id: str, flow_type: str) -> Dict[str, Any]:
        """Start a flow with atomic status update"""
        return await self.update_flow_status_atomically(
            flow_id=flow_id,
            flow_type=flow_type,
            child_status="active",
            master_status="running",
            metadata={
                "operation": "start",
                "started_at": datetime.utcnow().isoformat(),
            },
        )

    async def pause_flow(
        self, flow_id: str, flow_type: str, reason: str = "user_requested"
    ) -> Dict[str, Any]:
        """Pause a flow with atomic status update"""
        return await self.update_flow_status_atomically(
            flow_id=flow_id,
            flow_type=flow_type,
            child_status="paused",
            master_status="paused",
            metadata={
                "operation": "pause",
                "reason": reason,
                "paused_at": datetime.utcnow().isoformat(),
            },
        )

    async def resume_flow(self, flow_id: str, flow_type: str) -> Dict[str, Any]:
        """Resume a flow with atomic status update"""
        return await self.update_flow_status_atomically(
            flow_id=flow_id,
            flow_type=flow_type,
            child_status="active",
            master_status="running",
            metadata={
                "operation": "resume",
                "resumed_at": datetime.utcnow().isoformat(),
            },
        )

    async def update_operational_status(
        self,
        flow_id: str,
        flow_type: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update operational status via event (non-critical)"""
        event = FlowStatusEvent(
            flow_id=flow_id,
            flow_type=flow_type,
            child_status=status,
            requires_master_sync=False,  # Operational changes don't affect master
            metadata=metadata,
        )
        await self.publish_status_event(event)

    async def validate_flow_consistency(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Validate consistency between master and child flow status"""
        try:
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                return {"consistent": False, "error": "Master flow not found"}

            child_repo = self._get_child_repo(flow_type)
            child_flow = await child_repo.get_by_flow_id(flow_id)
            if not child_flow:
                return {"consistent": False, "error": "Child flow not found"}

            # Define consistency rules
            inconsistencies = []

            # Rule 1: If master is deleted, child should be ignored
            if master_flow.flow_status == "deleted":
                return {
                    "consistent": True,
                    "note": "Master flow deleted - child flow ignored",
                }

            # Rule 2: If master is completed, child should be completed
            if (
                master_flow.flow_status == "completed"
                and child_flow.status != "completed"
            ):
                inconsistencies.append("Master completed but child not completed")

            # Rule 3: If master is running, child should be active or operational
            if master_flow.flow_status == "running" and child_flow.status in [
                "failed",
                "deleted",
            ]:
                inconsistencies.append("Master running but child in terminal state")

            return {
                "consistent": len(inconsistencies) == 0,
                "inconsistencies": inconsistencies,
                "master_status": master_flow.flow_status,
                "child_status": child_flow.status,
            }

        except Exception as e:
            logger.error(
                f"❌ [FlowStatusSync] Consistency validation failed: {flow_id} - {e}"
            )
            return {"consistent": False, "error": str(e)}

    async def recover_from_partial_update(
        self, flow_id: str, flow_type: str
    ) -> Dict[str, Any]:
        """Recover from partial status updates"""
        logger.info(f"🔧 [FlowStatusSync] Recovering from partial update: {flow_id}")

        try:
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            child_repo = self._get_child_repo(flow_type)
            child_flow = await child_repo.get_by_flow_id(flow_id)

            if not master_flow or not child_flow:
                raise FlowNotFoundError(flow_id)

            # Use child flow as source of truth for operational decisions (ADR-012)
            if child_flow.status in ["active", "paused"]:
                # Sync master from child
                master_status = "running" if child_flow.status == "active" else "paused"
                await self.master_repo.update_flow_status(
                    flow_id=flow_id,
                    status=master_status,
                    metadata={
                        "operation": "recovery",
                        "recovered_at": datetime.utcnow().isoformat(),
                    },
                )

                return {
                    "success": True,
                    "recovery_action": "synced_master_from_child",
                    "new_master_status": master_status,
                    "child_status": child_flow.status,
                }

            return {"success": False, "error": "No recovery action needed"}

        except Exception as e:
            logger.error(f"❌ [FlowStatusSync] Recovery failed: {flow_id} - {e}")
            return {"success": False, "error": str(e)}


# Factory function for dependency injection
async def get_flow_status_sync_service(
    db: AsyncSession, context: RequestContext
) -> FlowStatusSyncService:
    """Factory function to create FlowStatusSyncService with proper dependencies"""
    return FlowStatusSyncService(db, context)
