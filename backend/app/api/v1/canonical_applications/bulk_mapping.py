"""
Bulk Asset Mapping API Endpoint.

Provides bulk mapping capabilities for associating multiple assets with canonical applications.
Implements multi-tenant validation, atomic transactions, and audit logging per ADR requirements.

Phase 2.1 of Assessment Canonical Grouping Remediation Plan.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context_dependency
from app.core.database import get_db
from app.models.asset.models import Asset
from app.models.canonical_applications.canonical_application import CanonicalApplication
from app.models.canonical_applications.collection_flow_app import (
    CollectionFlowApplication,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class AssetMapping(BaseModel):
    """Single asset-to-canonical application mapping."""

    asset_id: str = Field(..., description="Asset UUID to map")
    canonical_application_id: str = Field(
        ..., description="Target canonical application UUID"
    )

    @validator("asset_id", "canonical_application_id")
    def validate_uuid_format(cls, v: str) -> str:
        """Validate UUID format."""
        try:
            UUID(v)
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid UUID format: {v}") from None


class BulkMappingRequest(BaseModel):
    """Bulk asset mapping request with validation."""

    mappings: List[AssetMapping] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="Asset-to-canonical mappings (max 100 per request)",
    )
    collection_flow_id: Optional[str] = Field(
        None, description="Optional collection flow ID for context"
    )

    @validator("mappings")
    def validate_unique_assets(cls, v: List[AssetMapping]) -> List[AssetMapping]:
        """Ensure no duplicate asset IDs in request."""
        asset_ids = [m.asset_id for m in v]
        if len(asset_ids) != len(set(asset_ids)):
            raise ValueError(
                "Duplicate asset_id entries detected in mappings"
            ) from None
        return v

    @validator("collection_flow_id")
    def validate_collection_flow_uuid(cls, v: Optional[str]) -> Optional[str]:
        """Validate collection flow UUID format if provided."""
        if v is not None:
            try:
                UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(
                    f"Invalid collection_flow_id UUID format: {v}"
                ) from None
        return v


class MappingError(BaseModel):
    """Individual mapping error details."""

    asset_id: str = Field(..., description="Asset ID that failed")
    error: str = Field(..., description="Error message")


class BulkMappingResponse(BaseModel):
    """Bulk asset mapping response with detailed results."""

    total_requested: int = Field(..., description="Total mappings requested")
    successfully_mapped: int = Field(..., description="Count of successful mappings")
    already_mapped: int = Field(
        ..., description="Count of assets already mapped (idempotent)"
    )
    errors: List[MappingError] = Field(..., description="List of mapping errors")
    canonical_application_name: Optional[str] = Field(
        None, description="Name of canonical application if single target"
    )


def _validate_tenant_context(context: RequestContext) -> tuple[UUID, UUID]:
    """Validate tenant context and return UUIDs."""
    if not context.client_account_id or not context.engagement_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing tenant headers: X-Client-Account-ID and X-Engagement-ID required",
        )
    try:
        return UUID(context.client_account_id), UUID(context.engagement_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tenant UUID format: {str(e)}",
        )


async def _process_single_mapping(
    mapping: AssetMapping,
    db: AsyncSession,
    valid_assets: dict,
    canonical_apps: dict,
    client_account_uuid: UUID,
    engagement_uuid: UUID,
    collection_flow_id: Optional[str],
    context: RequestContext,
) -> tuple[str, Optional[dict]]:
    """
    Process a single asset mapping.

    Returns:
        Tuple of (result_type, error_dict) where result_type is
        'success', 'already_mapped', or 'error'
    """
    asset_uuid = UUID(mapping.asset_id)
    canonical_uuid = UUID(mapping.canonical_application_id)

    # Validate asset exists and belongs to tenant (pre-fetched)
    asset = valid_assets.get(mapping.asset_id)
    if not asset:
        return "error", {
            "asset_id": mapping.asset_id,
            "error": "Asset not found or does not belong to tenant",
        }

    canonical_app = canonical_apps.get(mapping.canonical_application_id)

    # Check if mapping already exists
    existing_query = select(CollectionFlowApplication).where(
        CollectionFlowApplication.asset_id == asset_uuid,
        CollectionFlowApplication.client_account_id == client_account_uuid,
        CollectionFlowApplication.engagement_id == engagement_uuid,
    )
    existing_result = await db.execute(existing_query)
    existing_mapping = existing_result.scalar_one_or_none()

    if existing_mapping:
        existing_mapping.canonical_application_id = canonical_uuid
        existing_mapping.collection_flow_id = (
            UUID(collection_flow_id)
            if collection_flow_id
            else existing_mapping.collection_flow_id
        )
        existing_mapping.deduplication_method = "bulk_manual_mapping"
        existing_mapping.match_confidence = 1.0
        existing_mapping.collection_status = "mapped"
        result_type = "already_mapped"
    else:
        new_mapping = CollectionFlowApplication(
            collection_flow_id=UUID(collection_flow_id) if collection_flow_id else None,
            asset_id=asset_uuid,
            canonical_application_id=canonical_uuid,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
            application_name=asset.name,
            deduplication_method="bulk_manual_mapping",
            match_confidence=1.0,
            collection_status="mapped",
        )
        db.add(new_mapping)
        result_type = "success"

    # Audit logging
    logger.info(
        f"[AUDIT] Asset mapped: asset_id={mapping.asset_id}, "
        f"asset_name={asset.name}, "
        f"canonical_app_id={mapping.canonical_application_id}, "
        f"canonical_app_name={canonical_app.canonical_name if canonical_app else 'unknown'}, "
        f"tenant={context.client_account_id}/{context.engagement_id}, "
        f"user={context.user_id or 'system'}"
    )

    return result_type, None


@router.post("/bulk-map-assets", response_model=BulkMappingResponse)
async def bulk_map_assets(
    request: BulkMappingRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context_dependency),
) -> BulkMappingResponse:
    """
    Bulk map assets to canonical applications with multi-tenant validation.

    Security features:
    - Multi-tenant isolation: Validates all asset and canonical app IDs belong to tenant
    - Atomic transactions: All mappings succeed or all fail
    - Idempotent: Duplicate mappings return already_mapped count
    - Audit logging: Logs all successful mappings with tenant context
    """
    # Validate tenant context
    client_account_uuid, engagement_uuid = _validate_tenant_context(context)

    # Initialize results tracking
    results = {"successfully_mapped": 0, "already_mapped": 0, "errors": []}

    canonical_app_name: Optional[str] = None

    # Track unique canonical app IDs for validation optimization
    canonical_app_ids = set(m.canonical_application_id for m in request.mappings)

    # Pre-validate all canonical applications exist and belong to tenant
    # This prevents partial failures and provides clear error messages
    try:
        canonical_apps_query = select(CanonicalApplication).where(
            CanonicalApplication.id.in_([UUID(cid) for cid in canonical_app_ids]),
            CanonicalApplication.client_account_id == client_account_uuid,
            CanonicalApplication.engagement_id == engagement_uuid,
        )
        canonical_apps_result = await db.execute(canonical_apps_query)
        canonical_apps = {
            str(app.id): app for app in canonical_apps_result.scalars().all()
        }

        # Check for missing canonical apps
        missing_canonical_ids = canonical_app_ids - set(canonical_apps.keys())
        if missing_canonical_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Canonical application(s) not found or do not belong to tenant: "
                    f"{', '.join(list(missing_canonical_ids)[:5])}"
                    f"{'...' if len(missing_canonical_ids) > 5 else ''}"
                ),
            )

        # Store canonical app name if single target (for response)
        if len(canonical_apps) == 1:
            canonical_app_name = list(canonical_apps.values())[0].canonical_name

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to validate canonical applications: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate canonical applications: {str(e)}",
        )

    # Pre-fetch all assets in a single query to avoid N+1 problem (Qodo review fix)
    asset_ids_to_validate = [UUID(m.asset_id) for m in request.mappings]
    assets_query = select(Asset).where(
        Asset.id.in_(asset_ids_to_validate),
        Asset.client_account_id == client_account_uuid,
        Asset.engagement_id == engagement_uuid,
    )
    assets_result = await db.execute(assets_query)
    valid_assets = {str(asset.id): asset for asset in assets_result.scalars().all()}

    # Process each mapping with tenant validation and idempotent upsert
    # Note: Session uses autobegin, so we don't call begin() explicitly
    try:
        for mapping in request.mappings:
            try:
                result_type, error = await _process_single_mapping(
                    mapping,
                    db,
                    valid_assets,
                    canonical_apps,
                    client_account_uuid,
                    engagement_uuid,
                    request.collection_flow_id,
                    context,
                )
                if result_type == "error":
                    results["errors"].append(error)
                elif result_type == "already_mapped":
                    results["already_mapped"] += 1
                else:
                    results["successfully_mapped"] += 1
            except Exception as e:
                logger.error(
                    f"Failed to map asset {mapping.asset_id}: {e}", exc_info=True
                )
                results["errors"].append(
                    {"asset_id": mapping.asset_id, "error": f"Mapping failed: {str(e)}"}
                )

        # Commit all changes atomically
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk mapping failed, rolled back: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk mapping failed: {str(e)}",
        )

    return BulkMappingResponse(
        total_requested=len(request.mappings),
        successfully_mapped=results["successfully_mapped"],
        already_mapped=results["already_mapped"],
        errors=results["errors"],
        canonical_application_name=canonical_app_name,
    )
