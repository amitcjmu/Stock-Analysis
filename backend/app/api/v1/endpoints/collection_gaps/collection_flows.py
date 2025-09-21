"""
Collection flows API endpoints.

This module provides endpoints for collection flow management including
questionnaire generation, response processing, and gap analysis.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    get_async_db,
    get_client_account_id,
    get_engagement_id,
)
from app.models.api.collection_gaps import (
    AdaptiveQuestionnaire,
    CollectionFlowCreateRequest,
    CollectionFlowResponse,
    CollectionGapsResponse,
    QuestionnaireGenerationRequest,
    ResponseProcessingResult,
    ResponsesBatchRequest,
    StandardErrorResponse,
)
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.collection_gaps import ResponseMappingService
from app.services.collection_gaps.agent_tool_registry import AgentToolRegistry

logger = logging.getLogger(__name__)

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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Create a new collection flow.

    This endpoint creates a collection flow that will be integrated with the
    Master Flow Orchestrator for lifecycle management.
    """
    try:
        # Initialize repository
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)

        # Create collection flow (this would integrate with MasterFlowOrchestrator)
        collection_flow = await collection_repo.create(
            flow_name=request.flow_name,
            automation_tier=request.automation_tier,
            # subject and other fields would be set based on request.subject
            flow_metadata={"subject": request.subject},
            collection_config={"automation_tier": request.automation_tier},
        )

        return CollectionFlowResponse(
            id=str(collection_flow.id),
            flow_id=str(collection_flow.flow_id),
            subject=request.subject,
            collection_config=collection_flow.collection_config,
            current_phase=collection_flow.current_phase,
            progress_percentage=collection_flow.progress_percentage,
        )

    except Exception as e:
        logger.error(f"Failed to create collection flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection flow",
        )


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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Get collection flow details with completeness metrics.
    """
    try:
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        flow = collection_flow[0]

        # Calculate completeness by category (stub implementation)
        completeness_by_category = {
            "lifecycle": 75.0,
            "resilience": 60.0,
            "compliance": 85.0,
            "licensing": 40.0,
        }

        return CollectionFlowResponse(
            id=str(flow.id),
            flow_id=str(flow.flow_id),
            subject=flow.flow_metadata.get("subject", {}),
            collection_config=flow.collection_config,
            current_phase=flow.current_phase,
            progress_percentage=flow.progress_percentage,
            completeness_by_category=completeness_by_category,
            pending_gaps=15,  # Stub value
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection flow",
        )


@router.post(
    "/flows/{flow_id}/questionnaires/generate",
    response_model=List[AdaptiveQuestionnaire],
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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Generate adaptive questionnaires based on data gaps.

    This endpoint uses the QuestionnaireGenerationTool from the AgentToolRegistry
    to create targeted questionnaires that address specific data gaps.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Get questionnaire generation tool from registry
        questionnaire_tool = AgentToolRegistry.get("questionnaire_generation")

        # Prepare gap analysis (stub implementation)
        gap_analysis = {
            "missing_fields_by_category": {
                "lifecycle": ["end_of_life_date", "vendor_support_status"],
                "resilience": ["rto_minutes", "rpo_minutes"],
                "compliance": ["data_classification"],
                "licensing": ["license_type", "renewal_date"],
            }
        }

        # Filter by requested categories if specified
        if request.categories:
            filtered_gaps = {
                "missing_fields_by_category": {
                    cat: fields
                    for cat, fields in gap_analysis[
                        "missing_fields_by_category"
                    ].items()
                    if cat in request.categories
                }
            }
            gap_analysis = filtered_gaps

        # Generate questionnaire using agent tool
        questionnaire_data = questionnaire_tool._run(
            gap_analysis, stakeholder_role="technical"
        )

        # Convert to API response format
        questionnaire = AdaptiveQuestionnaire(
            questionnaire_id=questionnaire_data["questionnaire_id"],
            title=questionnaire_data["title"],
            sections=questionnaire_data["sections"],
            estimated_completion_time=questionnaire_data["estimated_completion_time"],
            target_gaps=list(gap_analysis["missing_fields_by_category"].keys()),
        )

        return [questionnaire]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate questionnaires for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate questionnaires",
        )


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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Submit questionnaire responses for processing.

    This endpoint processes responses using the ResponseMappingService which
    maps questionnaire responses to appropriate database tables using the
    QUESTION_TO_TABLE_MAPPING configuration.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Initialize response mapping service
        response_service = ResponseMappingService(db, client_account_id, engagement_id)

        # Convert Pydantic models to dictionaries for processing
        responses_data = [response.model_dump() for response in request.responses]

        # Process responses batch
        results = await response_service.process_responses_batch(responses_data)

        return ResponseProcessingResult(
            upserted=results["upserted"],
            by_target=results["by_target"],
            errors=results.get("errors"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process responses for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process responses",
        )


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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Get prioritized collection gaps analysis.

    This endpoint returns a prioritized list of data gaps that need to be
    addressed for complete asset migration planning.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Get gap analysis tool from registry
        gap_tool = AgentToolRegistry.get("gap_analysis")

        # Prepare input for gap analysis (stub implementation)
        subject = {"scope": "engagement", "ids": [engagement_id]}
        existing_data = {"assets_count": 150, "coverage": 65.0}

        # Run gap analysis
        gap_tool._run(subject, existing_data)

        # Convert to API response format
        from app.models.api.collection_gaps import CollectionGap

        critical_gaps = [
            CollectionGap(
                category="lifecycle",
                field_name="end_of_life_date",
                description="Product end-of-life date is not available",
                priority="critical",
                affected_assets=25,
            )
        ]

        high_gaps = [
            CollectionGap(
                category="resilience",
                field_name="rto_minutes",
                description="Recovery Time Objective not defined",
                priority="high",
                affected_assets=40,
            )
        ]

        return CollectionGapsResponse(
            critical=critical_gaps,
            high=high_gaps,
            optional=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gaps for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection gaps",
        )


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
    db: AsyncSession = Depends(get_async_db),
    client_account_id: str = Depends(get_client_account_id),
    engagement_id: str = Depends(get_engagement_id),
):
    """
    Get flow status for polling (5s active/15s waiting pattern).
    """
    try:
        collection_repo = CollectionFlowRepository(db, client_account_id, engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        flow = collection_flow[0]

        return {
            "flow_id": str(flow.flow_id),
            "status": flow.status.value if flow.status else "unknown",
            "current_phase": flow.current_phase,
            "progress_percentage": flow.progress_percentage,
            "last_updated": flow.updated_at.isoformat() if flow.updated_at else None,
            "is_active": flow.status
            and flow.status.value not in ["completed", "failed", "cancelled"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flow status",
        )
