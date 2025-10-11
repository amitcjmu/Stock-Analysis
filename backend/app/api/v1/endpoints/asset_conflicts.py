"""
Asset Conflict Resolution API Endpoints.

KEY CHANGE: No /detect endpoint - detection happens in executor.
Only expose /list and /resolve-bulk for UI interaction.

CC: User-driven conflict resolution during discovery flow
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.api.v1.auth.auth_utils import get_current_user
from app.models.client_account import User
from app.models.asset import Asset
from app.models.asset_conflict_resolution import AssetConflictResolution
from app.schemas.asset_conflict import (
    AssetConflictDetail,
    BulkConflictResolutionRequest,
    ConflictResolutionResponse,
)
from app.services.asset_service import AssetService
from app.services.asset_service.deduplication import (
    overwrite_asset,
    DEFAULT_ALLOWED_MERGE_FIELDS,
    NEVER_MERGE_FIELDS,
)

router = APIRouter(prefix="/asset-conflicts", tags=["asset-conflicts"])
logger = logging.getLogger(__name__)


@router.get("/list", response_model=List[AssetConflictDetail])
async def list_pending_conflicts(
    flow_id: UUID,  # Use flow_id to derive tenant context
    data_import_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # AUTH REQUIRED
    request_context: RequestContext = Depends(get_request_context),  # TENANT CONTEXT
):
    """
    List all pending conflicts for a tenant+engagement.

    NEW: Uses RequestContext dependency for tenant scoping (per GPT-5 feedback)
    - Eliminates custom x-tenant-id header
    - Reuses existing auth infrastructure
    - Automatically validates tenant access

    Query Parameters:
        flow_id: Discovery flow UUID (used to derive tenant context)
        data_import_id: Filter by specific data import (optional)

    Returns:
        List of AssetConflictDetail with side-by-side comparison data
    """
    # Extract tenant IDs from RequestContext (already validated by dependency)
    client_account_id = UUID(request_context.client_account_id)
    engagement_id = UUID(request_context.engagement_id)

    # Query pending conflicts for this context
    stmt = select(AssetConflictResolution).where(
        and_(
            AssetConflictResolution.client_account_id == client_account_id,
            AssetConflictResolution.engagement_id == engagement_id,
            AssetConflictResolution.discovery_flow_id == flow_id,
            AssetConflictResolution.resolution_status == "pending",
        )
    )

    if data_import_id:
        stmt = stmt.where(AssetConflictResolution.data_import_id == data_import_id)

    result = await db.execute(stmt)
    conflicts = result.scalars().all()

    logger.info(
        f"📋 Retrieved {len(conflicts)} pending conflicts for "
        f"client={client_account_id}, engagement={engagement_id}"
    )

    return [
        AssetConflictDetail(
            conflict_id=c.id,
            conflict_type=c.conflict_type,
            conflict_key=c.conflict_key,
            existing_asset=c.existing_asset_snapshot,
            new_asset=c.new_asset_data,
        )
        for c in conflicts
    ]


@router.post("/resolve-bulk", response_model=ConflictResolutionResponse)
async def resolve_conflicts_bulk(  # noqa: C901
    request: BulkConflictResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),  # AUTH REQUIRED
    request_context: RequestContext = Depends(get_request_context),  # TENANT CONTEXT
):
    """
    Apply user's conflict resolution choices in bulk.

    NEW FEATURES:
    - resolved_by extracted from authenticated user context (not payload)
    - "replace_with_new" implemented as UPDATE (not delete+create)
    - Field merge allowlist validation
    - Multi-tenant access control

    Resolution Actions:
        keep_existing: Do nothing, existing asset unchanged
        replace_with_new: UPDATE existing asset with new data (preserves FKs)
        merge: Update specific fields based on user selections

    Returns:
        ConflictResolutionResponse with success count and errors
    """
    resolved_count = 0
    errors = []

    for resolution in request.resolutions:
        try:
            conflict_id = resolution.conflict_id
            action = resolution.resolution_action
            merge_selections = resolution.merge_field_selections or {}

            # Fetch conflict record
            conflict = await db.get(AssetConflictResolution, conflict_id)
            if not conflict:
                errors.append(f"Conflict {conflict_id} not found")
                continue

            # Validate tenant access via RequestContext (auto-validated by dependency)
            if conflict.client_account_id != UUID(request_context.client_account_id):
                errors.append(f"Conflict {conflict_id}: tenant access denied")
                continue

            # Validate conflict is still pending
            if conflict.resolution_status != "pending":
                errors.append(
                    f"Conflict {conflict_id} already resolved with action: "
                    f"{conflict.resolution_action}"
                )
                continue

            # Execute resolution based on action
            if action == "keep_existing":
                # Do nothing - existing asset stays unchanged
                logger.info(f"✅ Keeping existing asset for conflict {conflict_id}")

            elif action == "replace_with_new":
                # NEW: UPDATE existing asset (not delete+create)
                # Preserves FK relationships, audit history, and dependencies
                existing_asset = await db.get(Asset, conflict.existing_asset_id)
                if not existing_asset:
                    errors.append(
                        f"Conflict {conflict_id}: existing asset {conflict.existing_asset_id} not found"
                    )
                    continue

                # Use overwrite_asset from service (respects field allowlist)
                # NEW: Pass real RequestContext (per GPT-5 feedback - never pass None)
                asset_service = AssetService(db, request_context)
                await overwrite_asset(
                    asset_service,
                    existing_asset,
                    conflict.new_asset_data,
                    allowed_merge_fields=DEFAULT_ALLOWED_MERGE_FIELDS,
                )

                logger.info(
                    f"✅ Replaced existing asset {existing_asset.name} "
                    f"with new data for conflict {conflict_id}"
                )

            elif action == "merge":
                # Validate merge_field_selections against allowlist
                invalid_fields = (
                    set(merge_selections.keys()) - DEFAULT_ALLOWED_MERGE_FIELDS
                )
                protected_fields = set(merge_selections.keys()) & NEVER_MERGE_FIELDS

                if invalid_fields:
                    errors.append(
                        f"Conflict {conflict_id}: invalid merge fields: {invalid_fields}"
                    )
                    continue

                if protected_fields:
                    errors.append(
                        f"Conflict {conflict_id}: cannot merge protected fields: {protected_fields}"
                    )
                    continue

                # Update existing asset with selected fields
                existing_asset = await db.get(Asset, conflict.existing_asset_id)
                if not existing_asset:
                    errors.append(
                        f"Conflict {conflict_id}: existing asset {conflict.existing_asset_id} not found"
                    )
                    continue

                # Apply merge selections
                for field_name, source in merge_selections.items():
                    if source == "new" and field_name in conflict.new_asset_data:
                        setattr(
                            existing_asset,
                            field_name,
                            conflict.new_asset_data[field_name],
                        )

                existing_asset.updated_at = datetime.utcnow()

                logger.info(
                    f"✅ Merged {len(merge_selections)} fields for "
                    f"asset {existing_asset.name} (conflict {conflict_id})"
                )

            # Mark conflict as resolved
            conflict.resolution_status = "resolved"
            conflict.resolution_action = action
            conflict.merge_field_selections = (
                merge_selections if action == "merge" else None
            )
            conflict.resolved_by = current_user.id  # FROM AUTH CONTEXT
            conflict.resolved_at = datetime.utcnow()

            resolved_count += 1

        except Exception as e:
            error_msg = f"Conflict {resolution.conflict_id}: {str(e)}"
            logger.error(f"❌ Resolution failed: {error_msg}")
            errors.append(error_msg)

    # Flush changes (caller commits per ADR-012)
    await db.flush()

    logger.info(
        f"✅ Resolved {resolved_count}/{len(request.resolutions)} conflicts, "
        f"{len(errors)} errors"
    )

    return ConflictResolutionResponse(
        resolved_count=resolved_count,
        total_requested=len(request.resolutions),
        errors=errors if errors else None,
    )
