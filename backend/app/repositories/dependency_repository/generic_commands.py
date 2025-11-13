"""
Generic dependency creation command methods.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, delete
from sqlalchemy.future import select

from app.core.security.secure_logging import safe_log_format
from app.models.asset import Asset, AssetDependency

logger = logging.getLogger(__name__)


class GenericCommandMixin:
    """Mixin for generic dependency creation operations."""

    async def bulk_create_dependencies(
        self,
        source_asset_id: str,
        target_asset_ids: list[str],
        dependency_type: str,
        confidence_score: float = 1.0,
        description: Optional[str] = None,
    ) -> list[AssetDependency]:
        """
        Efficiently create multiple dependencies for a source asset in a single operation.

        Validates all asset IDs upfront and creates dependencies atomically.
        Prevents N+1 query problem when creating multiple dependencies.

        Args:
            source_asset_id: ID of the source asset
            target_asset_ids: List of target asset IDs
            dependency_type: Type of dependency (e.g., 'manual', 'auto-detected')
            confidence_score: Confidence score (0.0-1.0), default 1.0 for manual
            description: Optional description for all dependencies

        Returns:
            List of created AssetDependency objects
        """
        if not target_asset_ids:
            return []

        # Validate all asset IDs exist in a single query
        all_ids = [UUID(source_asset_id)] + [UUID(tid) for tid in target_asset_ids]
        stmt = select(Asset).where(Asset.id.in_(all_ids))
        result = await self.db.execute(stmt)
        found_assets = {str(asset.id): asset for asset in result.scalars().all()}

        # Validate source asset exists
        if source_asset_id not in found_assets:
            raise ValueError(f"Source asset not found: {source_asset_id}")

        source_asset = found_assets[source_asset_id]

        # Validate all target assets exist
        missing_target_ids = set(target_asset_ids) - set(found_assets.keys())
        if missing_target_ids:
            raise ValueError(
                f"Invalid target asset IDs: {', '.join(missing_target_ids)}"
            )

        # Check for existing dependencies to avoid duplicates
        existing_stmt = select(AssetDependency).where(
            and_(
                AssetDependency.asset_id == UUID(source_asset_id),
                AssetDependency.depends_on_asset_id.in_(
                    [UUID(tid) for tid in target_asset_ids]
                ),
            )
        )
        existing_result = await self.db.execute(existing_stmt)
        existing_deps = {
            str(dep.depends_on_asset_id): dep for dep in existing_result.scalars().all()
        }

        created_dependencies = []

        # Create or update dependencies
        for target_id in target_asset_ids:
            if target_id in existing_deps:
                # Update existing dependency
                existing_dep = existing_deps[target_id]
                existing_dep.confidence_score = confidence_score
                if description:
                    existing_dep.description = description
                created_dependencies.append(existing_dep)
                logger.info(
                    f"Updated existing dependency: {source_asset_id} -> {target_id}"
                )
            else:
                # Create new dependency
                dep = AssetDependency(
                    client_account_id=source_asset.client_account_id,
                    engagement_id=source_asset.engagement_id,
                    asset_id=UUID(source_asset_id),
                    depends_on_asset_id=UUID(target_id),
                    dependency_type=dependency_type,
                    confidence_score=confidence_score,
                    description=description,
                )
                self.db.add(dep)
                created_dependencies.append(dep)

        await self.db.flush()
        logger.info(
            f"Bulk created/updated {len(created_dependencies)} dependencies "
            f"for source asset {source_asset_id}"
        )

        return created_dependencies

    async def create_dependency(
        self,
        source_asset_id: str,
        target_asset_id: str,
        dependency_type: str,
        confidence_score: float = 1.0,
        description: Optional[str] = None,
    ) -> AssetDependency:
        """
        Create a generic dependency between two assets.

        Per Issue #910: Supports confidence_score to distinguish between manual and auto-detected dependencies.
        - confidence_score = 1.0: Manual/user-created dependencies
        - confidence_score < 1.0: Auto-detected dependencies

        Args:
            source_asset_id: ID of the asset that depends on another
            target_asset_id: ID of the asset being depended upon
            dependency_type: Type of dependency (e.g., 'hosting', 'infrastructure', 'server')
            confidence_score: Confidence score (0.0-1.0), default 1.0 for manual
            description: Optional description of the dependency

        Returns:
            Created AssetDependency object
        """
        # Validate both assets exist
        assets = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(Asset).where(Asset.id.in_([source_asset_id, target_asset_id]))
        )

        found_assets = list(assets.scalars())
        if len(found_assets) != 2:
            raise ValueError(f"Invalid asset IDs: {source_asset_id}, {target_asset_id}")

        # Check if dependency already exists
        existing = await self.db.execute(
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(AssetDependency).where(
                and_(
                    AssetDependency.asset_id == source_asset_id,
                    AssetDependency.depends_on_asset_id == target_asset_id,
                )
            )
        )

        existing_dep = existing.scalar()
        if existing_dep:
            logger.info(
                f"Dependency already exists between {source_asset_id} and {target_asset_id}, updating confidence_score"
            )
            # Update existing dependency's confidence_score if provided
            existing_dep.confidence_score = confidence_score
            if description:
                existing_dep.description = description
            await self.db.flush()
            return existing_dep

        # Get client_account_id and engagement_id from the source asset
        source_asset = next(
            (a for a in found_assets if str(a.id) == source_asset_id), None
        )
        if not source_asset:
            raise ValueError(f"Source asset not found: {source_asset_id}")

        # Create new dependency with multi-tenant context
        return await self.create(
            client_account_id=source_asset.client_account_id,
            engagement_id=source_asset.engagement_id,
            asset_id=source_asset_id,
            depends_on_asset_id=target_asset_id,
            dependency_type=dependency_type,
            confidence_score=confidence_score,
            description=description,
        )

    async def delete_dependencies_for_application(
        self,
        application_id: str,
    ) -> int:
        """
        Delete all dependencies for a specific application (source asset).

        Used to clear existing dependencies before creating new ones,
        preventing duplicates when updating dependencies via the UI.

        SECURITY: Multi-tenant isolation enforced via client_account_id and engagement_id.

        Args:
            application_id: ID of the application whose dependencies should be deleted

        Returns:
            Number of dependencies deleted
        """
        # Convert to UUID if string
        app_uuid = (
            UUID(application_id) if isinstance(application_id, str) else application_id
        )

        # Convert tenant IDs to UUID
        client_uuid = UUID(self.client_account_id)
        engagement_uuid = UUID(self.engagement_id)

        # Delete all dependencies where this application is the source
        # WITH multi-tenant isolation to prevent cross-tenant deletion
        stmt = delete(AssetDependency).where(
            and_(
                AssetDependency.asset_id == app_uuid,
                AssetDependency.client_account_id == client_uuid,
                AssetDependency.engagement_id == engagement_uuid,
            )
        )

        result = await self.db.execute(stmt)
        deleted_count = result.rowcount

        logger.info(
            safe_log_format(
                "Deleted dependencies for application: app_id={app_id}, "
                "client_id={client_id}, engagement_id={engagement_id}",
                app_id=application_id,
                client_id=self.client_account_id,
                engagement_id=self.engagement_id,
            )
        )

        return deleted_count
