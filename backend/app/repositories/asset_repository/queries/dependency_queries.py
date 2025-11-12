"""
Asset dependency query operations.

Handles read-only operations for asset dependencies.
"""

from typing import List

from sqlalchemy.future import select

from app.models.asset import AssetDependency
from app.repositories.asset_repository.queries.base import BaseAssetDependencyQueries


class AssetDependencyQueries(BaseAssetDependencyQueries):
    """Query operations for asset dependencies."""

    async def get_dependencies_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the source."""
        query = select(
            AssetDependency
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
            AssetDependency.source_asset_id == asset_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_dependents_for_asset(self, asset_id: int) -> List[AssetDependency]:
        """Get all dependencies where the asset is the target."""
        query = select(
            AssetDependency
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
            AssetDependency.target_asset_id == asset_id
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_dependency_type(
        self, dependency_type: str
    ) -> List[AssetDependency]:
        """Get dependencies by type."""
        query = select(
            AssetDependency
        ).where(  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
            AssetDependency.dependency_type == dependency_type
        )
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_critical_dependencies(self) -> List[AssetDependency]:
        """Get dependencies marked as critical."""
        query = select(AssetDependency).where(
            AssetDependency.criticality == "critical"
        )  # SKIP_TENANT_CHECK: _apply_context_filter() adds tenant scoping
        query = self._apply_context_filter(query)
        result = await self.db.execute(query)
        return result.scalars().all()
