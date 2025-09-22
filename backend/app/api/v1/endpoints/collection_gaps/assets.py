"""
Asset-agnostic collection endpoints for Collection Gaps Phase 2.

These endpoints enable starting collection for any asset type without requiring
application-specific configuration, and provide conflict detection and resolution.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.core.feature_flags import require_feature
from app.models.asset import Asset  # CORRECT IMPORT PATH
from app.models.collection_flow import CollectionFlow
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict

router = APIRouter(prefix="/assets")


# Pydantic models for request/response
class AssetCollectionStartRequest(BaseModel):
    """Request to start asset-agnostic collection."""

    scope: str = Field(
        ..., description="Collection scope: 'tenant' | 'engagement' | 'asset'"
    )
    scope_id: str = Field(..., description="ID of the scope entity")
    asset_type: Optional[str] = Field(None, description="Optional asset type filter")


class AssetCollectionStartResponse(BaseModel):
    """Response from starting asset collection."""

    flow_id: str = Field(..., description="ID of the created collection flow")
    status: str = Field(..., description="Initial status of the collection")
    scope: str = Field(..., description="Collection scope that was used")


class ConflictResolution(BaseModel):
    """Request to resolve a field conflict."""

    value: str = Field(..., description="The resolved value for the field")
    rationale: Optional[str] = Field(None, description="Reason for choosing this value")


class ConflictResolutionResponse(BaseModel):
    """Response from resolving a conflict."""

    status: str = Field(..., description="Resolution status")
    resolved_value: str = Field(..., description="The value that was resolved")


@router.post("/start", response_model=AssetCollectionStartResponse)
@require_feature("collection.gaps.v1")
async def start_asset_collection(
    request: AssetCollectionStartRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> AssetCollectionStartResponse:
    """
    Start collection for any asset type without requiring application configuration.

    This endpoint enables asset-agnostic collection by accepting flexible scope
    parameters and storing the collection metadata for later processing.
    """
    # Validate scope parameter
    valid_scopes = {"tenant", "engagement", "asset"}
    if request.scope not in valid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scope '{request.scope}'. Must be one of: {', '.join(valid_scopes)}",
        )

    # If scope is 'asset', validate that the asset exists and is accessible
    if request.scope == "asset":
        try:
            asset_uuid = UUID(request.scope_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid asset ID format. Must be a valid UUID.",
            )

        # Check if asset exists and is accessible by this tenant
        asset_result = await db.execute(
            select(Asset)
            .where(Asset.id == asset_uuid)
            .where(Asset.client_account_id == context.client_account_id)
            .where(Asset.engagement_id == context.engagement_id)
        )
        asset = asset_result.scalar_one_or_none()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {request.scope_id} not found or not accessible",
            )

    # Create collection flow with scope metadata
    flow = CollectionFlow(
        flow_metadata={
            "scope": request.scope,
            "scope_id": request.scope_id,
            "asset_type": request.asset_type,
            "collection_type": "asset_agnostic",
            "phase": "data_gathering",
        },
        client_account_id=context.client_account_id,
        engagement_id=context.engagement_id,
        status="active",
    )

    db.add(flow)
    await db.commit()
    await db.refresh(flow)

    return AssetCollectionStartResponse(
        flow_id=str(flow.id), status="started", scope=request.scope
    )


@router.get("/{asset_id}/conflicts")
@require_feature("collection.gaps.v1")
async def get_asset_conflicts(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> List[dict]:
    """
    Get real conflicts from asset_field_conflicts table for a specific asset.

    Returns field-level conflicts detected across multiple data sources
    (custom_attributes, technical_details, raw_imports).
    """
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset ID format. Must be a valid UUID.",
        )

    # Verify asset exists and is accessible
    asset_result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_uuid)
        .where(Asset.client_account_id == context.client_account_id)
        .where(Asset.engagement_id == context.engagement_id)
    )
    asset = asset_result.scalar_one_or_none()

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found or not accessible",
        )

    # Get conflicts for this asset with proper tenant scoping
    conflicts_result = await db.execute(
        select(AssetFieldConflict)
        .where(AssetFieldConflict.asset_id == asset_uuid)
        .where(AssetFieldConflict.client_account_id == context.client_account_id)
        .where(AssetFieldConflict.engagement_id == context.engagement_id)
        .order_by(AssetFieldConflict.created_at.desc())
    )
    conflicts = conflicts_result.scalars().all()

    # Convert to dict format for API response
    return [conflict.to_dict() for conflict in conflicts]


@router.post(
    "/{asset_id}/conflicts/{field_name}/resolve",
    response_model=ConflictResolutionResponse,
)
@require_feature("collection.gaps.v1")
async def resolve_asset_conflict(
    asset_id: str,
    field_name: str,
    resolution: ConflictResolution,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> ConflictResolutionResponse:
    """
    Resolve a specific field conflict for an asset.

    Marks the conflict as manually resolved with the provided value and rationale.
    """
    try:
        asset_uuid = UUID(asset_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid asset ID format. Must be a valid UUID.",
        )

    # Find the specific conflict with proper tenant scoping
    conflict_result = await db.execute(
        select(AssetFieldConflict)
        .where(AssetFieldConflict.asset_id == asset_uuid)
        .where(AssetFieldConflict.field_name == field_name)
        .where(AssetFieldConflict.client_account_id == context.client_account_id)
        .where(AssetFieldConflict.engagement_id == context.engagement_id)
    )
    conflict = conflict_result.scalar_one_or_none()

    if not conflict:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conflict not found for asset {asset_id}, field '{field_name}'",
        )

    # Check if already resolved
    if conflict.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict for field '{field_name}' is already resolved",
        )

    # Resolve the conflict
    conflict.resolve_conflict(
        resolved_value=resolution.value,
        resolved_by=context.user_id,
        rationale=resolution.rationale,
        auto_resolved=False,
    )

    await db.commit()
    await db.refresh(conflict)

    return ConflictResolutionResponse(
        status="resolved", resolved_value=resolution.value
    )
