"""
Canonical Application Bootstrap Service.

Creates real canonical applications from asset.application_name values
when canonical_applications table is empty for a tenant.

This implements the "assessment bootstrap" pattern - a lazy initialization
that creates the canonical app infrastructure on-demand when users first
access the assessment flow without having gone through bulk import.

Related: Bug #999, Bug #1195, Issue #1197, ADR-036
"""

import logging
import uuid as uuid_module
from collections import defaultdict
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset.models import Asset
from app.models.canonical_applications import (
    CanonicalApplication,
    CollectionFlowApplication,
)
from app.models.collection_flow.collection_flow_model import CollectionFlow
from app.models.collection_flow.schemas import AutomationTier, CollectionFlowStatus

logger = logging.getLogger(__name__)

# System bootstrap flow name - used for audit trail
SYSTEM_BOOTSTRAP_FLOW_NAME = "System Bootstrap - Assessment Initialization"


async def get_or_create_system_bootstrap_flow(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    user_id: UUID,
) -> CollectionFlow:
    """
    Get or create the "System Bootstrap" collection flow.

    This special flow is used as the FK reference for junction records
    created during assessment bootstrap. It satisfies the NOT NULL
    constraint on collection_flow_applications.collection_flow_id.

    Per Bug #999 data migration strategy.

    Args:
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID
        user_id: User ID for audit trail

    Returns:
        The system bootstrap CollectionFlow instance
    """
    # Check for existing bootstrap flow
    stmt = select(CollectionFlow).where(
        CollectionFlow.client_account_id == client_account_id,
        CollectionFlow.engagement_id == engagement_id,
        CollectionFlow.flow_name == SYSTEM_BOOTSTRAP_FLOW_NAME,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        logger.debug(
            f"Found existing system bootstrap flow: {existing.id} "
            f"for tenant {client_account_id}/{engagement_id}"
        )
        return existing

    # Create new bootstrap flow
    # Generate a single UUID for both flow_id and id (MFO two-table pattern)
    flow_uuid = uuid_module.uuid4()
    bootstrap_flow = CollectionFlow(
        id=flow_uuid,
        flow_id=flow_uuid,  # Per MFO pattern: flow_id == id for child flows
        flow_name=SYSTEM_BOOTSTRAP_FLOW_NAME,
        client_account_id=client_account_id,
        engagement_id=engagement_id,
        user_id=user_id,
        automation_tier=AutomationTier.TIER_1,  # Manual tier
        status=CollectionFlowStatus.COMPLETED,
        current_phase="finalization",
        progress_percentage=100.0,
        flow_metadata={
            "type": "system_bootstrap",
            "description": "Auto-created for canonical app bootstrap during assessment flow initialization",
            "created_by": "assessment_bootstrap_service",
        },
    )
    db.add(bootstrap_flow)
    await db.flush()  # Get ID without committing

    logger.info(
        f"Created system bootstrap flow: {bootstrap_flow.id} "
        f"for tenant {client_account_id}/{engagement_id}"
    )

    return bootstrap_flow


async def count_assets_with_application_names(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Count assets that have application_name values.

    Args:
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Count of assets with non-empty application_name
    """
    count_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
        Asset.application_name.isnot(None),
        Asset.application_name != "",
    )
    result = await db.execute(count_query)
    return result.scalar() or 0


async def get_canonical_apps_count(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
) -> int:
    """
    Count canonical applications for tenant.

    Args:
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID

    Returns:
        Count of canonical applications
    """
    count_query = select(func.count(CanonicalApplication.id)).where(
        CanonicalApplication.client_account_id == client_account_id,
        CanonicalApplication.engagement_id == engagement_id,
    )
    result = await db.execute(count_query)
    return result.scalar() or 0


async def bootstrap_canonical_applications_from_assets(
    db: AsyncSession,
    client_account_id: UUID,
    engagement_id: UUID,
    user_id: UUID,
) -> Tuple[int, int]:
    """
    Bootstrap canonical applications from assets when none exist.

    This function:
    1. Finds all distinct application_name values from assets table
    2. Creates CanonicalApplication records using find_or_create pattern
    3. Creates CollectionFlowApplication junction records
    4. Returns counts of created records

    Uses "System Bootstrap" collection flow for junction record FK constraint.

    IMPORTANT: This function is idempotent - running multiple times will not
    create duplicate canonical apps (due to unique constraint) or junction
    records (checked before creation).

    Args:
        db: Database session
        client_account_id: Tenant client account ID
        engagement_id: Tenant engagement ID
        user_id: User ID for audit trail

    Returns:
        Tuple of (canonical_apps_created, junction_records_created)
    """
    logger.info(
        f"[ISSUE-1197] Starting canonical app bootstrap for tenant "
        f"{client_account_id}/{engagement_id}"
    )

    # Step 1: Get all assets with application_name, grouped by name
    assets_query = select(Asset.id, Asset.application_name, Asset.name).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
        Asset.application_name.isnot(None),
        Asset.application_name != "",
    )
    result = await db.execute(assets_query)
    assets = result.all()

    if not assets:
        logger.info(
            f"[ISSUE-1197] No assets with application_name found for tenant "
            f"{client_account_id}/{engagement_id} - nothing to bootstrap"
        )
        return 0, 0

    # Group assets by application_name
    assets_by_app_name: Dict[str, List[Tuple[UUID, str]]] = defaultdict(list)
    for asset in assets:
        assets_by_app_name[asset.application_name].append((asset.id, asset.name))

    logger.info(
        f"[ISSUE-1197] Found {len(assets)} assets with "
        f"{len(assets_by_app_name)} unique application_name values"
    )

    # Step 2: Get or create system bootstrap flow for FK constraint
    bootstrap_flow = await get_or_create_system_bootstrap_flow(
        db, client_account_id, engagement_id, user_id
    )

    # Step 3: Create canonical apps and junction records
    canonical_apps_created = 0
    junction_records_created = 0

    for app_name, asset_list in assets_by_app_name.items():
        # Create or find canonical application using existing method with retry logic
        try:
            canonical_app, is_new, _ = (
                await CanonicalApplication.find_or_create_canonical(
                    db=db,
                    application_name=app_name,
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    user_id=user_id,
                    confidence_score=1.0,  # Direct match from asset data
                    is_verified=False,
                    verification_source="assessment_bootstrap",
                )
            )

            if is_new:
                canonical_apps_created += 1
                logger.debug(
                    f"[ISSUE-1197] Created canonical app: '{app_name}' (ID: {canonical_app.id})"
                )

            # Create junction records for all assets with this application_name
            for asset_id, asset_name in asset_list:
                # Check if junction record already exists (idempotency)
                existing_junction_query = select(CollectionFlowApplication.id).where(
                    CollectionFlowApplication.asset_id == asset_id,
                    CollectionFlowApplication.canonical_application_id
                    == canonical_app.id,
                    CollectionFlowApplication.client_account_id == client_account_id,
                    CollectionFlowApplication.engagement_id == engagement_id,
                )
                existing_result = await db.execute(existing_junction_query)
                if existing_result.scalar_one_or_none():
                    logger.debug(
                        f"[ISSUE-1197] Junction record already exists for "
                        f"asset {asset_id} → app {canonical_app.id}"
                    )
                    continue

                # Create new junction record
                junction = CollectionFlowApplication(
                    id=uuid_module.uuid4(),
                    collection_flow_id=bootstrap_flow.flow_id,
                    asset_id=asset_id,
                    canonical_application_id=canonical_app.id,
                    application_name=app_name,  # Legacy field for backward compatibility
                    client_account_id=client_account_id,
                    engagement_id=engagement_id,
                    deduplication_method="assessment_bootstrap",  # Audit trail
                    match_confidence=1.0,  # Exact match by application_name
                    collection_status="validated",
                )
                db.add(junction)
                junction_records_created += 1

                logger.debug(
                    f"[ISSUE-1197] Created junction: asset '{asset_name}' ({asset_id}) "
                    f"→ app '{app_name}' ({canonical_app.id})"
                )

        except Exception as e:
            logger.error(
                f"[ISSUE-1197] Failed to bootstrap canonical app '{app_name}': {e}",
                exc_info=True,
            )
            # Continue with other apps - don't fail entire bootstrap
            continue

    # Flush to ensure all records are written
    await db.flush()

    logger.info(
        f"[ISSUE-1197] Bootstrap complete for tenant {client_account_id}/{engagement_id}: "
        f"created {canonical_apps_created} canonical apps, "
        f"{junction_records_created} junction records"
    )

    return canonical_apps_created, junction_records_created


def get_bootstrap_guidance() -> Dict[str, Any]:
    """
    Get UI guidance message for when no applications can be bootstrapped.

    Returns:
        Guidance dict with message and suggested action
    """
    return {
        "message": (
            "No applications found. Assets need application names assigned "
            "through Collection Flow or bulk import before starting assessment."
        ),
        "action": "collection_flow",
        "action_label": "Start Collection Flow",
        "action_url": "/collection",
    }
