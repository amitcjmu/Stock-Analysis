"""
Assessment Flow-specific dependency query methods.
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.future import select
from sqlalchemy.orm import aliased

from app.models.asset import Asset, AssetDependency, AssetType

logger = logging.getLogger(__name__)


class FlowQueryMixin:
    """Mixin for Assessment Flow-specific dependency queries."""

    async def get_app_server_dependencies_for_flow(
        self, engagement_id: str, application_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Get application-to-server dependencies filtered by application IDs.

        Used by Assessment Flow to retrieve dependencies for only selected applications.

        Args:
            engagement_id: Engagement UUID for filtering
            application_ids: List of application UUIDs to filter by

        Returns:
            List of dependency dicts with application and server metadata
        """
        if not application_ids:
            return []

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
            .where(AppAsset.id.in_(application_ids))  # Filter by selected apps
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

    async def get_app_app_dependencies_for_flow(
        self, engagement_id: str, application_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Get application-to-application dependencies filtered by application IDs.

        Used by Assessment Flow to retrieve dependencies for only selected applications.

        Args:
            engagement_id: Engagement UUID for filtering
            application_ids: List of application UUIDs to filter by

        Returns:
            List of dependency dicts with source and target application metadata
        """
        if not application_ids:
            return []

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
            .where(SourceAppAsset.id.in_(application_ids))  # Filter by selected apps
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

    async def get_all_dependencies_for_flow(
        self, engagement_id: str, application_ids: List[UUID]
    ) -> List[Dict[str, Any]]:
        """
        Get ALL dependencies for selected applications regardless of target asset type.

        This method returns dependencies to servers, databases, networks, and other asset types.
        Used by Assessment Flow dependency analysis to display complete dependency graph.

        Args:
            engagement_id: Engagement UUID for filtering
            application_ids: List of application UUIDs to filter by

        Returns:
            List of dependency dicts with source application and target asset metadata
        """
        if not application_ids:
            return []

        # Create aliases for the two Asset joins
        SourceAppAsset = aliased(Asset)
        TargetAsset = aliased(Asset)

        query = (
            select(  # SKIP_TENANT_CHECK - Tenant filtering via joined Asset tables
                AssetDependency,
                SourceAppAsset.name.label("source_app_name"),
                SourceAppAsset.asset_type.label("source_app_type"),
                SourceAppAsset.id.label("source_app_id"),
                SourceAppAsset.application_name.label("source_app_display_name"),
                func.json_build_object(
                    "name",
                    TargetAsset.name,
                    "type",
                    TargetAsset.asset_type,
                    "id",
                    TargetAsset.id,
                    "hostname",
                    TargetAsset.hostname,
                    "application_name",
                    TargetAsset.application_name,
                ).label("target_info"),
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
                TargetAsset,
                TargetAsset.id == AssetDependency.depends_on_asset_id,
                # NOTE: No asset_type filter - accepts ALL types (server, database, network, etc.)
            )
            .where(SourceAppAsset.id.in_(application_ids))  # Filter by selected apps
        )

        # Apply context filtering through the Asset tables
        if self.client_account_id:
            query = query.where(
                SourceAppAsset.client_account_id == self.client_account_id
            )
            query = query.where(TargetAsset.client_account_id == self.client_account_id)
        if self.engagement_id:
            query = query.where(SourceAppAsset.engagement_id == self.engagement_id)
            query = query.where(TargetAsset.engagement_id == self.engagement_id)

        result = await self.db.execute(query)
        rows = result.all()

        dependencies = []
        for row in rows:
            dep = {
                "dependency_id": str(row.AssetDependency.id),
                "source_app_id": str(row.source_app_id),
                "source_app_name": row.source_app_name,
                "target_info": row.target_info,
                "dependency_type": row.AssetDependency.dependency_type,
                "created_at": (
                    row.AssetDependency.created_at.isoformat()
                    if row.AssetDependency.created_at
                    else None
                ),
            }
            dependencies.append(dep)

        return dependencies
