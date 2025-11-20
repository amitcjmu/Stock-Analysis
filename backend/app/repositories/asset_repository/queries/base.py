"""
Base query classes for asset repository operations.

Provides base classes with common filtering methods used by all query classes.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset, AssetDependency, WorkflowProgress


class BaseAssetQueries:
    """Base query class for assets with context filtering."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
        include_deleted: bool = False,
    ):
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


class BaseAssetDependencyQueries:
    """Base query class for asset dependencies with context filtering."""

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


class BaseWorkflowProgressQueries:
    """Base query class for workflow progress with context filtering."""

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
