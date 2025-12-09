"""
Command operations for assessment repository.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_, update

from app.models.asset import Asset as DiscoveryAsset
from app.models.discovery_flow import DiscoveryFlow

from .base import AssessmentRepositoryBase

logger = logging.getLogger(__name__)


class AssessmentRepositoryCommands(AssessmentRepositoryBase):
    """Command methods for assessment repository."""

    async def update_flow_completion_status(
        self, flow_id: str, completion_data: Dict[str, Any]
    ) -> DiscoveryFlow:
        """
        Update flow completion status and assessment data.

        Args:
            flow_id: Discovery flow identifier
            completion_data: Completion status and assessment data

        Returns:
            Updated DiscoveryFlow object
        """
        try:
            # Prepare update values
            update_values = {
                "status": "completed",
                "progress_percentage": 100.0,
                "assessment_ready": True,
                "completed_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            # Add assessment package if provided
            if "assessment_package" in completion_data:
                update_values["assessment_package"] = completion_data[
                    "assessment_package"
                ]
                update_values["assessment_package_generated"] = True

            # Add migration readiness score if provided
            if "migration_readiness_score" in completion_data:
                update_values["migration_readiness_score"] = completion_data[
                    "migration_readiness_score"
                ]

            # Execute update
            await self.db.execute(
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .values(**update_values)
            )

            await self.db.commit()

            # Return updated flow - import get_flow_by_id locally to avoid circular import
            from .queries import AssessmentRepositoryQueries

            queries = AssessmentRepositoryQueries(self.db, self.context)
            updated_flow = await queries.get_flow_by_id(flow_id)
            if not updated_flow:
                raise ValueError(f"Failed to retrieve updated flow: {flow_id}")

            logger.info(f"✅ Flow completion status updated: {flow_id}")
            return updated_flow

        except Exception as e:
            logger.error(f"❌ Error updating flow completion status: {e}")
            await self.db.rollback()
            raise

    async def update_asset_assessment_data(
        self, asset_id: str, assessment_data: Dict[str, Any]
    ) -> DiscoveryAsset:
        """
        Update asset with assessment-specific data.

        Args:
            asset_id: Asset identifier
            assessment_data: Assessment data to update

        Returns:
            Updated DiscoveryAsset object
        """
        try:
            # Prepare update values
            update_values = {"updated_at": datetime.utcnow()}

            # Add assessment data to normalized_data - import get_asset_by_id locally
            from .queries import AssessmentRepositoryQueries

            queries = AssessmentRepositoryQueries(self.db, self.context)
            asset = await queries.get_asset_by_id(asset_id)
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")

            normalized_data = asset.normalized_data or {}
            normalized_data.update(assessment_data)
            update_values["normalized_data"] = normalized_data

            # Execute update
            await self.db.execute(
                update(DiscoveryAsset)
                .where(
                    and_(
                        DiscoveryAsset.id == uuid.UUID(asset_id),
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .values(**update_values)
            )

            await self.db.commit()

            # Return updated asset
            updated_asset = await queries.get_asset_by_id(asset_id)
            if not updated_asset:
                raise ValueError(f"Failed to retrieve updated asset: {asset_id}")

            logger.info(f"✅ Asset assessment data updated: {asset_id}")
            return updated_asset

        except Exception as e:
            logger.error(f"❌ Error updating asset assessment data: {e}")
            await self.db.rollback()
            raise

    async def bulk_update_assets(
        self, asset_ids: List[str], update_data: Dict[str, Any]
    ) -> int:
        """
        Bulk update multiple assets with common data.

        Args:
            asset_ids: List of asset identifiers
            update_data: Data to update for all assets

        Returns:
            Number of assets updated
        """
        try:
            if not asset_ids:
                return 0

            # Prepare update values
            update_values = dict(update_data)
            update_values["updated_at"] = datetime.utcnow()

            # Execute bulk update
            result = await self.db.execute(
                update(DiscoveryAsset)
                .where(
                    and_(
                        DiscoveryAsset.id.in_([uuid.UUID(aid) for aid in asset_ids]),
                        DiscoveryAsset.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .values(**update_values)
            )

            await self.db.commit()

            updated_count = result.rowcount
            logger.info(f"✅ Bulk updated {updated_count} assets")
            return updated_count

        except Exception as e:
            logger.error(f"❌ Error bulk updating assets: {e}")
            await self.db.rollback()
            raise

    async def delete_assessment_data(self, flow_id: str) -> bool:
        """
        Delete assessment data for a flow (for cleanup or reset).

        Args:
            flow_id: Discovery flow identifier

        Returns:
            True if successful
        """
        try:
            # Update flow to remove assessment data
            await self.db.execute(
                update(DiscoveryFlow)
                .where(
                    and_(
                        DiscoveryFlow.flow_id == flow_id,
                        DiscoveryFlow.client_account_id
                        == self.context.client_account_id,
                    )
                )
                .values(
                    assessment_package=None,
                    assessment_package_generated=False,
                    assessment_ready=False,
                    updated_at=datetime.utcnow(),
                )
            )

            await self.db.commit()

            logger.info(f"✅ Assessment data deleted for flow: {flow_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting assessment data: {e}")
            await self.db.rollback()
            raise
