"""
Asset Management Handlers for Unified Discovery

Handles asset listing and summary operations within the unified discovery context.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from typing import Dict, Optional

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
) -> Dict[str, any]:
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
