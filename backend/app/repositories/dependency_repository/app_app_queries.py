"""
Application-to-application dependency query methods.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from app.models.asset import Asset, AssetDependency, AssetType

logger = logging.getLogger(__name__)


class AppAppQueryMixin:
    """Mixin for application-to-application dependency queries."""

    async def get_app_app_dependencies(self) -> List[Dict[str, Any]]:
        """Get all application-to-application dependencies."""
        # Create aliases for the two Asset joins
        SourceAppAsset = aliased(Asset)
        TargetAppAsset = aliased(Asset)

        query = (
            select(  # SKIP_TENANT_CHECK - Tenant filtering via joined Asset tables
                AssetDependency,
                SourceAppAsset.name.label("source_app_name"),
                SourceAppAsset.asset_type.label("source_app_type"),
                SourceAppAsset.id.label("source_app_id"),
                SourceAppAsset.application_name.label("source_app_display_name"),
                func.json_build_object(
                    "name",
                    TargetAppAsset.name,
                    "type",
                    TargetAppAsset.asset_type,
                    "id",
                    TargetAppAsset.id,
                    "application_name",
                    TargetAppAsset.application_name,
                ).label("target_app_info"),
            )
            .select_from(AssetDependency)
            .join(
                SourceAppAsset,
                and_(
                    SourceAppAsset.id == AssetDependency.asset_id,
                    SourceAppAsset.asset_type == AssetType.APPLICATION,
                ),
            )
            .join(
                TargetAppAsset,
                and_(
                    TargetAppAsset.id == AssetDependency.depends_on_asset_id,
                    TargetAppAsset.asset_type == AssetType.APPLICATION,
                ),
            )
        )

        # Apply context filtering through the Asset tables
        if self.client_account_id:
            query = query.where(
                SourceAppAsset.client_account_id == self.client_account_id
            )
            query = query.where(
                TargetAppAsset.client_account_id == self.client_account_id
            )
        if self.engagement_id:
            query = query.where(SourceAppAsset.engagement_id == self.engagement_id)
            query = query.where(TargetAppAsset.engagement_id == self.engagement_id)

        result = await self.db.execute(query)
        rows = result.all()

        dependencies = []
        for row in rows:
            dep = {
                "dependency_id": str(row.AssetDependency.id),
                "source_app_id": str(row.source_app_id),
                "source_app_name": row.source_app_name,
                "target_app_info": row.target_app_info,
                "dependency_type": row.AssetDependency.dependency_type,
                "created_at": (
                    row.AssetDependency.created_at.isoformat()
                    if row.AssetDependency.created_at
                    else None
                ),
            }
            dependencies.append(dep)

        return dependencies

    async def get_available_applications(self) -> List[Dict[str, Any]]:
        """Get list of all applications."""
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(
            Asset.id, Asset.name, Asset.application_name, Asset.description
        ).where(Asset.asset_type == AssetType.APPLICATION)

        # Apply context filtering manually for Asset table
        if self.client_account_id:
            query = query.where(Asset.client_account_id == self.client_account_id)
        if self.engagement_id:
            query = query.where(Asset.engagement_id == self.engagement_id)
        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row.id),
                "name": row.name,
                "application_name": row.application_name,
                "description": row.description,
            }
            for row in rows
        ]

    async def create_app_app_dependency(
        self,
        source_app_id: str,
        target_app_id: str,
        dependency_type: str,
        description: Optional[str] = None,
    ) -> AssetDependency:
        """Create a new application-to-application dependency."""
        # Validate that both IDs are applications
        apps = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(Asset).where(
                and_(
                    Asset.id.in_([source_app_id, target_app_id]),
                    Asset.asset_type == AssetType.APPLICATION,
                )
            )
        )

        if len(list(apps.scalars())) != 2:
            raise ValueError("Invalid application IDs")

        # Check if dependency already exists
        existing = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(AssetDependency).where(
                and_(
                    AssetDependency.asset_id == source_app_id,
                    AssetDependency.depends_on_asset_id == target_app_id,
                )
            )
        )

        existing_dep = existing.scalar()
        if existing_dep:
            logger.info(
                f"Dependency already exists between {source_app_id} and {target_app_id}, returning existing"
            )
            return existing_dep

        return await self.create(
            asset_id=source_app_id,
            depends_on_asset_id=target_app_id,
            dependency_type=dependency_type,
            description=description,
        )
