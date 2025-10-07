"""
Collection Flow Bulk Import Handler
Handles bulk data import for Collection flows through CSV upload.
Processes each row through the Collection questionnaire system.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import COLLECTION_CREATE_ROLES, require_role
from app.models import User
from app.models.collection_flow import (
    CollectionFlow,
    CollectionFlowStatus,
    CollectionPhase,
)
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse
from app.config.asset_mappings import (
    create_or_update_asset,
    map_csv_to_questionnaire as config_map_csv_to_questionnaire,
)

# Import removed - unused in this module

logger = logging.getLogger(__name__)


async def _validate_collection_flow_for_import(
    flow_id: str, db: AsyncSession, context: RequestContext
) -> CollectionFlow:
    """Validate that the collection flow exists and is in correct state for import."""
    flow_result = await db.execute(
        select(CollectionFlow).where(
            CollectionFlow.flow_id == uuid.UUID(flow_id),
            CollectionFlow.engagement_id == context.engagement_id,
        )
    )
    collection_flow = flow_result.scalar_one_or_none()

    if not collection_flow:
        raise HTTPException(
            status_code=404, detail=f"Collection flow {flow_id} not found"
        )

    # Check flow is in a state that allows bulk import
    # Per ADR-012: Use lifecycle states instead of phase values
    allowed_statuses = [
        CollectionFlowStatus.INITIALIZED.value,
        CollectionFlowStatus.RUNNING.value,
        CollectionFlowStatus.PAUSED.value,
    ]

    if collection_flow.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Collection flow is in {collection_flow.status} state. "
            f"Bulk import is only allowed in: {', '.join(allowed_statuses)}",
        )

    return collection_flow


async def _process_csv_rows(
    csv_data: List[Dict[str, Any]],
    asset_type: str,
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> tuple[int, List[Dict], List[Any]]:
    """Process CSV rows and create assets."""
    processed_count = 0
    errors = []
    created_assets = []

    for row_idx, row_data in enumerate(csv_data):
        try:
            # Map CSV row to questionnaire format
            questionnaire_data = config_map_csv_to_questionnaire(row_data, asset_type)

            # Create/update asset based on type
            asset = await create_or_update_asset(
                asset_type=asset_type,
                data=questionnaire_data,
                db=db,
                context=context,
            )

            if asset:
                created_assets.append(asset)

                # Store questionnaire response for this asset
                response = CollectionQuestionnaireResponse(
                    id=uuid.uuid4(),
                    flow_id=uuid.UUID(flow_id),
                    questionnaire_id=f"bulk_import_{asset_type}",
                    asset_id=asset.id,
                    asset_type=asset_type,
                    responses=questionnaire_data,
                    submitted_by=current_user.id,
                    submitted_at=datetime.now(timezone.utc),
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                )
                db.add(response)
                processed_count += 1

        except Exception as e:
            errors.append({"row": row_idx + 1, "error": str(e), "data": row_data})
            logger.error(f"Error processing row {row_idx + 1}: {e}")

    return processed_count, errors, created_assets


def _update_flow_after_import(
    collection_flow: CollectionFlow,
    asset_type: str,
    processed_count: int,
    created_assets: List[Any],
    current_user: User,
):
    """Update flow configuration and status after successful import."""
    if processed_count == 0:
        return

    # Update flow configuration
    if not collection_flow.collection_config:
        collection_flow.collection_config = {}

    collection_flow.collection_config["bulk_import"] = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "asset_type": asset_type,
        "asset_count": processed_count,
        "imported_by": str(current_user.id),
    }

    # Add imported asset IDs to flow configuration
    if "selected_assets" not in collection_flow.collection_config:
        collection_flow.collection_config["selected_assets"] = {}

    asset_key = f"{asset_type}_ids"
    if asset_key not in collection_flow.collection_config["selected_assets"]:
        collection_flow.collection_config["selected_assets"][asset_key] = []

    # Use set to prevent duplicate asset IDs before extending
    existing_ids = set(collection_flow.collection_config["selected_assets"][asset_key])
    new_ids = [
        str(asset.id) for asset in created_assets if str(asset.id) not in existing_ids
    ]
    collection_flow.collection_config["selected_assets"][asset_key].extend(new_ids)

    # Update flow status after successful import
    # Per ADR-012: Status reflects lifecycle, not phase
    # Move from INITIALIZED or PAUSED -> RUNNING after successful import
    if collection_flow.status in [
        CollectionFlowStatus.INITIALIZED.value,
        CollectionFlowStatus.PAUSED.value,
    ]:
        collection_flow.status = CollectionFlowStatus.RUNNING.value

    # Update phase to GAP_ANALYSIS (phase reflects operational state)
    collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
    collection_flow.updated_at = datetime.now(timezone.utc)


async def _trigger_gap_analysis_if_needed(
    flow_id: str,
    created_assets: List[Any],
    asset_type: str,
    processed_count: int,
    db: AsyncSession,
    context: RequestContext,
) -> bool:
    """Trigger gap analysis if assets were imported.

    This function is called after the import transaction is committed,
    so gap analysis failure won't affect the import success.
    """
    if processed_count == 0:
        return False

    try:
        # Trigger gap analysis through MFO
        # Note: This function may not exist yet, but the try/except ensures graceful handling
        from app.api.v1.endpoints import collection_utils

        # Check if the function exists before calling
        if hasattr(collection_utils, "trigger_gap_analysis"):
            gap_result = await collection_utils.trigger_gap_analysis(
                flow_id=flow_id,
                asset_ids=[str(asset.id) for asset in created_assets],
                asset_type=asset_type,
                db=db,
                context=context,
            )
            gap_analysis_triggered = bool(gap_result)
            logger.info(f"Gap analysis triggered for flow {flow_id}: {gap_result}")
            return gap_analysis_triggered
        else:
            logger.warning(
                f"Gap analysis function not available, skipping for flow {flow_id}"
            )
            return False

    except Exception as e:
        logger.error(f"Failed to trigger gap analysis for flow {flow_id}: {e}")
        # Don't fail the import if gap analysis fails - import has already succeeded
        return False


async def process_bulk_import(
    flow_id: str,
    file_path: Optional[str],
    csv_data: Optional[List[Dict[str, Any]]],
    asset_type: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Process bulk CSV import for Collection flow.

    This function orchestrates the bulk import process by:
    1. Validating the Collection flow exists and is in correct state
    2. Processing each row through the Collection questionnaire system
    3. Creating/updating assets in the database
    4. Updating flow configuration and status
    5. Triggering gap analysis for all imported assets

    All database operations are performed within a single atomic transaction
    to ensure consistency. Gap analysis is triggered after successful commit.

    Args:
        flow_id: The Collection flow ID to import data into
        file_path: Path to the uploaded CSV file (unused - for future compatibility)
        csv_data: CSV data to import
        asset_type: Type of assets being imported
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dict with import results including processed count and any errors
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "bulk import collection data")

    try:
        # 1. Validate Collection flow (outside transaction for early validation)
        collection_flow = await _validate_collection_flow_for_import(
            flow_id, db, context
        )

        # 2. Validate CSV data
        if csv_data is None:
            raise HTTPException(
                status_code=400, detail="csv_data must be provided for bulk import"
            )

        if not csv_data:
            return {
                "success": False,
                "errors": ["No data provided for import"],
                "warnings": [],
            }

        # Atomic transaction for all database operations
        async with db.begin():
            # 3. Process CSV rows and create assets
            processed_count, errors, created_assets = await _process_csv_rows(
                csv_data, asset_type, flow_id, db, current_user, context
            )

            # 4. Update flow configuration and status
            _update_flow_after_import(
                collection_flow,
                asset_type,
                processed_count,
                created_assets,
                current_user,
            )

            # Flush to make changes available for gap analysis trigger
            await db.flush()

        # Transaction committed successfully - now trigger gap analysis
        # Gap analysis is triggered after commit to avoid transaction boundary issues
        # If gap analysis fails, the import has already succeeded
        gap_analysis_triggered = await _trigger_gap_analysis_if_needed(
            flow_id, created_assets, asset_type, processed_count, db, context
        )

        logger.info(
            f"Bulk import completed for flow {flow_id}: "
            f"{processed_count} {asset_type} processed, {len(errors)} errors"
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "asset_type": asset_type,
            "processed_count": processed_count,
            "created_assets": [str(asset.id) for asset in created_assets],
            "errors": errors,
            "gap_analysis_triggered": gap_analysis_triggered,
            "message": f"Successfully imported {processed_count} {asset_type}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk import failed for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk import failed: {str(e)}")


# Legacy map_csv_to_questionnaire function - replaced by config-driven approach
# Kept for backward compatibility if needed
def map_csv_to_questionnaire(
    csv_row: Dict[str, Any], asset_type: str
) -> Dict[str, Any]:
    """Legacy CSV to questionnaire mapping - use config_map_csv_to_questionnaire instead.

    This function is deprecated in favor of the data-driven approach in
    app.config.asset_mappings.map_csv_to_questionnaire.
    """
    # Delegate to the new configuration-driven implementation
    return config_map_csv_to_questionnaire(csv_row, asset_type)
