"""
Asset Soft Delete Service (Issue #912)

Handles soft delete, restore, and trash view operations for assets.
Maintains audit trail and supports bulk operations.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset_schemas import (
    AssetSoftDeleteResponse,
    AssetRestoreResponse,
    BulkSoftDeleteResponse,
    TrashAssetResponse,
    PaginatedTrashResponse,
)

logger = logging.getLogger(__name__)


class AssetSoftDeleteService:
    """
    Service for soft delete and restore operations on assets.

    Follows 7-layer architecture pattern:
    - Soft deletes assets (marks deleted_at timestamp)
    - Restores soft deleted assets
    - Provides trash view functionality
    - Ensures tenant scoping and audit trail
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        """
        Initialize the asset soft delete service.

        Args:
            db: Database session
            client_account_id: Client account ID for tenant scoping
            engagement_id: Engagement ID for tenant scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.repository = AssetRepository(
            db=db,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

    async def soft_delete(
        self,
        asset_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> AssetSoftDeleteResponse:
        """
        Soft delete an asset by setting deleted_at timestamp.

        Args:
            asset_id: Asset ID to soft delete
            deleted_by: User ID performing the deletion

        Returns:
            Response with deletion metadata

        Raises:
            ValueError: If asset not found, not accessible, or already deleted
        """
        # Get asset with tenant scoping
        asset = await self.repository.get_by_id(asset_id)
        if not asset:
            raise ValueError(
                f"Asset {asset_id} not found or not accessible in this account/engagement"
            )

        # Check if already deleted
        if asset.deleted_at is not None:
            raise ValueError(f"Asset {asset_id} is already deleted")

        # Soft delete the asset
        deleted_at = datetime.utcnow()
        await self.repository.update(
            asset_id,
            deleted_at=deleted_at,
            deleted_by=deleted_by,
            updated_at=deleted_at,
        )

        logger.info(
            f"Soft deleted asset {asset_id} by user {deleted_by} "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return AssetSoftDeleteResponse(
            asset_id=asset_id,
            deleted_at=deleted_at,
            deleted_by=deleted_by,
        )

    async def restore(
        self,
        asset_id: UUID,
    ) -> AssetRestoreResponse:
        """
        Restore a soft deleted asset by clearing deleted_at timestamp.

        Args:
            asset_id: Asset ID to restore

        Returns:
            Response with restore metadata

        Raises:
            ValueError: If asset not found, not accessible, or not deleted
        """
        # Get asset WITHOUT filtering deleted (need to find deleted assets)
        query = select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.client_account_id == UUID(self.client_account_id),
                Asset.engagement_id == UUID(self.engagement_id),
            )
        )
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            raise ValueError(
                f"Asset {asset_id} not found or not accessible in this account/engagement"
            )

        # Check if not deleted
        if asset.deleted_at is None:
            raise ValueError(f"Asset {asset_id} is not deleted, cannot restore")

        # Restore the asset using repository with include_deleted=True
        # to properly find and update the deleted asset
        restore_repository = AssetRepository(
            db=self.db,
            client_account_id=self.client_account_id,
            engagement_id=self.engagement_id,
            include_deleted=True,
        )
        restored_at = datetime.utcnow()
        await restore_repository.update(
            asset_id,
            deleted_at=None,
            deleted_by=None,
            updated_at=restored_at,
        )

        logger.info(
            f"Restored asset {asset_id} "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return AssetRestoreResponse(
            asset_id=asset_id,
            restored_at=restored_at,
        )

    async def bulk_soft_delete(
        self,
        asset_ids: List[UUID],
        deleted_by: Optional[UUID] = None,
    ) -> BulkSoftDeleteResponse:
        """
        Soft delete multiple assets in bulk.

        Args:
            asset_ids: List of asset IDs to soft delete
            deleted_by: User ID performing the deletions

        Returns:
            Response with success/failure counts and details
        """
        success_count = 0
        failure_count = 0
        deleted_assets: List[AssetSoftDeleteResponse] = []
        errors: List[dict] = []

        for asset_id in asset_ids:
            try:
                result = await self.soft_delete(
                    asset_id=asset_id,
                    deleted_by=deleted_by,
                )
                deleted_assets.append(result)
                success_count += 1

            except Exception as e:
                failure_count += 1
                errors.append(
                    {
                        "asset_id": str(asset_id),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                logger.error(f"Failed to soft delete asset {asset_id}: {e}")

        logger.info(
            f"Bulk soft delete completed: {success_count} succeeded, {failure_count} failed "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return BulkSoftDeleteResponse(
            success_count=success_count,
            failure_count=failure_count,
            deleted_assets=deleted_assets,
            errors=errors,
        )

    async def get_trash_view(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedTrashResponse:
        """
        Get paginated list of soft deleted assets (trash view).

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Paginated response with deleted assets
        """
        # Query deleted assets with tenant scoping
        query = (
            select(Asset)
            .where(
                and_(
                    Asset.client_account_id == UUID(self.client_account_id),
                    Asset.engagement_id == UUID(self.engagement_id),
                    Asset.deleted_at.isnot(None),
                )
            )
            .order_by(Asset.deleted_at.desc())
        )

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        result = await self.db.execute(query)
        assets = result.scalars().all()

        # Get total count efficiently
        count_query = select(func.count(Asset.id)).where(
            and_(
                Asset.client_account_id == UUID(self.client_account_id),
                Asset.engagement_id == UUID(self.engagement_id),
                Asset.deleted_at.isnot(None),
            )
        )
        total = (await self.db.execute(count_query)).scalar_one()

        # Convert to response models
        trash_assets = [
            TrashAssetResponse(
                id=asset.id,
                name=asset.name,
                asset_type=asset.asset_type,
                description=asset.description,
                environment=asset.environment,
                business_owner=asset.business_owner,
                technical_owner=asset.technical_owner,
                created_at=asset.created_at,
                updated_at=asset.updated_at,
                deleted_at=asset.deleted_at,
                deleted_by=asset.deleted_by,
                completeness_score=asset.completeness_score,
                quality_score=asset.quality_score,
                six_r_strategy=asset.six_r_strategy,
                status=asset.status,
                custom_attributes=asset.custom_attributes,
            )
            for asset in assets
        ]

        logger.info(
            f"Retrieved trash view: page {page}, {len(trash_assets)} assets "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )

        return PaginatedTrashResponse(
            total=total,
            page=page,
            page_size=page_size,
            assets=trash_assets,
        )

    async def permanent_delete(
        self,
        asset_id: UUID,
    ) -> None:
        """
        Permanently delete an asset (hard delete).

        WARNING: This operation is irreversible. Only use for compliance/GDPR requirements.

        Args:
            asset_id: Asset ID to permanently delete

        Raises:
            ValueError: If asset not found or not accessible
        """
        # Verify asset exists and is deleted
        query = select(Asset).where(
            and_(
                Asset.id == asset_id,
                Asset.client_account_id == UUID(self.client_account_id),
                Asset.engagement_id == UUID(self.engagement_id),
                Asset.deleted_at.isnot(None),
            )
        )
        result = await self.db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            raise ValueError(
                f"Asset {asset_id} not found, not accessible, or not in trash"
            )

        # Permanent delete
        await self.db.delete(asset)
        await self.db.commit()

        logger.warning(
            f"PERMANENTLY deleted asset {asset_id} "
            f"(tenant: {self.client_account_id}/{self.engagement_id})"
        )
