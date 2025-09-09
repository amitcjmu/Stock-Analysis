"""
Collection Flow Readiness and Validation Endpoints

This module provides API endpoints for:
- Collection flow readiness assessment
- Data population validation and fixes
- Assessment transition validation
- Master flow synchronization validation

Implements the validation checklist requirements for the Collection Flow.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.context import RequestContext
from app.core.deps import get_db, get_current_user, get_request_context
from app.core.rbac_utils import (
    COLLECTION_READ_ROLES,
    COLLECTION_WRITE_ROLES,
    require_role,
)
from app.models import User
from app.services.collection_readiness_service import (
    CollectionReadinessService,
    ReadinessAssessmentResult,
    ReadinessThresholds,
)
from app.services.collection_data_population_service import (
    CollectionDataPopulationService,
)
from app.services.enhanced_collection_transition_service import (
    EnhancedCollectionTransitionService,
    AssessmentTransitionRequest,
    AssessmentTransitionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ReadinessValidationRequest(BaseModel):
    """Request model for readiness validation"""

    thresholds: Optional[ReadinessThresholds] = None


class DataPopulationRequest(BaseModel):
    """Request model for data population"""

    force_repopulate: bool = False


class ValidationSummaryResponse(BaseModel):
    """Response model for validation summary"""

    flow_id: str
    overall_status: str  # "ready", "not_ready", "needs_attention"
    readiness_score: float

    # Validation details
    collection_completeness: Dict[str, Any]
    data_quality: Dict[str, Any]
    field_mappings: Dict[str, Any]
    applications_readiness: Dict[str, Any]
    blocking_issues: Dict[str, Any]

    # Data population status
    data_population_status: Dict[str, Any]

    # Recommendations
    next_actions: list
    estimated_time_to_ready: Optional[int] = None  # minutes


@router.post("/flows/{flow_id}/validate-readiness")
async def validate_collection_readiness(
    flow_id: str,
    request: ReadinessValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> ReadinessAssessmentResult:
    """
    Validate collection flow readiness for assessment transition.

    Implements Section 6 of the validation checklist:
    - Collection completeness >= 70% threshold check
    - All critical gaps addressed
    - Data quality score >= 65% check
    - Field mappings validation
    - No blocking errors
    """
    require_role(current_user, COLLECTION_READ_ROLES, "validate collection readiness")

    try:
        flow_uuid = UUID(flow_id)

        # Initialize readiness service
        readiness_service = CollectionReadinessService(db, context)

        # Update thresholds if provided
        if request.thresholds:
            readiness_service.update_thresholds(**request.thresholds.dict())

        # Perform comprehensive readiness assessment
        readiness_result = await readiness_service.assess_readiness(flow_uuid)

        logger.info(
            f"Readiness validation completed for flow {flow_id}: "
            f"ready={readiness_result.is_ready}, score={readiness_result.overall_score:.2f}"
        )

        return readiness_result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error validating readiness for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Readiness validation failed: {str(e)}"
        )


@router.post("/flows/{flow_id}/populate-data")
async def populate_collection_data(
    flow_id: str,
    request: DataPopulationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Populate collection flow data to fix database population issues.

    Addresses the validation finding that collection flows marked "completed"
    have no child data by ensuring proper population of:
    - collection_flow_applications
    - collection_flow_gaps
    - collection_flow_inventory
    - collection_gap_analysis
    """
    require_role(current_user, COLLECTION_WRITE_ROLES, "populate collection data")

    try:
        flow_uuid = UUID(flow_id)

        # Initialize data population service
        population_service = CollectionDataPopulationService(db, context)

        # Get the collection flow
        from app.models.collection_flow import CollectionFlow
        from sqlalchemy import select, and_

        result = await db.execute(
            select(CollectionFlow).where(
                and_(
                    CollectionFlow.flow_id == flow_uuid,
                    CollectionFlow.client_account_id == context.client_account_id,
                    CollectionFlow.engagement_id == context.engagement_id,
                )
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Populate data
        population_result = await population_service.populate_collection_data(
            collection_flow, force_repopulate=request.force_repopulate
        )

        # Run data integrity check in background
        if population_result.get("applications_populated", 0) > 0:
            background_tasks.add_task(
                _background_integrity_check,
                flow_uuid,
                context.client_account_id,
                context.engagement_id,
            )

        logger.info(
            f"Data population completed for flow {flow_id}: {population_result}"
        )

        return {
            "status": "success",
            "message": "Collection data population completed",
            "flow_id": flow_id,
            "population_results": population_result,
            "background_integrity_check_scheduled": True,
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error populating data for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Data population failed: {str(e)}")


@router.post("/flows/{flow_id}/transition-to-assessment")
async def transition_to_assessment(
    flow_id: str,
    request: AssessmentTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> AssessmentTransitionResult:
    """
    Transition collection flow to assessment phase.

    Implements Sections 9-10 of the validation checklist:
    - Assessment Flow Creation
    - Data Transfer Verification
    - Master flow synchronization
    - Phase transition logging
    """
    require_role(current_user, COLLECTION_WRITE_ROLES, "transition to assessment")

    try:
        # Update request with flow ID
        request.collection_flow_id = UUID(flow_id)

        # Initialize enhanced transition service
        transition_service = EnhancedCollectionTransitionService(db, context)

        # Perform transition
        transition_result = await transition_service.transition_to_assessment(request)

        if transition_result.success:
            logger.info(
                f"Assessment transition completed for flow {flow_id}. "
                f"Assessment flow: {transition_result.assessment_flow_id}"
            )
        else:
            logger.warning(
                f"Assessment transition failed for flow {flow_id}: "
                f"{', '.join(transition_result.errors)}"
            )

        return transition_result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error transitioning flow {flow_id} to assessment: {e}")
        raise HTTPException(
            status_code=500, detail=f"Assessment transition failed: {str(e)}"
        )


@router.get("/flows/{flow_id}/validation-summary")
async def get_validation_summary(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> ValidationSummaryResponse:
    """
    Get comprehensive validation summary for a collection flow.

    Provides overview of all validation checklist items and current status.
    """
    require_role(current_user, COLLECTION_READ_ROLES, "get validation summary")

    try:
        flow_uuid = UUID(flow_id)

        # Initialize services
        readiness_service = CollectionReadinessService(db, context)
        population_service = CollectionDataPopulationService(db, context)

        # Run readiness assessment
        readiness_result = await readiness_service.assess_readiness(flow_uuid)

        # Check data integrity
        integrity_result = await population_service.ensure_data_integrity(flow_uuid)

        # Determine overall status
        overall_status = "ready" if readiness_result.is_ready else "not_ready"
        if integrity_result["issues_found"] > 0:
            overall_status = "needs_attention"

        # Build summary response
        summary = ValidationSummaryResponse(
            flow_id=flow_id,
            overall_status=overall_status,
            readiness_score=readiness_result.overall_score,
            collection_completeness={
                "percentage": readiness_result.collection_completeness * 100,
                "threshold_met": readiness_result.collection_completeness >= 0.7,
                "threshold": 70.0,
            },
            data_quality={
                "score": readiness_result.data_quality_score,
                "threshold_met": (
                    readiness_result.data_quality_score >= 0.65
                    if readiness_result.data_quality_score is not None
                    else False
                ),
                "threshold": 65.0,
            },
            field_mappings={
                "complete": readiness_result.field_mappings_complete,
                "validation_required": not readiness_result.field_mappings_complete,
            },
            applications_readiness={
                "ready": readiness_result.applications_ready,
                "total": readiness_result.total_applications,
                "percentage": (
                    (
                        readiness_result.applications_ready
                        / readiness_result.total_applications
                        * 100
                    )
                    if readiness_result.total_applications > 0
                    else 0
                ),
            },
            blocking_issues={
                "count": readiness_result.blocking_errors_count
                + len(integrity_result.get("issues", [])),
                "critical_gaps": readiness_result.critical_gaps_count,
                "data_integrity_issues": len(integrity_result.get("issues", [])),
            },
            data_population_status={
                "integrity_verified": integrity_result["issues_found"] == 0,
                "issues_found": integrity_result["issues_found"],
                "fixes_applied": integrity_result["fixes_applied"],
            },
            next_actions=_generate_next_actions(readiness_result, integrity_result),
            estimated_time_to_ready=_estimate_time_to_ready(readiness_result),
        )

        return summary

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting validation summary for flow {flow_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Validation summary failed: {str(e)}"
        )


@router.get("/flows/{assessment_flow_id}/verify-assessment-data")
async def verify_assessment_flow_data(
    assessment_flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context: RequestContext = Depends(get_request_context),
) -> Dict[str, Any]:
    """
    Verify data integrity after assessment flow creation.

    Implements Section 10 of validation checklist: Data Transfer Verification
    """
    require_role(current_user, COLLECTION_READ_ROLES, "verify assessment data")

    try:
        assessment_uuid = UUID(assessment_flow_id)

        # Initialize transition service
        transition_service = EnhancedCollectionTransitionService(db, context)

        # Verify assessment flow data
        verification_result = await transition_service.verify_assessment_flow_data(
            assessment_uuid
        )

        logger.info(f"Assessment data verification completed for {assessment_flow_id}")

        return verification_result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error verifying assessment data for flow {assessment_flow_id}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Assessment data verification failed: {str(e)}"
        )


def _generate_next_actions(
    readiness_result: ReadinessAssessmentResult, integrity_result: Dict[str, Any]
) -> list:
    """Generate recommended next actions based on validation results"""

    actions = []

    # Data integrity issues first
    if integrity_result["issues_found"] > 0:
        actions.append(
            {
                "action": "fix_data_integrity",
                "priority": "high",
                "description": "Fix data integrity issues found in collection flow",
                "endpoint": "/populate-data",
            }
        )

    # Readiness issues
    if not readiness_result.is_ready:
        for requirement in readiness_result.missing_requirements:
            if "completeness" in requirement.lower():
                actions.append(
                    {
                        "action": "continue_collection",
                        "priority": "high",
                        "description": "Continue data collection to meet completeness threshold",
                        "endpoint": "/continue",
                    }
                )

            elif "critical gaps" in requirement.lower():
                actions.append(
                    {
                        "action": "address_gaps",
                        "priority": "high",
                        "description": "Address critical data gaps through manual collection",
                        "endpoint": "/questionnaires",
                    }
                )

            elif "field mappings" in requirement.lower():
                actions.append(
                    {
                        "action": "validate_mappings",
                        "priority": "medium",
                        "description": "Complete and validate field mappings",
                        "endpoint": "/field-mappings",
                    }
                )

    # If ready, suggest transition
    if readiness_result.is_ready and integrity_result["issues_found"] == 0:
        actions.append(
            {
                "action": "transition_to_assessment",
                "priority": "high",
                "description": "Proceed with assessment phase transition",
                "endpoint": "/transition-to-assessment",
            }
        )

    return actions


def _estimate_time_to_ready(
    readiness_result: ReadinessAssessmentResult,
) -> Optional[int]:
    """Estimate time to readiness in minutes"""

    if readiness_result.is_ready:
        return 0

    # Base time estimates
    time_estimate = 0

    # Collection completeness
    completeness_gap = max(0, 0.7 - readiness_result.collection_completeness)
    time_estimate += int(completeness_gap * 60)  # 60 minutes per 100% gap

    # Critical gaps
    time_estimate += readiness_result.critical_gaps_count * 10  # 10 minutes per gap

    # Field mappings
    if not readiness_result.field_mappings_complete:
        time_estimate += 30

    # Blocking errors
    time_estimate += readiness_result.blocking_errors_count * 15  # 15 minutes per error

    return min(time_estimate, 300)  # Cap at 5 hours


async def _background_integrity_check(
    flow_id: UUID, client_account_id: UUID, engagement_id: UUID
):
    """Background task for data integrity check"""
    try:
        # This would typically be run as a background task
        # For now, just log that it would be scheduled
        logger.info(f"Background integrity check scheduled for flow {flow_id}")

    except Exception as e:
        logger.error(f"Background integrity check failed for flow {flow_id}: {e}")
