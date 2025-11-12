"""
Asset query operations.

Handles read-only operations for assets, including:
- Basic queries by attribute (hostname, type, environment, etc.)
- Search and filtering operations
- Master flow and phase progression queries
"""

from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.future import select

from app.models.asset import Asset
from app.repositories.asset_repository.queries.base import BaseAssetQueries


class AssetQueries(BaseAssetQueries):
    """Query operations for assets."""

    async def get_by_hostname(self, hostname: str) -> Optional[Asset]:
        """Get asset by hostname with context filtering."""
        query = select(Asset).where(
            Asset.hostname == hostname
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_asset_type(self, asset_type: str) -> List[Asset]:
        """Get assets by type with context filtering."""
        query = select(Asset).where(
            Asset.asset_type == asset_type
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_environment(self, environment: str) -> List[Asset]:
        """Get assets by environment with context filtering."""
        query = select(Asset).where(
            Asset.environment == environment
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_status(self, status: str) -> List[Asset]:
        """Get assets by migration status with context filtering."""
        query = select(Asset).where(
            Asset.status == status
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_6r_strategy(self, strategy: str) -> List[Asset]:
        """Get assets by 6R strategy with context filtering."""
        query = select(Asset).where(
            Asset.six_r_strategy == strategy
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_workflow_status(self, phase: str, status: str) -> List[Asset]:
        """Get assets by workflow phase status."""
        field_name = f"{phase}_status"
        if not hasattr(Asset, field_name):
            return []

        query = select(Asset).where(
            getattr(Asset, field_name) == status
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assessment_ready_assets(self) -> List[Asset]:
        """Get assets that are ready for assessment phase."""
        query = select(Asset).where(
            Asset.assessment_readiness == "ready"
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_by_import_batch(self, batch_id: str) -> List[Asset]:
        """Get assets from a specific import batch."""
        query = select(Asset).where(
            Asset.import_batch_id == batch_id
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def search_assets(self, search_term: str) -> List[Asset]:
        """Search assets by name, hostname, or description."""
        query = select(
            Asset
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
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
        query = select(
            Asset
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
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
        query = select(Asset).where(
            Asset.business_criticality == criticality
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_by_department(self, department: str) -> List[Asset]:
        """Get assets by department."""
        query = select(Asset).where(
            Asset.department == department
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_assets_needing_analysis(self) -> List[Asset]:
        """Get assets that need AI analysis."""
        query = select(
            Asset
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
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
        query = select(Asset).where(
            Asset.master_flow_id == master_flow_id
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_discovery_flow(self, discovery_flow_id: str) -> List[Asset]:
        """Get assets by discovery flow ID with context filtering."""
        query = select(Asset).where(
            Asset.discovery_flow_id == discovery_flow_id
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_source_phase(self, source_phase: str) -> List[Asset]:
        """Get assets by source phase with context filtering."""
        query = select(Asset).where(
            Asset.source_phase == source_phase
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_current_phase(self, current_phase: str) -> List[Asset]:
        """Get assets by current phase with context filtering."""
        query = select(Asset).where(
            Asset.current_phase == current_phase
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_multi_phase_assets(self) -> List[Asset]:
        """Get assets that have progressed through multiple phases."""
        query = select(
            Asset
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
            and_(
                Asset.source_phase.isnot(None),
                Asset.current_phase.isnot(None),
                Asset.source_phase != Asset.current_phase,
            )
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
