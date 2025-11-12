"""
Asset Repository Query Operations

Handles all read-only operations for assets, including:
- Basic queries by attribute (hostname, type, environment, etc.)
- Search and filtering operations
- Analytics and aggregation queries
- Master flow and phase progression queries
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.asset import Asset, AssetDependency, WorkflowProgress

logger = logging.getLogger(__name__)


class AssetQueries:
    """Query operations for assets."""

    def __init__(self, db: AsyncSession, client_account_id: Optional[str] = None, engagement_id: Optional[str] = None, include_deleted: bool = False):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.include_deleted = include_deleted

    def _apply_context_filter(self, query):
        """Apply tenant scoping and soft delete filtering to a query."""
        # Tenant scoping
        if self.client_account_id:
            query = query.where(Asset.client_account_id == self.client_account_id)
        if self.engagement_id:
            query = query.where(Asset.engagement_id == self.engagement_id)

        # Soft delete filter
        if not self.include_deleted:
            query = query.where(Asset.deleted_at.is_(None))

        return query

    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Get asset by hostname with context filtering."""
        query = select(Asset).where(Asset.hostname == hostname)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_asset_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type with context filtering."""
        query = select(Asset).where(Asset.asset_type == asset_type)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_environment(self, environment: str) -> List[Asset]:
        """Get assets by environment with context filtering."""
        query = select(Asset).where(Asset.environment == environment)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_status(self, status: str) -> List[Asset]:
        """Get assets by migration status with context filtering."""
        query = select(Asset).where(Asset.status == status)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_6r_strategy(self, strategy: str) -> List[Asset]:
        """Get assets by 6R strategy with context filtering."""
        query = select(Asset).where(Asset.six_r_strategy == strategy)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_workflow_status(self, phase: str, status: str) -> List[Asset]:
        """Get assets by workflow phase status."""
        field_name = f"{phase}_status"
        if not hasattr(Asset, field_name):
            return []

        query = select(Asset).where(getattr(Asset, field_name) == status)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assessment_ready_assets(self) -> List[Asset]:
        """Get assets that are ready for assessment phase."""
        query = select(Asset).where(Asset.assessment_readiness == "ready")
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_by_import_batch(self, batch_id: str) -> List[Asset]:
        """Get assets from a specific import batch."""
        query = select(Asset).where(Asset.import_batch_id == batch_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_assets(self, search_term: str) -> List[Asset]:
        """Search assets by name, hostname, or description."""
        query = select(Asset).where(
            or_(
                Asset.name.ilike(f"%{search_term}%"),
                Asset.hostname.ilike(f"%{search_term}%"),
                Asset.description.ilike(f"%{search_term}%"),
                Asset.asset_name.ilike(f"%{search_term}%"),
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_with_dependencies(self) -> List[Asset]:
        """Get assets that have dependencies."""
        query = select(Asset).where(
            or_(
                Asset.dependencies.isnot(None),
                Asset.dependents.isnot(None),
                Asset.server_dependencies.isnot(None),
                Asset.application_dependencies.isnot(None),
                Asset.database_dependencies.isnot(None),
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_by_criticality(self, criticality: str) -> List[Asset]:
        """Get assets by business criticality."""
        query = select(Asset).where(Asset.business_criticality == criticality)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_by_department(self, department: str) -> List[Asset]:
        """Get assets by department."""
        query = select(Asset).where(Asset.department == department)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_needing_analysis(self) -> List[Asset]:
        """Get assets that need AI analysis."""
        query = select(Asset).where(
            or_(
                Asset.last_ai_analysis.is_(None),
                Asset.ai_confidence_score < 0.7,
                Asset.recommended_6r_strategy.is_(None),
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_master_flow(self, master_flow_id: str) -> List[Asset]:
        """Get assets by master flow ID with context filtering."""
        query = select(Asset).where(Asset.master_flow_id == master_flow_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_discovery_flow(self, discovery_flow_id: str) -> List[Asset]:
        """Get assets by discovery flow ID with context filtering."""
        query = select(Asset).where(Asset.discovery_flow_id == discovery_flow_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_source_phase(self, source_phase: str) -> List[Asset]:
        """Get assets by source phase with context filtering."""
        query = select(Asset).where(Asset.source_phase == source_phase)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_current_phase(self, current_phase: str) -> List[Asset]:
        """Get assets by current phase with context filtering."""
        query = select(Asset).where(Asset.current_phase == current_phase)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_multi_phase_assets(self) -> List[Asset]:
        """Get assets that have progressed through multiple phases."""
        query = select(Asset).where(
            and_(
                Asset.source_phase.isnot(None),
                Asset.current_phase.isnot(None),
                Asset.source_phase != Asset.current_phase,
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_data_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        query = select(
            func.avg(Asset.completeness_score).label("avg_completeness"),
            func.avg(Asset.quality_score).label("avg_quality"),
            func.count(Asset.id).label("total_assets"),
            func.count(Asset.missing_critical_fields).label("assets_with_missing_fields"),
        )
        query = self._apply_context_filter(query)

        result = await self.db.execute(query)
        row = result.first()

        return {
            "average_completeness": float(row.avg_completeness or 0),
            "average_quality": float(row.avg_quality or 0),
            "total_assets": row.total_assets,
            "assets_with_missing_fields": row.assets_with_missing_fields,
        }

    async def get_workflow_summary(self) -> Dict[str, Dict[str, int]]:
        """Get workflow progress summary across all phases."""
        phases = ["discovery", "mapping", "cleanup", "assessment"]
        statuses = ["pending", "in_progress", "completed", "failed"]

        summary = {}
        for phase in phases:
            summary[phase] = {}
            for status in statuses:
                field_name = f"{phase}_status"
                if not hasattr(Asset, field_name):
                    summary[phase][status] = 0
                    continue

                query = select(func.count(Asset.id)).where(
                    getattr(Asset, field_name) == status
                )
                query = self._apply_context_filter(query)
                result = await self.db.execute(query)
                count = result.scalar() or 0
                summary[phase][status] = count

        return summary

    async def get_master_flow_summary(self, master_flow_id: str) -> Dict[str, Any]:
        """Get comprehensive summary for a master flow."""
        assets = await self.get_by_master_flow(master_flow_id)

        summary = {
            "master_flow_id": master_flow_id,
            "total_assets": len(assets),
            "phases": {},
            "asset_types": {},
            "strategies": {},
            "status_distribution": {},
        }

        for asset in assets:
            phase = asset.current_phase or "unknown"
            summary["phases"][phase] = summary["phases"].get(phase, 0) + 1

            asset_type = asset.asset_type or "unknown"
            summary["asset_types"][asset_type] = (
                summary["asset_types"].get(asset_type, 0) + 1
            )

            strategy = asset.six_r_strategy or "unknown"
            summary["strategies"][strategy] = summary["strategies"].get(strategy, 0) + 1

            status = asset.status or "unknown"
            summary["status_distribution"][status] = (
                summary["status_distribution"].get(status, 0) + 1
            )

        return summary

    async def get_cross_phase_analytics(self) -> Dict[str, Any]:
        """Get analytics across all phases and master flows."""
        query = select(
            Asset.master_flow_id,
            Asset.source_phase,
            Asset.current_phase,
            func.count(Asset.id).label("asset_count"),
            func.avg(Asset.quality_score).label("avg_quality"),
            func.avg(Asset.completeness_score).label("avg_completeness"),
        ).group_by(Asset.master_flow_id, Asset.source_phase, Asset.current_phase)

        query = self._apply_context_filter(query)
        result = await self.db.execute(query)

        analytics = {
            "master_flows": {},
            "phase_transitions": {},
            "quality_by_phase": {},
        }

        for row in result:
            if row.master_flow_id not in analytics["master_flows"]:
                analytics["master_flows"][row.master_flow_id] = {
                    "total_assets": 0,
                    "phases": {},
                }

            analytics["master_flows"][row.master_flow_id]["total_assets"] += (
                row.asset_count
            )
            analytics["master_flows"][row.master_flow_id]["phases"][
                row.current_phase
            ] = row.asset_count

            transition = f"{row.source_phase} → {row.current_phase}"
            analytics["phase_transitions"][transition] = (
                analytics["phase_transitions"].get(transition, 0) + row.asset_count
            )

            if row.current_phase not in analytics["quality_by_phase"]:
                analytics["quality_by_phase"][row.current_phase] = {
                    "avg_quality": 0,
                    "avg_completeness": 0,
                    "asset_count": 0,
                }

            analytics["quality_by_phase"][row.current_phase]["avg_quality"] = float(
                row.avg_quality or 0
            )
            analytics["quality_by_phase"][row.current_phase]["avg_completeness"] = (
                float(row.avg_completeness or 0)
            )
            analytics["quality_by_phase"][row.current_phase]["asset_count"] += (
                row.asset_count
            )

        return analytics


class AssetDependencyQueries:
    """Query operations for asset dependencies."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    def _apply_context_filter(self, query):
        """Apply tenant scoping to a query."""
        if self.client_account_id:
            query = query.where(
                AssetDependency.client_account_id == self.client_account_id
            )
        if self.engagement_id:
            query = query.where(AssetDependency.engagement_id == self.engagement_id)

        return query

    async def get_dependencies_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the source."""
        query = select(AssetDependency).where(AssetDependency.source_asset_id == asset_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_dependents_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the target."""
        query = select(AssetDependency).where(AssetDependency.target_asset_id == asset_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_dependency_type(self, dependency_type: str) -> List[AssetDependency]:
        """Get dependencies by type."""
        query = select(AssetDependency).where(
            AssetDependency.dependency_type == dependency_type
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_critical_dependencies(self) -> List[AssetDependency]:
        """Get dependencies marked as critical."""
        query = select(AssetDependency).where(AssetDependency.criticality == "critical")
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()


class WorkflowProgressQueries:
    """Query operations for workflow progress."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """Initialize with database session and tenant context."""
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    def _apply_context_filter(self, query):
        """Apply tenant scoping to a query."""
        if self.client_account_id:
            query = query.where(
                WorkflowProgress.client_account_id == self.client_account_id
            )
        if self.engagement_id:
            query = query.where(WorkflowProgress.engagement_id == self.engagement_id)

        return query

    async def get_progress_for_asset(self, asset_id: int) -> List[WorkflowProgress]:
        """Get all workflow progress records for an asset."""
        query = select(WorkflowProgress).where(WorkflowProgress.asset_id == asset_id)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_progress_by_phase(self, phase: str) -> List[WorkflowProgress]:
        """Get workflow progress for a specific phase."""
        query = select(WorkflowProgress).where(WorkflowProgress.phase == phase)
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_active_workflows(self) -> List[WorkflowProgress]:
        """Get workflows that are currently in progress."""
        query = select(WorkflowProgress).where(WorkflowProgress.status == "in_progress")
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
