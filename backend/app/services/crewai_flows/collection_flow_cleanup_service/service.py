"""
Main Collection Flow Cleanup Service

Enhanced cleanup service for Collection flows combining all modularized components
for backward compatibility.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

from .expired_flows import ExpiredFlowsCleanupService
from .orphaned_flows import OrphanedFlowsCleanupService
from .recommendations import CleanupRecommendationsService

logger = logging.getLogger(__name__)


class CollectionFlowCleanupService:
    """
    Enhanced cleanup service for Collection flows with smart detection
    and multi-layer persistence cleanup.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

        # Initialize component services
        self._expired_flows = ExpiredFlowsCleanupService(db, context)
        self._orphaned_flows = OrphanedFlowsCleanupService(db, context)
        self._recommendations = CleanupRecommendationsService(db, context)

    async def cleanup_expired_flows(
        self,
        expiration_hours: int = 72,
        dry_run: bool = True,
        include_failed: bool = True,
        include_cancelled: bool = True,
        force_cleanup_active: bool = False,
    ) -> Dict[str, Any]:
        """
        Clean up expired Collection flows with smart filtering

        Args:
            expiration_hours: Hours after which flows are considered expired
            dry_run: Preview cleanup without actually deleting
            include_failed: Include failed flows in cleanup
            include_cancelled: Include cancelled flows in cleanup
            force_cleanup_active: Force cleanup of active flows (dangerous)
        """
        return await self._expired_flows.cleanup_expired_flows(
            expiration_hours=expiration_hours,
            dry_run=dry_run,
            include_failed=include_failed,
            include_cancelled=include_cancelled,
            force_cleanup_active=force_cleanup_active,
        )

    async def cleanup_orphaned_flows(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean up flows that have lost their CrewAI state but still exist in PostgreSQL
        """
        return await self._orphaned_flows.cleanup_orphaned_flows(dry_run=dry_run)

    async def get_cleanup_recommendations(self) -> Dict[str, Any]:
        """
        Analyze Collection flows and provide cleanup recommendations
        """
        return await self._recommendations.get_cleanup_recommendations()

    async def cleanup_stuck_initialized_flows(
        self, timeout_minutes: int = 5, dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up flows stuck in INITIALIZED state

        Args:
            timeout_minutes: Minutes after which INITIALIZED flows are considered stuck
            dry_run: Preview cleanup without actually performing it
        """
        return await self._recommendations.cleanup_stuck_initialized_flows(
            timeout_minutes=timeout_minutes, dry_run=dry_run
        )
