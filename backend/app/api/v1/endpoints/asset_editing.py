"""
Asset Editing API Endpoints (Issues #911 and #912)

Provides endpoints for:
- AI grid editing (single field and bulk updates) - Issue #911
- Soft delete and restore operations - Issue #912
- Trash view for deleted assets - Issue #912
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_request_context
from app.schemas.asset_schemas import (
    AssetFieldUpdateRequest,
    AssetFieldUpdateResponse,
    BulkAssetUpdateRequest,
    BulkAssetUpdateResponse,
    AssetSoftDeleteResponse,
    AssetRestoreResponse,
    BulkSoftDeleteRequest,
    BulkSoftDeleteResponse,
    PaginatedTrashResponse,
)
from app.services.asset_field_update_service import (
    AssetFieldUpdateService,
    FieldValidationError,
    ALLOWED_EDITABLE_FIELDS,
)
from app.services.asset_soft_delete_service import AssetSoftDeleteService

logger = logging.getLogger(__name__)

router = APIRouter()


# Issue #911: AI Grid Editing Endpoints


@router.patch(
    "/{asset_id}/fields/{field_name}",
    response_model=AssetFieldUpdateResponse,
    summary="Update Single Asset Field",
    description=f"""
    Update a single field on an asset (AI grid editing).

    **Allowed editable fields:** {sorted(ALLOWED_EDITABLE_FIELDS)}

    Field values are validated by type:
    - Numeric fields (cpu_cores, memory_gb, etc.) must be numbers
    - Enum fields (asset_type, status, etc.) must match valid enum values
    - Boolean fields (pii_flag, has_saas_replacement) must be true/false

    **Tenant Scoping:** All operations are scoped to client_account_id and engagement_id.
    """,
)
async def update_asset_field(
    asset_id: UUID = Path(..., description="Asset ID to update"),
    field_name: str = Path(..., description="Field name to update"),
    request: AssetFieldUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> AssetFieldUpdateResponse:
    """
    Update a single field on an asset with validation.

    Args:
        asset_id: UUID of the asset to update
        field_name: Name of the field to update
        request: Request body with new value
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Response with old and new values

    Raises:
        HTTPException 400: Field validation error
        HTTPException 404: Asset not found
    """
    try:
        service = AssetFieldUpdateService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        result = await service.update_single_field(
            asset_id=asset_id,
            field_name=field_name,
            request=request,
        )

        return result

    except FieldValidationError as e:
        logger.warning(f"Field validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        logger.warning(f"Asset not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update asset field: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/bulk-update",
    response_model=BulkAssetUpdateResponse,
    summary="Bulk Update Asset Fields",
    description="""
    Update multiple fields across multiple assets in a single request.

    Useful for:
    - Batch editing in AI grid interface
    - Applying AI suggestions to multiple assets
    - Bulk data corrections

    **Partial Success:** If some updates fail, successful updates are still applied.
    The response includes success/failure counts and error details.

    **Tenant Scoping:** All operations are scoped to client_account_id and engagement_id.
    """,
)
async def bulk_update_assets(
    request: BulkAssetUpdateRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> BulkAssetUpdateResponse:
    """
    Perform bulk field updates on multiple assets.

    Args:
        request: Request body with list of updates
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Response with success/failure counts and details
    """
    try:
        service = AssetFieldUpdateService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        # Convert Pydantic models to dicts for service
        updates = [
            {
                "asset_id": update.asset_id,
                "field_name": update.field_name,
                "value": update.value,
            }
            for update in request.updates
        ]

        result = await service.bulk_update_fields(
            updates=updates,
            updated_by=request.updated_by,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to bulk update assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Issue #912: Soft Delete Endpoints


@router.delete(
    "/{asset_id}",
    response_model=AssetSoftDeleteResponse,
    summary="Soft Delete Asset",
    description="""
    Soft delete an asset by setting deleted_at timestamp.

    The asset is not permanently removed from the database.
    It can be restored using the restore endpoint.

    **Tenant Scoping:** Only assets in the current account/engagement can be deleted.
    """,
)
async def soft_delete_asset(
    asset_id: UUID = Path(..., description="Asset ID to soft delete"),
    deleted_by: Optional[UUID] = Query(None, description="User ID performing deletion"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> AssetSoftDeleteResponse:
    """
    Soft delete an asset.

    Args:
        asset_id: UUID of the asset to delete
        deleted_by: User ID performing the deletion (optional)
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Response with deletion metadata

    Raises:
        HTTPException 404: Asset not found
        HTTPException 400: Asset already deleted
    """
    try:
        service = AssetSoftDeleteService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        result = await service.soft_delete(
            asset_id=asset_id,
            deleted_by=deleted_by,
        )

        return result

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to soft delete asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/{asset_id}/restore",
    response_model=AssetRestoreResponse,
    summary="Restore Soft Deleted Asset",
    description="""
    Restore a previously soft deleted asset.

    Clears the deleted_at timestamp and makes the asset active again.

    **Tenant Scoping:** Only assets in the current account/engagement can be restored.
    """,
)
async def restore_asset(
    asset_id: UUID = Path(..., description="Asset ID to restore"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> AssetRestoreResponse:
    """
    Restore a soft deleted asset.

    Args:
        asset_id: UUID of the asset to restore
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Response with restore metadata

    Raises:
        HTTPException 404: Asset not found
        HTTPException 400: Asset not deleted
    """
    try:
        service = AssetSoftDeleteService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        result = await service.restore(asset_id=asset_id)

        return result

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        logger.error(f"Failed to restore asset: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/bulk-delete",
    response_model=BulkSoftDeleteResponse,
    summary="Bulk Soft Delete Assets",
    description="""
    Soft delete multiple assets in a single request.

    **Partial Success:** If some deletions fail, successful deletions are still applied.
    The response includes success/failure counts and error details.

    **Tenant Scoping:** All operations are scoped to client_account_id and engagement_id.
    """,
)
async def bulk_soft_delete_assets(
    request: BulkSoftDeleteRequest = Body(...),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> BulkSoftDeleteResponse:
    """
    Bulk soft delete multiple assets.

    Args:
        request: Request body with list of asset IDs
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Response with success/failure counts and details
    """
    try:
        service = AssetSoftDeleteService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        result = await service.bulk_soft_delete(
            asset_ids=request.asset_ids,
            deleted_by=request.deleted_by,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to bulk soft delete assets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/trash",
    response_model=PaginatedTrashResponse,
    summary="Get Trash View",
    description="""
    Get paginated list of soft deleted assets (trash view).

    Shows all assets that have been soft deleted but not permanently removed.
    Assets can be restored from trash using the restore endpoint.

    **Tenant Scoping:** Only shows deleted assets in the current account/engagement.
    """,
)
async def get_trash_view(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> PaginatedTrashResponse:
    """
    Get trash view with paginated deleted assets.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page (1-200)
        db: Database session (injected)
        context: Request context with tenant info (injected)

    Returns:
        Paginated response with deleted assets
    """
    try:
        service = AssetSoftDeleteService(
            db=db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

        result = await service.get_trash_view(
            page=page,
            page_size=page_size,
        )

        return result

    except Exception as e:
        logger.error(f"Failed to get trash view: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
