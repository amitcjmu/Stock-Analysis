"""
Collection Flow CRUD Operations
Core database operations for collection flows including create, read, update, delete,
and flow management operations like execute, continue, and cleanup.
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.rbac_utils import (
    COLLECTION_CREATE_ROLES,
    COLLECTION_DELETE_ROLES,
    require_role,
)
from app.core.security.secure_logging import safe_log_format
from app.models import User
from app.models.asset import Asset
from app.models.collection_flow import (
    AdaptiveQuestionnaire,
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
    CollectionGapAnalysis,
    CollectionPhase,
)
from app.schemas.collection_flow import (
    CollectionFlowCreate,
    CollectionFlowResponse,
    CollectionFlowUpdate,
    CollectionGapAnalysisResponse,
    AdaptiveQuestionnaireResponse,
)

# Import modular functions
from app.api.v1.endpoints import collection_utils
from app.api.v1.endpoints import collection_validators
from app.api.v1.endpoints import collection_serializers

logger = logging.getLogger(__name__)


async def create_collection_from_discovery(
    discovery_flow_id: str,
    selected_application_ids: List[str],
    collection_strategy: Optional[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Create a Collection flow from Discovery results with selected applications.

    This function enables seamless transition from Discovery to Collection,
    allowing users to select applications from the Discovery inventory for
    detailed data collection and gap analysis.

    Args:
        discovery_flow_id: The Discovery flow ID to transition from
        selected_application_ids: List of application IDs to collect data for
        collection_strategy: Optional configuration for collection approach
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse with the created Collection flow details
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "create collection flows")

    try:
        # Validate Discovery flow exists and is complete
        discovery_flow = await collection_validators.validate_discovery_flow_exists(
            db, discovery_flow_id, context.engagement_id
        )

        # Validate selected applications exist and belong to the engagement
        applications = await collection_validators.validate_applications_exist(
            db, selected_application_ids, context.engagement_id
        )

        # Use actual application IDs if none were provided
        if not selected_application_ids:
            selected_application_ids = (
                collection_serializers.extract_application_ids_from_assets(applications)
            )

        # Build collection configuration
        collection_config = (
            collection_serializers.build_collection_config_from_discovery(
                discovery_flow,
                applications,
                selected_application_ids,
                collection_strategy,
            )
        )

        # Create collection flow record
        flow_id = uuid.uuid4()
        flow_name = collection_utils.format_flow_display_name(
            len(selected_application_ids)
        )

        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=flow_name,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=current_user.id,
            created_by=current_user.id,
            status=CollectionFlowStatus.INITIALIZED.value,
            automation_tier=collection_config["automation_tier"],
            collection_config=collection_config,
            current_phase=CollectionPhase.GAP_ANALYSIS.value,  # Start with gap analysis
            discovery_flow_id=uuid.UUID(discovery_flow_id),  # Link to Discovery flow
        )

        db.add(collection_flow)
        await db.commit()
        await db.refresh(collection_flow)

        # Initialize with Master Flow Orchestrator
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
            "start_phase": "gap_analysis",  # Skip platform detection since we have Discovery data
        }

        # Create the flow - it will be automatically started by the execution engine
        master_flow_id, master_flow_data = await collection_utils.create_mfo_flow(
            db, context, "collection", flow_input
        )

        # Update collection flow with master flow ID
        collection_flow.master_flow_id = master_flow_id
        await db.commit()
        await db.refresh(collection_flow)

        logger.info(
            "Created collection flow %s from discovery flow %s with %d applications",
            collection_flow.id,
            discovery_flow_id,
            len(selected_application_ids),
        )

        # Build collection metrics for discovery transition
        collection_metrics = (
            collection_serializers.build_collection_metrics_for_discovery_transition(
                selected_application_ids,
                discovery_flow_id,
                collection_config["automation_tier"],
            )
        )

        return collection_serializers.build_collection_flow_response(
            collection_flow, gaps_identified=0, collection_metrics=collection_metrics
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Error creating collection from discovery: {e}", e=e)
        )
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def ensure_collection_flow(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Return an active Collection flow for the engagement, or create one via MFO.

    This enables seamless navigation from Discovery to Collection without users
    needing to manually start a flow. It reuses any non-completed flow; if none
    exist, it creates a new one and returns it immediately.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse for existing or newly created flow
    """
    require_role(current_user, COLLECTION_CREATE_ROLES, "ensure collection flows")

    # Validate tenant context early
    collection_validators.validate_tenant_context(context)

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
            .limit(1)  # Ensure we only get one row
        )
        existing = result.scalar_one_or_none()

        if existing:
            return collection_serializers.build_collection_flow_response(existing)

        # Otherwise, create a new one (delegates to existing create logic)
        flow_data = CollectionFlowCreate(automation_tier=AutomationTier.TIER_2.value)
        return await create_collection_flow(flow_data, db, current_user, context)

    except HTTPException:
        # Pass through known HTTP exceptions intact
        raise
    except Exception:
        logger.error("Error ensuring collection flow", exc_info=True)
        # Sanitize error exposure
        raise HTTPException(status_code=500, detail="Failed to ensure collection flow")


async def get_collection_status(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Get collection flow status for current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Dictionary with collection status information
    """
    try:
        # Get active collection flow - use first() to handle multiple rows
        result = await db.execute(
            select(CollectionFlow)
            .where(
                CollectionFlow.engagement_id == context.engagement_id,
                CollectionFlow.status != CollectionFlowStatus.COMPLETED.value,
            )
            .order_by(CollectionFlow.created_at.desc())
            .limit(1)  # Ensure we only get one row
        )
        collection_flow = result.scalar_one_or_none()

        if not collection_flow:
            return collection_serializers.build_no_active_flow_response()

        return collection_serializers.build_collection_status_response(collection_flow)

    except Exception as e:
        logger.error(safe_log_format("Error getting collection status: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def create_collection_flow(
    flow_data: CollectionFlowCreate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Create and start a new collection flow.

    Args:
        flow_data: Collection flow creation data
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse for the created flow
    """
    # Check RBAC - only analysts and above can create collection flows
    require_role(current_user, COLLECTION_CREATE_ROLES, "create collection flows")

    logger.info(
        "🚀 Creating collection flow - automation_tier: %s, config keys: %s",
        flow_data.automation_tier,
        list((flow_data.collection_config or {}).keys()),
    )
    try:
        # Check for existing active flow
        existing_flow = await collection_validators.check_for_existing_active_flow(
            db, context.engagement_id
        )

        if existing_flow:
            # Check if the existing flow is stuck in INITIALIZED state
            if collection_utils.is_flow_stuck_in_initialization(existing_flow):
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
                if existing_flow.status == CollectionFlowStatus.INITIALIZED.value:
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
        flow_name = collection_utils.format_flow_display_name(
            0
        )  # No application count for new flows

        collection_flow = CollectionFlow(
            flow_id=flow_id,
            flow_name=flow_name,
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

        # Start the collection flow through MFO
        flow_input = {
            "flow_id": str(collection_flow.flow_id),
            "automation_tier": collection_flow.automation_tier,
            "collection_config": collection_flow.collection_config,
        }

        # Create the flow
        master_flow_id, master_flow_data = await collection_utils.create_mfo_flow(
            db, context, "collection", flow_input
        )

        # Update collection flow with master flow ID
        collection_flow.master_flow_id = master_flow_id
        await db.commit()
        await db.refresh(collection_flow)

        # Start the flow execution immediately
        try:
            logger.info(
                "Starting execution for collection flow %s (master flow %s)",
                collection_flow.id,
                master_flow_id,
            )

            # Execute the initialization phase
            execution_result = await collection_utils.execute_mfo_phase(
                db, context, str(collection_flow.flow_id), "initialization", flow_input
            )

            # Update flow status based on next phase
            next_phase = execution_result.get(
                "next_phase", CollectionPhase.PLATFORM_DETECTION.value
            )
            collection_flow.current_phase = next_phase
            collection_flow.status = collection_utils.determine_next_phase_status(
                next_phase
            )

            await db.commit()
            await db.refresh(collection_flow)

            logger.info(
                "Successfully started collection flow %s with initial phase %s",
                collection_flow.id,
                collection_flow.current_phase,
            )
        except Exception as e:
            logger.error(f"Failed to start collection flow execution: {e}")
            # Flow is created but not started - user can manually start it later

        logger.info(
            "Created collection flow %s linked to master flow %s for engagement %s",
            collection_flow.id,
            master_flow_id,
            context.engagement_id,
        )

        return collection_serializers.build_collection_flow_response(collection_flow)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error creating collection flow: {e}", e=e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Get collection flow details.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        CollectionFlowResponse with flow details
    """
    try:
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Get gap analysis if available
        gaps_result = await db.execute(
            select(CollectionGapAnalysis).where(
                CollectionGapAnalysis.collection_flow_id == collection_flow.id
            )
        )
        gap_list = gaps_result.scalars().all()

        # Build collection metrics
        collection_metrics = {
            "platforms_detected": len(
                collection_flow.collection_config.get("detected_platforms", [])
            ),
            "data_collected": collection_flow.collection_quality_score or 0,
            "gaps_resolved": 0,  # CollectionGapAnalysis doesn't have resolution_status
        }

        return collection_serializers.build_collection_flow_response(
            collection_flow,
            gaps_identified=len(gap_list),
            collection_metrics=collection_metrics,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error getting collection flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def update_collection_flow(
    flow_id: str,
    update_data: CollectionFlowUpdate,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> CollectionFlowResponse:
    """Update collection flow (e.g., provide user input, continue flow).

    Args:
        flow_id: Collection flow ID
        update_data: Update data
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Updated CollectionFlowResponse
    """
    try:
        # Get the flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Handle different update types
        if update_data.action == "continue":
            # Continue flow execution through MFO
            await collection_utils.resume_mfo_flow(
                db, context, flow_id, update_data.user_input or {}
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

        return collection_serializers.build_collection_flow_response(collection_flow)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error updating collection flow: {e}", e=e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def execute_collection_flow(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Execute a collection flow phase through Master Flow Orchestrator.

    This function triggers actual CrewAI execution of the collection flow,
    enabling phase progression and questionnaire generation.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Execution result dictionary
    """
    try:
        # Get the collection flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be executed
        await collection_validators.validate_flow_can_be_executed(collection_flow)

        # Execute the current phase
        current_phase = collection_flow.current_phase or "initialization"
        execution_result = await collection_utils.execute_mfo_phase(
            db, context, flow_id, current_phase, {}
        )

        logger.info(
            f"Executed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_execution_response(
            flow_id, execution_result
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error executing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_gaps(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[CollectionGapAnalysisResponse]:
    """Get gap analysis results for a collection flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of gap analysis responses
    """
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

        return [collection_serializers.build_gap_analysis_response(gap) for gap in gaps]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error getting collection gaps: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_adaptive_questionnaires(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[AdaptiveQuestionnaireResponse]:
    """Get adaptive questionnaires for manual collection.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of questionnaire responses
    """
    try:
        # Get flow by flow_id (not database id)
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Get questionnaires using the database id
        result = await db.execute(
            select(AdaptiveQuestionnaire)
            .where(AdaptiveQuestionnaire.collection_flow_id == collection_flow.id)
            .order_by(AdaptiveQuestionnaire.created_at.desc())
        )
        questionnaires = result.scalars().all()

        return [
            collection_serializers.build_questionnaire_response(q)
            for q in questionnaires
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error getting questionnaires: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def submit_questionnaire_response(
    flow_id: str,
    questionnaire_id: str,
    responses: Dict[str, Any],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Submit responses to an adaptive questionnaire.

    Args:
        flow_id: Collection flow ID
        questionnaire_id: Questionnaire ID
        responses: Questionnaire responses
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Submission response dictionary
    """
    try:
        # Validate responses structure
        collection_validators.validate_questionnaire_responses(responses)

        # First get the collection flow to get its database id
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Get questionnaire using the database id
        result = await db.execute(
            select(AdaptiveQuestionnaire).where(
                AdaptiveQuestionnaire.id == uuid.UUID(questionnaire_id),
                AdaptiveQuestionnaire.collection_flow_id == collection_flow.id,
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
        await collection_utils.resume_mfo_flow(
            db,
            context,
            flow_id,
            {"questionnaire_responses": {questionnaire_id: responses}},
        )

        await db.commit()

        return collection_serializers.build_questionnaire_submission_response(
            questionnaire_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format("Error submitting questionnaire response: {e}", e=e)
        )
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_collection_readiness(
    flow_id: str,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Read-only readiness and quality summary for a collection flow.

    Returns engagement-scoped readiness counts and validator phase scores for
    collection→discovery, plus quality/confidence stored on the flow.

    Args:
        flow_id: Collection flow ID
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Readiness response dictionary
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
            client_uuid, engagement_uuid = collection_serializers.normalize_tenant_ids(
                context.client_account_id, context.engagement_id
            )
        except ValueError:
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
            logger.warning(safe_log_format("Readiness count unavailable: {e}", e=e))
            apps_ready = 0

        # Run validator for collection/discovery phases
        validation_results = await collection_utils.validate_data_flow(
            db, context.engagement_id, {"collection", "discovery"}
        )

        # Log failure if validation failed (best-effort)
        if validation_results["phase_scores"]["collection"] == 0.0:
            await collection_utils.log_collection_failure(
                db,
                context,
                "collection_readiness",
                "validator",
                {"flow_id": flow_id},
                "Validator unavailable",
            )

        return collection_serializers.build_readiness_response(
            flow_id,
            context.engagement_id,
            apps_ready,
            collection_flow,
            validation_results,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Error getting collection readiness: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def get_incomplete_flows(
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> List[CollectionFlowResponse]:
    """Get all incomplete collection flows for the current engagement.

    Args:
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        List of incomplete collection flow responses
    """
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
            collection_serializers.build_collection_flow_response(flow)
            for flow in incomplete_flows
        ]

    except Exception as e:
        logger.error(safe_log_format("Error getting incomplete flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


async def continue_flow(
    flow_id: str,
    resume_context: Optional[Dict[str, Any]],
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Continue/resume a paused or incomplete collection flow.

    Args:
        flow_id: Collection flow ID
        resume_context: Optional context for resuming
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Continue flow response dictionary
    """
    try:
        # Verify flow exists and belongs to engagement
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be resumed
        await collection_validators.validate_flow_can_be_resumed(collection_flow)

        # Resume flow through MFO
        result = await collection_utils.resume_mfo_flow(
            db, context, flow_id, resume_context or {}
        )

        logger.info(
            f"Resumed collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_continue_flow_response(flow_id, result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error continuing collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


async def delete_flow(
    flow_id: str,
    force: bool,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Delete a collection flow and all related data.

    Args:
        flow_id: Collection flow ID
        force: Force delete even if flow is active
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Delete flow response dictionary
    """
    # Check RBAC - only managers and above can delete collection flows
    require_role(current_user, COLLECTION_DELETE_ROLES, "delete collection flows")

    try:
        # Get the flow
        collection_flow = await collection_validators.validate_collection_flow_exists(
            db, flow_id, context.engagement_id
        )

        # Check if flow can be deleted
        await collection_validators.validate_flow_can_be_deleted(collection_flow, force)

        # Delete through MFO if flow is managed there
        await collection_utils.delete_mfo_flow(db, context, flow_id)

        # Delete from database (cascade will handle related records)
        await db.delete(collection_flow)
        await db.commit()

        logger.info(
            f"Deleted collection flow {flow_id} for engagement {context.engagement_id}"
        )

        return collection_serializers.build_delete_flow_response(flow_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Error deleting collection flow {flow_id}: {e}", flow_id=flow_id, e=e
            )
        )
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def cleanup_flows(
    expiration_hours: int,
    dry_run: bool,
    include_failed: bool,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Clean up expired collection flows.

    Args:
        expiration_hours: Hours after which flows are considered expired
        dry_run: Preview cleanup without actually deleting
        include_failed: Include failed flows in cleanup
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Cleanup response dictionary
    """
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
            flow_details = collection_serializers.build_cleanup_flow_details(flow)
            flows_to_clean.append(flow_details)
            total_size += flow_details["estimated_size"]

        if not dry_run and flows_to_clean:
            # Perform actual cleanup
            for flow in expired_flows:
                # Try to cleanup from MFO first
                await collection_utils.delete_mfo_flow(db, context, str(flow.flow_id))
                # Delete from database
                await db.delete(flow)

            await db.commit()
            logger.info(
                safe_log_format(
                    "Cleaned up {len_flows_to_clean} expired collection flows",
                    len_flows_to_clean=len(flows_to_clean),
                )
            )

        cleanup_criteria = {
            "expiration_hours": expiration_hours,
            "include_failed": include_failed,
            "cutoff_time": cutoff_time.isoformat(),
        }

        return collection_serializers.build_cleanup_response(
            flows_to_clean, total_size, dry_run, cleanup_criteria
        )

    except Exception as e:
        logger.error(safe_log_format("Error during collection flow cleanup: {e}", e=e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def batch_delete_flows(
    flow_ids: List[str],
    force: bool,
    db: AsyncSession,
    current_user: User,
    context: RequestContext,
) -> Dict[str, Any]:
    """Delete multiple collection flows in batch.

    Args:
        flow_ids: List of flow IDs to delete
        force: Force delete even if flows are active
        db: Database session
        current_user: Current authenticated user
        context: Request context

    Returns:
        Batch delete response dictionary
    """
    try:
        deleted_flows = []
        failed_deletions = []

        # Validate flows for batch deletion
        valid_flows, invalid_flow_ids = (
            await collection_validators.validate_batch_delete_permissions(
                flow_ids, context.engagement_id, db
            )
        )

        # Add invalid flow IDs to failed deletions
        for invalid_id in invalid_flow_ids:
            failed_deletions.append({"flow_id": invalid_id, "error": "Flow not found"})

        # Process valid flows
        for flow in valid_flows:
            try:
                flow_id = str(flow.id)  # Using database id for batch delete

                # Check if flow can be deleted
                if not force:
                    await collection_validators.validate_flow_can_be_deleted(
                        flow, force
                    )

                # Delete through MFO if possible
                await collection_utils.delete_mfo_flow(db, context, flow_id)

                # Delete from database
                await db.delete(flow)
                deleted_flows.append(flow_id)

            except HTTPException as e:
                failed_deletions.append({"flow_id": str(flow.id), "error": e.detail})
            except Exception as e:
                failed_deletions.append({"flow_id": str(flow.id), "error": str(e)})

        await db.commit()

        logger.info(
            f"Batch deleted {len(deleted_flows)} collection flows, {len(failed_deletions)} failures"
        )

        return collection_serializers.build_batch_delete_response(
            deleted_flows, failed_deletions
        )

    except Exception as e:
        logger.error(safe_log_format("Error in batch delete: {e}", e=e))
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
