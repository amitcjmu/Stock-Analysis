"""
Query operations for assessment repository.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select

from app.models.asset import Asset as DiscoveryAsset
from app.models.discovery_flow import DiscoveryFlow

from .base import AssessmentRepositoryBase

logger = logging.getLogger(__name__)


class AssessmentRepositoryQueries(AssessmentRepositoryBase):
    """Query methods for assessment repository."""

    async def get_flow_by_id(self, flow_id: str) -> Optional[DiscoveryFlow]:
        """
        Get discovery flow by flow ID.

        Args:
            flow_id: Discovery flow identifier

        Returns:
            DiscoveryFlow object or None if not found
        """
        try:
            result = await self.db.execute(
                select(DiscoveryFlow).where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id
                        == self.context.client_account_id,
                    )
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"❌ Error retrieving flow {flow_id}: {e}")
            raise

    async def get_flow_assets(
        self, flow: DiscoveryFlow, filters: Optional[Dict[str, Any]] = None
    ) -> List[DiscoveryAsset]:
        """
        Get assets for a discovery flow with optional filtering.

        Args:
            flow: DiscoveryFlow object
            filters: Optional filters for asset selection

        Returns:
            List of DiscoveryAsset objects
        """
        try:
            # Base query
            query = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow.id,
                    DiscoveryAsset.client_account_id == self.context.client_account_id,
                )
            )

            # Apply filters
            if filters:
                query = self._apply_asset_filters(query, filters)

            # Order by creation date
            query = query.order_by(desc(DiscoveryAsset.created_at))

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"❌ Error retrieving assets for flow {flow.flow_id}: {e}")
            raise

    async def get_assessment_ready_assets(self, flow_id: str) -> List[DiscoveryAsset]:
        """
        Get assets that are ready for assessment.

        Args:
            flow_id: Discovery flow identifier

        Returns:
            List of assessment-ready DiscoveryAsset objects
        """
        try:
            # Get flow first
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Query for assessment-ready assets
            query = (
                select(DiscoveryAsset)
                .where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                        DiscoveryAsset.migration_ready == True,  # noqa: E712
                        DiscoveryAsset.validation_status == "approved",
                    )
                )
                .order_by(desc(DiscoveryAsset.updated_at))
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"❌ Error retrieving assessment-ready assets for flow {flow_id}: {e}"
            )
            raise

    async def get_asset_by_id(self, asset_id: str) -> Optional[DiscoveryAsset]:
        """
        Get discovery asset by asset ID.

        Args:
            asset_id: Asset identifier

        Returns:
            DiscoveryAsset object or None if not found
        """
        try:
            result = await self.db.execute(
                select(DiscoveryAsset).where(
                    and_(
                        DiscoveryAsset.id == uuid.UUID(asset_id),
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"❌ Error retrieving asset {asset_id}: {e}")
            raise

    async def get_flow_statistics(self, flow_id: str) -> Dict[str, Any]:
        """
        Get statistical summary for a discovery flow.

        Args:
            flow_id: Discovery flow identifier

        Returns:
            Dict containing flow statistics
        """
        try:
            # Get flow
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Asset count queries
            base_query = select(func.count(DiscoveryAsset.id)).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow.id,
                    DiscoveryAsset.client_account_id == self.context.client_account_id,
                )
            )

            # Total assets
            total_result = await self.db.execute(base_query)
            total_assets = total_result.scalar()

            # Migration ready assets
            ready_result = await self.db.execute(
                base_query.where(DiscoveryAsset.migration_ready == True)  # noqa: E712
            )
            migration_ready = ready_result.scalar()

            # Validated assets
            validated_result = await self.db.execute(
                base_query.where(DiscoveryAsset.validation_status == "approved")
            )
            validated_assets = validated_result.scalar()

            # Assets by type
            type_query = (
                select(
                    DiscoveryAsset.asset_type,
                    func.count(DiscoveryAsset.id).label("count"),
                )
                .where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .group_by(DiscoveryAsset.asset_type)
            )

            type_result = await self.db.execute(type_query)
            asset_types = {
                row.asset_type or "unknown": row.count for row in type_result
            }

            # Assets by complexity
            complexity_query = (
                select(
                    DiscoveryAsset.migration_complexity,
                    func.count(DiscoveryAsset.id).label("count"),
                )
                .where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .group_by(DiscoveryAsset.migration_complexity)
            )

            complexity_result = await self.db.execute(complexity_query)
            complexity_distribution = {
                row.migration_complexity or "unknown": row.count
                for row in complexity_result
            }

            # Calculate percentages
            ready_percentage = (
                (migration_ready / total_assets * 100) if total_assets > 0 else 0
            )
            validated_percentage = (
                (validated_assets / total_assets * 100) if total_assets > 0 else 0
            )

            statistics = {
                "flow_id": flow_id,
                "total_assets": total_assets,
                "migration_ready": migration_ready,
                "migration_ready_percentage": round(ready_percentage, 1),
                "validated_assets": validated_assets,
                "validated_percentage": round(validated_percentage, 1),
                "asset_types": asset_types,
                "complexity_distribution": complexity_distribution,
                "flow_status": flow.status,
                "progress_percentage": flow.progress_percentage,
                "assessment_ready": flow.assessment_ready or False,
            }

            return statistics

        except Exception as e:
            logger.error(f"❌ Error retrieving flow statistics: {e}")
            raise

    async def get_assets_by_criteria(
        self, flow_id: str, criteria: Dict[str, Any]
    ) -> List[DiscoveryAsset]:
        """
        Get assets matching specific criteria.

        Args:
            flow_id: Discovery flow identifier
            criteria: Asset selection criteria

        Returns:
            List of matching DiscoveryAsset objects
        """
        try:
            # Get flow
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Build query
            query = select(DiscoveryAsset).where(
                and_(
                    DiscoveryAsset.discovery_flow_id == flow.id,
                    DiscoveryAsset.client_account_id == self.context.client_account_id,
                )
            )

            # Apply criteria
            query = self._apply_asset_filters(query, criteria)

            # Order by priority and name
            query = query.order_by(
                DiscoveryAsset.migration_priority.asc(), DiscoveryAsset.asset_name.asc()
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"❌ Error retrieving assets by criteria: {e}")
            raise

    async def search_assets(
        self, flow_id: str, search_term: str, limit: int = 50
    ) -> List[DiscoveryAsset]:
        """
        Search assets by name or type within a flow.

        Args:
            flow_id: Discovery flow identifier
            search_term: Search term for asset name or type
            limit: Maximum number of results

        Returns:
            List of matching DiscoveryAsset objects
        """
        try:
            # Get flow
            flow = await self.get_flow_by_id(flow_id)
            if not flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Build search query
            search_pattern = f"%{search_term.lower()}%"

            query = (
                select(DiscoveryAsset)
                .where(
                    and_(
                        DiscoveryAsset.discovery_flow_id == flow.id,
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                        func.lower(DiscoveryAsset.asset_name).like(search_pattern)
                        | func.lower(DiscoveryAsset.asset_type).like(search_pattern)
                        | func.lower(DiscoveryAsset.asset_subtype).like(search_pattern),
                    )
                )
                .order_by(DiscoveryAsset.asset_name.asc())
                .limit(limit)
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"❌ Error searching assets: {e}")
            raise
