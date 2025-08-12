"""
Flow Recovery and Validation API Endpoints

This module provides API endpoints for flow state validation, recovery, and routing
to handle critical flow routing issues where Discovery Flow fails on attribute mapping
when resuming from incomplete initialization phase.

CC Enhanced for critical flow routing issue resolution.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.security.secure_logging import mask_id, safe_log_format
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

logger = get_logger(__name__)
router = APIRouter()


class FlowValidationRequest(BaseModel):
    """Request model for flow validation"""

    flow_id: str
    validate_routing: bool = True
    check_consistency: bool = True


class FlowRecoveryRequest(BaseModel):
    """Request model for flow recovery"""

    flow_id: str
    recovery_type: str = "automatic"  # automatic, manual, diagnostic
    force_recovery: bool = False


class PhaseTransitionRequest(BaseModel):
    """Request model for phase transition validation"""

    flow_id: str
    from_phase: str
    to_phase: str


class BulkFlowDeleteRequest(BaseModel):
    """Request model for bulk flow deletion"""

    flowIds: List[str]


class BlockingFlow(BaseModel):
    """Model representing a blocking flow"""

    flow_id: str
    phase: str
    status: str
    created_at: str
    issue: str


class BlockingFlowsResponse(BaseModel):
    """Response model for blocking flows detection"""

    blocking_flows: List[BlockingFlow]
    count: int


class FlowDeleteResponse(BaseModel):
    """Response model for single flow deletion"""

    success: bool
    message: str
    flow_id: str


class FlowDeleteResult(BaseModel):
    """Individual flow deletion result"""

    flowId: str
    success: bool
    message: str


class BulkFlowDeleteResponse(BaseModel):
    """Response model for bulk flow deletion"""

    success: bool
    message: str
    results: List[FlowDeleteResult]


@router.post("/validate/{flow_id}")
async def validate_flow_state(
    flow_id: str,
    request: FlowValidationRequest = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Validate flow state consistency and detect initialization issues.

    This endpoint analyzes a flow for initialization issues, state inconsistencies,
    and provides routing recommendations for recovery.
    """
    try:
        # Use flow_id from path if not in request body
        if request:
            flow_id = request.flow_id

        logger.info(
            safe_log_format(
                "🔍 Validating flow state for flow: {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Initialize Master Flow Orchestrator to get status manager
        orchestrator = MasterFlowOrchestrator(db, context)
        status_manager = orchestrator.status_manager

        # Perform flow state validation
        validation_result = await status_manager.validate_flow_state_consistency(
            flow_id
        )

        if validation_result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Flow validation failed: {validation_result['error']}",
            )

        return {
            "success": True,
            "flow_id": flow_id,
            "validation": validation_result,
            "timestamp": validation_result.get("validation_timestamp"),
        }

    except ValueError as e:
        # Flow not found or context issues
        logger.warning(
            safe_log_format(
                "Flow validation failed - flow not found: {flow_id}, error: {error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Flow validation error for {flow_id}: {error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=f"Flow validation failed: {str(e)}")


@router.post("/recover/{flow_id}")
async def recover_flow_state(
    flow_id: str,
    request: FlowRecoveryRequest = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Attempt automatic recovery of a flow with initialization issues.

    This endpoint attempts to automatically recover flows that are in inconsistent
    or problematic states, such as being in attribute mapping phase without proper
    data import completion.
    """
    try:
        # Use flow_id from path if not in request body
        if request:
            flow_id = request.flow_id
            force_recovery = request.force_recovery
            recovery_type = request.recovery_type
        else:
            force_recovery = False
            recovery_type = "automatic"

        logger.info(
            safe_log_format(
                "🔄 Attempting flow recovery for: {flow_id}, type: {recovery_type}",
                flow_id=mask_id(flow_id),
                recovery_type=recovery_type,
            )
        )

        # Initialize Master Flow Orchestrator to get status manager
        orchestrator = MasterFlowOrchestrator(db, context)
        status_manager = orchestrator.status_manager

        # Attempt flow recovery
        recovery_result = await status_manager.attempt_flow_recovery(flow_id)

        if not recovery_result.get("success", False) and not force_recovery:
            # Recovery failed, return the result with guidance
            return {
                "success": False,
                "flow_id": flow_id,
                "recovery": recovery_result,
                "message": recovery_result.get("message", "Flow recovery failed"),
                "requires_manual_intervention": True,
            }

        logger.info(
            safe_log_format(
                "✅ Flow recovery completed for {flow_id}: {action}",
                flow_id=mask_id(flow_id),
                action=recovery_result.get("action", "unknown"),
            )
        )

        return {
            "success": recovery_result.get("success", False),
            "flow_id": flow_id,
            "recovery": recovery_result,
            "message": "Flow recovery attempt completed",
            "timestamp": recovery_result.get("recovery_timestamp"),
        }

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Flow recovery failed - flow not found: {flow_id}, error: {error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Flow recovery error for {flow_id}: {error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=f"Flow recovery failed: {str(e)}")


@router.post("/intercept-transition")
async def intercept_phase_transition(
    request: PhaseTransitionRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Intercept and validate phase transitions, redirecting if necessary.

    This endpoint is called before phase transitions to check if the transition
    should be allowed or if the flow should be redirected to a different phase
    to address initialization issues.
    """
    try:
        flow_id = request.flow_id
        from_phase = request.from_phase
        to_phase = request.to_phase

        logger.info(
            safe_log_format(
                "🔍 Intercepting phase transition for {flow_id}: {from_phase} → {to_phase}",
                flow_id=mask_id(flow_id),
                from_phase=from_phase,
                to_phase=to_phase,
            )
        )

        # Initialize Master Flow Orchestrator to get status manager
        orchestrator = MasterFlowOrchestrator(db, context)
        status_manager = orchestrator.status_manager

        # Intercept phase transition
        interception_result = await status_manager.intercept_phase_transition(
            flow_id, from_phase, to_phase
        )

        if interception_result.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"Phase transition interception failed: {interception_result['error']}",
            )

        # Log interception result
        if interception_result.get("intercepted", False):
            logger.info(
                safe_log_format(
                    "🚫 Phase transition intercepted for {flow_id}: {original} → redirected to {redirected}",
                    flow_id=mask_id(flow_id),
                    original=interception_result.get("original_transition"),
                    redirected=interception_result.get("redirected_to"),
                )
            )
        else:
            logger.info(
                safe_log_format(
                    "✅ Phase transition allowed for {flow_id}: {from_phase} → {to_phase}",
                    flow_id=mask_id(flow_id),
                    from_phase=from_phase,
                    to_phase=to_phase,
                )
            )

        return {
            "success": True,
            "flow_id": flow_id,
            "interception": interception_result,
            "timestamp": interception_result.get("interception_timestamp"),
        }

    except ValueError as e:
        logger.warning(
            safe_log_format(
                "Phase transition interception failed - flow not found: {flow_id}, error: {error}",
                flow_id=mask_id(request.flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Phase transition interception error for {flow_id}: {error}",
                flow_id=mask_id(request.flow_id),
                error=str(e),
            )
        )
        raise HTTPException(
            status_code=500, detail=f"Phase transition interception failed: {str(e)}"
        )


@router.get("/system-analysis")
async def get_system_wide_analysis(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Perform system-wide analysis of flow states and provide recommendations.

    This endpoint analyzes all active flows in the current context and identifies
    flows that have initialization issues or require routing interventions.
    """
    try:
        logger.info("🔍 Performing system-wide flow analysis")

        # Initialize Master Flow Orchestrator to get status manager
        orchestrator = MasterFlowOrchestrator(db, context)
        status_manager = orchestrator.status_manager

        # Get system-wide analysis from flow detector
        analysis = await status_manager.flow_detector.detect_system_wide_issues()

        # Get routing recommendations
        routing_recommendations = (
            await status_manager.flow_router.get_routing_recommendations()
        )

        return {
            "success": True,
            "system_analysis": analysis,
            "routing_recommendations": routing_recommendations,
            "timestamp": analysis.get("analysis_timestamp"),
            "context": {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
            },
        }

    except Exception as e:
        logger.error(f"❌ System-wide analysis error: {e}")
        raise HTTPException(
            status_code=500, detail=f"System-wide analysis failed: {str(e)}"
        )


@router.get("/routing-recommendations")
async def get_routing_recommendations(
    flow_ids: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get routing recommendations for specific flows or all active flows.

    This endpoint provides routing recommendations for flows that may need
    to be redirected to different phases to resolve initialization issues.
    """
    try:
        logger.info("🧭 Getting flow routing recommendations")

        # Initialize Master Flow Orchestrator to get status manager
        orchestrator = MasterFlowOrchestrator(db, context)
        status_manager = orchestrator.status_manager

        # Get routing recommendations
        recommendations = await status_manager.flow_router.get_routing_recommendations(
            flow_ids
        )

        return {
            "success": True,
            "recommendations": recommendations,
            "timestamp": recommendations.get("analysis_timestamp"),
            "context": {
                "client_account_id": str(context.client_account_id),
                "engagement_id": str(context.engagement_id),
            },
        }

    except Exception as e:
        logger.error(f"❌ Routing recommendations error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get routing recommendations: {str(e)}"
        )


@router.get("/blocking-flows", response_model=BlockingFlowsResponse)
async def get_blocking_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Detect all incomplete/blocking flows for the current user context.

    Returns list of blocking flows with details (id, phase, status, created_at, issues).
    Uses proper context filtering (client_id, engagement_id, user_id) for multi-tenant safety.
    """
    try:
        logger.info("🔍 Detecting blocking flows for current context")

        # Initialize Master Flow Orchestrator to get flow detector
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_detector = orchestrator.status_manager.flow_detector

        # Get system-wide analysis to find all incomplete flows
        analysis = await flow_detector.detect_system_wide_issues()

        blocking_flows = []

        # Process critical flows from the analysis
        if "critical_flows" in analysis:
            for critical_flow in analysis["critical_flows"]:
                flow_id = critical_flow.get("flow_id", "")
                issue = critical_flow.get("issue", "Unknown issue")

                # Get additional flow information
                try:
                    master_flow = await orchestrator.master_repo.get_by_flow_id(flow_id)
                    if master_flow:
                        # Try to get discovery flow for phase information
                        phase = "unknown"
                        if master_flow.flow_type == "discovery":
                            discovery_flow = await flow_detector._get_discovery_flow(
                                flow_id
                            )
                            if discovery_flow:
                                phase = getattr(
                                    discovery_flow, "current_phase", "unknown"
                                )

                        blocking_flows.append(
                            BlockingFlow(
                                flow_id=flow_id,
                                phase=phase,
                                status=master_flow.flow_status,
                                created_at=master_flow.created_at.isoformat(),
                                issue=issue,
                            )
                        )
                except Exception as flow_error:
                    logger.warning(
                        f"Could not get details for flow {flow_id}: {flow_error}"
                    )
                    # Still add the flow with basic info
                    blocking_flows.append(
                        BlockingFlow(
                            flow_id=flow_id,
                            phase="unknown",
                            status="incomplete",
                            created_at="",
                            issue=issue,
                        )
                    )

        # Additionally, check for flows with non-critical issues that might still be blocking
        if analysis.get("flows_with_issues", 0) > len(
            analysis.get("critical_flows", [])
        ):
            logger.info("Detecting additional blocking flows with non-critical issues")

            # Get all active flows and check each for blocking issues
            from sqlalchemy import and_, select
            from app.models.crewai_flow_state_extensions import (
                CrewAIFlowStateExtensions,
            )

            master_flows_query = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.client_account_id
                    == context.client_account_id,
                    CrewAIFlowStateExtensions.engagement_id == context.engagement_id,
                    CrewAIFlowStateExtensions.flow_status.in_(
                        [
                            "active",
                            "running",
                            "waiting_for_approval",
                            "paused",
                            "incomplete",
                        ]
                    ),
                )
            )
            result = await db.execute(master_flows_query)
            master_flows = list(result.scalars().all())

            # Check each flow for issues
            for master_flow in master_flows:
                flow_id = str(master_flow.flow_id)

                # Skip if already in critical flows
                if any(
                    cf.get("flow_id") == flow_id
                    for cf in analysis.get("critical_flows", [])
                ):
                    continue

                # Check for issues
                issues = await flow_detector.detect_incomplete_initialization(flow_id)
                if issues:
                    # Get the most severe issue
                    high_priority_issue = next(
                        (
                            issue
                            for issue in issues
                            if issue.severity in ["critical", "high"]
                        ),
                        issues[0] if issues else None,
                    )

                    if high_priority_issue:
                        phase = "unknown"
                        if master_flow.flow_type == "discovery":
                            discovery_flow = await flow_detector._get_discovery_flow(
                                flow_id
                            )
                            if discovery_flow:
                                phase = getattr(
                                    discovery_flow, "current_phase", "unknown"
                                )

                        blocking_flows.append(
                            BlockingFlow(
                                flow_id=flow_id,
                                phase=phase,
                                status=master_flow.flow_status,
                                created_at=master_flow.created_at.isoformat(),
                                issue=high_priority_issue.description,
                            )
                        )

        logger.info(f"📊 Found {len(blocking_flows)} blocking flows")

        return BlockingFlowsResponse(
            blocking_flows=blocking_flows, count=len(blocking_flows)
        )

    except Exception as e:
        logger.error(f"❌ Failed to detect blocking flows: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to detect blocking flows: {str(e)}"
        )


@router.delete("/{flow_id}", response_model=FlowDeleteResponse)
async def delete_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Delete a single flow and all its related records.

    Ensures cascade deletion of child records with proper context filtering
    for multi-tenant safety. Returns success/failure status.
    """
    try:
        logger.info(
            safe_log_format(
                "🗑️ Deleting flow: {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        # First, validate the flow exists and belongs to this tenant
        master_flow = await orchestrator.master_repo.get_by_flow_id(flow_id)
        if not master_flow:
            logger.warning(
                safe_log_format(
                    "Flow not found for deletion: {flow_id}",
                    flow_id=mask_id(flow_id),
                )
            )
            raise HTTPException(status_code=404, detail=f"Flow not found: {flow_id}")

        # Delete the flow using the orchestrator's cleanup capabilities (hard delete for cleanup)
        await orchestrator.lifecycle_manager.delete_flow(
            flow_id, soft_delete=False, reason="blocking_flow_cleanup"
        )

        logger.info(
            safe_log_format(
                "✅ Successfully deleted flow: {flow_id}",
                flow_id=mask_id(flow_id),
            )
        )

        return FlowDeleteResponse(
            success=True, message="Flow deleted successfully", flow_id=flow_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Failed to delete flow {flow_id}: {error}",
                flow_id=mask_id(flow_id),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")


@router.delete("/bulk", response_model=BulkFlowDeleteResponse)
async def delete_multiple_flows(
    request: BulkFlowDeleteRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Delete multiple flows in a single transaction.

    Accepts list of flow IDs in request body and deletes multiple flows.
    Returns results for each flow (success/failure) and handles partial failures gracefully.
    All operations use proper context filtering for multi-tenant safety.
    """
    try:
        flow_ids = request.flowIds
        logger.info(f"🗑️ Starting bulk deletion of {len(flow_ids)} flows")

        if not flow_ids:
            raise HTTPException(
                status_code=400, detail="No flow IDs provided for deletion"
            )

        if len(flow_ids) > 100:  # Safety limit
            raise HTTPException(
                status_code=400,
                detail="Too many flows requested for bulk deletion (max: 100)",
            )

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        results = []
        deleted_count = 0
        failed_count = 0

        # Process each flow deletion
        for flow_id in flow_ids:
            try:
                logger.info(
                    safe_log_format(
                        "🗑️ Processing bulk deletion for flow: {flow_id}",
                        flow_id=mask_id(flow_id),
                    )
                )

                # Validate the flow exists and belongs to this tenant
                master_flow = await orchestrator.master_repo.get_by_flow_id(flow_id)
                if not master_flow:
                    results.append(
                        FlowDeleteResult(
                            flowId=flow_id, success=False, message="Flow not found"
                        )
                    )
                    failed_count += 1
                    continue

                # Delete the flow (hard delete for cleanup)
                await orchestrator.lifecycle_manager.delete_flow(
                    flow_id, soft_delete=False, reason="bulk_blocking_flow_cleanup"
                )

                results.append(
                    FlowDeleteResult(
                        flowId=flow_id,
                        success=True,
                        message="Flow deleted successfully",
                    )
                )
                deleted_count += 1

                logger.info(
                    safe_log_format(
                        "✅ Successfully deleted flow in bulk: {flow_id}",
                        flow_id=mask_id(flow_id),
                    )
                )

            except Exception as flow_error:
                logger.error(
                    safe_log_format(
                        "❌ Failed to delete flow {flow_id} in bulk: {error}",
                        flow_id=mask_id(flow_id),
                        error=str(flow_error),
                    )
                )
                results.append(
                    FlowDeleteResult(
                        flowId=flow_id, success=False, message=str(flow_error)
                    )
                )
                failed_count += 1

        logger.info(
            f"📊 Bulk deletion completed: {deleted_count} deleted, {failed_count} failed"
        )

        # Determine overall success
        overall_success = failed_count == 0
        message = (
            f"Bulk deletion completed: {deleted_count} deleted, {failed_count} failed"
        )

        return BulkFlowDeleteResponse(
            success=overall_success, message=message, results=results
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Bulk flow deletion failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Bulk flow deletion failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for the flow recovery API."""
    return {
        "status": "healthy",
        "service": "flow_recovery",
        "features": {
            "flow_state_detection": "active",
            "flow_routing_intelligence": "active",
            "automatic_recovery": "active",
            "phase_transition_interception": "active",
            "system_wide_analysis": "active",
            "blocking_flows_detection": "active",
            "single_flow_deletion": "active",
            "bulk_flow_deletion": "active",
        },
        "timestamp": "2025-01-12T00:00:00Z",
    }
