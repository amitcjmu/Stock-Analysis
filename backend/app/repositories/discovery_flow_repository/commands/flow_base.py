"""
Base functionality for flow commands.

Contains core utilities, initialization, and shared helper methods.
"""

import logging
import uuid
from typing import Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.discovery_flow import DiscoveryFlow
from app.services.caching.redis_cache import get_redis_cache

from ..queries.flow_queries import FlowQueries

logger = logging.getLogger(__name__)


class FlowCommandsBase:
    """Base class for flow command operations"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.flow_queries = FlowQueries(db, client_account_id, engagement_id)
        self.redis = get_redis_cache()

    def _ensure_uuid(self, flow_id: Any) -> uuid.UUID:
        """Ensure flow_id is a UUID object"""
        if isinstance(flow_id, uuid.UUID):
            return flow_id
        try:
            return uuid.UUID(str(flow_id))
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Invalid UUID: {flow_id}, error: {e}")
            raise ValueError(f"Invalid UUID: {flow_id}. Must be a valid UUID.")

    async def _invalidate_flow_cache(self, flow: DiscoveryFlow):
        """Invalidate cached data for a discovery flow"""
        if not self.redis or not self.redis.enabled:
            return

        try:
            # Invalidate cache by master flow ID
            if flow.master_flow_id:
                cache_key = f"v1:flow:discovery:by_master:{flow.master_flow_id}"
                await self.redis.delete(cache_key)
                logger.debug(
                    f"Invalidated cache for master_flow_id: {flow.master_flow_id}"
                )
        except Exception as e:
            logger.warning(f"Failed to invalidate flow cache: {e}")

    async def _update_master_flow_completion(self, flow_id: str) -> bool:
        """
        Update the master flow state to completed status.

        Args:
            flow_id: The flow ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from app.repositories.crewai_flow_state_extensions_repository import (
                CrewAIFlowStateExtensionsRepository,
            )

            # Create master repo with same context
            master_repo = CrewAIFlowStateExtensionsRepository(
                db=self.db,
                client_account_id=str(self.client_account_id),
                engagement_id=str(self.engagement_id),
                user_id="system",
            )

            # Update master flow status
            await master_repo.update_flow_status(
                flow_id=flow_id,
                status="completed",
                phase_data={
                    "completed_by": "discovery_flow_completion",
                    "completion_timestamp": datetime.utcnow().isoformat(),
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_completed",
                    "source": "discovery_flow_completion",
                    "message": "Discovery flow completed successfully - all phases finished",
                },
            )

            logger.info(f"✅ Master flow state updated to completed for: {flow_id}")
            return True

        except Exception as e:
            logger.warning(
                f"⚠️ Failed to update master flow completion for {flow_id}: {e}"
            )
            # Don't fail the whole operation if master flow update fails
            return False
