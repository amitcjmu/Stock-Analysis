"""
Collection to Assessment Transition Endpoints

Dedicated endpoints for transitioning collection flows to assessment flows.
Does NOT modify existing continue_flow semantics - creates separate transition path.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID

from app.core.database import get_db  # Correct import
from app.core.context import RequestContext, get_request_context
from app.services.collection_transition_service import CollectionTransitionService
from app.schemas.collection_transition import TransitionResponse  # Proper schema

router = APIRouter()


@router.post(
    "/flows/{flow_id}/transition-to-assessment", response_model=TransitionResponse
)
async def transition_to_assessment(
    flow_id: UUID,
    db: AsyncSession = Depends(get_db),  # Fixed: Use get_db, NOT get_async_db
    context: RequestContext = Depends(get_request_context),
) -> TransitionResponse:
    """
    Dedicated endpoint for collection to assessment transition.
    Does NOT modify existing continue_flow semantics.
    """

    transition_service = CollectionTransitionService(db, context)

    # Validate readiness using existing service
    readiness = await transition_service.validate_readiness(flow_id)
    if not readiness.is_ready:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "not_ready",
                "reason": readiness.reason,
                "missing_requirements": readiness.missing_requirements,
            },
        )

    # Create assessment via MFO/Repository
    result = await transition_service.create_assessment_flow(flow_id)

    return TransitionResponse(
        status="transitioned",
        assessment_flow_id=str(result.assessment_flow_id),
        collection_flow_id=str(flow_id),
        message="Assessment flow created successfully",
        created_at=result.created_at,
    )
