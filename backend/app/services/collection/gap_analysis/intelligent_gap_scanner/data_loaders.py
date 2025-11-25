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

        Note:
            Enrichment tables do NOT have client_account_id/engagement_id columns.
            Tenant isolation is inherited through asset_id foreign key relationship.
            Asset passed to scan_gaps() is already tenant-validated.
        """
        enrichment = {}

        # Tech Debt - Query by asset_id only (tenant context via FK relationship)
        stmt_tech = select(AssetTechDebt).where(
            AssetTechDebt.asset_id == asset_id
        )
        result_tech = await self.db.execute(stmt_tech)
        tech_debt = result_tech.scalar_one_or_none()
        if tech_debt:
            # Map to actual model fields (fixed field name mismatches)
            enrichment["tech_debt_score"] = tech_debt.tech_debt_score
            enrichment["modernization_priority"] = tech_debt.modernization_priority
            enrichment["code_quality_score"] = tech_debt.code_quality_score
            enrichment["debt_items"] = tech_debt.debt_items

        # Performance Metrics - Query by asset_id only
        stmt_perf = select(AssetPerformanceMetrics).where(
            AssetPerformanceMetrics.asset_id == asset_id
        )
        result_perf = await self.db.execute(stmt_perf)
        performance = result_perf.scalar_one_or_none()
        if performance:
            # Map to actual model fields (fixed field name mismatches)
            enrichment["cpu_utilization_avg"] = performance.cpu_utilization_avg
            enrichment["cpu_utilization_peak"] = performance.cpu_utilization_peak
            enrichment["memory_utilization_avg"] = performance.memory_utilization_avg
            enrichment["memory_utilization_peak"] = performance.memory_utilization_peak
            enrichment["disk_iops_avg"] = performance.disk_iops_avg
            enrichment["network_throughput_mbps"] = performance.network_throughput_mbps

        # Cost Optimization - Query by asset_id only
        stmt_cost = select(AssetCostOptimization).where(
            AssetCostOptimization.asset_id == asset_id
        )
        result_cost = await self.db.execute(stmt_cost)
        cost = result_cost.scalar_one_or_none()
        if cost:
            # Map to actual model fields (fixed field name mismatches)
            enrichment["monthly_cost_usd"] = cost.monthly_cost_usd
            enrichment["annual_cost_usd"] = cost.annual_cost_usd
            enrichment["optimization_potential_pct"] = cost.optimization_potential_pct
            enrichment["optimization_opportunities"] = cost.optimization_opportunities

        return enrichment

    async def load_canonical_applications(
        self, asset_id: UUID
    ) -> List[CanonicalApplication]:
        """
        Load canonical applications associated with asset.

        Returns:
            List of CanonicalApplication objects linked via junction table
        """
        from app.models.canonical_applications.collection_flow_app import (
            CollectionFlowApplication,
        )

        # Query via junction table explicitly (Asset doesn't have canonical_applications relationship)
        stmt = (
            select(CanonicalApplication)
            .join(
                CollectionFlowApplication,
                CollectionFlowApplication.canonical_application_id == CanonicalApplication.id,
            )
            .where(
                CollectionFlowApplication.asset_id == asset_id,
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
        # ✅ FIX Bug #3 (AssetDependency AttributeError):
        # Correct column names: asset_id (source), depends_on_asset_id (target)
        # NOT source_asset_id/target_asset_id
        stmt = (
            select(Asset)
            .join(AssetDependency, Asset.id == AssetDependency.depends_on_asset_id)
            .where(
                AssetDependency.asset_id == asset_id,
                AssetDependency.client_account_id == self.client_account_id,
                AssetDependency.engagement_id == self.engagement_id,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
