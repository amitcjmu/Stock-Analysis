"""
Utility functions for collection flows API endpoints.

This module contains helper functions for calculating metrics, gap analysis,
and data processing used by the collection flows API endpoints.
"""

import logging
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def calculate_completeness_metrics(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, float]:
    """
    Calculate actual completeness metrics by category based on database data.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Dictionary with completeness percentages by category
    """
    from app.repositories.resilience_repository import (
        ResilienceRepository,
        ComplianceRepository,
        LicenseRepository,
    )
    from app.repositories.vendor_product_repository import LifecycleRepository
    from sqlalchemy import select, func
    from app.models import Asset

    # Get total asset count for this engagement
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    total_assets = result.scalar() or 1  # Avoid division by zero

    # Initialize repositories
    resilience_repo = ResilienceRepository(db, client_account_id, engagement_id)
    compliance_repo = ComplianceRepository(db, client_account_id, engagement_id)
    license_repo = LicenseRepository(db, client_account_id, engagement_id)
    lifecycle_repo = LifecycleRepository(db, client_account_id, engagement_id)

    # Calculate lifecycle completeness
    lifecycle_milestones = await lifecycle_repo.get_all()
    lifecycle_completeness = (
        (len(lifecycle_milestones) / total_assets) * 100 if total_assets > 0 else 0.0
    )

    # Calculate resilience completeness
    resilience_records = await resilience_repo.get_all()
    resilience_completeness = (
        (len(resilience_records) / total_assets) * 100 if total_assets > 0 else 0.0
    )

    # Calculate compliance completeness
    compliance_records = await compliance_repo.get_all()
    compliance_completeness = (
        (len(compliance_records) / total_assets) * 100 if total_assets > 0 else 0.0
    )

    # Calculate licensing completeness
    license_records = await license_repo.get_all()
    licensing_completeness = (
        (len(license_records) / total_assets) * 100 if total_assets > 0 else 0.0
    )

    return {
        "lifecycle": min(lifecycle_completeness, 100.0),
        "resilience": min(resilience_completeness, 100.0),
        "compliance": min(compliance_completeness, 100.0),
        "licensing": min(licensing_completeness, 100.0),
    }


async def calculate_pending_gaps(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> int:
    """
    Calculate the number of pending gaps that need to be addressed.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Number of pending gaps
    """
    # Get completeness metrics and calculate pending gaps based on thresholds
    completeness = await calculate_completeness_metrics(
        db, client_account_id, engagement_id
    )

    # Count categories with less than 80% completeness as pending gaps
    pending_gaps = sum(1 for percentage in completeness.values() if percentage < 80.0)

    return pending_gaps


async def get_existing_data_snapshot(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, Any]:
    """
    Get snapshot of existing data for gap analysis.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Dictionary with current data state snapshot
    """
    from sqlalchemy import select, func
    from app.models import Asset

    # Get asset count
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    assets_count = result.scalar() or 0

    # Get completeness metrics
    completeness = await calculate_completeness_metrics(
        db, client_account_id, engagement_id
    )

    # Calculate overall coverage
    overall_coverage = (
        sum(completeness.values()) / len(completeness) if completeness else 0.0
    )

    return {
        "assets_count": assets_count,
        "coverage": overall_coverage,
        "completeness_by_category": completeness,
        "engagement_id": engagement_id,
        "client_account_id": client_account_id,
    }


async def convert_gap_analysis_to_response(
    gap_analysis_result: Dict[str, Any],
    db: AsyncSession,
    client_account_id: str,
    engagement_id: str,
):
    """
    Convert gap analysis results to API response format.

    Args:
        gap_analysis_result: Results from gap analysis tool
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        CollectionGapsResponse with prioritized gaps
    """
    from app.models.api.collection_gaps import CollectionGap, CollectionGapsResponse
    from sqlalchemy import select, func
    from app.models import Asset

    # Get total asset count for affected asset calculations
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    total_assets = result.scalar() or 1

    critical_gaps = []
    high_gaps = []
    optional_gaps = []

    # Extract missing fields by category
    missing_fields = gap_analysis_result.get("missing_fields_by_category", {})
    priorities = gap_analysis_result.get("priorities", {})

    # Create gap objects based on analysis results
    for category, fields in missing_fields.items():
        for field_name in fields:
            # Determine priority
            priority = "medium"  # default
            if field_name in priorities.get("critical", []):
                priority = "critical"
            elif field_name in priorities.get("high", []):
                priority = "high"
            elif field_name in priorities.get("medium", []):
                priority = "medium"
            else:
                priority = "optional"

            # Estimate affected assets (this could be made more sophisticated)
            affected_assets = int(
                total_assets * 0.3
            )  # Assume 30% of assets are affected by each gap

            gap = CollectionGap(
                category=category,
                field_name=field_name,
                description=f"{field_name.replace('_', ' ').title()} is not available for complete migration planning",
                priority=priority,
                affected_assets=affected_assets,
            )

            # Sort into priority buckets
            if priority == "critical":
                critical_gaps.append(gap)
            elif priority == "high":
                high_gaps.append(gap)
            else:
                optional_gaps.append(gap)

    return CollectionGapsResponse(
        critical=critical_gaps, high=high_gaps, optional=optional_gaps
    )
