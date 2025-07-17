"""
Unified Discovery Flow API - Master Flow Orchestrator Integration

This endpoint provides the proper architectural flow as shown in the DFD:
File upload → /api/v1/unified-discovery/flow/initialize → MasterFlowOrchestrator → UnifiedDiscoveryFlow

ARCHITECTURAL FIX: This ensures all discovery flows go through the Master Flow Orchestrator
instead of bypassing it with direct CrewAI flow creation.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.services.master_flow_orchestrator import MasterFlowOrchestrator
from app.services.flow_configs import initialize_all_flows

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


@router.post("/flow/initialize", response_model=FlowInitializationResponse)
async def initialize_discovery_flow(
    request: FlowInitializationRequest,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
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
        logger.info(f"🎯 Initializing Discovery Flow via Master Flow Orchestrator")
        logger.info(f"🔍 Client: {context.client_account_id}, Engagement: {context.engagement_id}, User: {context.user_id}")
        logger.info(f"🔍 Raw data count: {len(request.raw_data) if request.raw_data else 0}")
        
        # Ensure flow configurations are initialized
        initialize_all_flows()
        
        # Initialize Master Flow Orchestrator
        orchestrator = MasterFlowOrchestrator(db, context)
        
        # Prepare configuration
        configuration = request.configuration or {}
        configuration.update({
            "source": "unified_discovery_api",
            "initialization_timestamp": datetime.utcnow().isoformat()
        })
        
        # Prepare initial state with raw data
        initial_state = {
            "raw_data": request.raw_data or [],
            "metadata": request.metadata or {}
        }
        
        # Create discovery flow through orchestrator
        logger.info(f"🚀 Creating discovery flow through Master Flow Orchestrator...")
        flow_result = await orchestrator.create_flow(
            flow_type="discovery",
            flow_name=request.flow_name or f"Discovery Flow {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            configuration=configuration,
            initial_state=initial_state
        )
        
        # Extract flow_id from result tuple
        if isinstance(flow_result, tuple) and len(flow_result) >= 1:
            flow_id = flow_result[0]
            flow_details = flow_result[1] if len(flow_result) > 1 else {}
            
            logger.info(f"✅ Discovery flow created successfully: {flow_id}")
            
            return FlowInitializationResponse(
                success=True,
                flow_id=flow_id,
                flow_name=request.flow_name or flow_details.get("flow_name"),
                status="initialized",
                message=f"Discovery flow initialized successfully with automatic kickoff"
            )
        else:
            logger.error(f"❌ Unexpected flow creation result: {flow_result}")
            return FlowInitializationResponse(
                success=False,
                status="failed",
                message="Flow creation returned unexpected result",
                error="Invalid flow creation response"
            )
            
    except Exception as e:
        logger.error(f"❌ Discovery flow initialization failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return FlowInitializationResponse(
            success=False,
            status="failed",
            message="Discovery flow initialization failed",
            error=str(e)
        )


@router.get("/flow/{flow_id}/status")
async def get_discovery_flow_status(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """
    Get discovery flow operational status.
    
    ADR-012: This endpoint returns child flow status for operational decisions.
    The child flow (discovery_flows table) contains the operational state needed
    for frontend display and agent decisions.
    """
    try:
        logger.info(f"🔍 Getting discovery flow operational status: {flow_id}")
        logger.info(f"🔍 Context: Client={context.client_account_id}, Engagement={context.engagement_id}")
        
        # ADR-012: Get child flow status directly from discovery_flows table
        from app.models.discovery_flow import DiscoveryFlow
        from sqlalchemy import select, and_
        
        # Query discovery flow with tenant context
        stmt = select(DiscoveryFlow).where(
            and_(
                DiscoveryFlow.flow_id == flow_id,
                DiscoveryFlow.client_account_id == context.client_account_id,
                DiscoveryFlow.engagement_id == context.engagement_id
            )
        )
        
        result = await db.execute(stmt)
        discovery_flow = result.scalar_one_or_none()
        
        if not discovery_flow:
            logger.warning(f"Discovery flow not found in child table: {flow_id} for client {context.client_account_id}")
            
            # ADR-012 Fallback: If child flow doesn't exist, try to get from master flow
            # This handles cases where the flow was created but child flow sync failed
            logger.info(f"🔄 Attempting fallback to master flow for {flow_id}")
            
            # Initialize Master Flow Orchestrator as fallback
            initialize_all_flows()
            orchestrator = MasterFlowOrchestrator(db, context)
            
            try:
                # Get master flow status
                master_status = await orchestrator.get_flow_status(flow_id)
                
                logger.info(f"✅ Found master flow status for {flow_id}, returning degraded response")
                
                # Return a degraded response with master flow data
                response = {
                    "success": True,
                    "flow_id": flow_id,
                    "status": master_status.get("status", "unknown"),
                    "current_phase": master_status.get("current_phase", "unknown"),
                    "progress_percentage": master_status.get("progress_percentage", 0),
                    "summary": {
                        "data_import_completed": master_status.get("phase_completion", {}).get("data_import", False),
                        "field_mapping_completed": master_status.get("phase_completion", {}).get("field_mapping", False),
                        "data_cleansing_completed": master_status.get("phase_completion", {}).get("data_cleansing", False),
                        "asset_inventory_completed": master_status.get("phase_completion", {}).get("asset_inventory", False),
                        "dependency_analysis_completed": master_status.get("phase_completion", {}).get("dependency_analysis", False),
                        "tech_debt_assessment_completed": master_status.get("phase_completion", {}).get("tech_debt_analysis", False),
                        "total_records": 0,
                        "records_processed": 0,
                        "quality_score": 0
                    },
                    "created_at": master_status.get("created_at"),
                    "updated_at": master_status.get("updated_at"),
                    # Return field mappings from master flow if available
                    "field_mappings": master_status.get("field_mappings", []),
                    "errors": ["Child flow record missing - using master flow data"],
                    "warnings": ["This is a degraded response. Some operational data may be missing."]
                }
                
                # Log this as a data integrity issue
                logger.error(f"⚠️ DATA INTEGRITY: Discovery flow {flow_id} exists in master but not in child table")
                
                return response
                
            except Exception as e:
                logger.error(f"❌ Master flow fallback also failed for {flow_id}: {e}")
                raise ValueError(f"Discovery flow not found: {flow_id}")
        
        # Get field mappings
        from app.models.field_mapping import FieldMapping
        field_mappings_stmt = select(FieldMapping).where(FieldMapping.flow_id == flow_id)
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
                "field_mapping_completed": discovery_flow.field_mapping_completed or False,
                "data_cleansing_completed": discovery_flow.data_cleansing_completed or False,
                "asset_inventory_completed": discovery_flow.asset_inventory_completed or False,
                "dependency_analysis_completed": discovery_flow.dependency_analysis_completed or False,
                "tech_debt_assessment_completed": discovery_flow.tech_debt_assessment_completed or False,
                "total_records": discovery_flow.total_records or 0,
                "records_processed": discovery_flow.records_processed or 0,
                "quality_score": discovery_flow.quality_score or 0
            },
            "created_at": discovery_flow.created_at.isoformat() if discovery_flow.created_at else None,
            "updated_at": discovery_flow.updated_at.isoformat() if discovery_flow.updated_at else None,
            # Additional operational fields
            "field_mappings": [
                {
                    "id": str(fm.id),
                    "source_field": fm.source_field,
                    "target_field": fm.target_field,
                    "confidence": fm.confidence,
                    "is_approved": fm.is_approved,
                    "status": fm.status,
                    "match_type": fm.match_type
                } for fm in field_mappings
            ] if field_mappings else [],
            "errors": [],
            "warnings": []
        }
        
        logger.info(f"✅ Retrieved discovery flow operational status for {flow_id}")
        return response
        
    except ValueError as e:
        # Flow not found - proper 404 handling
        logger.warning(f"Flow not found: {flow_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Flow {flow_id} not found"
        )
    except Exception as e:
        logger.error(f"❌ Failed to get discovery flow status for {flow_id}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.post("/flow/{flow_id}/pause")
async def pause_discovery_flow(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
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
    context: RequestContext = Depends(get_current_context)
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
    context: RequestContext = Depends(get_current_context)
):
    """Delete a discovery flow through Master Flow Orchestrator."""
    try:
        orchestrator = MasterFlowOrchestrator(db, context)
        result = await orchestrator.delete_flow(flow_id)
        return {"success": True, "flow_id": flow_id, "result": result}
    except Exception as e:
        logger.error(f"❌ Failed to delete flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flow/{flow_id}/data-cleansing")
async def get_flow_data_cleansing(
    flow_id: str,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_current_context)
):
    """Get data cleansing analysis for a discovery flow."""
    try:
        # Import the data cleansing function from the new endpoint
        from app.api.v1.endpoints.data_cleansing import get_data_cleansing_analysis
        
        # Create a mock current user for compatibility (will be properly handled by auth middleware)
        from app.models.user import User
        mock_user = User(id=context.user_id, email="system@example.com")
        
        # Call the data cleansing analysis endpoint
        result = await get_data_cleansing_analysis(
            flow_id=flow_id,
            include_details=True,
            db=db,
            context=context,
            current_user=mock_user
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Failed to get data cleansing analysis for flow {flow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))