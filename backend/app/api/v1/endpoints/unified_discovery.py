"""
Unified Discovery Flow API - Master Flow Orchestrator Integration

This endpoint provides the proper architectural flow as shown in the DFD:
File upload → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

ARCHITECTURAL FIX: This ensures all discovery flows go through the Master Flow Orchestrator
instead of bypassing it with direct CrewAI flow creation.

This file has been modularized. Related endpoints can be found in:
- app.api.v1.endpoints.dependency_analysis - Dependency analysis endpoints
- app.api.v1.endpoints.agent_insights - Agent insights and questions endpoints
- app.api.v1.endpoints.clarifications - Clarification submission endpoints
- app.api.v1.endpoints.flow_management - Flow lifecycle management endpoints
- app.services.discovery.flow_execution_service - Flow execution logic
- app.services.discovery.flow_status_service - Flow status operations
- app.services.discovery.data_extraction_service - Data extraction utilities
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext, get_current_context
from app.core.database import get_db
from app.core.security.secure_logging import mask_id, safe_log_format
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.services.flow_configs import initialize_all_flows
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

# Import the service modules
from app.services.discovery.flow_execution_service import execute_flow_phase
from app.services.discovery.flow_status_service import (
    get_flow_status as get_flow_status_service,
    get_active_flows as get_active_flows_service,
)

# Data extraction service functions are available but not used in this main file
# They are used by the modularized endpoints in the separate files

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
                "record_count": len(request.raw_data) if request.raw_data else 0,
            },
        )

    except Exception as e:
        logger.error(
            safe_log_format(
                "❌ Failed to initialize discovery flow: {error}",
                error=str(e),
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
    """Get the status of a discovery flow."""
    try:
        result = await get_flow_status_service(flow_id, db, context)
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(safe_log_format("Failed to get flow status: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/active")
async def get_active_flows(
    limit: int = Query(10, description="Maximum number of flows to return"),
    flowType: Optional[str] = Query(
        None, description="Filter by flow type (e.g., 'discovery')"
    ),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get active discovery flows for the current context."""
    try:
        flows = await get_active_flows_service(db, context, limit)

        # Filter by flowType if specified (for frontend compatibility)
        if flowType and flowType.lower() == "discovery":
            # Convert to the format expected by the frontend
            formatted_flows = []
            for flow in flows:
                formatted_flows.append(
                    {
                        "flowId": flow["flow_id"],
                        "flowType": "discovery",
                        "flowName": flow["flow_name"],
                        "status": flow["status"],
                        "progress": flow["progress"],
                        "currentPhase": flow["current_phase"],
                        "createdAt": flow["created_at"],
                        "updatedAt": flow["updated_at"],
                        "source": flow.get("source", "discovery_flow"),
                        "metadata": {"flow_name": flow["flow_name"]},
                    }
                )
            return formatted_flows

        return {
            "success": True,
            "flows": flows,
            "count": len(flows),
        }
    except Exception as e:
        logger.error(safe_log_format("Failed to get active flows: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute a discovery flow phase with intelligent routing and validation."""
    try:
        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()

        if not discovery_flow:
            # Simple error - flow not found
            logger.warning(f"Discovery flow not found: {flow_id}")
            raise HTTPException(
                status_code=404, detail=f"Discovery flow not found: {flow_id}"
            )

        # Simple phase validation - removed complex interception
        current_phase = discovery_flow.current_phase or "unknown"
        next_phase = _determine_next_phase(discovery_flow)

        # Log phase transition for debugging
        if next_phase and next_phase != current_phase:
            logger.info(
                f"Phase transition for {flow_id}: {current_phase} → {next_phase}"
            )

        # Execute the flow phase
        result = await execute_flow_phase(flow_id, discovery_flow, context, db)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to execute flow: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


def _determine_next_phase(discovery_flow: DiscoveryFlow) -> str:
    """Determine the next phase for a discovery flow based on its current state"""
    # Phase progression logic
    if not discovery_flow.data_import_completed:
        return "data_import"
    elif not discovery_flow.field_mapping_completed:
        return "field_mapping"
    elif not discovery_flow.data_cleansing_completed:
        return "data_cleansing"
    elif not discovery_flow.asset_inventory_completed:
        return "asset_inventory"
    elif not discovery_flow.dependency_analysis_completed:
        return "dependency_analysis"
    elif not discovery_flow.tech_debt_assessment_completed:
        return "tech_debt_assessment"
    else:
        return "completion"


@router.get("/flows/{flow_id}/field-mappings")
async def get_field_mappings(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get field mappings for a discovery flow."""
    try:
        logger.info(
            safe_log_format(
                "Getting field mappings for flow: {flow_id}", flow_id=flow_id
            )
        )

        # Get the discovery flow
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flow = result.scalar_one_or_none()

        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")

        # Get field mappings from the database using data_import_id
        # If flow has a data_import_id, use it to get mappings
        if flow.data_import_id:
            mapping_stmt = select(ImportFieldMapping).where(
                ImportFieldMapping.data_import_id == flow.data_import_id
            )
            mapping_result = await db.execute(mapping_stmt)
            mappings = mapping_result.scalars().all()
        else:
            # No data import, no mappings
            mappings = []

        # Convert to response format
        field_mappings = [
            {
                "source_field": m.source_field,
                "target_attribute": m.target_field,  # Fixed: target_field not target_attribute
                "confidence": m.confidence_score,  # Fixed: confidence_score not confidence
                "mapping_type": getattr(m, "mapping_type", "auto"),
                "transformation": getattr(m, "transformation_rule", None),
                "validation_rules": getattr(m, "validation_rule", None),
            }
            for m in mappings
        ]

        return {
            "success": True,
            "flow_id": flow_id,
            "field_mappings": field_mappings,
            "count": len(field_mappings),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(safe_log_format("Failed to get field mappings: {e}", e=e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint for the unified discovery API."""
    return {
        "status": "healthy",
        "service": "unified_discovery",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules": {
            "dependency_analysis": "active",
            "agent_insights": "active",
            "flow_management": "active",
            "clarifications": "active",
            "data_extraction": "active",
        },
    }
