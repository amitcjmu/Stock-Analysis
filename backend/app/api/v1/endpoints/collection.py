"""
Collection Flow API Endpoints
Provides API interface for the Adaptive Data Collection System (ADCS)
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.auth_utils import get_current_user
from app.core.context import get_request_context
from app.core.database import get_db
from app.core.rbac_utils import (
    COLLECTION_CREATE_ROLES,
    COLLECTION_DELETE_ROLES,
    require_role,
)
from app.models import User
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
    CollectionGapAnalysis,
    CollectionPhase,
)
from app.models.asset import Asset

# from app.services.flow_state_service import FlowStateService
from app.schemas.collection_flow import (
    AdaptiveQuestionnaireResponse,
    CollectionFlowCreate,
    CollectionFlowResponse,
    CollectionFlowUpdate,
    CollectionGapAnalysisResponse,
)

# from app.services.workflow_orchestration.collection_phase_engine import CollectionPhaseEngine
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.integration.data_flow_validator import DataFlowValidator
from uuid import UUID
from app.services.integration.failure_journal import log_failure

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/flows/ensure", response_model=CollectionFlowResponse)
async def ensure_collection_flow(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery to Collection without users
    needing to manually start a flow. It reuses any non-completed flow; if none
    exist, it creates a new one and returns it immediately.
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "ensure collection flows")

    # Validate tenant context early
    if not getattr(context, "client_account_id", None) or not getattr(
        context, "engagement_id", None
    ):
        raise HTTPException(
            status_code=400, detail="Missing tenant context identifiers"
        )

    try:
        # Try to find an active collection flow for this engagement
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.client_account_id == context.client_account_id,
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
        )
        existing = result.scalar_one_or_none()

        if existing:
            return CollectionFlowResponse(
                id=str(existing.id),
                client_account_id=str(existing.client_account_id),
                engagement_id=str(existing.engagement_id),
                status=existing.status,
                automation_tier=existing.automation_tier,
                current_phase=existing.current_phase,
                progress=existing.progress_percentage or 0,
                collection_config=existing.collection_config,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
                completed_at=existing.completed_at,
            )

        # Otherwise, create a new one (delegates to existing create logic)
        return await create_collection_flow(
            flow_data=CollectionFlowCreate(automation_tier=AutomationTier.TIER_2.value),
            db=db,
            current_user=current_user,
            context=context,
        )

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")


@router.get("/status", response_model=Dict[str, Any])
async def get_collection_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Get collection flow status for current engagement"""
    try:
        # Get active collection flow
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status != CollectionFlowStatus.COMPLETED.value,
            )
            .order_by(CollectionFlow.created_at.desc())
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            return {
                "status": "no_active_flow",
                "message": "No active collection flow found",
            }

        return {
            "flow_id": str(collection_flow.id),
            "status": collection_flow.status,
            "current_phase": collection_flow.current_phase,
            "automation_tier": collection_flow.automation_tier,
            "progress": collection_flow.progress_percentage or 0,
            "created_at": collection_flow.created_at.isoformat(),
            "updated_at": collection_flow.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows", response_model=CollectionFlowResponse)
async def create_collection_flow(
    flow_data: CollectionFlowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Create and start a new collection flow"""
    # Check RBAC - only analysts and above can create collection flows
    require_role(current_user, COLLECTION_CREATE_ROLES, "create collection flows")

    logger.info(
        "🚀 Creating collection flow - automation_tier: %s, config keys: %s",
        flow_data.automation_tier,
        list((flow_data.collection_config or {}).keys()),
    )
    try:
        # Check for existing active flow
        existing = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.FAILED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
        )
        existing_flow = existing.scalar_one_or_none()

        if existing_flow:
            # Check if the existing flow is stuck in INITIALIZED state
            if existing_flow.status == CollectionFlowStatus.INITIALIZED.value:
                # Calculate time since creation
                # Ensure we're comparing timezone-aware datetimes
                now = datetime.now(timezone.utc)
                created_at = existing_flow.created_at
                if created_at.tzinfo is None:
                    # If created_at is timezone-naive, assume UTC
                    created_at = created_at.replace(tzinfo=timezone.utc)
                time_since_creation = now - created_at

                # If flow is stuck in INITIALIZED for more than 5 minutes, cancel it
                if time_since_creation > timedelta(minutes=5):
                    logger.warning(
                        f"Found stale INITIALIZED flow {existing_flow.id}, cancelling it"
                    )
                    existing_flow.status = CollectionFlowStatus.CANCELLED.value
                    existing_flow.completed_at = datetime.now(timezone.utc)
                    existing_flow.error_message = (
                        "Flow cancelled due to initialization timeout"
                    )
                    await db.commit()
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "An active collection flow is being initialized. "
                            "Please wait or use the flow management UI to cancel it."
                        ),
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"An active collection flow already exists with status: {existing_flow.status}",
                )

        # Create collection flow record
        flow_id = uuid.uuid4()
        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=f"Collection Flow - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,  # This is the required field, not created_by
            created_by=current_user.id,
            status=CollectionFlowStatus.INITIALIZED.value,
            automation_tier=flow_data.automation_tier or AutomationTier.TIER_2.value,
            collection_config=flow_data.collection_config or {},
            current_phase=CollectionPhase.INITIALIZATION.value,
        )

        db.add(collection_flow)
        await db.commit()
        await db.refresh(collection_flow)

        # Initialize with Master Flow Orchestrator
        mfo = MasterFlowOrchestrator(db, context)

        # Start the collection flow through MFO
        flow_input = {
            "flow_id": str(collection_flow.id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
        }

        # Create the flow - it will be automatically started by the execution engine
        master_flow_id, master_flow_data = await mfo.create_flow(
            flow_type="collection", initial_state=flow_input
        )

        # Update collection flow with master flow ID
        collection_flow.master_flow_id = master_flow_id
        await db.commit()
        await db.refresh(collection_flow)

        logger.info(
            "Created collection flow %s linked to master flow %s for engagement %s - execution started",
            collection_flow.id,
            master_flow_id,
            context.engagement_id,
        )

        return CollectionFlowResponse(
            id=str(collection_flow.id),
            client_account_id=str(collection_flow.client_account_id),
            engagement_id=str(collection_flow.engagement_id),
            status=collection_flow.status,
            automation_tier=collection_flow.automation_tier,
            current_phase=collection_flow.current_phase,
            progress=collection_flow.progress_percentage or 0,
            collection_config=collection_flow.collection_config,
            created_at=collection_flow.created_at,
            updated_at=collection_flow.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating collection flow: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}", response_model=CollectionFlowResponse)
async def get_collection_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Get collection flow details"""
    try:
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get gap analysis if available
        gaps = await db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )
        gap_list = gaps.scalars().all()

        response = CollectionFlowResponse(
            id=str(collection_flow.id),
            client_account_id=str(collection_flow.client_account_id),
            engagement_id=str(collection_flow.engagement_id),
            status=collection_flow.status,
            automation_tier=collection_flow.automation_tier,
            current_phase=collection_flow.current_phase,
            progress=collection_flow.progress_percentage or 0,
            collection_config=collection_flow.collection_config,
            created_at=collection_flow.created_at,
            updated_at=collection_flow.updated_at,
            completed_at=collection_flow.completed_at,
            gaps_identified=len(gap_list),
            collection_metrics={
                "platforms_detected": len(
                    collection_flow.collection_config.get("detected_platforms", [])
                ),
                "data_collected": collection_flow.collection_quality_score or 0,
                "gaps_resolved": 0,  # CollectionGapAnalysis doesn't have resolution_status
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/flows/{flow_id}", response_model=CollectionFlowResponse)
async def update_collection_flow(
    flow_id: str,
    update_data: CollectionFlowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> CollectionFlowResponse:
    """Update collection flow (e.g., provide user input, continue flow)"""
    try:
        # Get the flow
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Handle different update types
        if update_data.action == "continue":
            # Continue flow execution through MFO
            mfo = MasterFlowOrchestrator(db, context)
            result = await mfo.resume_flow(
                flow_id=flow_id, resume_context=update_data.user_input or {}
            )

        elif update_data.action == "pause":
            # Note: There's no PAUSED status in the enum, keep current status
            collection_flow.updated_at = datetime.now(timezone.utc)

        elif update_data.action == "cancel":
            collection_flow.status = CollectionFlowStatus.CANCELLED.value
            collection_flow.updated_at = datetime.now(timezone.utc)
            collection_flow.completed_at = datetime.now(timezone.utc)

        # Update any provided data
        if update_data.collection_config:
            collection_flow.collection_config.update(update_data.collection_config)

        await db.commit()
        await db.refresh(collection_flow)

        return CollectionFlowResponse(
            id=str(collection_flow.id),
            client_account_id=str(collection_flow.client_account_id),
            engagement_id=str(collection_flow.engagement_id),
            status=collection_flow.status,
            automation_tier=collection_flow.automation_tier,
            current_phase=collection_flow.current_phase,
            progress=collection_flow.progress_percentage or 0,
            collection_config=collection_flow.collection_config,
            created_at=collection_flow.created_at,
            updated_at=collection_flow.updated_at,
            completed_at=collection_flow.completed_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating collection flow: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/gaps", response_model=List[CollectionGapAnalysisResponse])
async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[CollectionGapAnalysisResponse]:
    """Get gap analysis results for a collection flow"""
    try:
        # Verify flow exists and belongs to engagement
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        if not flow_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get gaps
        result = await db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == uuid.UUID(flow_id)
            )
        )
        gaps = result.scalars().all()

        return [
            CollectionGapAnalysisResponse(
                id=str(gap.id),
                collection_flow_id=str(gap.collection_flow_id),
                attribute_name=gap.attribute_name,
                attribute_category=gap.attribute_category,
                business_impact=gap.business_impact,
                priority=gap.priority,
                collection_difficulty=gap.collection_difficulty,
                affects_strategies=gap.affects_strategies,
                blocks_decision=gap.blocks_decision,
                recommended_collection_method=gap.recommended_collection_method,
                resolution_status=gap.resolution_status,
                created_at=gap.created_at,
            )
            for gap in gaps
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/flows/{flow_id}/questionnaires",
    response_model=List[AdaptiveQuestionnaireResponse],
)
async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for manual collection"""
    try:
        # Verify flow exists
        flow_result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        if not flow_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Get questionnaires
        result = await db.execute(
            select(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.collection_flow_id == uuid.UUID(flow_id))
            .order_by(AdaptiveQuestionnaire.created_at.desc())
        )
        questionnaires = result.scalars().all()

        return [
            AdaptiveQuestionnaireResponse(
                id=str(q.id),
                collection_flow_id=str(q.collection_flow_id),
                title=q.title,
                description=q.description,
                target_gaps=q.target_gaps,
                questions=q.questions,
                validation_rules=q.validation_rules,
                completion_status=q.completion_status,
                responses_collected=q.responses_collected,
                created_at=q.created_at,
                completed_at=q.completed_at,
            )
            for q in questionnaires
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting questionnaires: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/questionnaires/{questionnaire_id}/submit")
async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    responses: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire"""
    try:
        # Get questionnaire
        result = await db.execute(
            select(AdaptiveQuestionnaire).where(
                AdaptiveQuestionnaire.id == uuid.UUID(questionnaire_id),
                AdaptiveQuestionnaire.collection_flow_id == uuid.UUID(flow_id),
            )
        )
        questionnaire = result.scalar_one_or_none()

        if not questionnaire:
            raise HTTPException(status_code=404, detail="Questionnaire not found")

        # Update questionnaire with responses
        questionnaire.responses_collected = responses
        questionnaire.completion_status = "completed"
        questionnaire.completed_at = datetime.now(timezone.utc)
        questionnaire.updated_at = datetime.now(timezone.utc)

        # Continue flow with questionnaire responses
        mfo = MasterFlowOrchestrator(db, context)
        result = await mfo.resume_flow(
            flow_id=flow_id,
            resume_context={"questionnaire_responses": {questionnaire_id: responses}},
        )

        await db.commit()

        return {
            "status": "success",
            "message": "Questionnaire responses submitted successfully",
            "questionnaire_id": questionnaire_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting questionnaire response: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/readiness")
async def get_collection_readiness(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Read-only readiness and quality summary for a collection flow.

    Returns engagement-scoped readiness counts and validator phase scores for
    collection→discovery, plus quality/confidence stored on the flow.
    """
    try:
        # Verify flow belongs to engagement
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()
        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Normalize tenant IDs to UUIDs
        try:
            client_uuid = UUID(str(context.client_account_id))
            engagement_uuid = UUID(str(context.engagement_id))
        except Exception:
            raise HTTPException(
                status_code=400, detail="Invalid tenant identifiers in context"
            )

        # Count assessment-ready assets for engagement (best-effort)
        try:
            ready_count_row = await db.execute(
                select(func.count(Asset.id)).where(
                    Asset.client_account_id == client_uuid,
                    Asset.engagement_id == engagement_uuid,
                    Asset.assessment_readiness == "ready",
                )
            )
            apps_ready = int(ready_count_row.scalar() or 0)
        except Exception as e:
            logger.warning(f"Readiness count unavailable: {e}")
            apps_ready = 0

        # Run validator for collection/discovery phases
        try:
            validator = DataFlowValidator()
            validation = await validator.validate_end_to_end_data_flow(
                engagement_id=context.engagement_id,
                validation_scope={"collection", "discovery"},
            )
            phase_scores = validation.phase_scores
            issues = {
                "total": len(validation.issues),
                "critical": len(
                    [i for i in validation.issues if i.severity.value == "critical"]
                ),
                "warning": len(
                    [i for i in validation.issues if i.severity.value == "warning"]
                ),
                "info": len(
                    [i for i in validation.issues if i.severity.value == "info"]
                ),
            }
            # Extended readiness details
            readiness = {
                "architecture_minimums_present": validation.summary.get(
                    "architecture_minimums_present", False
                ),
                "missing_fields": validation.summary.get("missing_fields", []),
                "readiness_score": validation.summary.get("readiness_score", 0.0),
            }
        except Exception as e:  # validator is best-effort
            logger.warning(f"Validator unavailable for readiness: {e}")
            phase_scores = {"collection": 0.0, "discovery": 0.0}
            issues = {"total": 0, "critical": 0, "warning": 0, "info": 0}
            readiness = {
                "architecture_minimums_present": False,
                "missing_fields": [],
                "readiness_score": 0.0,
            }
            # Log to failure journal (best-effort)
            await log_failure(
                db,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id,
                source="collection_readiness",
                operation="validator",
                payload={"flow_id": flow_id},
                error_message=str(e),
            )

        return {
            "flow_id": flow_id,
            "engagement_id": str(context.engagement_id),
            "apps_ready_for_assessment": apps_ready,
            "quality": {
                "collection_quality_score": collection_flow.collection_quality_score
                or 0.0,
                "confidence_score": collection_flow.confidence_score or 0.0,
            },
            "phase_scores": phase_scores,
            "issues": issues,
            "readiness": readiness,
            "updated_at": collection_flow.updated_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collection readiness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# COLLECTION FLOW LIFECYCLE MANAGEMENT
# ========================================


@router.get("/incomplete", response_model=List[CollectionFlowResponse])
async def get_incomplete_flows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> List[CollectionFlowResponse]:
    """Get all incomplete collection flows for the current engagement"""
    try:
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status.notin_(
                    [
                        CollectionFlowStatus.COMPLETED.value,
                        CollectionFlowStatus.CANCELLED.value,
                    ]
                ),
            )
            .order_by(CollectionFlow.created_at.desc())
        )
        incomplete_flows = result.scalars().all()

        return [
            CollectionFlowResponse(
                id=str(flow.id),
                client_account_id=str(flow.client_account_id),
                engagement_id=str(flow.engagement_id),
                status=flow.status,
                automation_tier=flow.automation_tier,
                current_phase=flow.current_phase,
                progress=flow.progress_percentage or 0,
                collection_config=flow.collection_config,
                created_at=flow.created_at,
                updated_at=flow.updated_at,
                completed_at=flow.completed_at,
            )
            for flow in incomplete_flows
        ]

    except Exception as e:
        logger.error(f"Error getting incomplete flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/continue")
async def continue_flow(
    flow_id: str,
    resume_context: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Continue/resume a paused or incomplete collection flow"""
    try:
        # Verify flow exists and belongs to engagement
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Check if flow can be resumed
        if collection_flow.status in [
            CollectionFlowStatus.COMPLETED.value,
            CollectionFlowStatus.CANCELLED.value,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot resume flow with status: {collection_flow.status}",
            )

        # Resume flow through MFO
        mfo = MasterFlowOrchestrator(db, context)
        result = await mfo.resume_flow(
            flow_id=flow_id, resume_context=resume_context or {}
        )

        logger.info(
            f"Resumed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return {
            "status": "success",
            "message": "Collection flow resumed successfully",
            "flow_id": flow_id,
            "resume_result": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error continuing collection flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flows/{flow_id}")
async def delete_flow(
    flow_id: str,
    force: bool = Query(False, description="Force delete even if flow is active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Delete a collection flow and all related data"""
    # Check RBAC - only managers and above can delete collection flows
    require_role(current_user, COLLECTION_DELETE_ROLES, "delete collection flows")

    try:
        # Get the flow
        result = await db.execute(
            select(CollectionFlow).where(
                CollectionFlow.id == uuid.UUID(flow_id),
                CollectionFlow.engagement_id == context.engagement_id,
            )
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            raise HTTPException(status_code=404, detail="Collection flow not found")

        # Check if flow can be deleted
        if not force and collection_flow.status in [
            CollectionFlowStatus.PLATFORM_DETECTION.value,
            CollectionFlowStatus.AUTOMATED_COLLECTION.value,
            CollectionFlowStatus.GAP_ANALYSIS.value,
        ]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete active flow. Use force=true to override.",
            )

        # Delete through MFO if flow is managed there
        try:
            mfo = MasterFlowOrchestrator(db, context)
            await mfo.delete_flow(flow_id)
        except Exception as e:
            logger.warning(f"MFO deletion failed for flow {flow_id}: {e}")
            # Continue with DB deletion even if MFO fails

        # Delete from database (cascade will handle related records)
        await db.delete(collection_flow)
        await db.commit()

        logger.info(
            f"Deleted collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return {
            "status": "success",
            "message": "Collection flow deleted successfully",
            "flow_id": flow_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting collection flow {flow_id}: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_flows(
    expiration_hours: int = Query(
        72, description="Hours after which flows are considered expired"
    ),
    dry_run: bool = Query(
        True, description="Preview cleanup without actually deleting"
    ),
    include_failed: bool = Query(True, description="Include failed flows in cleanup"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Clean up expired collection flows"""
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=expiration_hours)

        # Build query for expired flows
        query = select(CollectionFlow).where(
            CollectionFlow.engagement_id == context.engagement_id,
            CollectionFlow.updated_at < cutoff_time,
        )

        # Add status filters
        status_filters = [CollectionFlowStatus.CANCELLED.value]
        if include_failed:
            status_filters.append(CollectionFlowStatus.FAILED.value)

        query = query.where(CollectionFlow.status.in_(status_filters))

        result = await db.execute(query)
        expired_flows = result.scalars().all()

        flows_to_clean = []
        total_size = 0

        for flow in expired_flows:
            flow_data = {
                "flow_id": str(flow.id),
                "status": flow.status,
                "age_hours": (
                    datetime.now(timezone.utc) - flow.updated_at
                ).total_seconds()
                / 3600,
                "estimated_size": len(str(flow.collection_config))
                + len(str(flow.phase_state))
                + len(str(flow.collection_results)),
            }
            flows_to_clean.append(flow_data)
            total_size += flow_data["estimated_size"]

        if not dry_run and flows_to_clean:
            # Perform actual cleanup
            for flow in expired_flows:
                try:
                    # Try to cleanup from MFO first
                    mfo = MasterFlowOrchestrator(db, context)
                    await mfo.delete_flow(str(flow.id))
                except Exception as e:
                    logger.warning(f"MFO cleanup failed for flow {flow.id}: {e}")

                # Delete from database
                await db.delete(flow)

            await db.commit()
            logger.info(f"Cleaned up {len(flows_to_clean)} expired collection flows")

        return {
            "status": "success",
            "dry_run": dry_run,
            "flows_cleaned": len(flows_to_clean),
            "total_size_bytes": total_size,
            "space_recovered": (
                f"{total_size / 1024:.1f} KB" if total_size > 0 else "0 KB"
            ),
            "flows_details": flows_to_clean,
            "cleanup_criteria": {
                "expiration_hours": expiration_hours,
                "include_failed": include_failed,
                "cutoff_time": cutoff_time.isoformat(),
            },
        }

    except Exception as e:
        logger.error(f"Error during collection flow cleanup: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/batch-delete")
async def batch_delete_flows(
    flow_ids: List[str],
    force: bool = Query(False, description="Force delete even if flows are active"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    context=Depends(get_request_context),
) -> Dict[str, Any]:
    """Delete multiple collection flows in batch"""
    try:
        deleted_flows = []
        failed_deletions = []

        for flow_id in flow_ids:
            try:
                # Get the flow
                result = await db.execute(
                    select(CollectionFlow).where(
                        CollectionFlow.id == uuid.UUID(flow_id),
                        CollectionFlow.engagement_id == context.engagement_id,
                    )
                )
                collection_flow = result.scalar_one_or_none()

                if not collection_flow:
                    failed_deletions.append(
                        {"flow_id": flow_id, "error": "Flow not found"}
                    )
                    continue

                # Check if flow can be deleted
                if not force and collection_flow.status in [
                    CollectionFlowStatus.PLATFORM_DETECTION.value,
                    CollectionFlowStatus.AUTOMATED_COLLECTION.value,
                    CollectionFlowStatus.GAP_ANALYSIS.value,
                ]:
                    failed_deletions.append(
                        {
                            "flow_id": flow_id,
                            "error": "Cannot delete active flow without force flag",
                        }
                    )
                    continue

                # Delete through MFO if possible
                try:
                    mfo = MasterFlowOrchestrator(db, context)
                    await mfo.delete_flow(flow_id)
                except Exception as e:
                    logger.warning(f"MFO deletion failed for flow {flow_id}: {e}")

                # Delete from database
                await db.delete(collection_flow)
                deleted_flows.append(flow_id)

            except Exception as e:
                failed_deletions.append({"flow_id": flow_id, "error": str(e)})

        await db.commit()

        logger.info(
            f"Batch deleted {len(deleted_flows)} collection flows, {len(failed_deletions)} failures"
        )

        return {
            "status": "success",
            "deleted_count": len(deleted_flows),
            "failed_count": len(failed_deletions),
            "deleted_flows": deleted_flows,
            "failed_deletions": failed_deletions,
        }

    except Exception as e:
        logger.error(f"Error in batch delete: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
