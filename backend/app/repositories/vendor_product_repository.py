"""
Repository for vendor products catalog management.

This module provides data access methods for vendor/product catalog,
tenant overrides, and product version management.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.vendor_products_catalog import (
    AssetProductLinks,
    LifecycleMilestones,
    TenantVendorProducts,
    VendorProductsCatalog,
)
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class VendorProductRepository(ContextAwareRepository[VendorProductsCatalog]):
    """Repository for global vendor products catalog."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, VendorProductsCatalog, client_account_id, engagement_id)

    async def search_by_name(
        self, vendor_name: Optional[str] = None, product_name: Optional[str] = None
    ) -> List[VendorProductsCatalog]:
        """
        Search vendor products by name patterns.

        Args:
            vendor_name: Vendor name pattern (case-insensitive)
            product_name: Product name pattern (case-insensitive)

        Returns:
            List of matching vendor products
        """
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(VendorProductsCatalog)

        filters = []
        if vendor_name:
            filters.append(VendorProductsCatalog.vendor_name.ilike(f"%{vendor_name}%"))
        if product_name:
            filters.append(
                VendorProductsCatalog.product_name.ilike(f"%{product_name}%")
            )

        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_normalized_key(
        self, normalized_key: str
    ) -> Optional[VendorProductsCatalog]:
        """
        Get vendor product by normalized key.

        Args:
            normalized_key: Normalized key for exact matching

        Returns:
            Vendor product if found, None otherwise
        """
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(VendorProductsCatalog).where(
            VendorProductsCatalog.normalized_key == normalized_key
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_with_versions(
        self, vendor_product_id: str
    ) -> Optional[VendorProductsCatalog]:
        """
        Get vendor product with all its versions loaded.

        Args:
            vendor_product_id: Vendor product UUID

        Returns:
            Vendor product with versions loaded
        """
        query = (
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(VendorProductsCatalog)
            .options(selectinload(VendorProductsCatalog.product_versions))
            .where(VendorProductsCatalog.id == vendor_product_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class TenantVendorProductRepository(ContextAwareRepository[TenantVendorProducts]):
    """Repository for tenant-specific vendor products."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: str,
    ):
        super().__init__(db, TenantVendorProducts, client_account_id, engagement_id)

    async def search_unified_products(
        self, vendor_name: Optional[str] = None, product_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across both global catalog and tenant-specific products.

        Args:
            vendor_name: Vendor name pattern
            product_name: Product name pattern

        Returns:
            List of unified product dictionaries
        """
        # Get tenant-specific products
        tenant_filters = []
        if vendor_name:
            tenant_filters.append(
                TenantVendorProducts.custom_vendor_name.ilike(f"%{vendor_name}%")
            )
        if product_name:
            tenant_filters.append(
                TenantVendorProducts.custom_product_name.ilike(f"%{product_name}%")
            )

        # SKIP_TENANT_CHECK - Service-level/monitoring query
        tenant_query = select(TenantVendorProducts).options(
            joinedload(TenantVendorProducts.catalog_reference)
        )
        tenant_query = self._apply_context_filter(tenant_query)

        if tenant_filters:
            tenant_query = tenant_query.where(or_(*tenant_filters))

        tenant_result = await self.db.execute(tenant_query)
        tenant_products = tenant_result.scalars().all()

        # Get global catalog products not overridden by tenant
        global_filters = []
        if vendor_name:
            global_filters.append(
                VendorProductsCatalog.vendor_name.ilike(f"%{vendor_name}%")
            )
        if product_name:
            global_filters.append(
                VendorProductsCatalog.product_name.ilike(f"%{product_name}%")
            )

        # Exclude products that have tenant overrides
        tenant_catalog_ids = [tp.catalog_id for tp in tenant_products if tp.catalog_id]

        # SKIP_TENANT_CHECK - Service-level/monitoring query
        global_query = select(VendorProductsCatalog)
        if global_filters:
            global_query = global_query.where(and_(*global_filters))
        if tenant_catalog_ids:
            global_query = global_query.where(
                ~VendorProductsCatalog.id.in_(tenant_catalog_ids)
            )

        global_result = await self.db.execute(global_query)
        global_products = global_result.scalars().all()

        # Combine results
        unified_products = []

        # Add tenant products (these take precedence)
        for tp in tenant_products:
            unified_products.append(
                {
                    "id": str(tp.id),
                    "vendor_name": tp.custom_vendor_name
                    or (
                        tp.catalog_reference.vendor_name if tp.catalog_reference else ""
                    ),
                    "product_name": tp.custom_product_name
                    or (
                        tp.catalog_reference.product_name
                        if tp.catalog_reference
                        else ""
                    ),
                    "is_tenant_override": True,
                    "source": "tenant",
                    "catalog_reference_id": (
                        str(tp.catalog_id) if tp.catalog_id else None
                    ),
                }
            )

        # Add global products not overridden
        for gp in global_products:
            unified_products.append(
                {
                    "id": str(gp.id),
                    "vendor_name": gp.vendor_name,
                    "product_name": gp.product_name,
                    "is_tenant_override": False,
                    "source": "global",
                    "catalog_reference_id": str(gp.id),
                }
            )

        return unified_products

    async def get_or_create_from_catalog(
        self, catalog_id: str, commit: bool = True
    ) -> TenantVendorProducts:
        """
        Get or create a tenant vendor product from global catalog.

        Args:
            catalog_id: Global catalog product ID
            commit: Whether to commit the transaction

        Returns:
            Tenant vendor product instance
        """
        # Check if already exists
        existing = await self.get_by_filters(catalog_id=catalog_id)
        if existing:
            return existing[0]

        # Create new tenant product referencing catalog
        return await self.create(commit=commit, catalog_id=catalog_id)

    async def create_custom_product(
        self,
        vendor_name: str,
        product_name: str,
        normalized_key: Optional[str] = None,
        commit: bool = True,
    ) -> TenantVendorProducts:
        """
        Create a custom tenant-specific product.

        Args:
            vendor_name: Custom vendor name
            product_name: Custom product name
            normalized_key: Optional normalized key for matching
            commit: Whether to commit the transaction

        Returns:
            Created tenant vendor product
        """
        if not normalized_key:
            normalized_key = f"{vendor_name.lower().replace(' ', '_')}_{product_name.lower().replace(' ', '_')}"

        return await self.create(
            commit=commit,
            custom_vendor_name=vendor_name,
            custom_product_name=product_name,
            normalized_key=normalized_key,
        )


class LifecycleRepository(ContextAwareRepository[LifecycleMilestones]):
    """Repository for product lifecycle milestones."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, LifecycleMilestones, client_account_id, engagement_id)

    async def get_by_version(
        self,
        catalog_version_id: Optional[str] = None,
        tenant_version_id: Optional[str] = None,
        milestone_type: Optional[str] = None,
    ) -> List[LifecycleMilestones]:
        """
        Get lifecycle milestones for a specific version.

        Args:
            catalog_version_id: Global catalog version ID
            tenant_version_id: Tenant version ID
            milestone_type: Optional milestone type filter

        Returns:
            List of lifecycle milestones
        """
        filters = []

        if catalog_version_id:
            filters.append(LifecycleMilestones.catalog_version_id == catalog_version_id)
        if tenant_version_id:
            filters.append(LifecycleMilestones.tenant_version_id == tenant_version_id)
        if milestone_type:
            filters.append(LifecycleMilestones.milestone_type == milestone_type)

        if not filters:
            raise ValueError("At least one version ID must be provided")

        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(LifecycleMilestones).where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_critical_milestones(
        self, days_ahead: int = 365
    ) -> List[LifecycleMilestones]:
        """
        Get critical milestones approaching within specified days.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of approaching critical milestones
        """
        from datetime import date, timedelta

        cutoff_date = date.today() + timedelta(days=days_ahead)

        query = (
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(LifecycleMilestones)
            .where(
                and_(
                    LifecycleMilestones.milestone_type.in_(
                        ["end_of_support", "end_of_life"]
                    ),
                    LifecycleMilestones.milestone_date <= cutoff_date,
                    LifecycleMilestones.milestone_date >= date.today(),
                )
            )
            .order_by(LifecycleMilestones.milestone_date)
        )

        result = await self.db.execute(query)
        return result.scalars().all()


class AssetProductLinkRepository(ContextAwareRepository[AssetProductLinks]):
    """Repository for asset-product links."""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        super().__init__(db, AssetProductLinks, client_account_id, engagement_id)

    async def get_by_asset(self, asset_id: str) -> List[AssetProductLinks]:
        """
        Get all product links for an asset.

        Args:
            asset_id: Asset UUID

        Returns:
            List of asset product links
        """
        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = (
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            select(AssetProductLinks)
            .options(
                joinedload(AssetProductLinks.catalog_version),
                joinedload(AssetProductLinks.tenant_version),
            )
            .where(AssetProductLinks.asset_id == asset_id)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def link_asset_to_product(
        self,
        asset_id: str,
        catalog_version_id: Optional[str] = None,
        tenant_version_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        matched_by: str = "manual",
        commit: bool = True,
    ) -> AssetProductLinks:
        """
        Link an asset to a product version.

        Args:
            asset_id: Asset UUID
            catalog_version_id: Global catalog version ID
            tenant_version_id: Tenant version ID
            confidence_score: Confidence score for the link
            matched_by: How the link was established
            commit: Whether to commit the transaction

        Returns:
            Created asset product link
        """
        if not catalog_version_id and not tenant_version_id:
            raise ValueError("At least one version ID must be provided")

        # Check for existing link with same asset and version
        existing_filters = {"asset_id": asset_id}
        if catalog_version_id:
            existing_filters["catalog_version_id"] = catalog_version_id
        if tenant_version_id:
            existing_filters["tenant_version_id"] = tenant_version_id

        existing = await self.get_by_filters(**existing_filters)
        if existing:
            # Update existing link
            return await self.update(
                existing[0].id,
                commit=commit,
                confidence_score=confidence_score,
                matched_by=matched_by,
            )

        # Create new link
        return await self.create(
            commit=commit,
            asset_id=asset_id,
            catalog_version_id=catalog_version_id,
            tenant_version_id=tenant_version_id,
            confidence_score=confidence_score,
            matched_by=matched_by,
        )

    async def get_assets_by_product(
        self,
        catalog_version_id: Optional[str] = None,
        tenant_version_id: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> List[AssetProductLinks]:
        """
        Get all assets linked to a specific product version.

        Args:
            catalog_version_id: Global catalog version ID
            tenant_version_id: Tenant version ID
            min_confidence: Minimum confidence score filter

        Returns:
            List of asset product links
        """
        filters = [AssetProductLinks.confidence_score >= min_confidence]

        if catalog_version_id:
            filters.append(AssetProductLinks.catalog_version_id == catalog_version_id)
        if tenant_version_id:
            filters.append(AssetProductLinks.tenant_version_id == tenant_version_id)

        if not catalog_version_id and not tenant_version_id:
            # SKIP_TENANT_CHECK - Service-level/monitoring query
            raise ValueError("At least one version ID must be provided")

        # SKIP_TENANT_CHECK - Service-level/monitoring query
        query = select(AssetProductLinks).where(and_(*filters))
        result = await self.db.execute(query)
        return result.scalars().all()
