"""
Application-to-server dependency query methods.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from app.models.asset import Asset, AssetDependency, AssetType

logger = logging.getLogger(__name__)


class AppServerQueryMixin:
    """Mixin for application-to-server dependency queries."""

    async def get_app_server_dependencies(self) -> List[Dict[str, Any]]:
        """Get all application-to-server dependencies."""
        # Create aliases for the two Asset joins
        AppAsset = aliased(Asset)
        ServerAsset = aliased(Asset)

        query = (
            select(  # SKIP_TENANT_CHECK - Tenant filtering via joined Asset tables
                AssetDependency,
                AppAsset.name.label("app_name"),
                AppAsset.asset_type.label("app_type"),
                AppAsset.id.label("app_id"),
                AppAsset.application_name.label("app_display_name"),
                func.json_build_object(
                    "name",
                    ServerAsset.name,
                    "type",
                    ServerAsset.asset_type,
                    "id",
                    ServerAsset.id,
                    "hostname",
                    ServerAsset.hostname,
                ).label("server_info"),
            )
            .select_from(AssetDependency)
            .join(
                AppAsset,
                and_(
                    AppAsset.id == AssetDependency.asset_id,
                    AppAsset.asset_type == AssetType.APPLICATION,
                ),
            )
            .join(
                ServerAsset,
                and_(
                    ServerAsset.id == AssetDependency.depends_on_asset_id,
                    ServerAsset.asset_type == AssetType.SERVER,
                ),
            )
        )

        # Apply context filtering through the Asset tables
        if self.client_account_id:
            query = query.where(AppAsset.client_account_id == self.client_account_id)
            query = query.where(ServerAsset.client_account_id == self.client_account_id)
        if self.engagement_id:
            query = query.where(AppAsset.engagement_id == self.engagement_id)
            query = query.where(ServerAsset.engagement_id == self.engagement_id)

        result = await self.db.execute(query)
        rows = result.all()

        dependencies = []
        for row in rows:
            dep = {
                "dependency_id": str(row.AssetDependency.id),
                "application_id": str(row.app_id),
                "application_name": row.app_name,
                "server_info": row.server_info,
                "dependency_type": row.AssetDependency.dependency_type,
                "created_at": (
                    row.AssetDependency.created_at.isoformat()
                    if row.AssetDependency.created_at
                    else None
                ),
            }
            dependencies.append(dep)

        return dependencies

    async def get_available_servers(self) -> List[Dict[str, Any]]:
        """Get list of all servers."""
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(Asset.id, Asset.name, Asset.hostname, Asset.description).where(
            Asset.asset_type == AssetType.SERVER
        )

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
                "hostname": row.hostname,
                "description": row.description,
            }
            for row in rows
        ]

    async def create_app_server_dependency(
        self,
        app_id: str,
        server_id: str,
        dependency_type: str,
        description: Optional[str] = None,
    ) -> AssetDependency:
        """Create a new application-to-server dependency."""
        # Validate that app_id is an application and server_id is a server
        app = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(Asset).where(
                and_(Asset.id == app_id, Asset.asset_type == AssetType.APPLICATION)
            )
        )
        server = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(Asset).where(
                and_(Asset.id == server_id, Asset.asset_type == AssetType.SERVER)
            )
        )

        if not app.scalar() or not server.scalar():
            raise ValueError("Invalid application or server ID")

        # Check if dependency already exists with context filtering
        existing_query = select(
            AssetDependency
        ).where(  # SKIP_TENANT_CHECK - Tenant filtering via joined Asset table
            and_(
                AssetDependency.asset_id == app_id,
                AssetDependency.depends_on_asset_id == server_id,
            )
        )

        # Apply context filtering through joined Asset tables
        existing_query = existing_query.join(
            Asset, Asset.id == AssetDependency.asset_id
        )
        if self.client_account_id:
            existing_query = existing_query.where(
                Asset.client_account_id == self.client_account_id
            )
        if self.engagement_id:
            existing_query = existing_query.where(
                Asset.engagement_id == self.engagement_id
            )

        existing = await self.db.execute(existing_query)

        # Apply context filtering through joined Asset tables
        existing_query = existing_query.join(
            Asset, Asset.id == AssetDependency.asset_id
        )
        if self.client_account_id:
            existing_query = existing_query.where(
                Asset.client_account_id == self.client_account_id
            )
        if self.engagement_id:
            existing_query = existing_query.where(
                Asset.engagement_id == self.engagement_id
            )

        existing = await self.db.execute(existing_query)

        existing_dep = existing.scalar()
        if existing_dep:
            logger.info(
                f"Dependency already exists between {app_id} and {server_id}, returning existing"
            )
            return existing_dep

        return await self.create(
            asset_id=app_id,
            depends_on_asset_id=server_id,
            dependency_type=dependency_type,
            description=description,
        )
