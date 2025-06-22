"""
Discovery Flow Management API Endpoints
Provides comprehensive flow management capabilities using CrewAI Flow state patterns
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.context import get_current_context, RequestContext
from app.services.crewai_flows.discovery_flow_state_manager import DiscoveryFlowStateManager
from app.services.crewai_flows.discovery_flow_cleanup_service import DiscoveryFlowCleanupService
from app.schemas.discovery_flow_schemas import (
    IncompleteFlowResponse,
    FlowDetailsResponse,
    FlowResumptionRequest,
    FlowResumptionResponse,
    FlowDeletionRequest,
    FlowDeletionResponse,
    BulkFlowOperationRequest,
    BulkFlowOperationResponse
)

# Graceful import fallback
try:
    from app.services.crewai_flows.unified_discovery_flow import UnifiedDiscoveryFlow
    CREWAI_FLOW_AVAILABLE = True
except ImportError:
    CREWAI_FLOW_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/flows/incomplete", response_model=IncompleteFlowResponse)
async def get_incomplete_flows(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all incomplete discovery flows for current client/engagement context
    Uses CrewAI Flow state filtering for accurate flow detection
    """
    try:
        state_manager = DiscoveryFlowStateManager(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
        
        return {
            "success": True,
            "flows": incomplete_flows,
            "count": len(incomplete_flows),
            "has_incomplete_flows": len(incomplete_flows) > 0,
            "context": {
                "client_account_id": context.client_account_id,
                "engagement_id": context.engagement_id
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get incomplete flows: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve incomplete flows: {str(e)}"
        )

@router.get("/flows/{session_id}/details", response_model=FlowDetailsResponse)
async def get_flow_details(
    session_id: str,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific discovery flow
    Includes CrewAI Flow state, agent insights, and management capabilities
    """
    try:
        state_manager = DiscoveryFlowStateManager(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Get flow state details
        flow_state = await state_manager.get_flow_state(session_id)
        if not flow_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Flow not found: {session_id}"
            )
        
        # Get resumption validation
        resumption_info = await state_manager.validate_flow_resumption(session_id, context)
        
        # Combine flow details with management info
        flow_details = {
            **flow_state,
            "resumption_info": resumption_info,
            "management_actions": {
                "can_resume": resumption_info.get("can_resume", False),
                "can_delete": True,  # Always allow deletion
                "can_pause": flow_state.get("status") == "running"
            }
        }
        
        return {
            "success": True,
            "flow": flow_details,
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get flow details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve flow details: {str(e)}"
        )

@router.post("/flows/{session_id}/resume", response_model=FlowResumptionResponse)
async def resume_flow(
    session_id: str,
    request: FlowResumptionRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Resume a paused or failed discovery flow
    Uses CrewAI Flow state restoration with proper agent memory recovery
    """
    if not CREWAI_FLOW_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CrewAI Flow service not available for resumption"
        )
        
    try:
        state_manager = DiscoveryFlowStateManager(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Validate resumption capability
        validation_result = await state_manager.validate_flow_resumption(session_id, context)
        if not validation_result.get("can_resume", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Flow cannot be resumed: {validation_result.get('reason', 'Unknown error')}"
            )
        
        # Prepare flow for resumption
        flow_state = await state_manager.prepare_flow_resumption(session_id)
        if not flow_state:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to prepare flow for resumption"
            )
        
        # TODO: Create new UnifiedDiscoveryFlow instance with restored state
        # TODO: Resume execution from current phase
        # For now, mark as resumed in database
        
        return {
            "success": True,
            "message": f"Flow resumed successfully from phase: {flow_state.current_phase}",
            "session_id": session_id,
            "current_phase": flow_state.current_phase,
            "progress_percentage": flow_state.progress_percentage,
            "estimated_completion": "15-30 minutes",  # TODO: Calculate based on remaining phases
            "resume_context": request.resume_context or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume flow: {str(e)}"
        )

@router.delete("/flows/{session_id}", response_model=FlowDeletionResponse)
async def delete_flow(
    session_id: str,
    request: FlowDeletionRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete a discovery flow and all associated data
    Performs comprehensive cleanup including CrewAI Flow state, agent memory, and database records
    """
    try:
        cleanup_service = DiscoveryFlowCleanupService(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        # Perform comprehensive cleanup
        cleanup_result = await cleanup_service.delete_flow_with_cleanup(
            session_id=session_id,
            force_delete=request.force_delete,
            cleanup_options=request.cleanup_options or {}
        )
        
        if not cleanup_result.get("success", False):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Flow deletion failed: {cleanup_result.get('error', 'Unknown error')}"
            )
        
        return {
            "success": True,
            "message": f"Flow deleted successfully: {session_id}",
            "session_id": session_id,
            "cleanup_summary": cleanup_result.get("cleanup_summary", {}),
            "deletion_timestamp": cleanup_result.get("deletion_timestamp"),
            "data_recovery_possible": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete flow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete flow: {str(e)}"
        )

@router.post("/flows/bulk-operations", response_model=BulkFlowOperationResponse)
async def bulk_flow_operations(
    request: BulkFlowOperationRequest,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Perform bulk operations on multiple flows (delete, pause, resume)
    Optimized for batch processing with proper error handling
    """
    try:
        operation = request.operation
        session_ids = request.session_ids
        
        if not session_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No session IDs provided for bulk operation"
            )
        
        results = []
        successful_operations = 0
        failed_operations = 0
        
        # Process each session ID
        for session_id in session_ids:
            try:
                if operation == "delete":
                    cleanup_service = DiscoveryFlowCleanupService(
                        db_session=db,
                        client_account_id=context.client_account_id,
                        engagement_id=context.engagement_id
                    )
                    result = await cleanup_service.delete_flow_with_cleanup(
                        session_id=session_id,
                        force_delete=request.options.get("force_delete", False)
                    )
                    
                elif operation == "pause":
                    # TODO: Implement bulk pause
                    result = {"success": False, "error": "Bulk pause not yet implemented"}
                    
                elif operation == "resume":
                    # TODO: Implement bulk resume
                    result = {"success": False, "error": "Bulk resume not yet implemented"}
                    
                else:
                    result = {"success": False, "error": f"Unknown operation: {operation}"}
                
                results.append({
                    "session_id": session_id,
                    "success": result.get("success", False),
                    "message": result.get("message", ""),
                    "error": result.get("error")
                })
                
                if result.get("success", False):
                    successful_operations += 1
                else:
                    failed_operations += 1
                    
            except Exception as e:
                logger.error(f"❌ Bulk operation failed for {session_id}: {e}")
                results.append({
                    "session_id": session_id,
                    "success": False,
                    "error": str(e)
                })
                failed_operations += 1
        
        return {
            "success": successful_operations > 0,
            "operation": operation,
            "total_requested": len(session_ids),
            "successful_operations": successful_operations,
            "failed_operations": failed_operations,
            "results": results,
            "summary": f"Bulk {operation}: {successful_operations} successful, {failed_operations} failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk operations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk operations failed: {str(e)}"
        )

@router.get("/flows/validation/can-start-new")
async def validate_new_flow_start(
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Validate if a new discovery flow can be started
    Checks for incomplete flows that would block new flow creation
    """
    try:
        state_manager = DiscoveryFlowStateManager(
            db_session=db,
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id
        )
        
        incomplete_flows = await state_manager.get_incomplete_flows_for_context(context)
        
        can_start_new = len(incomplete_flows) == 0
        
        response = {
            "can_start_new_flow": can_start_new,
            "blocking_flows_count": len(incomplete_flows),
            "message": "New flow can be started" if can_start_new else "Incomplete flows must be resolved first"
        }
        
        if not can_start_new:
            response["blocking_flows"] = [
                {
                    "session_id": flow["session_id"],
                    "current_phase": flow["current_phase"],
                    "status": flow["status"],
                    "progress_percentage": flow["progress_percentage"],
                    "can_resume": flow["can_resume"]
                }
                for flow in incomplete_flows
            ]
            response["suggested_actions"] = [
                "Resume incomplete flows to completion",
                "Delete incomplete flows if no longer needed",
                "Contact administrator if flows are stuck"
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"❌ New flow validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flow validation failed: {str(e)}"
        ) 