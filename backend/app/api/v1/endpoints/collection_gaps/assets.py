"""
Asset-agnostic collection endpoints for Collection Gaps Phase 2.

These endpoints enable starting collection for any asset type without requiring
application-specific configuration, and provide conflict detection and resolution.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_request_context, RequestContext
from app.core.feature_flags import require_feature
from app.models.asset import Asset  # CORRECT IMPORT PATH
from app.models.collection_flow import CollectionFlow
from app.models.asset_agnostic.asset_field_conflicts import AssetFieldConflict


def _convert_context_ids_to_uuid(context: RequestContext) -> tuple[UUID, UUID]:
    """
    Convert string context IDs to UUID objects for database queries.

    Args:
        context: RequestContext with string ID values

    Returns:
        Tuple of (client_account_uuid, engagement_uuid)

    Raises:
        HTTPException: If context IDs are missing or invalid UUID format
    """
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required tenant context (client_account_id or engagement_id)",
        )

    try:
        client_account_uuid = UUID(context.client_account_id)
        engagement_uuid = UUID(context.engagement_id)
        return client_account_uuid, engagement_uuid
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format in context: {str(e)}",
        )


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


class AssetSummary(BaseModel):
    """Minimal asset data for selection UI"""

    id: str
    name: str
    asset_type: str  # 'application', 'database', 'server', etc.
    status: str
    completeness_score: float = Field(0.0, ge=0.0, le=1.0)  # 0.0 to 1.0
    gap_count: int = 0
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssetListResponse(BaseModel):
    """Paginated asset listing response"""

    assets: List[AssetSummary]
    total_count: int
    page: int
    page_size: int
    has_more: bool


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

    # Convert context IDs to UUID for database queries
    client_account_uuid, engagement_uuid = _convert_context_ids_to_uuid(context)

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
            .where(Asset.client_account_id == client_account_uuid)
            .where(Asset.engagement_id == engagement_uuid)
        )
        asset = asset_result.scalar_one_or_none()

        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset {request.scope_id} not found or not accessible",
            )

    # Create collection flow with scope metadata
    import uuid as uuid_module

    flow_id = uuid_module.uuid4()

    flow = CollectionFlow(
        flow_id=flow_id,
        flow_name=f"Asset {request.asset_type or 'Generic'} Collection",
        user_id=(
            UUID(context.user_id)
            if context.user_id
            else UUID("33333333-3333-3333-3333-333333333333")
        ),
        automation_tier="tier_1",
        flow_metadata={
            "scope": request.scope,
            "scope_id": request.scope_id,
            "asset_type": request.asset_type,
            "collection_type": "asset_agnostic",
            "phase": "data_gathering",
        },
        client_account_id=client_account_uuid,
        engagement_id=engagement_uuid,
        status="initialized",
    )

    db.add(flow)
    await db.commit()
    await db.refresh(flow)

    return AssetCollectionStartResponse(
        flow_id=str(flow.flow_id), status="started", scope=request.scope
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

    # Convert context IDs to UUID for database queries
    client_account_uuid, engagement_uuid = _convert_context_ids_to_uuid(context)

    # Verify asset exists and is accessible
    asset_result = await db.execute(
        select(Asset)
        .where(Asset.id == asset_uuid)
        .where(Asset.client_account_id == client_account_uuid)
        .where(Asset.engagement_id == engagement_uuid)
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
        .where(AssetFieldConflict.client_account_id == client_account_uuid)
        .where(AssetFieldConflict.engagement_id == engagement_uuid)
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

    # Convert context IDs to UUID for database queries
    client_account_uuid, engagement_uuid = _convert_context_ids_to_uuid(context)

    # Find the specific conflict with proper tenant scoping
    conflict_result = await db.execute(
        select(AssetFieldConflict)
        .where(AssetFieldConflict.asset_id == asset_uuid)
        .where(AssetFieldConflict.field_name == field_name)
        .where(AssetFieldConflict.client_account_id == client_account_uuid)
        .where(AssetFieldConflict.engagement_id == engagement_uuid)
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

    # Convert user_id to UUID if present
    try:
        resolved_by_uuid = UUID(context.user_id) if context.user_id else None
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format in context",
        )

    # Resolve the conflict
    conflict.resolve_conflict(
        resolved_value=resolution.value,
        resolved_by=resolved_by_uuid,
        rationale=resolution.rationale,
        auto_resolved=False,
    )

    await db.commit()
    await db.refresh(conflict)

    return ConflictResolutionResponse(
        status="resolved", resolved_value=resolution.value
    )


@router.get("/available", response_model=AssetListResponse)
@require_feature("collection.gaps.v2")
async def get_available_assets(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    asset_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> AssetListResponse:
    """
    Get available assets for selection in collection flows.

    Returns paginated list of assets with completeness scores and gap counts.
    Properly scoped to tenant/engagement context.
    """
    # Convert context IDs to UUID for database queries
    client_account_uuid, engagement_uuid = _convert_context_ids_to_uuid(context)

    # Base query with tenant scoping
    query = select(Asset).where(
        Asset.client_account_id == client_account_uuid,
        Asset.engagement_id == engagement_uuid,
        Asset.status != "decommissioned",  # Only active-ish assets
    )

    # Apply asset type filter if provided
    if asset_type:
        query = query.where(Asset.asset_type == asset_type)

    # Apply search filter if provided
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.application_name.ilike(search_pattern),
                Asset.asset_type.ilike(search_pattern),
                Asset.hostname.ilike(search_pattern),
            )
        )

    # Get total count before pagination
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total_count = count_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(Asset.created_at.desc()).offset(offset).limit(page_size)

    # Execute query
    result = await db.execute(query)
    assets = result.scalars().all()

    # Calculate completeness for each asset
    asset_summaries = []
    for asset in assets:
        # Calculate completeness based on populated fields
        required_fields = [
            "name",
            "asset_type",
            "status",
            "business_owner",
            "business_criticality",
        ]
        optional_fields = [
            "technical_details",
            "custom_attributes",
            "dependencies",
            "description",
            "operating_system",
        ]

        populated_required = sum(
            1 for field in required_fields if getattr(asset, field, None)
        )
        populated_optional = sum(
            1 for field in optional_fields if getattr(asset, field, None)
        )

        completeness = (populated_required / len(required_fields)) * 0.7 + (
            populated_optional / len(optional_fields)
        ) * 0.3

        # Count gaps (simplified - in real implementation, query collection_data_gaps table)
        gap_count = len(required_fields) - populated_required

        asset_summaries.append(
            AssetSummary(
                id=str(asset.id),
                name=asset.name
                or asset.application_name
                or f"Asset {str(asset.id)[:8]}",
                asset_type=asset.asset_type or "unknown",
                status=asset.status or "active",
                completeness_score=min(completeness, 1.0),
                gap_count=gap_count,
                last_updated=asset.updated_at,
                metadata={
                    "business_criticality": asset.business_criticality,
                    "business_owner": asset.business_owner,
                    "technical_owner": asset.technical_owner,
                    "has_dependencies": bool(asset.dependencies),
                    "environment": asset.environment,
                },
            )
        )

    return AssetListResponse(
        assets=asset_summaries,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_more=(offset + len(assets)) < total_count,
    )
