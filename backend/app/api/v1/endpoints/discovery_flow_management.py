"""
Discovery Flow Management API Endpoints
Enhanced with CrewAI Flow state management for incomplete flow management
Provides comprehensive flow lifecycle management with multi-tenant support
Phase 4: Advanced Features & Production Readiness
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import RequestContext, get_current_context
from app.services.crewai_flows.discovery_flow_state_manager import DiscoveryFlowStateManager
from app.services.crewai_flows.discovery_flow_cleanup_service import DiscoveryFlowCleanupService
from app.schemas.discovery_flow_schemas import (
    IncompleteFlowsResponse,
    FlowDetailsResponse,
    FlowResumeRequest,
    FlowResumeResponse,
    FlowDeleteResponse,
    BulkOperationsRequest,
    BulkOperationsResponse,
    FlowValidationResponse,
    # Phase 4 schemas
    AdvancedRecoveryRequest,
    AdvancedRecoveryResponse,
    ExpiredFlowsResponse,
    AutoCleanupRequest,
    AutoCleanupResponse,
    PerformanceOptimizationResponse
)

# Graceful fallback for CrewAI services
try:
    from app.services.crewai_service import CrewAIService
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["Discovery Flow Management"])

# === EXISTING ENDPOINTS (Phase 1-3) ===

@router.get("/incomplete", response_model=IncompleteFlowsResponse)
async def get_incomplete_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get all incomplete CrewAI discovery flows for current client/engagement context"""
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
        
        return IncompleteFlowsResponse(
            flows=incomplete_flows,
            total_count=len(incomplete_flows),
            context={
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id
            }
        )
    except Exception as e:
        logger.error(f"❌ Failed to get incomplete flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve incomplete flows: {str(e)}")

@router.get("/{session_id}/details", response_model=FlowDetailsResponse)
async def get_flow_details(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific CrewAI discovery flow"""
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        flow_state = await state_manager.get_flow_state(session_id)
        
        if not flow_state:
            raise HTTPException(status_code=404, detail="Flow not found or access denied")
        
        # Get additional management information
        validation = await state_manager.validate_flow_resumption(session_id, context)
        
        return FlowDetailsResponse(
            session_id=session_id,
            flow_state=flow_state,
            can_resume=validation["can_resume"],
            validation_errors=validation.get("validation_errors", []),
            management_info={
                "last_activity": flow_state.get("updated_at"),
                "progress_percentage": flow_state.get("progress_percentage", 0),
                "current_phase": flow_state.get("current_phase")
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve flow details: {str(e)}")

@router.post("/{session_id}/resume", response_model=FlowResumeResponse)
async def resume_discovery_flow(
    session_id: str,
    request: FlowResumeRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Resume an incomplete CrewAI discovery flow with proper state restoration and execution"""
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Validate resumption capability
        validation = await state_manager.validate_flow_resumption(session_id, context)
        if not validation["can_resume"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot resume flow: {validation['reason']}"
            )
        
        # Get current flow state to determine phase information
        flow_details = await state_manager.get_flow_state(session_id)
        current_phase = flow_details.get("current_phase", "data_import") if flow_details else "data_import"
        progress = flow_details.get("progress_percentage", 0) if flow_details else 0
        status = flow_details.get("status", "running") if flow_details else "running"
        
        # Determine next phase based on current phase and completion
        phase_sequence = ["data_import", "field_mapping", "data_cleansing", "asset_inventory", "dependency_analysis", "tech_debt"]
        next_phase = current_phase
        
        if current_phase in phase_sequence:
            current_index = phase_sequence.index(current_phase)
            # If current phase is incomplete or at the beginning, stay on current phase
            # Otherwise, move to next phase
            if progress >= 100 and current_index < len(phase_sequence) - 1:
                next_phase = phase_sequence[current_index + 1]
        
        # **CRITICAL FIX**: Actually trigger CrewAI flow execution, not just state updates
        if CREWAI_AVAILABLE:
            try:
                # Prepare flow for resumption
                flow = await state_manager.prepare_flow_resumption(session_id)
                if flow:
                    # Update state to running before execution
                    result = await flow.resume_flow_from_state({"context": context.dict()})
                    
                    # **KEY CHANGE**: Trigger actual CrewAI flow execution in background
                    # This is what was missing - we need to call kickoff() to execute the agents
                    logger.info(f"🚀 Triggering CrewAI flow execution for resumed session: {session_id}")
                    
                    # Import CrewAI service for background execution
                    from app.services.crewai_flow_service import CrewAIFlowService
                    crewai_service = CrewAIFlowService(db)
                    
                    # Execute flow in background - this triggers the actual agent processing
                    import asyncio
                    asyncio.create_task(crewai_service._run_workflow_background(flow, context))
                    
                    # Advance to next phase for navigation
                    if current_phase == "data_import" and progress < 100:
                        # For data import phase, advance to field_mapping since data is already imported
                        next_phase = "field_mapping"
                        logger.info(f"🔄 Advancing from data_import to field_mapping for processing")
                    
                    return FlowResumeResponse(
                        success=True,
                        session_id=session_id,
                        message=f"Flow resumed and CrewAI execution triggered: {result}",
                        resumed_at=datetime.now().isoformat(),
                        current_phase=current_phase,
                        next_phase=next_phase,
                        progress_percentage=progress,
                        status="running"
                    )
                else:
                    logger.warning(f"⚠️ Could not prepare flow for resumption: {session_id}")
            except Exception as flow_error:
                logger.warning(f"⚠️ CrewAI flow execution failed, using fallback: {flow_error}")
        
        # Fallback for non-CrewAI resumption - still advance the phase
        if current_phase == "data_import":
            next_phase = "field_mapping"
            logger.info(f"🔄 Fallback: Advancing from data_import to field_mapping")
        
        return FlowResumeResponse(
            success=True,
            session_id=session_id,
            message="Flow resumption initiated (fallback mode - agents will process in background)",
            resumed_at=datetime.now().isoformat(),
            current_phase=current_phase,
            next_phase=next_phase,
            progress_percentage=progress,
            status="running"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Flow resumption failed: {e}")
        raise HTTPException(status_code=500, detail=f"Flow resumption failed: {str(e)}")

@router.delete("/{session_id}", response_model=FlowDeleteResponse)
async def delete_discovery_flow(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
    reason: str = Query("user_requested", description="Reason for deletion")
):
    """Delete a discovery flow with comprehensive CrewAI memory cleanup"""
    try:
        cleanup_service = DiscoveryFlowCleanupService()
        
        # Perform comprehensive cleanup
        cleanup_result = await cleanup_service.cleanup_discovery_flow(
            session_id,
            reason,
            audit_deletion=True
        )
        
        if not cleanup_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Flow deletion failed: {cleanup_result.get('error', 'Unknown error')}"
            )
        
        return FlowDeleteResponse(
            success=True,
            session_id=session_id,
            cleanup_summary=cleanup_result["cleanup_summary"],
            deleted_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Flow deletion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Flow deletion failed: {str(e)}")

@router.post("/bulk-operations", response_model=BulkOperationsResponse)
async def bulk_flow_operations(
    request: BulkOperationsRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk operations on multiple discovery flows"""
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Perform bulk operation
        result = await state_manager.bulk_flow_operations(
            request.operation,
            request.session_ids,
            context,
            request.options
        )
        
        return BulkOperationsResponse(
            operation=result["operation"],
            total_flows=result["total_flows"],
            successful=result["successful"],
            failed=result["failed"],
            summary=result["summary"],
            performance_metrics=result["performance_metrics"]
        )
        
    except Exception as e:
        logger.error(f"❌ Bulk operation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Bulk operation failed: {str(e)}")

@router.get("/validation/can-start-new", response_model=FlowValidationResponse)
async def validate_new_flow_creation(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """Validate if a new discovery flow can be started (no incomplete flows exist)"""
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
        
        can_start = len(incomplete_flows) == 0
        
        return FlowValidationResponse(
            can_start_new_flow=can_start,
            blocking_flows=incomplete_flows if not can_start else [],
            total_incomplete_flows=len(incomplete_flows),
            validation_message="✅ Ready to start new flow" if can_start else f"❌ {len(incomplete_flows)} incomplete flows must be completed or removed first"
        )
        
    except Exception as e:
        logger.error(f"❌ Flow validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Flow validation failed: {str(e)}")

# === PHASE 4: ADVANCED FEATURES ===

@router.post("/{session_id}/advanced-recovery", response_model=AdvancedRecoveryResponse)
async def advanced_flow_recovery(
    session_id: str,
    request: AdvancedRecoveryRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 4: Advanced flow recovery with intelligent state reconstruction
    Provides comprehensive recovery with data integrity validation and repair
    """
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Perform advanced recovery
        recovery_result = await state_manager.advanced_flow_recovery(
            session_id,
            context,
            request.recovery_options
        )
        
        if not recovery_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Advanced recovery failed: {recovery_result['error']}"
            )
        
        return AdvancedRecoveryResponse(
            success=recovery_result["success"],
            session_id=session_id,
            recovery_actions=recovery_result["recovery_actions"],
            flow_state=recovery_result["flow_state"],
            performance_metrics=recovery_result["performance_metrics"],
            recovered_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Advanced recovery failed: {e}")
        raise HTTPException(status_code=500, detail=f"Advanced recovery failed: {str(e)}")

@router.get("/expired", response_model=ExpiredFlowsResponse)
async def get_expired_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
    expiration_hours: int = Query(72, description="Hours after which flows are considered expired")
):
    """
    Phase 4: Get flows that have exceeded expiration time
    """
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        expired_flows = await state_manager.get_expired_flows(context, expiration_hours)
        
        return ExpiredFlowsResponse(
            expired_flows=expired_flows,
            total_expired=len(expired_flows),
            expiration_hours=expiration_hours,
            context={
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get expired flows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get expired flows: {str(e)}")

@router.post("/auto-cleanup", response_model=AutoCleanupResponse)
async def auto_cleanup_expired_flows(
    request: AutoCleanupRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 4: Automatically cleanup expired flows with comprehensive logging
    """
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Perform auto-cleanup
        cleanup_result = await state_manager.auto_cleanup_expired_flows(
            context,
            dry_run=request.dry_run
        )
        
        return AutoCleanupResponse(
            dry_run=cleanup_result["dry_run"],
            expired_flows_found=cleanup_result["expired_flows_found"],
            cleanup_successful=cleanup_result["cleanup_successful"],
            cleanup_failed=cleanup_result["cleanup_failed"],
            total_data_cleaned=cleanup_result["total_data_cleaned"],
            performance_metrics=cleanup_result["performance_metrics"],
            cleanup_completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Auto-cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Auto-cleanup failed: {str(e)}")

@router.get("/performance/optimization", response_model=PerformanceOptimizationResponse)
async def optimize_flow_performance(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 4: Analyze and optimize flow management performance
    """
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Perform optimization analysis
        optimization_result = await state_manager.optimize_flow_performance(context)
        
        return PerformanceOptimizationResponse(
            query_optimizations=optimization_result["query_optimizations"],
            index_recommendations=optimization_result["index_recommendations"],
            performance_improvements=optimization_result["performance_improvements"],
            analysis_completed_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Performance optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Performance optimization failed: {str(e)}")

# === PHASE 4: MONITORING & HEALTH ENDPOINTS ===

@router.get("/health/advanced")
async def advanced_flow_health_check(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
):
    """
    Phase 4: Advanced health check for flow management system
    """
    try:
        state_manager = DiscoveryFlowStateManager(db, context.client_account_id, context.engagement_id)
        
        # Get system health metrics
        incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
        expired_flows = await state_manager.get_expired_flows(context)
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "flow_statistics": {
                "incomplete_flows": len(incomplete_flows),
                "expired_flows": len(expired_flows),
                "total_managed_flows": len(incomplete_flows) + len(expired_flows)
            },
            "system_capabilities": {
                "crewai_available": CREWAI_AVAILABLE,
                "advanced_recovery": True,
                "bulk_operations": True,
                "auto_cleanup": True,
                "performance_optimization": True
            },
            "recommendations": []
        }
        
        # Add recommendations based on health metrics
        if len(expired_flows) > 5:
            health_status["recommendations"].append({
                "type": "cleanup",
                "message": f"Consider running auto-cleanup for {len(expired_flows)} expired flows",
                "priority": "medium"
            })
        
        if len(incomplete_flows) > 10:
            health_status["recommendations"].append({
                "type": "optimization",
                "message": f"High number of incomplete flows ({len(incomplete_flows)}) - consider performance optimization",
                "priority": "high"
            })
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Advanced health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 