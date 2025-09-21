"""
Collection flows API endpoints.

This module provides endpoints for collection flow management including
questionnaire generation, response processing, and gap analysis.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Create a new collection flow.

    This endpoint creates a collection flow that will be integrated with the
    Master Flow Orchestrator for lifecycle management.
    """
    try:
        # Initialize repository
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)

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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get collection flow details with completeness metrics.
    """
    try:
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        flow = collection_flow[0]

        # Calculate actual completeness by category based on database data
        completeness_by_category = await _calculate_completeness_metrics(
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
            pending_gaps=await _calculate_pending_gaps(
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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Generate adaptive questionnaires based on data gaps.

    This endpoint uses the QuestionnaireGenerationTool from the AgentToolRegistry
    to create targeted questionnaires that address specific data gaps.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)
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
        existing_data_snapshot = await _get_existing_data_snapshot(
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
    """
    Submit questionnaire responses for processing.

    This endpoint processes responses using the ResponseMappingService which
    maps questionnaire responses to appropriate database tables using the
    QUESTION_TO_TABLE_MAPPING configuration.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)
        collection_flow = await collection_repo.get_by_filters(flow_id=flow_id)

        if not collection_flow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection flow not found",
            )

        # Initialize response mapping service
        response_service = ResponseMappingService(db, context.client_account_id, context.engagement_id)

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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get prioritized collection gaps analysis.

    This endpoint returns a prioritized list of data gaps that need to be
    addressed for complete asset migration planning.
    """
    try:
        # Verify flow exists
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)
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
        existing_data_snapshot = await _get_existing_data_snapshot(
            db, context.client_account_id, context.engagement_id
        )

        # Run gap analysis
        gap_analysis_result = gap_tool._run(subject, existing_data_snapshot)

        # Convert gap analysis results to API response format
        return await _convert_gap_analysis_to_response(
            gap_analysis_result, db, context.client_account_id, context.engagement_id
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
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get flow status for polling (5s active/15s waiting pattern).
    """
    try:
        collection_repo = CollectionFlowRepository(db, context.client_account_id, context.engagement_id)
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


async def _calculate_completeness_metrics(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, float]:
    """
    Calculate actual completeness metrics by category based on database data.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Dictionary with completeness percentages by category
    """
    from app.repositories.resilience_repository import (
        ResilienceRepository,
        ComplianceRepository,
        LicenseRepository,
    )
    from app.repositories.vendor_product_repository import LifecycleRepository
    from sqlalchemy import select, func
    from app.models.assets import Asset

    # Get total asset count for this engagement
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    total_assets = result.scalar() or 1  # Avoid division by zero

    # Initialize repositories
    resilience_repo = ResilienceRepository(db, client_account_id, engagement_id)
    compliance_repo = ComplianceRepository(db, client_account_id, engagement_id)
    license_repo = LicenseRepository(db, client_account_id, engagement_id)
    lifecycle_repo = LifecycleRepository(db, client_account_id, engagement_id)

    # Calculate lifecycle completeness
    lifecycle_milestones = await lifecycle_repo.get_all()
    lifecycle_completeness = (len(lifecycle_milestones) / total_assets) * 100 if total_assets > 0 else 0.0

    # Calculate resilience completeness
    resilience_records = await resilience_repo.get_all()
    resilience_completeness = (len(resilience_records) / total_assets) * 100 if total_assets > 0 else 0.0

    # Calculate compliance completeness
    compliance_records = await compliance_repo.get_all()
    compliance_completeness = (len(compliance_records) / total_assets) * 100 if total_assets > 0 else 0.0

    # Calculate licensing completeness
    license_records = await license_repo.get_all()
    licensing_completeness = (len(license_records) / total_assets) * 100 if total_assets > 0 else 0.0

    return {
        "lifecycle": min(lifecycle_completeness, 100.0),
        "resilience": min(resilience_completeness, 100.0),
        "compliance": min(compliance_completeness, 100.0),
        "licensing": min(licensing_completeness, 100.0),
    }


async def _calculate_pending_gaps(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> int:
    """
    Calculate the number of pending gaps that need to be addressed.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Number of pending gaps
    """
    # Get completeness metrics and calculate pending gaps based on thresholds
    completeness = await _calculate_completeness_metrics(db, client_account_id, engagement_id)

    # Count categories with less than 80% completeness as pending gaps
    pending_gaps = sum(1 for percentage in completeness.values() if percentage < 80.0)

    return pending_gaps


async def _get_existing_data_snapshot(
    db: AsyncSession, client_account_id: str, engagement_id: str
) -> Dict[str, Any]:
    """
    Get snapshot of existing data for gap analysis.

    Args:
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        Dictionary with current data state snapshot
    """
    from sqlalchemy import select, func
    from app.models.assets import Asset

    # Get asset count
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    assets_count = result.scalar() or 0

    # Get completeness metrics
    completeness = await _calculate_completeness_metrics(db, client_account_id, engagement_id)

    # Calculate overall coverage
    overall_coverage = sum(completeness.values()) / len(completeness) if completeness else 0.0

    return {
        "assets_count": assets_count,
        "coverage": overall_coverage,
        "completeness_by_category": completeness,
        "engagement_id": engagement_id,
        "client_account_id": client_account_id,
    }


async def _convert_gap_analysis_to_response(
    gap_analysis_result: Dict[str, Any],
    db: AsyncSession,
    client_account_id: str,
    engagement_id: str,
) -> "CollectionGapsResponse":
    """
    Convert gap analysis results to API response format.

    Args:
        gap_analysis_result: Results from gap analysis tool
        db: Database session
        client_account_id: Client account UUID for tenant scoping
        engagement_id: Engagement UUID for project scoping

    Returns:
        CollectionGapsResponse with prioritized gaps
    """
    from app.models.api.collection_gaps import CollectionGap, CollectionGapsResponse
    from sqlalchemy import select, func
    from app.models.assets import Asset

    # Get total asset count for affected asset calculations
    total_assets_query = select(func.count(Asset.id)).where(
        Asset.client_account_id == client_account_id,
        Asset.engagement_id == engagement_id,
    )
    result = await db.execute(total_assets_query)
    total_assets = result.scalar() or 1

    critical_gaps = []
    high_gaps = []
    optional_gaps = []

    # Extract missing fields by category
    missing_fields = gap_analysis_result.get("missing_fields_by_category", {})
    priorities = gap_analysis_result.get("priorities", {})

    # Create gap objects based on analysis results
    for category, fields in missing_fields.items():
        for field_name in fields:
            # Determine priority
            priority = "medium"  # default
            if field_name in priorities.get("critical", []):
                priority = "critical"
            elif field_name in priorities.get("high", []):
                priority = "high"
            elif field_name in priorities.get("medium", []):
                priority = "medium"
            else:
                priority = "optional"

            # Estimate affected assets (this could be made more sophisticated)
            affected_assets = int(total_assets * 0.3)  # Assume 30% of assets are affected by each gap

            gap = CollectionGap(
                category=category,
                field_name=field_name,
                description=f"{field_name.replace('_', ' ').title()} is not available for complete migration planning",
                priority=priority,
                affected_assets=affected_assets,
            )

            # Sort into priority buckets
            if priority == "critical":
                critical_gaps.append(gap)
            elif priority == "high":
                high_gaps.append(gap)
            else:
                optional_gaps.append(gap)

    return CollectionGapsResponse(
        critical=critical_gaps,
        high=high_gaps,
        optional=optional_gaps,
    )
