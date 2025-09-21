"""
Route handlers for collection flows API endpoints.

This module contains the actual handler functions for each API endpoint,
separated from the router definitions for better modularity.
"""

import logging
from typing import Any, Dict, List

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.api.collection_gaps import (
    AdaptiveQuestionnaire,
    CollectionFlowCreateRequest,
    CollectionFlowResponse,
    CollectionGapsResponse,
    QuestionnaireGenerationRequest,
    ResponseProcessingResult,
    ResponsesBatchRequest,
)
from app.repositories.collection_flow_repository import CollectionFlowRepository
from app.services.collection_gaps import ResponseMappingService
from app.services.collection_gaps.agent_tool_registry import AgentToolRegistry

from .utils import (
    calculate_completeness_metrics,
    calculate_pending_gaps,
    convert_gap_analysis_to_response,
    get_existing_data_snapshot,
)

logger = logging.getLogger(__name__)


async def create_collection_flow_handler(
    request: CollectionFlowCreateRequest,
    db: AsyncSession,
    context: RequestContext,
) -> CollectionFlowResponse:
    """
    Create a new collection flow.

    This endpoint creates a collection flow that will be integrated with the
    Master Flow Orchestrator for lifecycle management.
    """
    try:
        # Initialize repository
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )

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


async def get_collection_flow_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> CollectionFlowResponse:
    """
    Get collection flow details with completeness metrics.
    """
    try:
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        flow = collection_flow[0]

        # Calculate actual completeness by category based on database data
        completeness_by_category = await calculate_completeness_metrics(
            db, context.client_account_id, context.engagement_id
        )

        return CollectionFlowResponse(
            id=str(flow.id),
            flow_id=str(flow.flow_id),
            subject=flow.flow_metadata.get("subject", {}),
            collection_config=flow.collection_config,
            current_phase=flow.current_phase,
            progress_percentage=flow.progress_percentage,
            completeness_by_category=completeness_by_category,
            pending_gaps=await calculate_pending_gaps(
                db, context.client_account_id, context.engagement_id
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection flow",
        )


async def generate_questionnaires_handler(
    flow_id: str,
    request: QuestionnaireGenerationRequest,
    db: AsyncSession,
    context: RequestContext,
) -> List[AdaptiveQuestionnaire]:
    """
    Generate adaptive questionnaires based on data gaps.

    This endpoint uses the QuestionnaireGenerationTool from the AgentToolRegistry
    to create targeted questionnaires that address specific data gaps.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Get questionnaire generation tool from registry
        questionnaire_tool = AgentToolRegistry.get("questionnaire_generation")

        # Perform actual gap analysis using agent tool
        gap_tool = AgentToolRegistry.get("gap_analysis")
        subject = {"scope": "engagement", "ids": [context.engagement_id]}
        existing_data_snapshot = await get_existing_data_snapshot(
            db, context.client_account_id, context.engagement_id
        )
        gap_analysis = gap_tool._run(subject, existing_data_snapshot)

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


async def submit_responses_handler(
    flow_id: str,
    request: ResponsesBatchRequest,
    db: AsyncSession,
    context: RequestContext,
) -> ResponseProcessingResult:
    """
    Submit questionnaire responses for processing.

    This endpoint processes responses using the ResponseMappingService which
    maps questionnaire responses to appropriate database tables using the
    QUESTION_TO_TABLE_MAPPING configuration.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Initialize response mapping service
        response_service = ResponseMappingService(
            db, context.client_account_id, context.engagement_id
        )

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


async def get_collection_gaps_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> CollectionGapsResponse:
    """
    Get prioritized collection gaps analysis.

    This endpoint returns a prioritized list of data gaps that need to be
    addressed for complete asset migration planning.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Get gap analysis tool from registry and perform actual analysis
        gap_tool = AgentToolRegistry.get("gap_analysis")

        # Prepare input for gap analysis based on actual data
        subject = {"scope": "engagement", "ids": [context.engagement_id]}
        existing_data_snapshot = await get_existing_data_snapshot(
            db, context.client_account_id, context.engagement_id
        )

        # Run gap analysis
        gap_analysis_result = gap_tool._run(subject, existing_data_snapshot)

        # Convert gap analysis results to API response format
        return await convert_gap_analysis_to_response(
            gap_analysis_result,
            db,
            context.client_account_id,
            context.engagement_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gaps for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collection gaps",
        )


async def get_flow_status_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> dict:
    """
    Get flow status for polling (5s active/15s waiting pattern).
    """
    try:
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        flow = collection_flow[0]

        return {
            "flow_id": str(flow.flow_id),
            "status": (getattr(flow.status, "value", flow.status) or "unknown"),
            "current_phase": flow.current_phase,
            "progress_percentage": flow.progress_percentage,
            "last_updated": flow.updated_at.isoformat() if flow.updated_at else None,
            "is_active": flow.status
            and getattr(flow.status, "value", flow.status)
            not in ["completed", "failed", "cancelled"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve flow status",
        )


async def get_completeness_metrics_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """
    Get completeness metrics for a collection flow.

    Returns detailed completeness metrics by category and overall progress.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Calculate completeness metrics
        completeness_by_category = await calculate_completeness_metrics(
            db, context.client_account_id, context.engagement_id
        )

        # Calculate overall completeness
        if completeness_by_category:
            overall_completeness = sum(completeness_by_category.values()) / len(
                completeness_by_category
            )
        else:
            overall_completeness = 0.0

        # Get pending gaps count
        pending_gaps = await calculate_pending_gaps(
            db, context.client_account_id, context.engagement_id
        )

        return {
            "flow_id": flow_id,
            "overall_completeness": round(overall_completeness, 2),
            "completeness_by_category": completeness_by_category,
            "pending_gaps": pending_gaps,
            "last_calculated": "now",  # Could add actual timestamp
            "categories": (
                list(completeness_by_category.keys())
                if completeness_by_category
                else []
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get completeness metrics for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve completeness metrics",
        )


async def refresh_completeness_metrics_handler(
    flow_id: str,
    db: AsyncSession,
    context: RequestContext,
) -> Dict[str, Any]:
    """
    Refresh completeness metrics for a collection flow.

    Forces recalculation of all completeness metrics and returns updated values.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(
            db, context.client_account_id, context.engagement_id
        )
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Force refresh by clearing any cached data (if applicable)
        # This would typically invalidate caches or trigger recalculation

        # Get fresh data snapshot
        existing_data_snapshot = await get_existing_data_snapshot(
            db, context.client_account_id, context.engagement_id
        )

        # Recalculate completeness metrics
        completeness_by_category = await calculate_completeness_metrics(
            db, context.client_account_id, context.engagement_id
        )

        # Calculate overall completeness
        if completeness_by_category:
            overall_completeness = sum(completeness_by_category.values()) / len(
                completeness_by_category
            )
        else:
            overall_completeness = 0.0

        # Get updated gaps count
        pending_gaps = await calculate_pending_gaps(
            db, context.client_account_id, context.engagement_id
        )

        logger.info(
            f"✅ Refreshed completeness metrics for flow {flow_id} - "
            f"Overall: {overall_completeness:.1f}%, Pending gaps: {pending_gaps}"
        )

        return {
            "flow_id": flow_id,
            "overall_completeness": round(overall_completeness, 2),
            "completeness_by_category": completeness_by_category,
            "pending_gaps": pending_gaps,
            "last_calculated": "now",  # Could add actual timestamp
            "categories": (
                list(completeness_by_category.keys())
                if completeness_by_category
                else []
            ),
            "refreshed": True,
            "data_points_analyzed": (
                len(existing_data_snapshot) if existing_data_snapshot else 0
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh completeness metrics for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh completeness metrics",
        )
