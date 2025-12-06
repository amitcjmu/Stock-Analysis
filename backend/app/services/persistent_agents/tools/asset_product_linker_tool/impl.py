"""
Asset Product Linker Tool Implementation

Core implementation for linking assets to catalog products/versions after EOL lookup.
Creates entries in AssetProductLinks table with confidence scores.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .sync_wrapper import SyncWrapperMixin

logger = logging.getLogger(__name__)


class AssetProductLinkerToolImpl(SyncWrapperMixin):
    """Implementation for asset product linker tool"""

    def __init__(self, registry):
        self._registry = registry

    async def execute_async(
        self,
        asset_id: str,
        catalog_version_id: Optional[str] = None,
        tenant_version_id: Optional[str] = None,
        technology: Optional[str] = None,
        version: Optional[str] = None,
        confidence_score: float = 0.9,
        matched_by: str = "agent",
    ) -> str:
        """
        Link an asset to a catalog product version.

        Args:
            asset_id: UUID of the asset to link
            catalog_version_id: UUID of catalog version (from eol_catalog_lookup)
            tenant_version_id: UUID of tenant version (alternative to catalog)
            technology: Technology name (for logging/tracking)
            version: Version string (for logging/tracking)
            confidence_score: Confidence of the match (0.0 to 1.0)
            matched_by: How the match was made (agent, manual, import)

        Returns:
            JSON with link result
        """
        try:
            logger.info(
                f"🔗 Linking asset {asset_id} to product: {technology} {version}"
            )

            if not catalog_version_id and not tenant_version_id:
                return json.dumps(
                    {
                        "success": False,
                        "asset_id": asset_id,
                        "error": "Either catalog_version_id or tenant_version_id required",
                        "message": "Cannot link asset without a version reference",
                    }
                )

            from sqlalchemy import select
            from uuid import UUID

            from app.models.vendor_products_catalog import AssetProductLinks

            db_session = await self._registry.get_db_session()

            # Parse UUIDs
            try:
                asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id
                catalog_version_uuid = (
                    UUID(catalog_version_id)
                    if catalog_version_id and isinstance(catalog_version_id, str)
                    else catalog_version_id
                )
                tenant_version_uuid = (
                    UUID(tenant_version_id)
                    if tenant_version_id and isinstance(tenant_version_id, str)
                    else tenant_version_id
                )
            except ValueError as e:
                return json.dumps(
                    {
                        "success": False,
                        "asset_id": asset_id,
                        "error": f"Invalid UUID: {e}",
                        "message": "Failed to parse UUID",
                    }
                )

            # Check for existing link
            stmt = select(
                AssetProductLinks
            ).where(  # SKIP_TENANT_CHECK - via asset_id FK
                AssetProductLinks.asset_id == asset_uuid
            )
            if catalog_version_uuid:
                stmt = stmt.where(
                    AssetProductLinks.catalog_version_id == catalog_version_uuid
                )
            if tenant_version_uuid:
                stmt = stmt.where(
                    AssetProductLinks.tenant_version_id == tenant_version_uuid
                )

            result = await db_session.execute(stmt)
            existing_link = result.scalar_one_or_none()

            if existing_link:
                # Update existing link
                existing_link.confidence_score = confidence_score
                existing_link.matched_by = matched_by
                existing_link.updated_at = datetime.utcnow()
                await db_session.commit()

                logger.info(
                    f"✅ Updated existing asset-product link: {existing_link.id}"
                )

                return json.dumps(
                    {
                        "success": True,
                        "asset_id": asset_id,
                        "link_id": str(existing_link.id),
                        "catalog_version_id": catalog_version_id,
                        "tenant_version_id": tenant_version_id,
                        "technology": technology,
                        "version": version,
                        "confidence_score": confidence_score,
                        "matched_by": matched_by,
                        "status": "updated",
                        "message": "Updated existing asset-product link",
                    }
                )

            # Create new link
            new_link = AssetProductLinks(
                id=uuid.uuid4(),
                asset_id=asset_uuid,
                catalog_version_id=catalog_version_uuid,
                tenant_version_id=tenant_version_uuid,
                confidence_score=confidence_score,
                matched_by=matched_by,
            )
            db_session.add(new_link)
            await db_session.commit()

            logger.info(f"✅ Created asset-product link: {new_link.id}")

            return json.dumps(
                {
                    "success": True,
                    "asset_id": asset_id,
                    "link_id": str(new_link.id),
                    "catalog_version_id": catalog_version_id,
                    "tenant_version_id": tenant_version_id,
                    "technology": technology,
                    "version": version,
                    "confidence_score": confidence_score,
                    "matched_by": matched_by,
                    "status": "created",
                    "message": "Created new asset-product link",
                }
            )

        except Exception as e:
            logger.error(f"❌ Asset-product linking failed: {e}", exc_info=True)
            return json.dumps(
                {
                    "success": False,
                    "asset_id": asset_id,
                    "error": str(e),
                    "message": "Failed to link asset to product",
                }
            )

    async def bulk_link_async(
        self,
        links: List[Dict[str, Any]],
    ) -> str:
        """
        Link multiple assets to product versions.

        Args:
            links: List of link specifications, each containing:
                - asset_id: UUID of the asset
                - catalog_version_id: UUID of catalog version (optional)
                - tenant_version_id: UUID of tenant version (optional)
                - technology: Technology name (for logging)
                - version: Version string (for logging)
                - confidence_score: Confidence of the match
                - matched_by: How the match was made

        Returns:
            JSON with bulk link results
        """
        try:
            logger.info(f"🔗 Bulk linking {len(links)} assets to products")

            results = {
                "success": True,
                "total_requested": len(links),
                "created": 0,
                "updated": 0,
                "failed": 0,
                "links": [],
                "errors": [],
            }

            for link_spec in links:
                # OBSERVABILITY: tracking not needed - Agent tool internal execution
                link_result = await self.execute_async(
                    asset_id=link_spec.get("asset_id"),
                    catalog_version_id=link_spec.get("catalog_version_id"),
                    tenant_version_id=link_spec.get("tenant_version_id"),
                    technology=link_spec.get("technology"),
                    version=link_spec.get("version"),
                    confidence_score=link_spec.get("confidence_score", 0.9),
                    matched_by=link_spec.get("matched_by", "agent"),
                )

                link_data = json.loads(link_result)

                if link_data.get("success"):
                    if link_data.get("status") == "created":
                        results["created"] += 1
                    else:
                        results["updated"] += 1
                    results["links"].append(
                        {
                            "asset_id": link_spec.get("asset_id"),
                            "link_id": link_data.get("link_id"),
                            "status": link_data.get("status"),
                        }
                    )
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        {
                            "asset_id": link_spec.get("asset_id"),
                            "error": link_data.get("error"),
                        }
                    )

            logger.info(
                f"✅ Bulk link complete: {results['created']} created, "
                f"{results['updated']} updated, {results['failed']} failed"
            )

            return json.dumps(results)

        except Exception as e:
            logger.error(f"❌ Bulk asset-product linking failed: {e}", exc_info=True)
            return json.dumps(
                {
                    "success": False,
                    "error": str(e),
                    "message": "Bulk linking failed",
                }
            )

    async def get_asset_products_async(self, asset_id: str) -> str:
        """
        Get all products linked to an asset with their EOL status.

        Args:
            asset_id: UUID of the asset

        Returns:
            JSON with linked products and EOL information
        """
        try:
            logger.info(f"🔍 Getting products for asset {asset_id}")

            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            from uuid import UUID

            from app.models.vendor_products_catalog import (
                AssetProductLinks,
                ProductVersionsCatalog,
            )

            db_session = await self._registry.get_db_session()
            asset_uuid = UUID(asset_id) if isinstance(asset_id, str) else asset_id

            # Get all links for this asset
            stmt = (
                select(AssetProductLinks)  # SKIP_TENANT_CHECK - via asset_id FK
                .where(AssetProductLinks.asset_id == asset_uuid)
                .options(
                    selectinload(AssetProductLinks.catalog_version).options(
                        selectinload(ProductVersionsCatalog.catalog_product),
                        selectinload(ProductVersionsCatalog.lifecycle_milestones),
                    )
                )
            )
            result = await db_session.execute(stmt)
            links = result.scalars().all()

            products = []
            for link in links:
                product_info = {
                    "link_id": str(link.id),
                    "confidence_score": link.confidence_score,
                    "matched_by": link.matched_by,
                }

                if link.catalog_version:
                    cv = link.catalog_version
                    product_info["version_label"] = cv.version_label
                    product_info["catalog_version_id"] = str(cv.id)

                    if cv.catalog_product:
                        product_info["vendor_name"] = cv.catalog_product.vendor_name
                        product_info["product_name"] = cv.catalog_product.product_name
                        product_info["normalized_key"] = (
                            cv.catalog_product.normalized_key
                        )

                    # Get EOL info from milestones
                    for milestone in cv.lifecycle_milestones:
                        if milestone.milestone_type == "end_of_life":
                            product_info["eol_date"] = (
                                milestone.milestone_date.isoformat()
                                if milestone.milestone_date
                                else None
                            )
                            product_info["eol_source"] = milestone.source
                        elif milestone.milestone_type == "extended_support_end":
                            product_info["extended_support_date"] = (
                                milestone.milestone_date.isoformat()
                                if milestone.milestone_date
                                else None
                            )

                products.append(product_info)

            logger.info(f"✅ Found {len(products)} products for asset {asset_id}")

            return json.dumps(
                {
                    "success": True,
                    "asset_id": asset_id,
                    "products": products,
                    "total_products": len(products),
                }
            )

        except Exception as e:
            logger.error(f"❌ Failed to get asset products: {e}", exc_info=True)
            return json.dumps(
                {
                    "success": False,
                    "asset_id": asset_id,
                    "error": str(e),
                    "message": "Failed to get asset products",
                }
            )
