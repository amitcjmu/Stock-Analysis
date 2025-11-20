"""
Asset Management Handlers for Unified Discovery

Handles asset listing and summary operations within the unified discovery context.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_request_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format

# Import the asset list handler
from app.services.unified_discovery_handlers.asset_list_handler import (
    create_asset_list_handler,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _create_context_validation_response(
    missing_headers: list, is_read_operation: bool = False
) -> Dict[str, Any]:
    """
    Create a user-friendly response for missing context headers.

    Args:
        missing_headers: List of missing header names
        is_read_operation: If True, provides fallback options for read-only operations

    Returns:
        Dictionary with error details and helpful guidance
    """
    base_message = (
        "This operation requires multi-tenant context headers to ensure proper data isolation. "
        f"Please include the following headers in your request: {', '.join(missing_headers)}"
    )

    guidance = {
        "X-Client-Account-Id": "Your unique client account identifier",
        "X-Engagement-ID": "The engagement/project identifier you're working with",
    }

    response = {
        "error": "Missing required context headers",
        "message": base_message,
        "missing_headers": missing_headers,
        "header_guidance": {
            header: guidance.get(header, "Required header")
            for header in missing_headers
        },
        "documentation": "Ensure your API client includes these headers for proper multi-tenant data access.",
    }

    if is_read_operation:
        response["note"] = (
            "For read-only operations, you can sometimes use fallback authentication methods. "
            "However, multi-tenant context headers are strongly recommended for data consistency."
        )
        response["alternatives"] = [
            "Include the required headers for full functionality",
            "Contact your administrator for proper header configuration",
            "Use the frontend application which handles headers automatically",
        ]

    return response


def _validate_context_with_fallback(
    context: RequestContext, operation_type: str = "read"
) -> Optional[HTTPException]:
    """
    Validate context headers with graceful error handling and fallback options.

    Args:
        context: Request context to validate
        operation_type: Type of operation ("read" or "write")

    Returns:
        HTTPException if validation fails, None if validation passes
    """
    missing_headers = []
    if not context.client_account_id:
        missing_headers.append("X-Client-Account-Id")
    if not context.engagement_id:
        missing_headers.append("X-Engagement-ID")

    if not missing_headers:
        return None

    is_read_operation = operation_type.lower() == "read"
    error_response = _create_context_validation_response(
        missing_headers, is_read_operation
    )

    # For read operations, use 400 but include helpful guidance
    # For write operations, use 400 with stricter messaging
    status_code = 400

    if is_read_operation:
        logger.warning(
            safe_log_format(
                "Read operation attempted without proper context headers: {headers}",
                headers=missing_headers,
            )
        )
    else:
        logger.error(
            safe_log_format(
                "Write operation blocked due to missing context headers: {headers}",
                headers=missing_headers,
            )
        )

    return HTTPException(status_code=status_code, detail=error_response)


@router.get("/assets")
async def list_assets(
    page_size: int = Query(50, ge=1, le=200, description="Number of assets per page"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    status_filter: Optional[str] = Query(None, description="Filter by asset status"),
    flow_id: Optional[str] = Query(None, description="Filter by discovery flow ID"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
):
    """
    List assets with tenant isolation and pagination support.

    This endpoint provides asset listing functionality within the unified discovery
    context, following the established modular handler pattern.

    Features:
    - Auto-executes asset_inventory phase if not yet completed
    - Tenant-scoped queries (client_account_id, engagement_id)
    - Pagination with configurable page sizes
    - Optional filtering by asset type, status, and flow ID
    - Graceful context header validation with helpful error messages
    - Fallback behavior for resilience
    - Comprehensive error handling and logging
    """
    try:
        # Validate context headers with improved error handling
        validation_error = _validate_context_with_fallback(context, "read")
        if validation_error:
            raise validation_error

        # CRITICAL FIX: Auto-execute asset_inventory phase if needed
        if flow_id:
            from sqlalchemy import select, and_
            from app.models.discovery_flow import DiscoveryFlow

            logger.info(
                f"🔍 Checking asset_inventory auto-execution for flow_id: {flow_id}"
            )

            # Check if asset_inventory phase has been completed
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
            flow_result = await db.execute(stmt)
            discovery_flow = flow_result.scalar_one_or_none()

            if not discovery_flow:
                logger.error(
                    safe_log_format(
                        "Invalid flow_id provided: flow does not exist or access denied | {flow_id}",
                        flow_id=flow_id,
                    )
                )
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "flow_not_found",
                        "message": "Discovery flow does not exist or access is denied.",
                        "flow_id": flow_id,
                        "suggestion": "Please navigate from the Discovery Dashboard or verify your flow ID.",
                        "context": {
                            "client_account_id": str(context.client_account_id),
                            "engagement_id": str(context.engagement_id),
                        },
                    },
                )

            logger.info(
                safe_log_format(
                    "Flow found | current_phase: {phase}, asset_inventory_completed: {completed}, flow_id: {flow_id}",
                    phase=discovery_flow.current_phase,
                    completed=discovery_flow.asset_inventory_completed,
                    flow_id=discovery_flow.flow_id,
                )
            )

            # At this point, discovery_flow is guaranteed to exist (validated above)
            if discovery_flow.current_phase == "asset_inventory":
                # CC: CRITICAL FIX - Check for pending conflict resolution BEFORE auto-execution
                # If conflicts are pending, DON'T re-run phase (would create duplicate conflicts)
                has_pending_conflicts = (
                    discovery_flow.phase_state
                    and discovery_flow.phase_state.get("conflict_resolution_pending")
                    is True
                )

                if has_pending_conflicts:
                    logger.info(
                        f"⏸️ Skipping auto-execution - flow {flow_id} has pending conflict resolution"
                    )
                # Check if asset_inventory has been executed
                elif not discovery_flow.asset_inventory_completed:
                    logger.info(
                        f"🏗️ Auto-executing asset_inventory phase for flow {flow_id}"
                    )

                    # Execute the asset_inventory phase
                    from app.services.master_flow_orchestrator.core import (
                        MasterFlowOrchestrator,
                    )

                    try:
                        orchestrator = MasterFlowOrchestrator(db, context)

                        # Get master_flow_id if available
                        master_flow_id = discovery_flow.master_flow_id or flow_id

                        logger.info(
                            f"🎯 Preparing to execute asset_inventory with "
                            f"master_flow_id: {master_flow_id}, data_import_id: {discovery_flow.data_import_id}"
                        )

                        # Prepare phase input with necessary IDs
                        phase_input = {
                            "flow_id": str(master_flow_id),
                            "master_flow_id": str(master_flow_id),
                            "discovery_flow_id": str(flow_id),
                            "data_import_id": (
                                str(discovery_flow.data_import_id)
                                if discovery_flow.data_import_id
                                else None
                            ),
                            "client_account_id": str(context.client_account_id),
                            "engagement_id": str(context.engagement_id),
                        }

                        logger.info(
                            f"🚀 Executing asset_inventory phase with input: {phase_input}"
                        )

                        # Execute the phase
                        exec_result = await orchestrator.execute_phase(
                            flow_id=str(master_flow_id),
                            phase_name="asset_inventory",
                            phase_input=phase_input,
                        )

                        logger.info(
                            f"📋 Asset inventory execution result: {exec_result}"
                        )

                        if exec_result.get("status") in ("success", "completed"):
                            # Mark phase as completed
                            discovery_flow.asset_inventory_completed = True
                            await db.commit()
                            logger.info(
                                f"✅ Asset inventory phase executed successfully for flow {flow_id}"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Asset inventory phase execution had issues: {exec_result}"
                            )

                    except Exception as exec_error:
                        logger.error(
                            f"❌ Failed to execute asset_inventory phase: {exec_error}",
                            exc_info=True,
                        )

        # Create asset list handler following the modular pattern
        asset_handler = await create_asset_list_handler(db, context)

        # Execute asset listing with provided parameters
        result = await asset_handler.list_assets(
            page_size=page_size,
            page=page,
            asset_type=asset_type,
            status_filter=status_filter,
            flow_id=flow_id,
        )

        logger.info(
            safe_log_format(
                "Asset listing request completed: {success}, assets returned: {count}",
                success=result["success"],
                count=len(result.get("assets", [])),
            )
        )

        return result

    except Exception as e:
        logger.error(
            safe_log_format(
                "Asset listing endpoint failed: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list assets: {str(e)}",
        )


@router.get("/assets/summary")
async def get_assets_summary(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
):
    """
    Get asset summary statistics for the current tenant context.

    Provides overview information about assets including:
    - Total asset count
    - Asset type distribution
    - Status distribution
    - Graceful context header validation with user-friendly error messages
    """
    try:
        # Validate context headers with improved error handling
        validation_error = _validate_context_with_fallback(context, "read")
        if validation_error:
            raise validation_error

        # Create asset list handler
        asset_handler = await create_asset_list_handler(db, context)

        # Get asset summary
        result = await asset_handler.get_asset_summary()

        logger.info(
            safe_log_format(
                "Asset summary request completed: {success}",
                success=result["success"],
            )
        )

        return result

    except Exception as e:
        logger.error(
            safe_log_format(
                "Asset summary endpoint failed: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get asset summary: {str(e)}",
        )


@router.get("/assets/{asset_id}")
async def get_single_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
):
    """
    Get a single asset by ID.

    Required for AI gap analysis status checking in frontend.
    Returns asset with ai_gap_analysis_status and ai_gap_analysis_timestamp fields.
    """
    from uuid import UUID
    from sqlalchemy import select
    from app.models.asset.models import Asset

    try:
        # Validate context headers
        validation_error = _validate_context_with_fallback(context, "read")
        if validation_error:
            raise validation_error

        # Parse and validate UUID
        try:
            asset_uuid = UUID(asset_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid asset ID format: {asset_id}. Must be a valid UUID.",
            )

        # Query asset with tenant scoping
        stmt = select(Asset).where(
            Asset.id == asset_uuid,
            Asset.client_account_id == context.client_account_id,
            Asset.engagement_id == context.engagement_id,
        )
        result = await db.execute(stmt)
        asset = result.scalar_one_or_none()

        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

        logger.info(
            safe_log_format(
                "Retrieved asset: {asset_id} with AI status: {status}",
                asset_id=str(asset.id),
                status=asset.ai_gap_analysis_status,
            )
        )

        # Return asset as dict (FastAPI will serialize to JSON)
        return {
            "id": str(asset.id),
            "name": asset.name,
            "asset_type": asset.asset_type,
            "environment": asset.environment,
            "application_name": asset.application_name,
            "ai_gap_analysis_status": asset.ai_gap_analysis_status,
            "ai_gap_analysis_timestamp": (
                asset.ai_gap_analysis_timestamp.isoformat()
                if asset.ai_gap_analysis_timestamp
                else None
            ),
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "updated_at": asset.updated_at.isoformat() if asset.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Get single asset endpoint failed: {error}",
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get asset: {str(e)}",
        )
