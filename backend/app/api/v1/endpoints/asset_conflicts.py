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
from app.models.discovery_flow import DiscoveryFlow
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

router = APIRouter(prefix="/asset-conflicts")
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

    # SECURITY: Verify flow ownership before accessing conflicts (IDOR prevention)
    flow_check = await db.execute(
        select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,  # CC: Use flow_id column, not PK id
                DiscoveryFlow.client_account_id == client_account_id,
                DiscoveryFlow.engagement_id == engagement_id,
            )
        )
    )
    flow = flow_check.scalar_one_or_none()

    if not flow:
        from fastapi import HTTPException, status

        logger.warning(
            f"⚠️ IDOR attempt: User {current_user.id} tried to access "
            f"flow {flow_id} not in their tenant context"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Flow {flow_id} not found in your account context",
        )

    # Query pending conflicts for this context
    # CC: Use flow.id (PK) to match conflict.discovery_flow_id FK relationship
    stmt = select(AssetConflictResolution).where(
        and_(
            AssetConflictResolution.client_account_id == client_account_id,
            AssetConflictResolution.engagement_id == engagement_id,
            AssetConflictResolution.discovery_flow_id == flow.id,
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

    # SECURITY: Validate all conflicts belong to same flow and flow has pending conflicts
    # Per Qodo Bot feedback: Prevent targeted updates if conflict IDs are leaked
    if not request.resolutions:
        return ConflictResolutionResponse(
            resolved_count=0,
            total_requested=0,
            errors=["No resolutions provided"],
        )

    # Extract tenant IDs from RequestContext
    client_account_id = UUID(request_context.client_account_id)
    engagement_id = UUID(request_context.engagement_id)

    # Fetch all conflicts to validate flow association
    conflict_ids = [r.conflict_id for r in request.resolutions]
    conflicts_query = select(AssetConflictResolution).where(
        and_(
            AssetConflictResolution.id.in_(conflict_ids),
            AssetConflictResolution.client_account_id == client_account_id,
            AssetConflictResolution.engagement_id == engagement_id,
        )
    )
    conflicts_result = await db.execute(conflicts_query)
    conflicts_batch = conflicts_result.scalars().all()

    # Check if all conflicts were found
    if len(conflicts_batch) != len(conflict_ids):
        found_ids = {str(c.id) for c in conflicts_batch}
        missing_ids = set(str(cid) for cid in conflict_ids) - found_ids
        return ConflictResolutionResponse(
            resolved_count=0,
            total_requested=len(request.resolutions),
            errors=[f"Conflicts not found or access denied: {', '.join(missing_ids)}"],
        )

    # Validate all conflicts belong to the same flow
    flow_ids = {c.discovery_flow_id for c in conflicts_batch}
    if len(flow_ids) != 1:
        return ConflictResolutionResponse(
            resolved_count=0,
            total_requested=len(request.resolutions),
            errors=[
                f"Conflicts belong to multiple flows ({len(flow_ids)} flows). "
                "All conflicts must belong to the same discovery flow."
            ],
        )

    flow_id = flow_ids.pop()

    # Verify flow exists and is waiting for conflict resolution
    flow_query = select(DiscoveryFlow).where(
        and_(
            DiscoveryFlow.id
            == flow_id,  # CC: Here we use id (PK) because it comes from conflict.discovery_flow_id
            DiscoveryFlow.client_account_id == client_account_id,
            DiscoveryFlow.engagement_id == engagement_id,
        )
    )
    flow_result = await db.execute(flow_query)
    flow = flow_result.scalar_one_or_none()

    if not flow:
        logger.warning(
            f"⚠️ Flow association validation failed: Flow {flow_id} not found "
            f"for user {current_user.id}"
        )
        return ConflictResolutionResponse(
            resolved_count=0,
            total_requested=len(request.resolutions),
            errors=[f"Flow {flow_id} not found in your account context"],
        )

    # CC FIX: Allow conflict resolution for flows with conflict_resolution_pending flag
    # regardless of status (assessment_ready, paused, etc.). The conflict_resolution_pending
    # flag is the authoritative indicator, not the status field.
    # Check if flow still has conflict_resolution_pending flag
    conflict_pending = (
        flow.phase_state and flow.phase_state.get("conflict_resolution_pending") is True
    )
    if not conflict_pending:
        logger.warning(
            f"⚠️ Flow {flow_id} no longer has conflict_resolution_pending flag"
        )
        return ConflictResolutionResponse(
            resolved_count=0,
            total_requested=len(request.resolutions),
            errors=[
                f"Flow {flow_id} is no longer waiting for conflict resolution. "
                "Conflicts may have already been resolved."
            ],
        )

    logger.info(
        f"✅ Flow association validated: {len(conflict_ids)} conflicts belong to "
        f"flow {flow_id} (status: {flow.status}, conflict_resolution_pending: true)"
    )

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

                # CC FIX: Associate asset with current flow after replacement
                # This ensures the flow has assets even when resolving conflicts
                existing_asset.discovery_flow_id = flow.id
                existing_asset.updated_at = datetime.utcnow()

                logger.info(
                    f"✅ Replaced existing asset {existing_asset.name} "
                    f"with new data and associated with flow {flow.flow_id} (conflict {conflict_id})"
                )

            elif action == "merge":
                # VALIDATION: Reject empty merge selections (Qodo Bot feedback)
                # Empty dict would result in no-op merge but conflict marked as resolved
                if not merge_selections:
                    errors.append(
                        f"Conflict {conflict_id}: merge action requires at least one field selection. "
                        "Use 'keep_existing' action if no changes are needed."
                    )
                    continue

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
                        new_value = conflict.new_asset_data[field_name]

                        # SPECIAL HANDLING: Merge dict fields like custom_attributes (Qodo Bot feedback)
                        # Prevents data loss by merging dictionaries instead of overwriting
                        if field_name == "custom_attributes" and isinstance(
                            new_value, dict
                        ):
                            existing_value = getattr(existing_asset, field_name, None)
                            if isinstance(existing_value, dict):
                                # Merge dicts: new values override existing, but keep other existing keys
                                merged_value = {**existing_value, **new_value}
                                setattr(existing_asset, field_name, merged_value)
                                logger.debug(
                                    f"Merged custom_attributes dict for asset "
                                    f"{existing_asset.name}: {len(existing_value)} existing + "
                                    f"{len(new_value)} new = {len(merged_value)} total keys"
                                )
                            else:
                                # Existing value is not a dict, just replace
                                setattr(existing_asset, field_name, new_value)
                        else:
                            # Normal field update - replace value
                            setattr(existing_asset, field_name, new_value)

                # CC FIX: Associate asset with current flow after merge
                # This ensures the flow has assets even when resolving conflicts
                existing_asset.discovery_flow_id = flow.id
                existing_asset.updated_at = datetime.utcnow()

                logger.info(
                    f"✅ Merged {len(merge_selections)} fields for "
                    f"asset {existing_asset.name} and associated with flow {flow.flow_id} (conflict {conflict_id})"
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

    # CC: CRITICAL - Check if ALL conflicts for this flow are now resolved
    # If yes, clear conflict_resolution_pending flag and resume flow
    if resolved_count > 0:
        # Query remaining pending conflicts for this flow
        remaining_conflicts_query = select(AssetConflictResolution).where(
            and_(
                AssetConflictResolution.discovery_flow_id == flow.id,
                AssetConflictResolution.resolution_status == "pending",
            )
        )
        remaining_result = await db.execute(remaining_conflicts_query)
        remaining_conflicts = remaining_result.scalars().all()

        if len(remaining_conflicts) == 0:
            # All conflicts resolved - resume flow AND mark as completed
            from app.repositories.discovery_flow_repository import (
                DiscoveryFlowRepository,
            )
            from app.services.crewai_flows.handlers.phase_executors.asset_inventory_executor.commands import (
                persist_asset_inventory_completion,
            )

            discovery_repo = DiscoveryFlowRepository(
                db, str(client_account_id), str(engagement_id)
            )

            # Step 1: Clear conflict resolution flags (removes phase_state flags, sets status='active')
            await discovery_repo.clear_conflict_resolution_pending(flow.flow_id)

            # Step 2: Mark flow as completed (since asset_inventory is the FINAL phase)
            # CC CRITICAL: asset_inventory is the last phase of discovery flow
            # After all conflicts resolved, the flow should be marked as "completed"
            await persist_asset_inventory_completion(
                db,
                flow_id=str(flow.flow_id),
                client_account_id=str(client_account_id),
                engagement_id=str(engagement_id),
                mark_flow_complete=True,  # ✅ Mark discovery flow as completed
            )

            await db.commit()  # Commit conflict resolutions + flow completion

            logger.info(
                f"🎉 All conflicts resolved for flow {flow.flow_id} - flow marked as COMPLETED"
            )
        else:
            logger.info(
                f"⏳ {len(remaining_conflicts)} conflicts still pending for flow {flow.flow_id}"
            )
            await db.commit()  # Commit partial resolutions
    else:
        await db.commit()  # Commit even if no resolutions succeeded

    return ConflictResolutionResponse(
        resolved_count=resolved_count,
        total_requested=len(request.resolutions),
        errors=errors if errors else None,
    )
