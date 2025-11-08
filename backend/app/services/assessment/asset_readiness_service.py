"""
Asset Readiness Service - Integrates GapAnalyzer with Assessment Flow.

Provides methods to:
1. Analyze individual asset readiness
2. Analyze batch asset readiness for an assessment flow
3. Get readiness summary statistics
4. Filter assets by readiness status

Part of Issue #980: Intelligent Multi-Layer Gap Detection System
Day 11: AssessmentFlowChildService Integration and API Endpoints
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset
from app.models.assessment_flow import AssessmentFlow
from app.models.canonical_applications.canonical_application import (
    CanonicalApplication,
)
from app.services.gap_detection import GapAnalyzer
from app.services.gap_detection.schemas import ComprehensiveGapReport

logger = logging.getLogger(__name__)


class AssetReadinessService:
    """Service for analyzing asset readiness for assessment flows."""

    def __init__(self):
        self.gap_analyzer = GapAnalyzer()

    async def analyze_asset_readiness(
        self,
        asset_id: UUID,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
    ) -> ComprehensiveGapReport:
        """
        Analyze readiness of a single asset.

        Args:
            asset_id: Asset UUID
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID
            db: AsyncSession for database queries

        Returns:
            ComprehensiveGapReport with full gap analysis

        Raises:
            ValueError: If asset not found or not in tenant scope
        """
        # Query asset with tenant scoping (CRITICAL: Multi-tenant isolation)
        stmt = select(Asset).where(
            Asset.id == asset_id,
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            raise ValueError(
                f"Asset {asset_id} not found or not in tenant scope "
                f"(client_account_id={client_account_id}, "
                f"engagement_id={engagement_id})"
            )

        # Query linked application (if any)
        application = None
        if asset.canonical_application_id:
            stmt = select(CanonicalApplication).where(
                CanonicalApplication.id == asset.canonical_application_id,
                CanonicalApplication.client_account_id == UUID(client_account_id),
            )
            result = await db.execute(stmt)
            application = result.scalar_one_or_none()

        # Run gap analysis (GapAnalyzer orchestrates all 5 inspectors)
        logger.info(
            f"Analyzing asset readiness for asset_id={asset_id}",
            extra={
                "asset_id": str(asset_id),
                "asset_name": getattr(asset, "asset_name", "unknown"),
                "has_application": application is not None,
                "client_account_id": client_account_id,
                "engagement_id": engagement_id,
            },
        )

        report = await self.gap_analyzer.analyze_asset(
            asset=asset,
            application=application,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=db,
        )

        return report

    async def analyze_flow_assets_readiness(
        self,
        flow_id: UUID,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
        detailed: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyze readiness of all assets selected in an assessment flow.

        Args:
            flow_id: AssessmentFlow UUID
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID
            db: AsyncSession for database queries
            detailed: If True, include full reports per asset; if False, counts only

        Returns:
            Dict with:
            {
                "flow_id": str,
                "total_assets": int,
                "ready_count": int,
                "not_ready_count": int,
                "overall_readiness_rate": float,  # Percentage ready (0-100)
                "asset_reports": List[Dict],  # Only if detailed=True
                "summary_by_type": Dict[str, Dict],  # Readiness by asset type
                "analyzed_at": str (ISO timestamp)
            }

        Raises:
            ValueError: If flow not found or not in tenant scope
        """
        # Query assessment flow with tenant scoping
        stmt = select(AssessmentFlow).where(
            AssessmentFlow.flow_id == flow_id,
            AssessmentFlow.client_account_id == UUID(client_account_id),
            AssessmentFlow.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise ValueError(
                f"Assessment flow {flow_id} not found or not in tenant scope "
                f"(client_account_id={client_account_id}, "
                f"engagement_id={engagement_id})"
            )

        # Get selected application IDs from flow
        selected_app_ids = flow.selected_application_ids or []

        if not selected_app_ids:
            logger.warning(
                f"Assessment flow {flow_id} has no selected applications",
                extra={"flow_id": str(flow_id), "client_account_id": client_account_id},
            )
            return {
                "flow_id": str(flow_id),
                "total_assets": 0,
                "ready_count": 0,
                "not_ready_count": 0,
                "overall_readiness_rate": 0.0,
                "asset_reports": [],
                "summary_by_type": {},
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        # Query all assets linked to selected applications
        stmt = select(Asset).where(
            Asset.canonical_application_id.in_(
                [UUID(app_id) for app_id in selected_app_ids]
            ),
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        assets = result.scalars().all()

        logger.info(
            f"Analyzing readiness for {len(assets)} assets in flow {flow_id}",
            extra={
                "flow_id": str(flow_id),
                "total_assets": len(assets),
                "selected_applications": len(selected_app_ids),
                "detailed": detailed,
            },
        )

        # Analyze each asset
        ready_count = 0
        not_ready_count = 0
        asset_reports = []
        summary_by_type: Dict[str, Dict[str, int]] = {}

        for asset in assets:
            try:
                report = await self.analyze_asset_readiness(
                    asset_id=asset.id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    db=db,
                )

                # Count readiness
                if report.is_ready_for_assessment:
                    ready_count += 1
                else:
                    not_ready_count += 1

                # Track by asset type
                asset_type = getattr(asset, "asset_type", "unknown")
                if asset_type not in summary_by_type:
                    summary_by_type[asset_type] = {"ready": 0, "not_ready": 0}

                if report.is_ready_for_assessment:
                    summary_by_type[asset_type]["ready"] += 1
                else:
                    summary_by_type[asset_type]["not_ready"] += 1

                # Include detailed report if requested
                if detailed:
                    asset_reports.append(
                        {
                            "asset_id": str(asset.id),
                            "asset_name": getattr(asset, "asset_name", "unknown"),
                            "asset_type": asset_type,
                            "is_ready": report.is_ready_for_assessment,
                            "overall_completeness": report.overall_completeness,
                            "readiness_blockers": report.readiness_blockers,
                            "critical_gaps_count": len(report.critical_gaps),
                            "high_priority_gaps_count": len(report.high_priority_gaps),
                        }
                    )

            except Exception as e:
                logger.error(
                    f"Failed to analyze asset {asset.id} in flow {flow_id}: {e}",
                    extra={"asset_id": str(asset.id), "flow_id": str(flow_id)},
                    exc_info=True,
                )
                not_ready_count += 1

        total_assets = len(assets)
        overall_readiness_rate = (
            (ready_count / total_assets * 100) if total_assets > 0 else 0.0
        )

        return {
            "flow_id": str(flow_id),
            "total_assets": total_assets,
            "ready_count": ready_count,
            "not_ready_count": not_ready_count,
            "overall_readiness_rate": round(overall_readiness_rate, 2),
            "asset_reports": asset_reports if detailed else [],
            "summary_by_type": summary_by_type,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    async def get_readiness_summary(
        self,
        flow_id: UUID,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Get high-level readiness summary for a flow (lightweight version).

        Returns counts only, no detailed reports.

        Args:
            flow_id: AssessmentFlow UUID
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID
            db: AsyncSession for database queries

        Returns:
            Dict with summary counts and readiness rate
        """
        # Delegate to analyze_flow_assets_readiness with detailed=False
        return await self.analyze_flow_assets_readiness(
            flow_id=flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            db=db,
            detailed=False,
        )

    async def filter_assets_by_readiness(
        self,
        flow_id: UUID,
        ready_only: bool,
        client_account_id: str,
        engagement_id: str,
        db: AsyncSession,
    ) -> List[UUID]:
        """
        Get list of asset IDs filtered by readiness status.

        Args:
            flow_id: AssessmentFlow UUID
            ready_only: If True, return only ready assets; if False, return not ready
            client_account_id: Tenant client account UUID
            engagement_id: Engagement UUID
            db: AsyncSession for database queries

        Returns:
            List of asset UUIDs matching readiness filter

        Raises:
            ValueError: If flow not found or not in tenant scope
        """
        # Query assessment flow with tenant scoping
        stmt = select(AssessmentFlow).where(
            AssessmentFlow.flow_id == flow_id,
            AssessmentFlow.client_account_id == UUID(client_account_id),
            AssessmentFlow.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise ValueError(
                f"Assessment flow {flow_id} not found or not in tenant scope "
                f"(client_account_id={client_account_id}, "
                f"engagement_id={engagement_id})"
            )

        # Get selected application IDs from flow
        selected_app_ids = flow.selected_application_ids or []

        if not selected_app_ids:
            return []

        # Query all assets linked to selected applications
        stmt = select(Asset).where(
            Asset.canonical_application_id.in_(
                [UUID(app_id) for app_id in selected_app_ids]
            ),
            Asset.client_account_id == UUID(client_account_id),
            Asset.engagement_id == UUID(engagement_id),
        )
        result = await db.execute(stmt)
        assets = result.scalars().all()

        # Filter by readiness status
        filtered_asset_ids = []

        for asset in assets:
            try:
                report = await self.analyze_asset_readiness(
                    asset_id=asset.id,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    db=db,
                )

                # Apply readiness filter
                if ready_only and report.is_ready_for_assessment:
                    filtered_asset_ids.append(asset.id)
                elif not ready_only and not report.is_ready_for_assessment:
                    filtered_asset_ids.append(asset.id)

            except Exception as e:
                logger.error(
                    f"Failed to analyze asset {asset.id} for filtering: {e}",
                    extra={"asset_id": str(asset.id), "flow_id": str(flow_id)},
                    exc_info=True,
                )

        logger.info(
            f"Filtered {len(filtered_asset_ids)} assets by readiness "
            f"(ready_only={ready_only}) for flow {flow_id}",
            extra={
                "flow_id": str(flow_id),
                "total_assets": len(assets),
                "filtered_count": len(filtered_asset_ids),
                "ready_only": ready_only,
            },
        )

        return filtered_asset_ids
