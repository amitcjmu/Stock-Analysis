"""
Collection flows API endpoints.

This module provides endpoints for collection flow management including
questionnaire generation, response processing, and gap analysis.

Modularized to maintain clean separation of concerns while preserving
backward compatibility with existing imports.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.models.api.collection_gaps import (
    CollectionFlowCreateRequest,
    CollectionFlowResponse,
    CollectionGapsResponse,
    QuestionnaireGenerationRequest,
    ResponseProcessingResult,
    ResponsesBatchRequest,
    StandardErrorResponse,
    AdaptiveQuestionnaire,
)

from .handlers import (
    create_collection_flow_handler,
    get_collection_flow_handler,
    generate_questionnaires_handler,
    submit_responses_handler,
    get_collection_gaps_handler,
    get_flow_status_handler,
)

# Router setup
router = APIRouter(
    prefix="/collection",
    tags=["Collection Gaps"],
)


@router.post(
    "/flows",
    response_model=CollectionFlowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Collection Flow",
    description="Create a new collection flow with specified subject scope and automation tier.",
    responses={
        201: {"description": "Collection flow created successfully"},
        400: {"model": StandardErrorResponse, "description": "Invalid request data"},
        409: {"model": StandardErrorResponse, "description": "Flow already exists"},
    },
)
async def create_collection_flow(
    request: CollectionFlowCreateRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Create a new collection flow."""
    return await create_collection_flow_handler(request, db, context)


@router.get(
    "/flows/{flow_id}",
    response_model=CollectionFlowResponse,
    summary="Get Collection Flow",
    description="Retrieve details of a specific collection flow including completeness metrics.",
    responses={
        200: {"description": "Collection flow retrieved successfully"},
        404: {"model": StandardErrorResponse, "description": "Flow not found"},
    },
)
async def get_collection_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get collection flow details with completeness metrics."""
    return await get_collection_flow_handler(flow_id, db, context)


@router.post(
    "/flows/{flow_id}/questionnaires/generate",
    response_model=list[AdaptiveQuestionnaire],
    summary="Generate Adaptive Questionnaires",
    description="Generate adaptive questionnaires based on identified data gaps.",
    responses={
        200: {"description": "Questionnaires generated successfully"},
        404: {"model": StandardErrorResponse, "description": "Flow not found"},
        400: {
            "model": StandardErrorResponse,
            "description": "Invalid generation parameters",
        },
    },
)
async def generate_questionnaires(
    flow_id: str,
    request: QuestionnaireGenerationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Generate adaptive questionnaires based on data gaps."""
    return await generate_questionnaires_handler(flow_id, request, db, context)


@router.post(
    "/flows/{flow_id}/responses",
    response_model=ResponseProcessingResult,
    summary="Submit Questionnaire Responses",
    description="Submit batch of questionnaire responses for processing and database mapping.",
    responses={
        200: {"description": "Responses processed successfully"},
        404: {"model": StandardErrorResponse, "description": "Flow not found"},
        400: {"model": StandardErrorResponse, "description": "Invalid responses data"},
    },
)
async def submit_responses(
    flow_id: str,
    request: ResponsesBatchRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Submit questionnaire responses for processing."""
    return await submit_responses_handler(flow_id, request, db, context)


@router.get(
    "/flows/{flow_id}/gaps",
    response_model=CollectionGapsResponse,
    summary="Get Collection Gaps",
    description="Retrieve prioritized list of data gaps for the collection flow.",
    responses={
        200: {"description": "Gaps retrieved successfully"},
        404: {"model": StandardErrorResponse, "description": "Flow not found"},
    },
)
async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get prioritized collection gaps analysis."""
    return await get_collection_gaps_handler(flow_id, db, context)


@router.get(
    "/flows/{flow_id}/status",
    response_model=dict,
    summary="Get Flow Status",
    description="Get current status of collection flow for polling.",
    responses={
        200: {"description": "Status retrieved successfully"},
        404: {"model": StandardErrorResponse, "description": "Flow not found"},
    },
)
async def get_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get flow status for polling (5s active/15s waiting pattern)."""
    return await get_flow_status_handler(flow_id, db, context)


# Backward compatibility exports
__all__ = [
    "router",
    "create_collection_flow",
    "get_collection_flow",
    "generate_questionnaires",
    "submit_responses",
    "get_collection_gaps",
    "get_flow_status",
]
