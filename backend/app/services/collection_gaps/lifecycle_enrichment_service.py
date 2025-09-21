"""
Lifecycle enrichment service for collection gaps.

This service provides lifecycle data enrichment functionality as a stub
for future integration with external lifecycle data sources.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.vendor_product_repository import (
    LifecycleRepository,
    VendorProductRepository,
)

logger = logging.getLogger(__name__)


class LifecycleEnrichmentService:
    """
    Service for enriching product lifecycle data.

    This is currently a stub implementation that provides the interface
    for future integration with external lifecycle data sources.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """
        Initialize the lifecycle enrichment service.

        Args:
            db: Database session
            client_account_id: Client account UUID for tenant scoping
            engagement_id: Engagement UUID for project scoping
        """
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

        # Initialize repositories
        self.vendor_product_repo = VendorProductRepository(
            db, client_account_id, engagement_id
        )
        self.lifecycle_repo = LifecycleRepository(db, client_account_id, engagement_id)

    async def enrich_product_lifecycle(
        self,
        vendor_name: str,
        product_name: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich lifecycle data for a product.

        Args:
            vendor_name: Vendor name
            product_name: Product name
            version: Optional product version

        Returns:
            Dictionary containing enriched lifecycle data
        """
        logger.info(
            f"Enriching lifecycle data for {vendor_name} {product_name} {version or 'latest'}"
        )

        # Stub implementation - in production this would query external sources
        # such as vendor APIs, security databases, etc.

        enrichment_result = {
            "vendor_name": vendor_name,
            "product_name": product_name,
            "version": version,
            "lifecycle_data": await self._get_mock_lifecycle_data(
                vendor_name, product_name, version
            ),
            "enrichment_metadata": {
                "sources_checked": self._get_data_sources(),
                "enriched_at": datetime.utcnow().isoformat(),
                "confidence_score": 0.7,  # Mock confidence score
                "data_freshness": "mock",
            },
        }

        return enrichment_result

    async def enrich_batch_products(
        self,
        products: List[Dict[str, str]],
        max_concurrent: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Enrich lifecycle data for multiple products.

        Args:
            products: List of product dictionaries with vendor_name, product_name, version
            max_concurrent: Maximum concurrent enrichment requests

        Returns:
            List of enrichment results
        """
        logger.info(f"Starting batch enrichment for {len(products)} products")

        results = []

        # Stub implementation - would use asyncio.gather with semaphore for real concurrent processing
        for product in products:
            try:
                result = await self.enrich_product_lifecycle(
                    vendor_name=product.get("vendor_name", ""),
                    product_name=product.get("product_name", ""),
                    version=product.get("version"),
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to enrich product {product}: {e}")
                results.append(
                    {
                        "vendor_name": product.get("vendor_name", ""),
                        "product_name": product.get("product_name", ""),
                        "version": product.get("version"),
                        "error": str(e),
                        "enrichment_metadata": {
                            "enriched_at": datetime.utcnow().isoformat(),
                            "status": "failed",
                        },
                    }
                )

        logger.info(
            f"Completed batch enrichment: {len([r for r in results if 'error' not in r])} successful, "
            f"{len([r for r in results if 'error' in r])} failed"
        )

        return results

    async def get_critical_lifecycle_alerts(
        self,
        days_ahead: int = 365,
    ) -> List[Dict[str, Any]]:
        """
        Get critical lifecycle alerts for upcoming EOL/EOS dates.

        Args:
            days_ahead: Number of days to look ahead for alerts

        Returns:
            List of critical lifecycle alerts
        """
        logger.info(f"Fetching critical lifecycle alerts for next {days_ahead} days")

        # Get critical milestones from repository
        critical_milestones = await self.lifecycle_repo.get_critical_milestones(
            days_ahead
        )

        alerts = []
        for milestone in critical_milestones:
            # Calculate days until milestone
            days_until = (milestone.milestone_date - date.today()).days

            # Determine alert severity
            severity = (
                "critical"
                if days_until <= 90
                else "high" if days_until <= 180 else "medium"
            )

            alert = {
                "id": str(milestone.id),
                "milestone_type": milestone.milestone_type,
                "milestone_date": milestone.milestone_date.isoformat(),
                "days_until": days_until,
                "severity": severity,
                "source": milestone.source,
                "catalog_version_id": (
                    str(milestone.catalog_version_id)
                    if milestone.catalog_version_id
                    else None
                ),
                "tenant_version_id": (
                    str(milestone.tenant_version_id)
                    if milestone.tenant_version_id
                    else None
                ),
                "provenance": milestone.provenance,
            }
            alerts.append(alert)

        # Sort by days until milestone (most urgent first)
        alerts.sort(key=lambda x: x["days_until"])

        logger.info(f"Found {len(alerts)} critical lifecycle alerts")
        return alerts

    async def refresh_lifecycle_data(
        self,
        vendor_name: Optional[str] = None,
        product_name: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Refresh lifecycle data from external sources.

        Args:
            vendor_name: Optional vendor filter
            product_name: Optional product filter
            force_refresh: Force refresh even if data is recent

        Returns:
            Dictionary with refresh results
        """
        logger.info(
            f"Refreshing lifecycle data: vendor={vendor_name}, product={product_name}, force={force_refresh}"
        )

        # Stub implementation - would implement actual refresh logic
        refresh_result = {
            "status": "completed",
            "refreshed_at": datetime.utcnow().isoformat(),
            "products_updated": 0,  # Mock count
            "milestones_added": 0,  # Mock count
            "milestones_updated": 0,  # Mock count
            "sources_queried": self._get_data_sources(),
            "execution_time_ms": 1500,  # Mock execution time
            "errors": [],
        }

        # In production, this would:
        # 1. Query configured external sources
        # 2. Parse and normalize lifecycle data
        # 3. Update database records
        # 4. Log refresh metrics

        return refresh_result

    async def _get_mock_lifecycle_data(
        self,
        vendor_name: str,
        product_name: str,
        version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate mock lifecycle data for demonstration.

        Args:
            vendor_name: Vendor name
            product_name: Product name
            version: Product version

        Returns:
            Mock lifecycle data
        """
        # Generate mock dates based on product name hash for consistency
        import hashlib

        product_hash = hashlib.md5(f"{vendor_name}_{product_name}".encode()).hexdigest()
        days_offset = int(product_hash[:4], 16) % 1000  # 0-999 days

        base_date = date.today() + timedelta(days=days_offset)

        mock_data = {
            "release_date": (
                base_date - timedelta(days=365 * 2)
            ).isoformat(),  # Released 2 years ago
            "end_of_support": (
                base_date + timedelta(days=365)
            ).isoformat(),  # EOS in ~1-3 years
            "end_of_life": (
                base_date + timedelta(days=365 * 2)
            ).isoformat(),  # EOL in ~2-4 years
            "extended_support_end": (
                base_date + timedelta(days=365 * 3)
            ).isoformat(),  # Extended support
            "latest_version": f"{version or '1.0'}.latest",
            "security_patches_until": (base_date + timedelta(days=180)).isoformat(),
            "vendor_recommendations": [
                f"Upgrade to latest version before {(base_date + timedelta(days=90)).isoformat()}",
                "Consider migration to next-generation product",
            ],
            "confidence_indicators": {
                "official_vendor_data": False,
                "community_maintained": True,
                "last_verified": datetime.utcnow().isoformat(),
            },
        }

        return mock_data

    def _get_data_sources(self) -> List[str]:
        """
        Get list of configured data sources.

        Returns:
            List of data source names
        """
        # In production, this would return actual configured sources
        return [
            "vendor_api_mock",
            "security_database_mock",
            "community_tracker_mock",
            "internal_knowledge_base",
        ]

    async def validate_lifecycle_data(
        self,
        lifecycle_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate lifecycle data for consistency and completeness.

        Args:
            lifecycle_data: Lifecycle data to validate

        Returns:
            Validation results
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "completeness_score": 0.0,
        }

        required_fields = ["end_of_support", "end_of_life"]
        optional_fields = [
            "release_date",
            "extended_support_end",
            "security_patches_until",
        ]

        # Check required fields
        missing_required = [
            field for field in required_fields if field not in lifecycle_data
        ]
        if missing_required:
            validation_result["errors"].extend(
                [f"Missing required field: {field}" for field in missing_required]
            )
            validation_result["is_valid"] = False

        # Check date consistency
        try:
            if "end_of_support" in lifecycle_data and "end_of_life" in lifecycle_data:
                eos_date = datetime.fromisoformat(
                    lifecycle_data["end_of_support"]
                ).date()
                eol_date = datetime.fromisoformat(lifecycle_data["end_of_life"]).date()

                if eos_date > eol_date:
                    validation_result["errors"].append(
                        "End of support date is after end of life date"
                    )
                    validation_result["is_valid"] = False

        except (ValueError, TypeError) as e:
            validation_result["errors"].append(f"Invalid date format: {e}")
            validation_result["is_valid"] = False

        # Calculate completeness score
        total_fields = len(required_fields) + len(optional_fields)
        present_fields = len(
            [f for f in required_fields + optional_fields if f in lifecycle_data]
        )
        validation_result["completeness_score"] = present_fields / total_fields

        return validation_result
