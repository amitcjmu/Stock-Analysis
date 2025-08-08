"""
Unified Discovery Flow API - Master Flow Orchestrator Integration

This endpoint provides the proper architectural flow as shown in the DFD:
File upload → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

ARCHITECTURAL FIX: This ensures all discovery flows go through the Master Flow Orchestrator
instead of bypassing it with direct CrewAI flow creation.
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
from app.models.data_import.mapping import ImportFieldMapping
from app.models.discovery_flow import DiscoveryFlow
from app.services.flow_configs import initialize_all_flows
from app.services.master_flow_orchestrator import MasterFlowOrchestrator

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
    flow_id: Optional[str] = None
    flow_name: Optional[str] = None
    status: str
    message: str
    error: Optional[str] = None


class ClarificationSubmissionRequest(BaseModel):
    """Request model for clarification submission"""

    clarifications: List[Dict[str, Any]]
    flow_id: Optional[str] = None


class DependencyAnalysisRequest(BaseModel):
    """Request model for dependency analysis"""

    analysis_type: str = "app-server"
    configuration: Optional[Dict[str, Any]] = None


@router.post("/flow/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
) -> FlowInitializationResponse:
    """
    Initialize a Discovery Flow through Master Flow Orchestrator.

    This is the proper architectural endpoint as shown in the DFD:
    Frontend → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

    Args:
        request: Flow initialization request with raw data and configuration
        db: Database session
        context: Request context with tenant information

    Returns:
        FlowInitializationResponse with flow_id and status
    """
    try:
        logger.info("🎯 Initializing Discovery Flow via Master Flow Orchestrator")
        logger.info(
            f"🔍 Client: {context.client_account_id}, Engagement: {context.engagement_id}, User: {context.user_id}"
        )
        logger.info(
            f"🔍 Raw data count: {len(request.raw_data) if request.raw_data else 0}"
        )

        # Ensure flow configurations are initialized
        initialize_all_flows()

        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)

        # Prepare configuration
        configuration = request.configuration or {}
        configuration.update(
            {
                "source": "unified_discovery_api",
                "initialization_timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Prepare initial state with raw data
        initial_state = {
            "raw_data": request.raw_data or [],
            "metadata": request.metadata or {},
        }

        # Create discovery flow through orchestrator
        logger.info("🚀 Creating discovery flow through Master Flow Orchestrator...")
        flow_result = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=request.flow_name
            or f"Discovery Flow {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            configuration=configuration,
            initial_state=initial_state,
        )

        # Extract flow_id from result tuple
        if isinstance(flow_result, tuple) and len(flow_result) >= 1:
            flow_id = flow_result[0]
            flow_id_str = str(flow_id) if flow_id else None

            # CC FIX: Create the corresponding DiscoveryFlow record that the system expects
            logger.info(
                f"🔗 Creating discovery flow record in discovery_flows table: {flow_id_str}"
            )
            try:
                from sqlalchemy import func

                from app.models.discovery_flow import DiscoveryFlow

                discovery_flow = DiscoveryFlow(
                    flow_id=flow_id_str,
                    flow_name=request.flow_name
                    or f"Discovery Flow {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    flow_type="discovery",
                    status="initializing",
                    current_phase="data_import",
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id or "system",
                    crewai_state_data=initial_state,  # Store raw_data in crewai_state_data
                    created_at=func.now(),
                )

                db.add(discovery_flow)
                await db.commit()

                logger.info(
                    f"✅ Discovery flow record created in discovery_flows table: {flow_id_str}"
                )

            except Exception as discovery_error:
                logger.error(
                    f"❌ Failed to create discovery flow record: {discovery_error}"
                )
                # Don't fail the entire flow creation, but log the error
                logger.warning(
                    "⚠️ Continuing without discovery flow record - some features may be limited"
                )

            flow_details = flow_result[1] if len(flow_result) > 1 else {}

            logger.info(f"✅ Discovery flow created successfully: {flow_id_str}")

            return FlowInitializationResponse(
                success=True,
                flow_id=flow_id_str,
                flow_name=request.flow_name or flow_details.get("flow_name"),
                status="initialized",
                message="Discovery flow initialized successfully with automatic kickoff",
            )
        else:
            logger.error(f"❌ Unexpected flow creation result: {flow_result}")
            return FlowInitializationResponse(
                success=False,
                status="failed",
                message="Flow creation returned unexpected result",
                error="Invalid flow creation response",
            )

    except Exception as e:
        logger.error(f"❌ Discovery flow initialization failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")

        return FlowInitializationResponse(
            success=False,
            status="failed",
            message="Discovery flow initialization failed",
            error=str(e),
        )


@router.get("/flow/{flow_id}/status")
async def get_discovery_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """
    Get discovery flow operational status.

    ADR-012: This endpoint returns child flow status for operational decisions.
    The child flow (discovery_flows table) contains the operational state needed
    for frontend display and agent decisions.
    """
    try:
        logger.info(f"🔍 Getting discovery flow operational status: {flow_id}")
        logger.info(
            f"🔍 Context: Client={context.client_account_id}, Engagement={context.engagement_id}"
        )

        # ADR-012: Get child flow status directly from discovery_flows table
        from sqlalchemy import and_, select

        from app.models.discovery_flow import DiscoveryFlow

        # Query discovery flow with tenant context
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
            logger.warning(
                f"Discovery flow not found in child table: {flow_id} for client {context.client_account_id}"
            )

            # ADR-012 Fallback: If child flow doesn't exist, try to get from master flow
            # This handles cases where the flow was created but child flow sync failed
            logger.info(f"🔄 Attempting fallback to master flow for {flow_id}")

            # Initialize Master Flow Orchestrator as fallback
            initialize_all_flows()
            orchestrator = MasterFlowOrchestrator(db, context)

            try:
                # Get master flow status
                master_status = await orchestrator.get_flow_status(flow_id)

                logger.info(
                    f"✅ Found master flow status for {flow_id}, returning degraded response"
                )

                # Return a degraded response with master flow data
                response = {
                    "success": True,
                    "flow_id": flow_id,
                    "status": master_status.get("status", "unknown"),
                    "current_phase": master_status.get("current_phase", "unknown"),
                    "progress_percentage": master_status.get("progress_percentage", 0),
                    "summary": {
                        "data_import_completed": master_status.get(
                            "phase_completion", {}
                        ).get("data_import", False),
                        "field_mapping_completed": master_status.get(
                            "phase_completion", {}
                        ).get("field_mapping", False),
                        "data_cleansing_completed": master_status.get(
                            "phase_completion", {}
                        ).get("data_cleansing", False),
                        "asset_inventory_completed": master_status.get(
                            "phase_completion", {}
                        ).get("asset_inventory", False),
                        "dependency_analysis_completed": master_status.get(
                            "phase_completion", {}
                        ).get("dependency_analysis", False),
                        "tech_debt_assessment_completed": master_status.get(
                            "phase_completion", {}
                        ).get("tech_debt_analysis", False),
                        "total_records": 0,
                        "records_processed": 0,
                        "quality_score": 0,
                    },
                    "created_at": master_status.get("created_at"),
                    "updated_at": master_status.get("updated_at"),
                    # Return field mappings from master flow if available
                    "field_mappings": master_status.get("field_mappings", []),
                    "errors": ["Child flow record missing - using master flow data"],
                    "warnings": [
                        "This is a degraded response. Some operational data may be missing."
                    ],
                }

                # Log this as a data integrity issue
                logger.error(
                    f"⚠️ DATA INTEGRITY: Discovery flow {flow_id} exists in master but not in child table"
                )

                return response

            except Exception as e:
                logger.error(f"❌ Master flow fallback also failed for {flow_id}: {e}")
                raise ValueError(f"Discovery flow not found: {flow_id}")

        # Get field mappings
        from app.models.data_import.mapping import ImportFieldMapping

        field_mappings_stmt = select(ImportFieldMapping).where(
            ImportFieldMapping.master_flow_id == flow_id
        )
        field_mappings_result = await db.execute(field_mappings_stmt)
        field_mappings = field_mappings_result.scalars().all()

        # Build operational status response
        response = {
            "success": True,
            "flow_id": discovery_flow.flow_id,
            "status": discovery_flow.status,
            "current_phase": discovery_flow.current_phase,
            "progress_percentage": discovery_flow.progress_percentage or 0,
            "summary": {
                "data_import_completed": discovery_flow.data_import_completed or False,
                "field_mapping_completed": discovery_flow.field_mapping_completed
                or False,
                "data_cleansing_completed": discovery_flow.data_cleansing_completed
                or False,
                "asset_inventory_completed": discovery_flow.asset_inventory_completed
                or False,
                "dependency_analysis_completed": discovery_flow.dependency_analysis_completed
                or False,
                "tech_debt_assessment_completed": discovery_flow.tech_debt_assessment_completed
                or False,
                "total_records": (
                    len(discovery_flow.crewai_state_data.get("raw_data", []))
                    if discovery_flow.crewai_state_data
                    else 0
                ),
                "records_processed": len(field_mappings),
                "quality_score": (
                    discovery_flow.progress_percentage / 100.0
                    if discovery_flow.progress_percentage
                    else 0.0
                ),
            },
            "created_at": (
                discovery_flow.created_at.isoformat()
                if discovery_flow.created_at
                else None
            ),
            "updated_at": (
                discovery_flow.updated_at.isoformat()
                if discovery_flow.updated_at
                else None
            ),
            # Additional operational fields
            "field_mappings": (
                [
                    {
                        "id": str(fm.id),
                        "source_field": fm.source_field,
                        "target_field": fm.target_field,
                        "confidence": fm.confidence_score,
                        "is_approved": fm.approved_by is not None,
                        "status": fm.status,
                        "match_type": fm.match_type,
                    }
                    for fm in field_mappings
                ]
                if field_mappings
                else []
            ),
            # CRITICAL FIX: Include phase results from JSONB columns
            "asset_inventory": discovery_flow.discovered_assets or {},
            "dependency_analysis": discovery_flow.dependencies or {},
            "dependencies": discovery_flow.dependencies
            or {},  # Alternative key for compatibility
            "tech_debt_analysis": discovery_flow.tech_debt_analysis or {},
            "raw_data": (
                discovery_flow.crewai_state_data.get("raw_data", [])
                if discovery_flow.crewai_state_data
                else []
            ),
            "cleaned_data": (
                discovery_flow.crewai_state_data.get("cleaned_data", [])
                if discovery_flow.crewai_state_data
                else []
            ),
            "errors": [],
            "warnings": [],
        }

        logger.info(f"✅ Retrieved discovery flow operational status for {flow_id}")
        return response

    except ValueError:
        # Flow not found - proper 404 handling
        logger.warning(f"Flow not found: {flow_id}")
        raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")
    except Exception as e:
        logger.error(f"❌ Failed to get discovery flow status for {flow_id}: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/flow/{flow_id}/pause")
async def pause_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Pause a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.pause_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to pause flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/resume")
async def resume_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Resume a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.resume_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to resume flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/flow/{flow_id}")
async def delete_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Delete a discovery flow - handles both master flow and discovery flow tables."""
    try:
        logger.info(f"🗑️ Starting deletion process for flow: {flow_id}")
        logger.info(
            f"🔍 Context - Client: {context.client_account_id}, Engagement: {context.engagement_id}"
        )

        # First try to delete via Master Flow Orchestrator
        try:
            logger.info(
                f"🔄 Attempting Master Flow Orchestrator deletion for flow: {flow_id}"
            )
            orchestrator = MasterFlowOrchestrator(db, context)
            result = await orchestrator.delete_flow(flow_id)
            logger.info(
                f"✅ Flow {flow_id} successfully deleted via Master Flow Orchestrator"
            )
            return {"success": True, "flow_id": flow_id, "result": result}
        except (ValueError, RuntimeError) as mfo_error:
            logger.info(f"⚠️ MFO Error: {mfo_error}")
            # If MFO can't find the flow, check if it exists in DiscoveryFlow table
            if "Flow not found" in str(mfo_error):
                logger.info(
                    f"🔍 Flow {flow_id} not found in master flows, searching discovery flows table..."
                )

                try:
                    # Check if flow exists in DiscoveryFlow table
                    stmt = select(DiscoveryFlow).where(
                        and_(
                            DiscoveryFlow.flow_id == flow_id,
                            DiscoveryFlow.client_account_id
                            == context.client_account_id,
                            DiscoveryFlow.engagement_id == context.engagement_id,
                        )
                    )
                    logger.info(
                        f"🔍 Executing DiscoveryFlow query with flow_id={flow_id}, client={context.client_account_id}, engagement={context.engagement_id}"
                    )
                    result = await db.execute(stmt)
                    discovery_flow = result.scalar_one_or_none()

                    if discovery_flow:
                        logger.info(
                            f"✅ Found discovery flow: {flow_id} with status: {discovery_flow.status}"
                        )

                        # Soft delete the discovery flow directly
                        previous_status = discovery_flow.status
                        discovery_flow.status = "deleted"
                        discovery_flow.updated_at = datetime.now(timezone.utc)

                        logger.info(
                            f"🔄 Committing status change from '{previous_status}' to 'deleted' for flow {flow_id}"
                        )
                        await db.commit()
                        logger.info(f"✅ Database commit successful for flow {flow_id}")

                        return {
                            "success": True,
                            "flow_id": flow_id,
                            "result": {
                                "deleted_from": "discovery_flows_table",
                                "status": "deleted",
                                "previous_status": previous_status,
                            },
                        }
                    else:
                        logger.error(
                            f"❌ Flow {flow_id} not found in DiscoveryFlow table with context client={context.client_account_id}, engagement={context.engagement_id}"
                        )

                        # Debug: Check if flow exists without context constraints
                        debug_stmt = select(DiscoveryFlow).where(
                            DiscoveryFlow.flow_id == flow_id
                        )
                        debug_result = await db.execute(debug_stmt)
                        debug_flow = debug_result.scalar_one_or_none()

                        if debug_flow:
                            logger.error(
                                f"❌ Flow {flow_id} exists but with different context: client={debug_flow.client_account_id}, engagement={debug_flow.engagement_id}"
                            )
                        else:
                            logger.error(
                                f"❌ Flow {flow_id} does not exist in DiscoveryFlow table at all"
                            )

                        raise HTTPException(
                            status_code=404,
                            detail=f"Flow {flow_id} not found in the specified engagement context",
                        )

                except Exception as db_error:
                    logger.error(
                        f"❌ Database error while checking DiscoveryFlow table: {db_error}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Database error during flow lookup: {str(db_error)}",
                    )
            else:
                # Re-raise other MFO errors
                logger.error(f"❌ MFO error (not 'Flow not found'): {mfo_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Master Flow Orchestrator error: {str(mfo_error)}",
                )
        except Exception as mfo_error:
            logger.error(f"❌ Unexpected MFO error: {mfo_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected Master Flow Orchestrator error: {str(mfo_error)}",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during flow deletion {flow_id}: {e}")
        import traceback

        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to delete flow: {str(e)}")


@router.get("/flows/active")
async def get_active_flows(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get active discovery flows for compatibility with frontend."""
    try:
        logger.info(f"Getting active flows for client: {context.client_account_id}")

        # Import master flow model for status checking
        from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
        from sqlalchemy.orm import aliased
        from sqlalchemy import or_

        # Query active discovery flows excluding flows with deleted master flows
        # This ensures proper deletion state consistency between master and child flows
        master_flow = aliased(CrewAIFlowStateExtensions)

        stmt = (
            select(DiscoveryFlow)
            .outerjoin(master_flow, DiscoveryFlow.flow_id == master_flow.flow_id)
            .where(
                and_(
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                    # Only include flows that are truly incomplete/active
                    DiscoveryFlow.status.in_(
                        [
                            "initialized",
                            "running",
                            "processing",
                            "paused",
                            "waiting_for_approval",
                            "in_progress",
                            "active",
                        ]
                    ),
                    # Also exclude flows whose master flow is completed/deleted/cancelled
                    or_(
                        master_flow.flow_status.is_(None),  # No master flow (old flows)
                        master_flow.flow_status.in_(
                            [
                                "initialized",
                                "initializing",
                                "running",
                                "processing",
                                "paused",
                                "waiting_for_approval",
                                "in_progress",
                                "active",
                            ]
                        ),
                    ),
                )
            )
        )

        result = await db.execute(stmt)
        active_flows = result.scalars().all()

        flow_details = []
        for flow in active_flows:
            flow_details.append(
                {
                    "flowId": str(
                        flow.flow_id
                    ),  # Match frontend expectation: flowId not flow_id
                    "flowType": flow.flow_type or "discovery",  # Add flowType field
                    "flowName": flow.flow_name,  # Add flowName field
                    "status": flow.status,
                    "currentPhase": flow.current_phase,  # Match frontend: currentPhase not current_phase
                    "progress": flow.progress_percentage or 0.0,
                    "createdAt": (
                        flow.created_at.isoformat() if flow.created_at else None
                    ),  # Match frontend: createdAt
                    "updatedAt": (
                        flow.updated_at.isoformat() if flow.updated_at else None
                    ),  # Match frontend: updatedAt
                    "metadata": {
                        "flow_name": flow.flow_name,
                        "client_id": str(flow.client_account_id),
                        "engagement_id": str(flow.engagement_id),
                    },
                }
            )

        # Return flow_details directly as array to match frontend expectation
        return flow_details

    except Exception as e:
        logger.error(f"Failed to get active flows: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/execute")
async def execute_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Execute a flow through Master Flow Orchestrator."""
    try:
        logger.info(f"Executing flow: {flow_id}")

        # Check if flow exists in discovery_flows table first
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
            logger.warning(f"Discovery flow not found: {flow_id}")
            raise HTTPException(status_code=404, detail=f"Flow {flow_id} not found")

        # Determine the next phase based on current status
        current_phase = discovery_flow.current_phase
        phase_to_execute = current_phase or "data_import"

        # For flows that are completed or in specific phases, determine next action
        if discovery_flow.status == "completed":
            return {
                "success": False,
                "flow_id": flow_id,
                "message": "Flow is already completed",
                "current_status": discovery_flow.status,
                "current_phase": current_phase,
            }
        elif discovery_flow.status in ["failed", "error"]:
            # For failed flows, restart from current phase
            phase_to_execute = current_phase or "data_import"
        elif discovery_flow.status in ["paused", "waiting_for_approval"]:
            # For paused flows, resume from current phase
            phase_to_execute = current_phase or "field_mapping"
        else:
            # For running flows, continue with next phase or current phase
            phase_to_execute = current_phase or "data_import"

        logger.info(
            f"Executing phase '{phase_to_execute}' for flow {flow_id} (status: {discovery_flow.status})"
        )

        # ADR-015: Update status based on proper initialization with persistent agents
        if discovery_flow.status == "initializing":
            logger.info(f"🔄 Performing proper initialization for flow {flow_id}")

            # Try to use persistent agents with graceful fallback
            initialization_result = None
            try:
                from app.services.persistent_agents.flow_initialization import (
                    initialize_flow_with_persistent_agents,
                )

                initialization_result = await initialize_flow_with_persistent_agents(
                    flow_id, context
                )

                if initialization_result.success:
                    logger.info(
                        f"✅ Flow {flow_id} initialization successful - transitioning to running"
                    )
                    logger.info(
                        f"   Agent pool: {len(initialization_result.agent_pool or {})} agents initialized"
                    )
                    logger.info(
                        f"   Initialization time: {initialization_result.initialization_time_ms}ms"
                    )
                    discovery_flow.status = "running"
                    await db.commit()
                else:
                    logger.error(
                        f"❌ Flow {flow_id} initialization failed - transitioning to failed"
                    )
                    discovery_flow.status = "failed"
                    discovery_flow.error_message = initialization_result.error
                    await db.commit()

                    return {
                        "message": f"Flow initialization failed: {initialization_result.error}",
                        "flow_id": flow_id,
                        "status": "failed",
                        "initialization_details": initialization_result.validation_results,
                    }

            except ImportError as e:
                logger.warning(
                    f"⚠️ Persistent agents not available, using fallback: {e}"
                )
                # Fallback to original initialization logic
                discovery_flow.status = "running"
                await db.commit()
                logger.info(
                    f"✅ Flow {flow_id} using fallback - transitioning to running"
                )

            except Exception as e:
                logger.error(
                    f"❌ Persistent agent initialization error, using fallback: {e}"
                )
                # Fallback to original initialization logic
                discovery_flow.status = "running"
                await db.commit()
                logger.info(
                    f"✅ Flow {flow_id} using fallback after error - transitioning to running"
                )

        # Continue with existing logic after initialization block...

        # Try to execute through Master Flow Orchestrator
        try:
            orchestrator = MasterFlowOrchestrator(db, context)
            result = await orchestrator.execute_phase(flow_id, phase_to_execute, {})
            return {
                "success": True,
                "flow_id": flow_id,
                "result": result,
                "phase_executed": phase_to_execute,
                "previous_status": discovery_flow.status,
            }
        except Exception as orchestrator_error:
            logger.warning(
                f"Master Flow Orchestrator execution failed: {orchestrator_error}"
            )

            # Return a graceful response indicating the issue
            return {
                "success": False,
                "flow_id": flow_id,
                "message": (
                    "Flow execution currently unavailable due to architectural "
                    "mismatch between discovery_flows and master flow tables"
                ),
                "details": {
                    "current_status": discovery_flow.status,
                    "current_phase": current_phase,
                    "attempted_phase": phase_to_execute,
                    "error": str(orchestrator_error),
                },
                "recommended_action": (
                    "Please check flow status and retry later, "
                    "or contact support for flow state synchronization"
                ),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flow/{flow_id}/retry")
async def retry_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Retry a failed flow through Master Flow Orchestrator."""
    try:
        logger.info(f"Retrying flow: {flow_id}")
        orchestrator = MasterFlowOrchestrator(db, context)

        # Resume the flow which effectively retries it
        result = await orchestrator.resume_flow(flow_id, {"retry": True})
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"Failed to retry flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{flow_id}/field-mappings")
async def get_field_mappings(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get field mappings for a discovery flow."""
    try:
        logger.info(f"Getting field mappings for flow: {flow_id}")

        # Get field mappings for this flow
        field_mappings_stmt = select(ImportFieldMapping).where(
            ImportFieldMapping.master_flow_id == flow_id
        )
        field_mappings_result = await db.execute(field_mappings_stmt)
        field_mappings = field_mappings_result.scalars().all()

        mappings_data = [
            {
                "id": str(fm.id),
                "source_field": fm.source_field,
                "target_field": fm.target_field,
                "confidence": fm.confidence_score,
                "is_approved": fm.approved_by is not None,
                "status": fm.status,
                "match_type": fm.match_type,
            }
            for fm in field_mappings
        ]

        return {
            "success": True,
            "flow_id": flow_id,
            "field_mappings": mappings_data,
            "count": len(mappings_data),
        }

    except Exception as e:
        logger.error(f"Failed to get field mappings for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/flows/{flow_id}/clarifications/submit")
async def submit_clarifications(
    flow_id: str,
    request: ClarificationSubmissionRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Submit clarifications for a discovery flow."""
    try:
        logger.info(f"Submitting clarifications for flow: {flow_id}")

        # Process clarifications through Master Flow Orchestrator by executing clarification phase
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.execute_phase(
            flow_id, "clarifications", {"clarifications": request.clarifications}
        )

        return {
            "success": True,
            "flow_id": flow_id,
            "processed_clarifications": len(request.clarifications),
            "result": result,
            "message": "Clarifications submitted successfully",
        }

    except Exception as e:
        logger.error(f"Failed to submit clarifications for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flow/{flow_id}/agent-insights")
async def get_agent_insights(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get agent insights for a discovery flow."""
    try:
        logger.info(f"Getting agent insights for flow: {flow_id}")

        # Try to import agent UI bridge, fallback to empty response if not available
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge

            insights = agent_ui_bridge.get_insights_for_flow(flow_id)
        except ImportError:
            logger.warning("Agent UI bridge not available, returning empty insights")
            insights = []

        return {
            "success": True,
            "flow_id": flow_id,
            "insights": insights,
            "count": len(insights),
        }

    except Exception as e:
        logger.error(f"Failed to get agent insights for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/analysis")
async def get_dependency_analysis(
    flow_id: str = Query(None, description="Flow ID for dependency analysis"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get dependency analysis results."""
    try:
        logger.info(f"Getting dependency analysis for flow: {flow_id}")

        if flow_id:
            # Get specific flow's dependency analysis
            stmt = select(DiscoveryFlow).where(
                and_(
                    DiscoveryFlow.flow_id == flow_id,
                    DiscoveryFlow.client_account_id == context.client_account_id,
                    DiscoveryFlow.engagement_id == context.engagement_id,
                )
            )
            result = await db.execute(stmt)
            flow = result.scalar_one_or_none()

            if flow:
                dependencies = flow.dependencies or {}
            else:
                dependencies = {}
        else:
            # Return generic dependency structure
            dependencies = {
                "total_dependencies": 0,
                "dependency_quality": {"quality_score": 0},
                "cross_application_mapping": {
                    "cross_app_dependencies": [],
                    "application_clusters": [],
                    "dependency_graph": {"nodes": [], "edges": []},
                },
                "impact_analysis": {"impact_summary": {}},
            }

        return {"success": True, "data": {"dependency_analysis": dependencies}}

    except Exception as e:
        logger.error(f"Failed to get dependency analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies")
async def create_dependencies(
    request: DependencyAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Create dependency analysis through Master Flow Orchestrator."""
    try:
        logger.info(f"Creating dependency analysis: {request.analysis_type}")

        # Create a new discovery flow for dependency analysis
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_id, flow_details = await orchestrator.create_flow(
            "discovery",
            f"Dependency Analysis - {request.analysis_type}",
            {
                "analysis_type": request.analysis_type,
                "focus": "dependency_analysis",
                **(request.configuration or {}),
            },
            {"analysis_request": request.dict()},
        )

        return {
            "success": True,
            "flow_id": str(flow_id),
            "analysis_type": request.analysis_type,
            "result": flow_details,
            "message": "Dependency analysis created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create dependency analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/applications")
async def get_available_applications(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get available applications for dependency analysis."""
    try:
        logger.info("Getting available applications")

        # Get applications from discovery flows in this engagement
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flows = result.scalars().all()

        applications = []
        for flow in flows:
            if flow.discovered_assets:
                assets = flow.discovered_assets.get("applications", [])
                applications.extend(assets)

        return {
            "success": True,
            "applications": applications,
            "count": len(applications),
        }

    except Exception as e:
        logger.error(f"Failed to get available applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dependencies/servers")
async def get_available_servers(
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get available servers for dependency analysis."""
    try:
        logger.info("Getting available servers")

        # Get servers from discovery flows in this engagement
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id,
            )
        )
        result = await db.execute(stmt)
        flows = result.scalars().all()

        servers = []
        for flow in flows:
            if flow.discovered_assets:
                assets = flow.discovered_assets.get("servers", [])
                servers.extend(assets)

        return {"success": True, "servers": servers, "count": len(servers)}

    except Exception as e:
        logger.error(f"Failed to get available servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies/analyze/{analysis_type}")
async def analyze_dependencies(
    analysis_type: str,
    request: Optional[DependencyAnalysisRequest] = None,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Analyze dependencies of a specific type."""
    try:
        logger.info(f"Analyzing dependencies: {analysis_type}")

        # Create a new discovery flow focused on dependency analysis
        orchestrator = MasterFlowOrchestrator(db, context)
        flow_id, flow_details = await orchestrator.create_flow(
            "discovery",
            f"Dependency Analysis - {analysis_type}",
            {
                "analysis_type": analysis_type,
                "focus": "dependency_analysis",
                "auto_execute": True,
                **(request.configuration if request else {}),
            },
            {
                "analysis_request": {
                    "analysis_type": analysis_type,
                    "configuration": (request.configuration if request else {}),
                }
            },
        )

        # Execute the dependency analysis phase
        analysis_result = await orchestrator.execute_phase(
            str(flow_id), "dependency_analysis", {"analysis_type": analysis_type}
        )

        return {
            "success": True,
            "flow_id": str(flow_id),
            "analysis_type": analysis_type,
            "result": analysis_result,
            "message": f"Dependency analysis '{analysis_type}' completed successfully",
        }

    except Exception as e:
        logger.error(f"Failed to analyze dependencies {analysis_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/discovery/agent-questions")
async def get_agent_questions(
    page: str = Query("dependencies", description="Page context for agent questions"),
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get agent questions for discovery agents."""
    try:
        logger.info(f"Getting agent questions for page: {page}")

        # Try to import agent UI bridge, fallback to sample data if not available
        try:
            from app.services.agent_ui_bridge import agent_ui_bridge

            questions = agent_ui_bridge.get_questions_for_page(page)
        except ImportError:
            logger.warning("Agent UI bridge not available, returning sample questions")
            questions = []

        # If no questions, provide sample questions
        if not questions and page == "dependencies":
            try:
                from app.services.agent_ui_bridge import agent_ui_bridge

                # Add sample dependency mapping question
                agent_ui_bridge.add_agent_question(
                    agent_id="dependency_analysis_agent",
                    agent_name="Dependency Analysis Agent",
                    question_type="dependency_validation",
                    page=page,
                    title="Verify Application Dependency",
                    question="Should 'WebApp-01' depend on 'Database-01' based on the network traffic patterns?",
                    context={
                        "source_app": "WebApp-01",
                        "target_app": "Database-01",
                        "confidence": 0.75,
                        "evidence": "Network traffic analysis shows regular connections",
                    },
                    options=[
                        "Yes, confirm this dependency",
                        "No, this is incorrect",
                        "Need more analysis",
                        "Mark as optional dependency",
                    ],
                    confidence="medium",
                    priority="normal",
                )

                # Get updated questions
                questions = agent_ui_bridge.get_questions_for_page(page)
            except ImportError:
                # Fallback to static sample questions if agent UI bridge not available
                questions = [
                    {
                        "id": "sample_dep_question_1",
                        "agent_id": "dependency_analysis_agent",
                        "agent_name": "Dependency Analysis Agent",
                        "question_type": "dependency_validation",
                        "page": page,
                        "title": "Verify Application Dependency",
                        "question": "Should 'WebApp-01' depend on 'Database-01' based on the network traffic patterns?",
                        "context": {
                            "source_app": "WebApp-01",
                            "target_app": "Database-01",
                            "confidence": 0.75,
                            "evidence": "Network traffic analysis shows regular connections",
                        },
                        "options": [
                            "Yes, confirm this dependency",
                            "No, this is incorrect",
                            "Need more analysis",
                            "Mark as optional dependency",
                        ],
                        "confidence": "medium",
                        "priority": "normal",
                    }
                ]

        return {
            "success": True,
            "questions": questions,
            "count": len(questions),
            "page": page,
        }

    except Exception as e:
        logger.error(f"Failed to get agent questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flow/{flow_id}/data-cleansing")
async def get_flow_data_cleansing(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context),
):
    """Get data cleansing analysis for a discovery flow."""
    try:
        # Import the data cleansing function from the new endpoint
        from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis

        # Create a mock current user for compatibility (will be properly handled by auth middleware)
        from app.models.client_account import User

        mock_user = User(id=context.user_id, email="system@example.com")

        # Call the data cleansing analysis endpoint
        result = await get_data_cleansing_analysis(
            flow_id=flow_id,
            include_details=True,
            db=db,
            context=context,
            current_user=mock_user,
        )

        return result
    except Exception as e:
        logger.error(
            f"❌ Failed to get data cleansing analysis for flow {flow_id}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def unified_discovery_health():
    """Health check endpoint for unified discovery API."""
    return {
        "status": "healthy",
        "service": "unified_discovery",
        "version": "1.0.0",
        "available_endpoints": [
            "GET /flows/active - Get active flows",
            "GET /flows/{flowId}/status - Get flow status",
            "POST /flow/{flowId}/execute - Execute flow",
            "POST /flow/{flowId}/resume - Resume flow",
            "POST /flow/{flowId}/retry - Retry flow",
            "DELETE /flow/{flowId} - Delete flow",
            "GET /flows/{flowId}/field-mappings - Get field mappings",
            "POST /flows/{flowId}/clarifications/submit - Submit clarifications",
            "GET /flow/{flowId}/agent-insights - Get agent insights",
            "GET /dependencies/analysis - Get dependency analysis",
            "POST /dependencies - Create dependencies",
            "GET /dependencies/applications - Get available applications",
            "GET /dependencies/servers - Get available servers",
            "POST /dependencies/analyze/{analysis_type} - Analyze dependencies",
            "GET /agents/discovery/agent-questions - Get agent questions",
        ],
        "integrated_with": [
            "Master Flow Orchestrator",
            "CrewAI Flows",
            "Multi-tenant Context",
            "Agent UI Bridge (optional)",
        ],
    }
