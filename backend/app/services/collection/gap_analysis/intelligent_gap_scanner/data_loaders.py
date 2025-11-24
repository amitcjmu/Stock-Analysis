"""
Data loaders for IntelligentGapScanner - Load data from 6 sources.

Extracts data loading methods (async database queries) from main scanner
to keep main scanner class under 400 lines.

CC Generated for Issue #1111 - IntelligentGapScanner Modularization
Per ADR-037: Intelligent Gap Detection and Questionnaire Generation Architecture
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset, CanonicalApplication, AssetDependency
from app.models.asset_enrichments import (
    AssetTechDebt,
    AssetPerformanceMetrics,
    AssetCostOptimization,
)

logger = logging.getLogger(__name__)


class DataLoaders:
    """Data loading methods for IntelligentGapScanner (6 sources)."""

    def __init__(self, db: AsyncSession, client_account_id: int, engagement_id: int):
        """Initialize data loaders with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def load_enrichment_data(self, asset_id: UUID) -> Dict[str, Optional[Any]]:
        """
        Load enrichment data from 3 enrichment tables.

        Returns:
            Dict with fields from tech_debt, performance_metrics, cost_optimization
        """
        enrichment = {}

        # Tech Debt
        stmt_tech = select(AssetTechDebt).where(
            AssetTechDebt.asset_id == asset_id,
            AssetTechDebt.client_account_id == self.client_account_id,
            AssetTechDebt.engagement_id == self.engagement_id,
        )
        result_tech = await self.db.execute(stmt_tech)
        tech_debt = result_tech.scalar_one_or_none()
        if tech_debt:
            enrichment["resilience_tier"] = tech_debt.resilience_tier
            enrichment["code_quality_score"] = tech_debt.code_quality_score

        # Performance Metrics
        stmt_perf = select(AssetPerformanceMetrics).where(
            AssetPerformanceMetrics.asset_id == asset_id,
            AssetPerformanceMetrics.client_account_id == self.client_account_id,
            AssetPerformanceMetrics.engagement_id == self.engagement_id,
        )
        result_perf = await self.db.execute(stmt_perf)
        performance = result_perf.scalar_one_or_none()
        if performance:
            enrichment["avg_response_time_ms"] = performance.avg_response_time_ms
            enrichment["peak_cpu_percent"] = performance.peak_cpu_percent

        # Cost Optimization
        stmt_cost = select(AssetCostOptimization).where(
            AssetCostOptimization.asset_id == asset_id,
            AssetCostOptimization.client_account_id == self.client_account_id,
            AssetCostOptimization.engagement_id == self.engagement_id,
        )
        result_cost = await self.db.execute(stmt_cost)
        cost = result_cost.scalar_one_or_none()
        if cost:
            enrichment["estimated_monthly_cost"] = cost.estimated_monthly_cost
            enrichment["rightsizing_recommendation"] = cost.rightsizing_recommendation

        return enrichment

    async def load_canonical_applications(
        self, asset_id: UUID
    ) -> List[CanonicalApplication]:
        """
        Load canonical applications associated with asset.

        Returns:
            List of CanonicalApplication objects linked via junction table
        """
        stmt = (
            select(CanonicalApplication)
            .join(
                Asset.canonical_applications
            )  # Uses collection_flow_applications junction
            .where(
                Asset.id == asset_id,
                Asset.client_account_id == self.client_account_id,
                Asset.engagement_id == self.engagement_id,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def load_related_assets(self, asset_id: UUID) -> List[Asset]:
        """
        Load related assets via asset_dependencies.

        Returns:
            List of Asset objects connected via dependencies (source or target)
        """
        stmt = (
            select(Asset)
            .join(AssetDependency, Asset.id == AssetDependency.target_asset_id)
            .where(
                AssetDependency.source_asset_id == asset_id,
                AssetDependency.client_account_id == self.client_account_id,
                AssetDependency.engagement_id == self.engagement_id,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
