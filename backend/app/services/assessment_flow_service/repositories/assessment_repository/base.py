"""
Base repository class for assessment operations.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.asset import Asset as DiscoveryAsset

logger = logging.getLogger(__name__)


class AssessmentRepositoryBase:
    """Base class for assessment repository operations."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

    def _apply_asset_filters(self, query, filters: Dict[str, Any]):
        """Apply filters to asset query."""

        if filters.get("migration_ready") is not None:
            query = query.where(
                DiscoveryAsset.migration_ready == filters["migration_ready"]
            )

        if filters.get("asset_type"):
            query = query.where(DiscoveryAsset.asset_type == filters["asset_type"])

        if filters.get("asset_subtype"):
            query = query.where(
                DiscoveryAsset.asset_subtype == filters["asset_subtype"]
            )

        if filters.get("validation_status"):
            query = query.where(
                DiscoveryAsset.validation_status == filters["validation_status"]
            )

        if filters.get("migration_complexity"):
            query = query.where(
                DiscoveryAsset.migration_complexity == filters["migration_complexity"]
            )

        if filters.get("migration_priority"):
            query = query.where(
                DiscoveryAsset.migration_priority == filters["migration_priority"]
            )

        if filters.get("min_confidence"):
            query = query.where(
                DiscoveryAsset.confidence_score >= filters["min_confidence"]
            )

        if filters.get("max_confidence"):
            query = query.where(
                DiscoveryAsset.confidence_score <= filters["max_confidence"]
            )

        if filters.get("discovered_in_phase"):
            query = query.where(
                DiscoveryAsset.discovered_in_phase == filters["discovered_in_phase"]
            )

        if filters.get("discovery_method"):
            query = query.where(
                DiscoveryAsset.discovery_method == filters["discovery_method"]
            )

        return query
