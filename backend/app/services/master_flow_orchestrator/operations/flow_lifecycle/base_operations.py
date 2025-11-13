"""
Base Flow Operations - Common functionality for flow lifecycle operations.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)
from app.services.flow_contracts import FlowAuditLogger

from ..flow_cache_manager import FlowCacheManager
from ..mock_monitor import MockFlowPerformanceMonitor

logger = logging.getLogger(__name__)


class BaseFlowOperations:
    """Base class for flow operations with common functionality."""

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
        flow_registry,
        performance_monitor: MockFlowPerformanceMonitor,
        audit_logger: FlowAuditLogger,
        cache_manager: FlowCacheManager,
    ):
        self.db = db
        self.context = context
        self.master_repo = master_repo
        self.flow_registry = flow_registry
        self.performance_monitor = performance_monitor
        self.audit_logger = audit_logger
        self.cache_manager = cache_manager

    async def _update_redis_flow_status(self, flow_id: str, status: str) -> None:
        """Update flow status in Redis cache"""
        try:
            from app.services.caching.redis_cache import redis_cache

            await redis_cache.update_flow_status(
                flow_id,
                status,
                self.context.client_account_id,
                self.context.engagement_id,
            )
        except Exception as e:
            logger.warning(f"Failed to update Redis status for {flow_id}: {e}")

    async def _check_for_orphaned_collection_flow(
        self, flow_id: str, operation: str
    ) -> Optional[dict]:
        """Check for orphaned collection flow and return info if found."""
        logger.info(
            f"🔍 Checking for orphaned collection flow data for {operation} operation on {flow_id}"
        )

        try:
            from sqlalchemy import select
            from app.models.collection_flow import CollectionFlow

            # Check if there's a collection flow with this ID but no master_flow_id
            result = await self.db.execute(
                select(CollectionFlow).where(
                    CollectionFlow.flow_id == flow_id,
                    CollectionFlow.client_account_id == self.context.client_account_id,
                    CollectionFlow.engagement_id == self.context.engagement_id,
                    CollectionFlow.master_flow_id.is_(None),
                )
            )
            orphaned_collection = result.scalar_one_or_none()

            if orphaned_collection:
                return {
                    "flow_id": flow_id,
                    "status": orphaned_collection.status,
                    "current_phase": orphaned_collection.current_phase,
                }

            return None

        except Exception as e:
            logger.error(f"Error checking for orphaned collection flow: {e}")
            return None
