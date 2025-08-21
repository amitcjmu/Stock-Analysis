"""
Flow Management Handlers for Unified Discovery

Handles flow initialization, status checking, execution, and active flow listing.
Extracted from the main unified_discovery.py file for better maintainability.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.discovery_flow import DiscoveryFlow
from app.services.flow_configs import initialize_all_flows
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# Import the service modules
from app.services.discovery.flow_execution_service import execute_flow_phase
from app.services.discovery.flow_status_service import (
    get_flow_status as get_flow_status_service,
    get_active_flows as get_active_flows_service,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class FlowInitializationRequest(BaseModel):
    """Request model for flow initialization"""

    flow_name: Optional[str] = None
    raw_data: Optional[List[Dict[str, Any]]] = None
    configuration: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class FlowInitializationResponse(BaseModel):
    """Response model for flow initialization"""

    success: bool
    flow_id: str
    flow_name: str
    status: str
    message: str
    metadata: Dict[str, Any]


@router.post("/flow/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Initialize a discovery flow through Master Flow Orchestrator.

    This is the main entry point for starting discovery flows. It ensures proper
    architectural flow through the Master Flow Orchestrator.
    """
    try:
        # Ensure flow configs are initialized
        await initialize_all_flows()

        # Extract configuration
        configuration = request.configuration or {}

        # Handle raw_data payload
        initial_data = {}
        if request.raw_data:
            logger.info(
                f"📊 Received raw_data with {len(request.raw_data)} records in flow initialization"
            )
            initial_data["raw_data"] = request.raw_data

            # Store import metadata separately for backward compatibility
            if (
                isinstance(request.raw_data, dict)
                and "import_metadata" in request.raw_data
            ):
                initial_data["import_metadata"] = request.raw_data["import_metadata"]
                logger.info("📋 Extracted import_metadata from raw_data payload")

        # Generate flow name if not provided
        flow_name = (
            request.flow_name
            or f"Discovery Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        # Initialize through Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        flow_id, flow_details = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=flow_name,
            configuration=configuration,
            initial_data=initial_data,
        )

        logger.info(
            safe_log_format(
                "✅ Discovery flow initialized successfully: {flow_id} (user: {user_id})",
                flow_id=mask_id(str(flow_id)),
                user_id=mask_id(context.user_id),
            )
        )

        return FlowInitializationResponse(
            success=True,
            flow_id=str(flow_id),
            flow_name=flow_name,
            status="initialized",
            message="Discovery flow initialized successfully through Master Flow Orchestrator",
            metadata={
                "flow_details": flow_details,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "has_raw_data": bool(request.raw_data),
                "configuration_keys": (
                    list(configuration.keys()) if configuration else []
                ),
            },
        )

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Flow initialization failed: {error} (user: {user_id})",
                error=str(e),
                user_id=mask_id(context.user_id),
            )
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize discovery flow: {str(e)}",
        )


@router.get("/flow/{flow_id}/status")
async def get_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get the current status of a discovery flow."""
    try:
        status = await get_flow_status_service(flow_id, db, context)
        return status
    except Exception as e:
        logger.error(safe_log_format("Flow status check failed: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/active")
async def get_active_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get all active discovery flows for the current tenant."""
    try:
        flows = await get_active_flows_service(db, context)
        return {
            "success": True,
            "flows": flows,
            "count": len(flows),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(safe_log_format("Active flows retrieval failed: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute the next phase of a discovery flow."""
    try:
        # Get the current flow state to determine next phase
        discovery_flow = await db.get(DiscoveryFlow, flow_id)
        if not discovery_flow:
            raise HTTPException(status_code=404, detail="Discovery flow not found")

        # Determine the next phase to execute
        next_phase = _determine_next_phase(discovery_flow)

        if not next_phase:
            return {
                "success": True,
                "message": "Flow execution completed - no more phases to execute",
                "status": "completed",
            }

        # Execute the phase
        result = await execute_flow_phase(flow_id, next_phase, db, context)

        logger.info(
            safe_log_format(
                "Flow phase executed: flow_id={flow_id}, phase={phase}, success={success}",
                flow_id=mask_id(str(flow_id)),
                phase=next_phase,
                success=result.get("success", False),
            )
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            safe_log_format(
                "Flow execution failed: flow_id={flow_id}, error={error}",
                flow_id=mask_id(str(flow_id)),
                error=str(e),
            )
        )
        raise HTTPException(status_code=500, detail=str(e))


def _determine_next_phase(discovery_flow: DiscoveryFlow) -> str:
    """
    Determine the next phase to execute based on the current flow state.

    This is a simplified phase determination - in production, this logic
    would be more sophisticated and potentially moved to a service.
    """
    current_phase = discovery_flow.current_phase or "initialization"

    phase_sequence = [
        "initialization",
        "data_collection",
        "analysis",
        "dependency_mapping",
        "recommendations",
        "completed",
    ]

    try:
        current_index = phase_sequence.index(current_phase)
        if current_index < len(phase_sequence) - 1:
            return phase_sequence[current_index + 1]
    except ValueError:
        # Current phase not in sequence, start from beginning
        return "data_collection"

    return None  # Flow is completed
