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
        # Extract validated data from Pydantic model
        selected_application_ids = request_data.selected_application_ids
        action = request_data.action

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

                    if not canonical_app_id:
                        logger.warning(
                            f"No canonical application for {application_name}, skipping persistence"
                        )
                        continue

                    # CRITICAL BUG FIX: Create CollectionFlowApplication record
                    # This was missing and causing no records in collection_flow_applications table
                    collection_flow_app = CollectionFlowApplication(
                        collection_flow_id=collection_flow.flow_id,
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
                    asset.collection_flow_id = collection_flow.flow_id
                    asset.updated_at = datetime.now(timezone.utc)
                except Exception as e:
                    logger.error(
                        f"Deduplication persistence failed for asset {asset_id}: {e}"
                    )
                    continue

                    deduplication_results.append(
                        {
                            "asset_id": str(asset_id),
                            "canonical_application_id": str(
                                dedup_result.canonical_application.id
                            ),
                            "application_name": application_name,
                            "match_method": dedup_result.match_method.value,
                            "similarity_score": dedup_result.similarity_score,
                            "confidence_score": dedup_result.confidence_score,
                            "is_new_canonical": dedup_result.is_new_canonical,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )

                    logger.info(
                        f"Successfully deduplicated application '{application_name}' -> "
                        f"canonical: '{dedup_result.canonical_application.canonical_name}' "
                        f"(method: {dedup_result.match_method.value}, score: {dedup_result.similarity_score:.3f})"
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

        # Commit all changes up to this point
        await db.commit()

        # Trigger questionnaire generation (if MFO exists)
        if collection_flow.master_flow_id:
            try:
                from app.services.master_flow_orchestrator import MasterFlowOrchestrator

                orchestrator = MasterFlowOrchestrator(db, context)

                # Execute data import phase for collection flow (which generates questionnaires)
                # CC: Collection flows use DATA_IMPORT phase to generate questionnaires based on selected applications
                execution_result = await orchestrator.execute_phase(
                    flow_id=str(collection_flow.master_flow_id),
                    phase_name="DATA_IMPORT",
                )

                # Sync master flow changes back to collection flow after data import
                try:
                    sync_service = MasterFlowSyncService(db, context)
                    await sync_service.sync_master_to_collection_flow(
                        master_flow_id=str(collection_flow.master_flow_id),
                        collection_flow_id=flow_id,
                    )
                except Exception as sync_error:
                    logger.warning(
                        f"Failed to sync master flow after data import: {sync_error}"
                    )

                logger.info(
                    f"Triggered questionnaire generation for master flow {collection_flow.master_flow_id}"
                )

                return {
                    "success": True,
                    "message": (
                        f"Successfully updated collection flow with {processed_count} "
                        f"applications, created {len(deduplication_results)} normalized records, "
                        "and triggered questionnaire generation"
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
                        "(questionnaire generation trigger failed)"
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
        logger.error(f"Error updating collection flow {flow_id} applications: {str(e)}")
        # CC: Don't echo exception text in responses (security concern)
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update collection flow applications. "
                "Please try again or contact support if the issue persists."
            ),
        )
