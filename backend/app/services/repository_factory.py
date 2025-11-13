"""
Repository Factory - Centralized Repository Initialization

This factory provides a single point of repository instantiation with automatic
multi-tenant context handling. It eliminates duplicate initialization code across
20-30+ files and ensures consistent context propagation.

ARCHITECTURE:
- Thin wrapper with zero business logic
- Handles string conversion of context IDs
- Supports optional engagement_id and user_id
- Each repository method performs lazy import to avoid circular dependencies

USAGE:
    from app.services.repository_factory import RepositoryFactory
    from app.core.context import RequestContext

    # In service or endpoint
    factory = RepositoryFactory(db, context)

    # Get repositories with automatic context
    flow_repo = factory.get_discovery_flow_repo()
    master_repo = factory.get_crewai_flow_repo()
    asset_repo = factory.get_asset_repo()

BENEFITS:
- Eliminates 20-30 lines of duplicate initialization per file
- Consistent context handling across all repositories
- Type-safe repository instantiation
- Single place to update if repository init signatures change
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for context-aware repository instantiation.

    Provides centralized repository creation with automatic multi-tenant context
    injection. All repository methods handle string conversion and None values
    appropriately.

    Attributes:
        db (AsyncSession): SQLAlchemy async database session
        context (RequestContext): Multi-tenant request context containing
            client_account_id, engagement_id, user_id, and flow_id
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize repository factory with database session and request context.

        Args:
            db: Async database session for repository operations
            context: Request context containing multi-tenant scoping information

        Example:
            factory = RepositoryFactory(db, context)
            flow_repo = factory.get_discovery_flow_repo()
        """
        self.db = db
        self.context = context
        logger.debug(
            f"RepositoryFactory initialized for client={context.client_account_id}, "
            f"engagement={context.engagement_id}"
        )

    def get_discovery_flow_repo(self):
        """
        Get DiscoveryFlowRepository with automatic context injection.

        Returns:
            DiscoveryFlowRepository: Configured discovery flow repository

        Example:
            flow_repo = factory.get_discovery_flow_repo()
            flows = await flow_repo.get_by_status('running')
        """
        # Lazy import to avoid circular dependencies
        from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

        return DiscoveryFlowRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_collection_flow_repo(self):
        """
        Get CollectionFlowRepository with automatic context injection.

        Returns:
            CollectionFlowRepository: Configured collection flow repository

        Example:
            collection_repo = factory.get_collection_flow_repo()
            flow = await collection_repo.get_by_flow_id(flow_id)
        """
        from app.repositories.collection_flow_repository import CollectionFlowRepository

        return CollectionFlowRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_assessment_flow_repo(self):
        """
        Get AssessmentFlowRepository with automatic context injection.

        NOTE: AssessmentFlowRepository requires integer IDs, not strings.
        This method converts context IDs to integers.

        Returns:
            AssessmentFlowRepository: Configured assessment flow repository

        Example:
            assessment_repo = factory.get_assessment_flow_repo()
            flow = await assessment_repo.get_assessment_flow(flow_id)
        """
        from app.repositories.assessment_flow_repository import AssessmentFlowRepository

        # Convert to int as AssessmentFlowRepository expects integer IDs
        client_id = (
            int(self.context.client_account_id)
            if self.context.client_account_id
            else None
        )
        engagement_id = (
            int(self.context.engagement_id) if self.context.engagement_id else None
        )

        return AssessmentFlowRepository(
            db=self.db,
            client_account_id=client_id,
            engagement_id=engagement_id,
            user_id=self.context.user_id,
        )

    def get_crewai_flow_repo(self):
        """
        Get CrewAIFlowStateExtensionsRepository (master flow repo) with context.

        This repository manages the master flow state table that coordinates
        all flow types (discovery, collection, assessment).

        Returns:
            CrewAIFlowStateExtensionsRepository: Configured master flow repository

        Example:
            master_repo = factory.get_crewai_flow_repo()
            master_flow = await master_repo.get_by_flow_id(flow_id)
        """
        from app.repositories.crewai_flow_state_extensions_repository import (
            CrewAIFlowStateExtensionsRepository,
        )

        return CrewAIFlowStateExtensionsRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
            user_id=self.context.user_id,
        )

    def get_asset_repo(self):
        """
        Get AssetRepository with automatic context injection.

        Returns:
            AssetRepository: Configured asset repository

        Example:
            asset_repo = factory.get_asset_repo()
            assets = await asset_repo.get_by_environment('production')
        """
        from app.repositories.asset_repository import AssetRepository

        return AssetRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_approval_request_repo(self):
        """
        Get ApprovalRequestRepository with automatic context injection.

        Returns:
            ApprovalRequestRepository: Configured approval request repository

        Example:
            approval_repo = factory.get_approval_request_repo()
            requests = await approval_repo.get_pending_requests()
        """
        from app.repositories.governance_repository import ApprovalRequestRepository

        return ApprovalRequestRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_dependency_repo(self):
        """
        Get DependencyRepository with automatic context injection.

        Returns:
            DependencyRepository: Configured dependency repository

        Example:
            dep_repo = factory.get_dependency_repo()
            dependencies = await dep_repo.get_dependencies_for_asset(asset_id)
        """
        from app.repositories.dependency_repository import DependencyRepository

        return DependencyRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_vendor_product_repo(self):
        """
        Get VendorProductRepository with automatic context injection.

        Returns:
            VendorProductRepository: Configured vendor product repository

        Example:
            vendor_repo = factory.get_vendor_product_repo()
            products = await vendor_repo.get_products_by_vendor(vendor_name)
        """
        from app.repositories.vendor_product_repository import VendorProductRepository

        return VendorProductRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )

    def get_maintenance_window_repo(self):
        """
        Get MaintenanceWindowRepository with automatic context injection.

        Returns:
            MaintenanceWindowRepository: Configured maintenance window repository

        Example:
            maintenance_repo = factory.get_maintenance_window_repo()
            windows = await maintenance_repo.get_upcoming_windows()
        """
        from app.repositories.maintenance_window_repository import (
            MaintenanceWindowRepository,
        )

        return MaintenanceWindowRepository(
            db=self.db,
            client_account_id=str(self.context.client_account_id),
            engagement_id=(
                str(self.context.engagement_id) if self.context.engagement_id else None
            ),
        )


# Convenience function for one-liner repository creation
def create_repository_factory(
    db: AsyncSession, context: RequestContext
) -> RepositoryFactory:
    """
    Convenience function to create a repository factory.

    This is useful for dependency injection scenarios where you want to
    create the factory inline.

    Args:
        db: Async database session
        context: Request context

    Returns:
        RepositoryFactory: Configured factory instance

    Example:
        factory = create_repository_factory(db, context)
        flow_repo = factory.get_discovery_flow_repo()
    """
    return RepositoryFactory(db, context)
