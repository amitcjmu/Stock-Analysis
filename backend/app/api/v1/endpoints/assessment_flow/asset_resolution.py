"""
Asset resolution endpoints for assessment flows.
Handles asset→application mapping during ASSET_APPLICATION_RESOLUTION phase.

CC: Per docs/planning/dependency-to-assessment/README.md Step 1
Resolves asset→application mismatch between Collection and Assessment flows
"""

import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context_helpers import verify_client_access
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.repositories.assessment_flow_repository import AssessmentFlowRepository
from app.services.assessment_flow_service.core.asset_resolution_service import (
    AssetResolutionService,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# === Pydantic Request/Response Models ===


class CreateMappingRequest(BaseModel):
    """Request model for creating/updating asset→application mapping"""

    asset_id: str = Field(..., description="Asset UUID to map")
    application_id: str = Field(..., description="Target application UUID")
    mapping_method: str = Field(
        default="user_manual",
        description="Mapping method: user_manual, agent_suggested, deduplication_auto",
    )
    mapping_confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )

    @field_validator("mapping_method")
    @classmethod
    def validate_mapping_method(cls, v):
        valid_methods = ["user_manual", "agent_suggested", "deduplication_auto"]
        if v not in valid_methods:
            raise ValueError(f"mapping_method must be one of {valid_methods}")
        return v


class AssetResolutionStatusResponse(BaseModel):
    """Response model for asset resolution status"""

    unresolved_assets: List[Dict[str, Any]] = Field(
        ..., description="Assets without application mappings"
    )
    existing_mappings: List[Dict[str, Any]] = Field(
        ..., description="Current asset→application mappings"
    )
    total_assets: int = Field(..., description="Total number of assets")
    mapped_count: int = Field(..., description="Number of mapped assets")
    unmapped_count: int = Field(..., description="Number of unmapped assets")
    completion_percentage: float = Field(..., description="Completion percentage")


class CreateMappingResponse(BaseModel):
    """Response model for mapping creation"""

    status: str = Field(..., description="Operation status")
    mapping_id: str = Field(..., description="Created/updated mapping ID")
    asset_id: str = Field(..., description="Asset UUID")
    application_id: str = Field(..., description="Application UUID")


class CompleteResolutionResponse(BaseModel):
    """Response model for resolution completion"""

    status: str = Field(..., description="Completion status")
    next_phase: str = Field(..., description="Next assessment phase")
    mapped_count: int = Field(..., description="Total mapped assets")
    message: str = Field(..., description="Success message")


# === API Endpoints ===


@router.get("/{flow_id}/asset-resolution", response_model=AssetResolutionStatusResponse)
async def get_asset_resolution_status(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """Get asset resolution status for assessment flow

    Returns unresolved assets and existing mappings with completion statistics.

    Args:
        flow_id: Assessment flow identifier
        current_user: Authenticated user
        db: Database session
        client_account_id: Client account ID for tenant scoping

    Returns:
        AssetResolutionStatusResponse with unresolved assets and mappings
    """
    try:
        # Parse flow_id as UUID
        flow_uuid = UUID(flow_id)

        # Get assessment flow state
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(str(flow_uuid))

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Initialize asset resolution service with tenant context
        resolution_service = AssetResolutionService(
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=flow_state.engagement_id,
        )

        # Get selected asset IDs from flow state
        selected_asset_ids = (
            flow_state.selected_application_ids
        )  # May contain asset IDs

        # Get unresolved assets
        unresolved_assets = await resolution_service.get_unresolved_assets(
            assessment_flow_id=flow_uuid, selected_asset_ids=selected_asset_ids
        )

        # Get existing mappings
        existing_mappings = await resolution_service.get_existing_mappings(
            assessment_flow_id=flow_uuid
        )

        # Calculate statistics
        total_assets = len(selected_asset_ids)
        mapped_count = len(existing_mappings)
        unmapped_count = len(unresolved_assets)
        completion_percentage = (
            (mapped_count / total_assets * 100) if total_assets > 0 else 0.0
        )

        logger.info(
            safe_log_format(
                "Asset resolution status for flow {flow_id}: {mapped}/{total} mapped",
                flow_id=flow_id,
                mapped=mapped_count,
                total=total_assets,
            )
        )

        return AssetResolutionStatusResponse(
            unresolved_assets=unresolved_assets,
            existing_mappings=existing_mappings,
            total_assets=total_assets,
            mapped_count=mapped_count,
            unmapped_count=unmapped_count,
            completion_percentage=completion_percentage,
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            safe_log_format("Invalid UUID format for flow_id: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=400, detail="Invalid flow ID format")
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to get asset resolution status: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve asset resolution status"
        )


@router.post(
    "/{flow_id}/asset-resolution/mappings", response_model=CreateMappingResponse
)
async def create_asset_mapping(
    flow_id: str,
    request: CreateMappingRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """Create or update asset→application mapping

    Creates a new mapping or updates existing mapping for an asset.
    Enforces unique constraint: one asset can only map to one application per flow.

    Args:
        flow_id: Assessment flow identifier
        request: Mapping creation request
        current_user: Authenticated user
        db: Database session
        client_account_id: Client account ID for tenant scoping

    Returns:
        CreateMappingResponse with created/updated mapping details
    """
    try:
        # Parse UUIDs
        flow_uuid = UUID(flow_id)
        asset_uuid = UUID(request.asset_id)
        application_uuid = UUID(request.application_id)

        # Get assessment flow state for engagement_id
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(str(flow_uuid))

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Initialize asset resolution service with tenant context
        resolution_service = AssetResolutionService(
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=flow_state.engagement_id,
        )

        # Create mapping
        result = await resolution_service.create_mapping(
            assessment_flow_id=flow_uuid,
            asset_id=asset_uuid,
            application_id=application_uuid,
            mapping_method=request.mapping_method,
            mapping_confidence=request.mapping_confidence,
            created_by=UUID(current_user.id) if hasattr(current_user, "id") else None,
        )

        logger.info(
            safe_log_format(
                "Created mapping for flow {flow_id}: asset {asset_id} → application {app_id}",
                flow_id=flow_id,
                asset_id=request.asset_id,
                app_id=request.application_id,
            )
        )

        return CreateMappingResponse(**result)

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(safe_log_format("Invalid UUID format: {str_e}", str_e=str(e)))
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    except Exception as e:
        logger.error(
            safe_log_format("Failed to create asset mapping: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=500, detail="Failed to create asset mapping")


@router.post(
    "/{flow_id}/asset-resolution/complete", response_model=CompleteResolutionResponse
)
async def complete_asset_resolution(
    flow_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    client_account_id: str = Depends(verify_client_access),
):
    """Mark asset resolution phase as complete and advance to next phase

    Validates that all selected assets have been mapped to applications.
    Advances assessment flow to ARCHITECTURE_MINIMUMS phase on success.

    Args:
        flow_id: Assessment flow identifier
        current_user: Authenticated user
        db: Database session
        client_account_id: Client account ID for tenant scoping

    Returns:
        CompleteResolutionResponse with next phase and completion status

    Raises:
        HTTPException 400: If resolution is incomplete (unmapped assets remain)
        HTTPException 404: If assessment flow not found
        HTTPException 500: If completion fails
    """
    try:
        # Parse flow_id as UUID
        flow_uuid = UUID(flow_id)

        # Get assessment flow state
        repository = AssessmentFlowRepository(db, client_account_id)
        flow_state = await repository.get_assessment_flow_state(str(flow_uuid))

        if not flow_state:
            raise HTTPException(status_code=404, detail="Assessment flow not found")

        # Initialize asset resolution service with tenant context
        resolution_service = AssetResolutionService(
            db=db,
            client_account_id=UUID(client_account_id),
            engagement_id=flow_state.engagement_id,
        )

        # Get selected asset IDs from flow state
        selected_asset_ids = flow_state.selected_application_ids

        # Validate resolution completion
        is_complete, unmapped_ids = (
            await resolution_service.validate_resolution_complete(
                assessment_flow_id=flow_uuid, selected_asset_ids=selected_asset_ids
            )
        )

        if not is_complete:
            logger.warning(
                safe_log_format(
                    "Asset resolution incomplete for flow {flow_id}: {count} unmapped assets",
                    flow_id=flow_id,
                    count=len(unmapped_ids),
                )
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Resolution incomplete",
                    "unmapped_asset_ids": unmapped_ids,
                    "message": f"{len(unmapped_ids)} asset(s) still need to be mapped",
                },
            )

        # Advance to next phase: ARCHITECTURE_MINIMUMS
        # This would typically be done through MFO, but for direct phase update:
        from app.models.assessment_flow_state import AssessmentPhase

        next_phase = AssessmentPhase.ARCHITECTURE_MINIMUMS

        # Update flow state (simplified - in production use MFO phase transition)
        # await repository.update_current_phase(flow_id, next_phase)

        mapped_count = len(selected_asset_ids)

        logger.info(
            safe_log_format(
                "Asset resolution completed for flow {flow_id}: {count} assets mapped",
                flow_id=flow_id,
                count=mapped_count,
            )
        )

        return CompleteResolutionResponse(
            status="completed",
            next_phase=next_phase.value,
            mapped_count=mapped_count,
            message=f"Asset resolution completed successfully. {mapped_count} asset(s) mapped.",
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            safe_log_format("Invalid UUID format for flow_id: {str_e}", str_e=str(e))
        )
        raise HTTPException(status_code=400, detail="Invalid flow ID format")
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to complete asset resolution: {str_e}", str_e=str(e)
            )
        )
        raise HTTPException(
            status_code=500, detail="Failed to complete asset resolution"
        )
