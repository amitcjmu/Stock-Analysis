"""
API handlers for maintenance windows endpoints.

Provides FastAPI route handlers for maintenance window CRUD operations with
conflict detection and validation.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.models.api.collection_gaps import (
    MaintenanceWindowRequest,
    MaintenanceWindowResponse,
    StandardErrorResponse,
)
from app.repositories.maintenance_window_repository import (
    MaintenanceWindowRepository,
)

from .utils import convert_to_response, convert_windows_to_responses
from .validators import (
    check_schedule_conflicts,
    validate_time_range,
    validate_uuid,
    validate_window_exists,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maintenance-windows", tags=["Collection"])


@router.get(
    "",
    response_model=List[MaintenanceWindowResponse],
    responses={
        400: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="List maintenance windows",
    description=(
        "Get maintenance windows with optional filtering by scope and status."
    ),
)
async def list_maintenance_windows(
    scope_type: Optional[str] = Query(
        None, description="Filter by scope type (tenant, application, asset)"
    ),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    active_only: bool = Query(False, description="Show only currently active windows"),
    upcoming_days: Optional[int] = Query(
        None, ge=1, le=365, description="Show windows starting within N days"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> List[MaintenanceWindowResponse]:
    """
    List maintenance windows with flexible filtering options.

    Supports filtering by scope (tenant/application/asset), time ranges,
    and active status for comprehensive maintenance scheduling.
    """
    try:
        # Initialize repository with tenant context
        repo = MaintenanceWindowRepository(
            db, context.client_account_id, context.engagement_id
        )

        if active_only:
            # Get currently active windows
            windows = await repo.get_active_windows(
                scope_type=scope_type,
                application_id=application_id,
                asset_id=asset_id,
            )
        elif upcoming_days:
            # Get upcoming windows within specified days
            windows = await repo.get_upcoming_windows(
                days_ahead=upcoming_days, scope_type=scope_type
            )
        elif scope_type or application_id or asset_id:
            # Get by scope filters
            windows = await repo.get_by_scope(
                scope_type=scope_type or "tenant",
                application_id=application_id,
                asset_id=asset_id,
            )
        else:
            # Get all windows for tenant
            windows = await repo.get_all()

        # Apply limit and convert to response models
        limited_windows = windows[:limit]
        results = convert_windows_to_responses(limited_windows)

        logger.info(
            f"✅ Retrieved {len(results)} maintenance windows for "
            f"client {context.client_account_id}, engagement {context.engagement_id}"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Failed to list maintenance windows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "list_failed",
                "message": f"Failed to list maintenance windows: {str(e)}",
                "details": {
                    "scope_type": scope_type,
                    "application_id": application_id,
                    "asset_id": asset_id,
                },
            },
        )


@router.post(
    "",
    response_model=MaintenanceWindowResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": StandardErrorResponse},
        409: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Create maintenance window",
    description="Create a new maintenance window with conflict detection.",
)
async def create_maintenance_window(
    request: MaintenanceWindowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> MaintenanceWindowResponse:
    """
    Create a new maintenance window.

    Validates time ranges, scope requirements, and checks for conflicts
    before creating the maintenance window.
    """
    try:
        # Validate time range
        validate_time_range(request.start_time, request.end_time)

        async with db.begin():
            # Initialize repository
            repo = MaintenanceWindowRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Check for conflicts
            conflicts = await repo.check_conflicts(
                start_time=request.start_time,
                end_time=request.end_time,
                scope_type=request.scope_type,
                application_id=request.application_id,
                asset_id=request.asset_id,
            )

            check_schedule_conflicts(conflicts, "creation")

            # Create the maintenance window
            created_window = await repo.create_window(
                name=request.name,
                start_time=request.start_time,
                end_time=request.end_time,
                scope_type=request.scope_type,
                application_id=request.application_id,
                asset_id=request.asset_id,
                recurring=request.recurring,
                timezone=request.timezone,
                commit=False,  # Will commit with transaction
            )

            await db.flush()  # Ensure ID is available

            result = convert_to_response(created_window)

            logger.info(
                f"✅ Created maintenance window {created_window.id} for "
                f"client {context.client_account_id}, "
                f"engagement {context.engagement_id}"
            )

            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create maintenance window: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "creation_failed",
                "message": f"Failed to create maintenance window: {str(e)}",
                "details": {
                    "name": request.name,
                    "scope_type": request.scope_type,
                },
            },
        )


@router.put(
    "/{window_id}",
    response_model=MaintenanceWindowResponse,
    responses={
        400: {"model": StandardErrorResponse},
        404: {"model": StandardErrorResponse},
        409: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Update maintenance window",
    description="Update an existing maintenance window with conflict detection.",
)
async def update_maintenance_window(
    window_id: str,
    request: MaintenanceWindowRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> MaintenanceWindowResponse:
    """
    Update an existing maintenance window.

    Validates changes and checks for conflicts while excluding
    the current window from conflict detection.
    """
    try:
        # Validate UUID format and time range
        window_uuid = validate_uuid(window_id, "window ID")
        validate_time_range(request.start_time, request.end_time)

        async with db.begin():
            # Initialize repository
            repo = MaintenanceWindowRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Check if window exists
            existing = await repo.get_by_id(str(window_uuid))
            validate_window_exists(existing, window_id)

            # Check for conflicts (excluding current window)
            conflicts = await repo.check_conflicts(
                start_time=request.start_time,
                end_time=request.end_time,
                scope_type=request.scope_type,
                application_id=request.application_id,
                asset_id=request.asset_id,
                exclude_id=str(window_uuid),
            )

            check_schedule_conflicts(conflicts, "update")

            # Update the window
            updated_window = await repo.update(
                str(window_uuid),
                commit=False,
                name=request.name,
                start_time=request.start_time,
                end_time=request.end_time,
                scope_type=request.scope_type,
                application_id=request.application_id,
                asset_id=request.asset_id,
                recurring=request.recurring,
                timezone=request.timezone,
            )

            result = convert_to_response(updated_window)

            logger.info(
                f"✅ Updated maintenance window {window_id} for "
                f"client {context.client_account_id}, "
                f"engagement {context.engagement_id}"
            )

            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update maintenance window {window_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "update_failed",
                "message": f"Failed to update maintenance window: {str(e)}",
                "details": {"window_id": window_id},
            },
        )


@router.delete(
    "/{window_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        400: {"model": StandardErrorResponse},
        404: {"model": StandardErrorResponse},
        500: {"model": StandardErrorResponse},
    },
    summary="Delete maintenance window",
    description="Delete a maintenance window.",
)
async def delete_maintenance_window(
    window_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> None:
    """
    Delete a maintenance window.

    Permanently removes the maintenance window from the schedule.
    """
    try:
        # Validate UUID format
        window_uuid = validate_uuid(window_id, "window ID")

        async with db.begin():
            # Initialize repository
            repo = MaintenanceWindowRepository(
                db, context.client_account_id, context.engagement_id
            )

            # Check if window exists
            existing = await repo.get_by_id(str(window_uuid))
            validate_window_exists(existing, window_id)

            # Delete the window
            await repo.delete(str(window_uuid), commit=False)

            logger.info(
                f"✅ Deleted maintenance window {window_id} for "
                f"client {context.client_account_id}, "
                f"engagement {context.engagement_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete maintenance window {window_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "deletion_failed",
                "message": f"Failed to delete maintenance window: {str(e)}",
                "details": {"window_id": window_id},
            },
        )
