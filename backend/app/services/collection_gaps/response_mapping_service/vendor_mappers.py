"""
Vendor and product mapping handlers for response mapping service.

Contains handlers for mapping vendor, product, and lifecycle-related responses
to appropriate database tables.
"""

import logging
from typing import Any, Dict, List

from .base import BaseResponseMapper

logger = logging.getLogger(__name__)


class VendorProductMappers(BaseResponseMapper):
    """Mappers for vendor and product related responses."""

    async def map_vendor_product(self, response: Dict[str, Any]) -> List[str]:
        """
        Map vendor/product response to tenant_vendor_products and asset_product_links.

        Expected response format:
        {
            "vendor_name": "string",
            "product_name": "string",
            "asset_ids": ["uuid1", "uuid2", ...],
            "metadata": {...}
        }
        """
        try:
            vendor_name = response.get("vendor_name")
            product_name = response.get("product_name")
            asset_ids = response.get("asset_ids", [])

            if not vendor_name or not product_name:
                raise ValueError("Missing required vendor_name or product_name")

            created_records = []

            # Check if vendor product already exists in catalog
            vendor_product = await self.vendor_product_repo.get_by_filters(
                vendor_name=vendor_name, product_name=product_name
            )

            if not vendor_product:
                # Create in catalog if doesn't exist
                vendor_product = await self.vendor_product_repo.create(
                    vendor_name=vendor_name,
                    product_name=product_name,
                    product_metadata=response.get("metadata", {}),
                )
                created_records.append(f"vendor_product:{vendor_product.id}")

            # Create or update tenant-specific vendor product
            tenant_vendor_product = await self.tenant_vendor_product_repo.upsert(
                catalog_vendor_product_id=vendor_product.id,
                tenant_product_name=product_name,
                tenant_vendor_name=vendor_name,
                tenant_metadata=response.get("tenant_metadata", {}),
            )
            created_records.append(f"tenant_vendor_product:{tenant_vendor_product.id}")

            # Link assets to the product
            for asset_id in asset_ids:
                asset_link = await self.asset_product_link_repo.upsert(
                    asset_id=asset_id,
                    tenant_vendor_product_id=tenant_vendor_product.id,
                    relationship_type="primary",
                    confidence_score=response.get("confidence_score", 0.9),
                )
                created_records.append(f"asset_product_link:{asset_link.id}")

            logger.info(
                f"✅ Successfully mapped vendor/product: {vendor_name}/{product_name} "
                f"to {len(asset_ids)} assets"
            )
            return created_records

        except Exception as e:
            logger.error(f"❌ Failed to map vendor/product response: {e}")
            raise

    async def map_product_version(self, response: Dict[str, Any]) -> List[str]:
        """
        Map product version response to tenant_product_versions and asset_product_links.

        Expected response format:
        {
            "vendor_name": "string",
            "product_name": "string",
            "version": "string",
            "asset_ids": ["uuid1", "uuid2", ...],
            "metadata": {...}
        }
        """
        try:
            vendor_name = response.get("vendor_name")
            product_name = response.get("product_name")
            version = response.get("version")
            asset_ids = response.get("asset_ids", [])

            if not all([vendor_name, product_name, version]):
                raise ValueError(
                    "Missing required vendor_name, product_name, or version"
                )

            created_records = []

            # Get the vendor product first (should exist from vendor_product mapping)
            vendor_product = await self.vendor_product_repo.get_by_filters(
                vendor_name=vendor_name, product_name=product_name
            )

            if not vendor_product:
                # Create if doesn't exist
                vendor_product = await self.vendor_product_repo.create(
                    vendor_name=vendor_name,
                    product_name=product_name,
                    product_metadata=response.get("metadata", {}),
                )

            # Get tenant vendor product
            tenant_vendor_product = (
                await self.tenant_vendor_product_repo.get_by_filters(
                    catalog_vendor_product_id=vendor_product.id
                )
            )

            if not tenant_vendor_product:
                # Create if doesn't exist
                tenant_vendor_product = await self.tenant_vendor_product_repo.create(
                    catalog_vendor_product_id=vendor_product.id,
                    tenant_product_name=product_name,
                    tenant_vendor_name=vendor_name,
                    tenant_metadata=response.get("tenant_metadata", {}),
                )

            # Create or update tenant product version
            tenant_version = await self.tenant_vendor_product_repo.upsert_version(
                tenant_vendor_product_id=tenant_vendor_product.id,
                version=version,
                version_metadata=response.get("version_metadata", {}),
            )
            created_records.append(f"tenant_product_version:{tenant_version.id}")

            # Update asset links to reference the specific version
            for asset_id in asset_ids:
                asset_link = await self.asset_product_link_repo.upsert(
                    asset_id=asset_id,
                    tenant_vendor_product_id=tenant_vendor_product.id,
                    tenant_version_id=tenant_version.id,
                    relationship_type="version_specific",
                    confidence_score=response.get("confidence_score", 0.95),
                )
                created_records.append(f"asset_product_link:{asset_link.id}")

            logger.info(
                f"✅ Successfully mapped product version: {vendor_name}/{product_name} v{version} "
                f"to {len(asset_ids)} assets"
            )
            return created_records

        except Exception as e:
            logger.error(f"❌ Failed to map product version response: {e}")
            raise

    async def map_lifecycle_dates(self, response: Dict[str, Any]) -> List[str]:
        """
        Map lifecycle dates response to lifecycle_milestones table.

        Expected response format:
        {
            "vendor_name": "string",
            "product_name": "string",
            "version": "string",
            "milestone_type": "string",
            "milestone_date": "YYYY-MM-DD",
            "metadata": {...}
        }
        """
        try:
            vendor_name = response.get("vendor_name")
            product_name = response.get("product_name")
            version = response.get("version")
            milestone_type = response.get("milestone_type")
            milestone_date = response.get("milestone_date")

            # Get version linkage from metadata
            catalog_version_id = response.get("metadata", {}).get("catalog_version_id")
            tenant_version_id = response.get("metadata", {}).get("tenant_version_id")

            if not milestone_type:
                raise ValueError("Missing milestone_type in response")

            if not milestone_date:
                raise ValueError("Missing milestone_date in response")

            if not catalog_version_id and not tenant_version_id:
                raise ValueError(
                    "Version linkage required: must provide either catalog_version_id "
                    "or tenant_version_id in response metadata"
                )

            # Create lifecycle milestone with required version linkage
            await self.lifecycle_repo.create(
                milestone_type=milestone_type,
                milestone_date=milestone_date,
                catalog_version_id=catalog_version_id,
                tenant_version_id=tenant_version_id,
                milestone_metadata=response.get("milestone_metadata", {}),
            )

            logger.info(
                f"✅ Successfully mapped lifecycle milestone: {milestone_type} "
                f"for {vendor_name}/{product_name} v{version} on {milestone_date}"
            )
            return [f"lifecycle_milestone:{milestone_type}"]

        except Exception as e:
            logger.error(f"❌ Failed to map lifecycle dates response: {e}")
            raise
