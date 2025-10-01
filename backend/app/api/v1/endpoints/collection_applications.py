"""Collection Application Selection endpoints.

This module handles application selection for collection flows,
enabling targeted questionnaire generation based on selected applications.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.models import User
from app.schemas.collection_flow import (
    CollectionApplicationSelectionRequest,
)
from app.api.v1.endpoints import collection_validators
from app.services.master_flow_sync_service import MasterFlowSyncService

logger = logging.getLogger(__name__)


async def update_flow_applications(
    flow_id: str,
    request_data: CollectionApplicationSelectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Update collection flow with selected applications for questionnaire generation.

    This endpoint allows users to specify which applications should be included
    in a collection flow, enabling targeted questionnaire generation and gap analysis.

    SECURITY: Validates that all selected applications belong to the current user's engagement.

    FIXED (v3 Diagnostic Report - Correction 1):
    - Loads Asset/Application objects to get names (not pass IDs directly)
    - Uses the deduplication service with application names
    - Creates CollectionFlowApplication records in normalized tables
    - Maintains both JSON config AND normalized table consistency
    - Triggers MFO execution if master_flow_id exists
    - Uses proper tenant scoping and atomic transactions

    Args:
        flow_id: The collection flow ID to update
        request_data: Validated request containing selected_application_ids and optional action

    Returns:
        Dict indicating success/failure and updated flow status

    Raises:
        HTTPException: If applications don't belong to the engagement or validation fails
    """
    # Use proper transaction management without nested contexts
    try:
        # DEBUG LOGGING: Log raw request data received
        logger.debug(
            f"update_flow_applications called - Flow ID: {flow_id}, "
            f"User ID: {current_user.id}, Engagement ID: {context.engagement_id}, "
            f"Raw request data: {request_data.dict()}"
        )

        # Extract validated data from Pydantic model
        selected_application_ids = request_data.selected_application_ids
        action = request_data.action

        # DEBUG LOGGING: Log parsed application_ids after validation
        logger.debug(
            f"Parsed application IDs after initial extraction - "
            f"Count: {len(selected_application_ids)}, IDs: {selected_application_ids}, "
            f"Action: {action}"
        )

        # CC: Normalize and deduplicate application IDs while preserving order
        normalized_ids = []
        seen_ids = set()
        for app_id in selected_application_ids:
            # Validate non-empty strings
            if not app_id or not isinstance(app_id, str) or not app_id.strip():
                logger.warning(
                    f"Skipping invalid application ID: {repr(app_id)} for flow {flow_id}"
                )
                continue

            normalized_id = app_id.strip()
            if normalized_id not in seen_ids:
                normalized_ids.append(normalized_id)
                seen_ids.add(normalized_id)

        # DEBUG LOGGING: Log normalized application IDs after deduplication
        logger.debug(
            f"Normalized application IDs after deduplication - "
            f"Original count: {len(selected_application_ids)}, "
            f"Normalized count: {len(normalized_ids)}, "
            f"Normalized IDs: {normalized_ids}"
        )

        if not normalized_ids:
            logger.warning(f"No valid application IDs provided for flow {flow_id}")
            raise HTTPException(
                status_code=400,
                detail="No valid application IDs provided. Please select at least one valid application.",
            )

        # SECURITY VALIDATION: Validate that all applications belong to this engagement
        logger.info(
            f"Validating {len(normalized_ids)} applications for engagement {context.engagement_id}"
        )

        try:
            validated_applications = (
                await collection_validators.validate_applications_exist(
                    db, normalized_ids, context.engagement_id
                )
            )
            logger.info(
                f"Successfully validated {len(validated_applications)} applications for collection flow {flow_id}"
            )
        except Exception as validation_error:
            logger.warning(
                f"Application validation failed for flow {flow_id}: validation error occurred"
            )
            # CC: Check if it's a validation failure vs permission issue
            error_msg = str(validation_error).lower()
            if (
                "engagement" in error_msg
                or "permission" in error_msg
                or "authorization" in error_msg
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Authorization failed: Some applications don't belong to your engagement.",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Validation failed: Some selected applications are invalid or not found.",
                )

        # Load the collection flow first (with tenant scoping)
        from sqlalchemy import select, and_
        from app.models.collection_flow import CollectionFlow

        flow_result = await db.execute(
            select(CollectionFlow)
            .where(CollectionFlow.flow_id == flow_id)
            .where(CollectionFlow.engagement_id == context.engagement_id)
            .where(CollectionFlow.client_account_id == context.client_account_id)
        )
        collection_flow = flow_result.scalar_one_or_none()
        if not collection_flow:
            raise HTTPException(404, "Collection flow not found")

        logger.info(
            f"Updating collection flow {flow_id} with {len(normalized_ids)} applications"
        )

        # Update JSON config first (preserve existing settings)
        existing_config = collection_flow.collection_config or {}
        merged_config = existing_config.copy()
        merged_config.update(
            {
                "selected_application_ids": normalized_ids,
                "has_applications": True,
                "application_count": len(normalized_ids),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "action": action,
            }
        )
        collection_flow.collection_config = merged_config

        # Flush to make sure flow updates are available
        await db.flush()

        # CC: Use deduplication service to populate normalized tables
        from app.models.asset import Asset
        from app.models.canonical_applications.collection_flow_app import (
            CollectionFlowApplication,
        )
        from app.services.application_deduplication_service import (
            create_deduplication_service,
        )

        processed_count = 0
        application_details = []
        deduplication_results = []

        # Initialize deduplication service
        dedup_service = create_deduplication_service()

        for asset_id in normalized_ids:
            try:
                # Load asset with tenant scoping
                asset = await db.scalar(
                    select(Asset).where(
                        and_(
                            Asset.id == asset_id,
                            Asset.client_account_id == context.client_account_id,
                            Asset.engagement_id == context.engagement_id,
                        )
                    )
                )
                if not asset:
                    logger.warning(f"Asset not found or out of scope: {asset_id}")
                    continue

                # Get application name (prefer name, fallback to application_name)
                application_name = asset.name or asset.application_name
                if not application_name:
                    logger.warning(f"Asset {asset_id} has no name or application_name")
                    continue

                # Run deduplication service to create normalized records
                try:
                    # CC: Convert string IDs to UUID objects for deduplication service
                    import uuid as uuid_lib

                    client_uuid = (
                        uuid_lib.UUID(context.client_account_id)
                        if context.client_account_id
                        else None
                    )
                    engagement_uuid = (
                        uuid_lib.UUID(context.engagement_id)
                        if context.engagement_id
                        else None
                    )

                    dedup_result = await dedup_service.deduplicate_application(
                        db=db,
                        application_name=application_name,
                        client_account_id=client_uuid,
                        engagement_id=engagement_uuid,
                        user_id=current_user.id,
                        collection_flow_id=collection_flow.id,
                        additional_metadata={
                            "asset_id": str(asset_id),
                            "environment": getattr(asset, "environment", "unknown"),
                            "source": "collection_flow_selection",
                        },
                    )

                    # Extract fields safely with null checks
                    canonical_app_id = getattr(
                        getattr(dedup_result, "canonical_application", None), "id", None
                    )
                    name_variant_id = getattr(
                        getattr(dedup_result, "name_variant", None), "id", None
                    )
                    match_method = getattr(dedup_result, "match_method", None)
                    similarity = getattr(dedup_result, "similarity_score", None)

                    # CC: Create CollectionFlowApplication record even for non-application assets
                    # or when canonical deduplication fails, to ensure all selected assets are tracked
                    if not canonical_app_id:
                        logger.warning(
                            f"No canonical application ID for {application_name} (asset type: {getattr(asset, 'asset_type', 'unknown')}), "
                            f"creating CollectionFlowApplication record without canonical reference"
                        )

                    # CRITICAL: Create CollectionFlowApplication record for ALL asset types
                    # This was missing and causing no records in collection_flow_applications table
                    collection_flow_app = CollectionFlowApplication(
                        collection_flow_id=collection_flow.id,  # FIXED: Use .id (PK) not .flow_id
                        asset_id=asset_id,
                        application_name=application_name,
                        canonical_application_id=canonical_app_id,
                        name_variant_id=name_variant_id,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id,
                        deduplication_method=getattr(match_method, "value", None),
                        match_confidence=similarity,
                        collection_status="selected",
                        discovery_data_snapshot={
                            "asset_id": str(asset_id),
                            "environment": getattr(asset, "environment", "unknown"),
                            "source": "collection_flow_selection",
                            "selected_at": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    db.add(collection_flow_app)
                    logger.info(
                        f"Created CollectionFlowApplication record for {application_name}"
                    )

                    # Also update asset table with collection reference if needed
                    asset.collection_flow_id = (
                        collection_flow.id
                    )  # FIXED: Use .id (PK) not .flow_id
                    asset.updated_at = datetime.now(timezone.utc)
                    db.add(asset)  # Persist asset FK update

                    # Flush to catch FK integrity issues early
                    await db.flush()

                    # CRITICAL FIX: Add to results BEFORE the except block
                    deduplication_results.append(
                        {
                            "asset_id": str(asset_id),
                            "canonical_application_id": str(canonical_app_id),
                            "application_name": application_name,
                            "match_method": getattr(match_method, "value", "unknown"),
                            "similarity_score": similarity if similarity else 0.0,
                            "confidence_score": getattr(
                                dedup_result, "confidence_score", 0.0
                            ),
                            "is_new_canonical": getattr(
                                dedup_result, "is_new_canonical", False
                            ),
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                    logger.info(
                        f"Successfully deduplicated application '{application_name}' -> "
                        f"canonical app ID: {canonical_app_id} "
                        f"(method: {getattr(match_method, 'value', 'unknown')}, score: {similarity if similarity else 0.0:.3f})"
                    )

                except Exception as dedup_error:
                    logger.error(
                        f"Deduplication failed for '{application_name}': {str(dedup_error)}"
                    )
                    # Continue processing other applications even if one fails
                    continue

                # Store application details for backward compatibility
                application_details.append(
                    {
                        "asset_id": asset_id,
                        "application_name": application_name,
                        "environment": getattr(asset, "environment", "unknown"),
                        "selected_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                processed_count += 1
                logger.info(f"Successfully processed application: {application_name}")

            except Exception as e:
                logger.error(f"Failed to process asset {asset_id}: {str(e)}")
                continue

        # Update collection config with application details and deduplication results
        merged_config.update(
            {
                "application_details": application_details,
                "deduplication_results": deduplication_results,
                "processed_application_count": processed_count,
                "normalized_records_created": len(deduplication_results),
            }
        )
        collection_flow.collection_config = merged_config

        logger.info(
            f"Successfully processed {processed_count}/{len(normalized_ids)} applications, "
            f"created {len(deduplication_results)} normalized records"
        )

        # DEBUG LOGGING: Log database update attempt
        logger.debug(
            f"Attempting database commit for flow {flow_id} - "
            f"Processed applications: {processed_count}, "
            f"Normalized records: {len(deduplication_results)}"
        )

        # Commit all changes up to this point
        await db.commit()

        # DEBUG LOGGING: Log successful database update
        logger.debug(
            f"Database update successful for flow {flow_id} - "
            f"Collection config updated, {processed_count} applications processed, "
            f"{len(deduplication_results)} normalized records created"
        )

        # Transition to GAP_ANALYSIS phase after asset selection (if in ASSET_SELECTION phase)
        if collection_flow.master_flow_id:
            try:
                from app.services.master_flow_orchestrator import MasterFlowOrchestrator
                from app.models.collection_flow.schemas import CollectionPhase

                orchestrator = MasterFlowOrchestrator(db, context)

                # Only transition if currently in ASSET_SELECTION phase
                if (
                    collection_flow.current_phase
                    == CollectionPhase.ASSET_SELECTION.value
                ):
                    # Execute gap analysis phase now that assets are selected
                    execution_result = await orchestrator.execute_phase(
                        flow_id=str(collection_flow.master_flow_id),
                        phase_name="gap_analysis",
                    )

                    # Update collection flow phase to match
                    collection_flow.current_phase = CollectionPhase.GAP_ANALYSIS.value
                    collection_flow.status = CollectionPhase.GAP_ANALYSIS.value
                    await db.commit()

                    logger.info(
                        f"Transitioned collection flow {flow_id} from ASSET_SELECTION to GAP_ANALYSIS"
                    )
                else:
                    # If not in asset_selection, just trigger execution of current phase
                    execution_result = await orchestrator.execute_phase(
                        flow_id=str(collection_flow.master_flow_id),
                        phase_name=collection_flow.current_phase,
                    )

                # Sync master flow changes back to collection flow after phase execution
                try:
                    sync_service = MasterFlowSyncService(db, context)
                    await sync_service.sync_master_to_collection_flow(
                        master_flow_id=str(collection_flow.master_flow_id),
                        collection_flow_id=flow_id,
                    )
                except Exception as sync_error:
                    logger.warning(
                        f"Failed to sync master flow after phase execution: {sync_error}"
                    )

                logger.info(
                    f"Triggered phase execution for master flow {collection_flow.master_flow_id}"
                )

                return {
                    "success": True,
                    "message": (
                        f"Successfully updated collection flow with {processed_count} "
                        f"applications, created {len(deduplication_results)} normalized records, "
                        "and transitioned to gap analysis phase"
                    ),
                    "flow_id": flow_id,
                    "selected_application_count": processed_count,
                    "normalized_records_created": len(deduplication_results),
                    "mfo_execution_triggered": True,
                    "execution_result": execution_result,
                }
            except Exception as mfo_error:
                logger.error(f"MFO execution failed: {str(mfo_error)}")
                # Still return success for the application selection part
                return {
                    "success": True,
                    "message": (
                        f"Successfully updated collection flow with {processed_count} "
                        f"applications, created {len(deduplication_results)} normalized records "
                        "(phase transition failed)"
                    ),
                    "flow_id": flow_id,
                    "selected_application_count": processed_count,
                    "normalized_records_created": len(deduplication_results),
                    "mfo_execution_triggered": False,
                    "mfo_error": str(mfo_error),
                }
        else:
            logger.warning(
                f"Collection flow {flow_id} has no master_flow_id - skipping execution"
            )
            return {
                "success": True,
                "message": (
                    f"Successfully updated collection flow with {processed_count} applications, "
                    f"created {len(deduplication_results)} normalized records"
                ),
                "flow_id": flow_id,
                "selected_application_count": processed_count,
                "normalized_records_created": len(deduplication_results),
                "mfo_execution_triggered": False,
                "warning": "no_master_flow_id",
            }

    except HTTPException:
        # HTTPExceptions should propagate as-is
        raise
    except Exception as e:
        # DEBUG LOGGING: Log detailed failure information
        logger.debug(
            f"Database update failed for flow {flow_id} - "
            f"User: {current_user.id}, Engagement: {context.engagement_id}, "
            f"Exception type: {type(e).__name__}, Exception: {str(e)}"
        )
        logger.error(f"Error updating collection flow {flow_id} applications: {str(e)}")
        # CC: Don't echo exception text in responses (security concern)
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update collection flow applications. "
                "Please try again or contact support if the issue persists."
            ),
        )
