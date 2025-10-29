"""
Recommendation acceptance endpoints for Assessment Flow.
Allows users to accept 6R recommendations and update asset status.

Part of Issue #842 (Assessment Flow Complete - Treatments Visible).
Implements Phase 6: Accept Recommendation Workflow.

Uses MFO integration per ADR-006 (Master Flow Orchestrator pattern).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import safe_log_format
from app.models.asset.models import Asset

# Import MFO integration functions (per ADR-006)
from .mfo_integration import get_assessment_status_via_mfo

logger = logging.getLogger(__name__)

router = APIRouter()


class AcceptRecommendationRequest(BaseModel):
    """Request to accept a 6R recommendation."""

    strategy: str = Field(
        ...,
        description="6R strategy (rehost, replatform, refactor, repurchase, retire, retain)",
    )
    reasoning: str = Field(..., description="Reasoning for accepting this strategy")
    confidence_level: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in decision"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy": "rehost",
                "reasoning": "Low complexity, quick migration path with minimal changes",
                "confidence_level": 0.9,
            }
        }


class AcceptRecommendationResponse(BaseModel):
    """Response from accepting recommendation."""

    success: bool
    flow_id: str
    app_id: str
    strategy: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "flow_id": "550e8400-e29b-41d4-a716-446655440000",
                "app_id": "650e8400-e29b-41d4-a716-446655440001",
                "strategy": "rehost",
                "message": "Recommendation 'rehost' accepted and asset updated",
            }
        }


@router.post(
    "/{flow_id}/sixr-decisions/{app_id}/accept",
    response_model=AcceptRecommendationResponse,
    summary="Accept 6R Recommendation",
    description="""
    Accept a 6R migration recommendation and update the asset.

    This endpoint replaces the deprecated POST /6r/{analysis_id}/accept endpoint.

    **Workflow**:
    1. Verify assessment flow exists via MFO (checks both master and child tables)
    2. Get asset and verify multi-tenant scoping
    3. Update asset with accepted 6R strategy
    4. Set migration_status to "analyzed"
    5. Commit changes atomically
    6. Return success response

    **Multi-tenant Isolation**:
    - Verifies asset belongs to current client_account
    - Ensures data security through tenant scoping

    **ADR Compliance**:
    - ADR-006: Uses MFO integration to verify flow existence
    - ADR-012: Reads from child flow for operational state
    """,
    tags=["Assessment Flow - Recommendations"],
)
async def accept_sixr_recommendation(
    flow_id: str,
    app_id: str,
    request: AcceptRecommendationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Accept 6R recommendation and update asset.

    Args:
        flow_id: Assessment flow UUID
        app_id: Application/Asset UUID
        request: Recommendation acceptance details
        db: Database session
        context: Request context with tenant scoping

    Returns:
        AcceptRecommendationResponse with success status

    Raises:
        HTTPException 404: Flow or asset not found
        HTTPException 403: Access denied to asset (multi-tenant violation)
        HTTPException 500: Database operation failed
    """
    try:
        # Step 1: Verify assessment flow exists via MFO (checks both master and child tables)
        logger.info(
            safe_log_format(
                "Verifying assessment flow via MFO: flow_id={flow_id}",
                flow_id=flow_id,
            )
        )

        try:
            flow_status = await get_assessment_status_via_mfo(UUID(flow_id), db)
            logger.debug(
                safe_log_format(
                    "Flow status retrieved: status={status}, phase={phase}",
                    status=flow_status.get("status"),
                    phase=flow_status.get("current_phase"),
                )
            )
        except ValueError as e:
            logger.warning(
                safe_log_format(
                    "Assessment flow not found: flow_id={flow_id}, error={str_e}",
                    flow_id=flow_id,
                    str_e=str(e),
                )
            )
            raise HTTPException(
                status_code=404,
                detail=f"Assessment flow {flow_id} not found",
            )

        # Step 2: Get asset with multi-tenant scoping
        logger.info(
            safe_log_format(
                "Fetching asset: app_id={app_id}, client={client_id}",
                app_id=app_id,
                client_id=str(context.client_account_id),
            )
        )

        query = select(Asset).where(
            Asset.id == UUID(app_id),
            Asset.client_account_id == UUID(context.client_account_id),
        )
        result = await db.execute(query)
        asset = result.scalar_one_or_none()

        if not asset:
            logger.warning(
                safe_log_format(
                    "Asset not found or access denied: app_id={app_id}, client={client_id}",
                    app_id=app_id,
                    client_id=str(context.client_account_id),
                )
            )
            raise HTTPException(
                status_code=404,
                detail=f"Asset {app_id} not found or access denied",
            )

        # Step 3: Verify multi-tenant scoping (defense in depth)
        if str(asset.client_account_id) != str(context.client_account_id):
            logger.error(
                safe_log_format(
                    "Multi-tenant violation detected: asset_client={asset_client}, request_client={req_client}",
                    asset_client=str(asset.client_account_id),
                    req_client=str(context.client_account_id),
                )
            )
            raise HTTPException(
                status_code=403,
                detail="Access denied to this asset",
            )

        # Step 4: Update asset with accepted recommendation
        logger.info(
            safe_log_format(
                "Updating asset with 6R strategy: app_id={app_id}, strategy={strategy}",
                app_id=app_id,
                strategy=request.strategy,
            )
        )

        asset.six_r_strategy = request.strategy
        asset.migration_status = "analyzed"
        asset.updated_by = context.user_id

        # Also update assessment_flow_id to track which flow made this decision
        if not asset.assessment_flow_id:
            asset.assessment_flow_id = UUID(flow_id)

        # Store reasoning in custom_attributes for audit trail
        if not asset.custom_attributes:
            asset.custom_attributes = {}

        asset.custom_attributes["sixr_decision"] = {
            "strategy": request.strategy,
            "reasoning": request.reasoning,
            "confidence_level": request.confidence_level,
            "accepted_by": context.user_id,
            "accepted_at": str(db.get_bind()),
            "flow_id": flow_id,
        }

        # Step 5: Commit atomic transaction
        await db.commit()
        await db.refresh(asset)

        logger.info(
            safe_log_format(
                "Successfully accepted 6R recommendation: app_id={app_id}, strategy={strategy}",
                app_id=app_id,
                strategy=request.strategy,
            )
        )

        # Step 6: Return success response
        return AcceptRecommendationResponse(
            success=True,
            flow_id=flow_id,
            app_id=app_id,
            strategy=request.strategy,
            message=f"Recommendation '{request.strategy}' accepted and asset updated",
        )

    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Failed to accept recommendation: flow_id={flow_id}, app_id={app_id}, error={str_e}",
                flow_id=flow_id,
                app_id=app_id,
                str_e=str(e),
            )
        )
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to accept recommendation: {str(e)}",
        )
