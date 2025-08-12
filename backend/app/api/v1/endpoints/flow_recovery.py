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
        },
        "timestamp": "2025-01-12T00:00:00Z",
    }
