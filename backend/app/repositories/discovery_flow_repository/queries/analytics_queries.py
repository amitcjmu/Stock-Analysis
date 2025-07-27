"""
Analytics Queries

Analytics and reporting queries for discovery flows.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class AnalyticsQueries:
    """Handles analytics and reporting queries"""

    def __init__(
        self, db: AsyncSession, client_account_id: uuid.UUID, engagement_id: uuid.UUID
    ):
        """Initialize with database session and context"""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_master_flow_coordination_summary(self) -> Dict[str, Any]:
        """Get summary of master flow coordination across the system"""
        try:
            # Count primary flows
            primary_stmt = select(func.count(DiscoveryFlow.id)).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.flow_type == "primary",
                )
            )
            primary_result = await self.db.execute(primary_stmt)
            primary_count = primary_result.scalar() or 0

            # Count supplemental flows
            supplemental_stmt = select(func.count(DiscoveryFlow.id)).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.flow_type == "supplemental",
                )
            )
            supplemental_result = await self.db.execute(supplemental_stmt)
            supplemental_count = supplemental_result.scalar() or 0

            # Count assessment flows
            assessment_stmt = select(func.count(DiscoveryFlow.id)).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.flow_type == "assessment",
                )
            )
            assessment_result = await self.db.execute(assessment_stmt)
            assessment_count = assessment_result.scalar() or 0

            # Get flows with master references
            master_ref_stmt = select(func.count(DiscoveryFlow.id)).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.master_flow_id is not None,
                )
            )
            master_ref_result = await self.db.execute(master_ref_stmt)
            flows_with_master_ref = master_ref_result.scalar() or 0

            # Get assessment-ready flows
            assessment_ready_stmt = select(func.count(DiscoveryFlow.id)).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.assessment_ready is True,
                )
            )
            assessment_ready_result = await self.db.execute(assessment_ready_stmt)
            assessment_ready_count = assessment_ready_result.scalar() or 0

            return {
                "flow_type_distribution": {
                    "primary": primary_count,
                    "supplemental": supplemental_count,
                    "assessment": assessment_count,
                },
                "master_flow_references": {
                    "flows_with_master_reference": flows_with_master_ref,
                    "flows_without_master_reference": primary_count
                    + supplemental_count
                    - flows_with_master_ref,
                },
                "assessment_readiness": {
                    "ready_for_assessment": assessment_ready_count,
                    "not_ready": primary_count
                    + supplemental_count
                    - assessment_ready_count,
                },
                "coordination_metrics": {
                    "avg_supplemental_per_primary": (
                        supplemental_count / primary_count if primary_count > 0 else 0
                    ),
                    "assessment_conversion_rate": (
                        assessment_count / primary_count if primary_count > 0 else 0
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error getting master flow coordination summary: {e}")
            return {
                "error": str(e),
                "flow_type_distribution": {},
                "master_flow_references": {},
                "assessment_readiness": {},
                "coordination_metrics": {},
            }

    async def get_flow_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get flow analytics for the specified period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get flow count by status
            status_stmt = (
                select(DiscoveryFlow.status, func.count(DiscoveryFlow.id))
                .where(
                    and_(
                        DiscoveryFlow.client_account_id == self.client_account_id,
                        DiscoveryFlow.engagement_id == self.engagement_id,
                        DiscoveryFlow.created_at >= start_date,
                    )
                )
                .group_by(DiscoveryFlow.status)
            )

            status_result = await self.db.execute(status_stmt)
            status_distribution = dict(status_result.all())

            # Get phase completion rates
            phase_stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.client_account_id == self.client_account_id,
                    DiscoveryFlow.engagement_id == self.engagement_id,
                    DiscoveryFlow.created_at >= start_date,
                )
            )

            phase_result = await self.db.execute(phase_stmt)
            flows = phase_result.scalars().all()

            total_flows = len(flows)
            phase_completion = {
                "data_import": (
                    sum(1 for f in flows if f.data_import_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
                "attribute_mapping": (
                    sum(1 for f in flows if f.attribute_mapping_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
                "data_cleansing": (
                    sum(1 for f in flows if f.data_cleansing_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
                "inventory": (
                    sum(1 for f in flows if f.inventory_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
                "dependencies": (
                    sum(1 for f in flows if f.dependencies_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
                "tech_debt": (
                    sum(1 for f in flows if f.tech_debt_completed) / total_flows
                    if total_flows > 0
                    else 0
                ),
            }

            # Get average progress
            avg_progress = (
                sum(f.progress_percentage or 0 for f in flows) / total_flows
                if total_flows > 0
                else 0
            )

            # Get asset count by flow
            asset_stmt = (
                select(
                    Asset.discovery_flow_id,  # CC FIX: Use column field, not custom_attributes
                    func.count(Asset.id),
                )
                .where(
                    and_(
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == self.engagement_id,
                        Asset.created_at >= start_date,
                    )
                )
                .group_by(Asset.discovery_flow_id)
            )

            asset_result = await self.db.execute(asset_stmt)
            assets_by_flow = dict(asset_result.all())

            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days,
                },
                "flow_metrics": {
                    "total_flows": total_flows,
                    "status_distribution": status_distribution,
                    "average_progress": avg_progress,
                    "phase_completion_rates": phase_completion,
                },
                "asset_metrics": {
                    "total_assets_discovered": sum(assets_by_flow.values()),
                    "average_assets_per_flow": (
                        sum(assets_by_flow.values()) / len(assets_by_flow)
                        if assets_by_flow
                        else 0
                    ),
                    "flows_with_assets": len(assets_by_flow),
                },
            }

        except Exception as e:
            logger.error(f"Error getting flow analytics: {e}")
            return {
                "error": str(e),
                "period": {},
                "flow_metrics": {},
                "asset_metrics": {},
            }
