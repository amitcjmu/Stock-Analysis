"""
Discovery Flow Completion Service - Query Module
Handles data retrieval for assessment-ready assets and filtering.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import and_, select

from app.models.asset import Asset as DiscoveryAsset

logger = logging.getLogger(__name__)


class AssetQueryManager:
    """Manager for querying assessment-ready assets"""

    def __init__(self, service):
        """
        Initialize query manager with parent service reference.

        Args:
            service: Parent DiscoveryFlowCompletionService instance
        """
        self.service = service
        self.db = service.db
        self.context = service.context
        self.discovery_repo = service.discovery_repo

    async def get_assessment_ready_assets(
        self, discovery_flow_id: uuid.UUID, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get assets that are ready for assessment with optional filtering.

        Args:
            discovery_flow_id: UUID of the discovery flow
            filters: Optional filters (migration_ready, asset_type, min_confidence, etc.)

        Returns:
            Dict containing filtered assets and metadata
        """
        try:
            logger.info(
                f"🔍 Getting assessment-ready assets for flow: {discovery_flow_id}"
            )

            # Get discovery flow
            flow = await self.discovery_repo.get_by_flow_id(str(discovery_flow_id))
            if not flow:
                raise ValueError(f"Discovery flow not found: {discovery_flow_id}")

            # Build and execute query
            assets = await self._execute_asset_query(flow.id, filters)

            # Convert to response format
            asset_list = self._format_assets(assets)

            # Generate summary statistics
            summary = self._generate_summary(asset_list)

            response = {
                "flow_id": str(discovery_flow_id),
                "filters_applied": filters or {},
                "assets": asset_list,
                "summary": summary,
            }

            logger.info(
                f"✅ Retrieved {len(asset_list)} assessment-ready assets for flow: {discovery_flow_id}"
            )
            return response

        except Exception as e:
            logger.error(f"❌ Error getting assessment-ready assets: {e}")
            raise

    async def _execute_asset_query(
        self, flow_internal_id: uuid.UUID, filters: Optional[Dict[str, Any]]
    ) -> list:
        """Build and execute asset query with filters"""
        # Base query for assets
        query = select(DiscoveryAsset).where(
            and_(
                DiscoveryAsset.discovery_flow_id == flow_internal_id,
                DiscoveryAsset.client_account_id == self.context.client_account_id,
            )
        )

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Execute query
        result = await self.db.execute(query)
        return result.scalars().all()

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """Apply filter conditions to query"""
        if filters.get("migration_ready") is True:
            query = query.where(DiscoveryAsset.migration_ready == True)  # noqa: E712

        if filters.get("asset_type"):
            query = query.where(DiscoveryAsset.asset_type == filters["asset_type"])

        if filters.get("min_confidence"):
            query = query.where(
                DiscoveryAsset.confidence_score >= filters["min_confidence"]
            )

        if filters.get("validation_status"):
            query = query.where(
                DiscoveryAsset.validation_status == filters["validation_status"]
            )

        if filters.get("migration_complexity"):
            query = query.where(
                DiscoveryAsset.migration_complexity == filters["migration_complexity"]
            )

        return query

    def _format_assets(self, assets: list) -> list:
        """Convert assets to response format"""
        asset_list = []
        for asset in assets:
            asset_dict = {
                "id": str(asset.id),
                "discovery_flow_id": str(asset.discovery_flow_id),
                "asset_name": asset.asset_name,
                "asset_type": asset.asset_type,
                "asset_subtype": asset.asset_subtype,
                "migration_ready": asset.migration_ready,
                "migration_complexity": asset.migration_complexity,
                "migration_priority": asset.migration_priority,
                "confidence_score": asset.confidence_score,
                "validation_status": asset.validation_status,
                "discovered_in_phase": asset.discovered_in_phase,
                "discovery_method": asset.discovery_method,
                "normalized_data": asset.normalized_data,
                "created_at": (
                    asset.created_at.isoformat() if asset.created_at else None
                ),
                "updated_at": (
                    asset.updated_at.isoformat() if asset.updated_at else None
                ),
            }
            asset_list.append(asset_dict)
        return asset_list

    def _generate_summary(self, asset_list: list) -> Dict[str, Any]:
        """Generate summary statistics for assets"""
        total_count = len(asset_list)
        migration_ready_count = sum(1 for a in asset_list if a["migration_ready"])

        asset_types = {}
        complexities = {}
        for asset in asset_list:
            asset_type = asset["asset_type"] or "unknown"
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1

            complexity = asset["migration_complexity"] or "unknown"
            complexities[complexity] = complexities.get(complexity, 0) + 1

        return {
            "total_assets": total_count,
            "migration_ready": migration_ready_count,
            "migration_ready_percentage": (
                (migration_ready_count / total_count * 100) if total_count > 0 else 0
            ),
            "by_type": asset_types,
            "by_complexity": complexities,
            "average_confidence": (
                sum(a["confidence_score"] or 0 for a in asset_list) / total_count
                if total_count > 0
                else 0
            ),
        }
