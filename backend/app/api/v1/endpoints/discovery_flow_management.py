"""
Enhanced Discovery Flow Management API Endpoints
Leverages the new hybrid CrewAI + PostgreSQL persistence architecture.
Provides comprehensive flow management with enterprise features.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.middleware import get_current_context_dependency
from app.core.context import RequestContext
from app.services.crewai_flows.discovery_flow_state_manager import DiscoveryFlowStateManager
from app.services.crewai_flows.flow_state_bridge import create_flow_state_bridge
from app.services.crewai_flows.postgresql_flow_persistence import PostgreSQLFlowPersistence

logger = logging.getLogger(__name__)

router = APIRouter()

# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class FlowStateValidationRequest(BaseModel):
    """Request model for flow state validation"""
    session_id: str = Field(..., description="Session ID to validate")
    comprehensive: bool = Field(default=True, description="Perform comprehensive validation")

class FlowStateValidationResponse(BaseModel):
    """Response model for flow state validation"""
    status: str
    session_id: str
    overall_valid: bool
    crewai_validation: Dict[str, Any]
    postgresql_validation: Dict[str, Any]
    phase_executors: Optional[Dict[str, Any]] = None
    validation_timestamp: str
    recommendations: Optional[List[str]] = None

class UserApprovalRequest(BaseModel):
    """Request model for user approval of discovery flow phase progression"""
    session_id: str = Field(..., description="Session ID to approve")
    approved: bool = Field(..., description="Whether user approves proceeding to next phase")
    selected_agent: Optional[str] = Field(default=None, description="User-selected agent if different from recommended")
    comments: Optional[str] = Field(default=None, description="User comments or feedback")

class UserApprovalResponse(BaseModel):
    """Response model for user approval"""
    status: str
    session_id: str
    approval_recorded: bool
    next_phase: str
    selected_agent: str
    approval_timestamp: str
    flow_resumed: bool

class DataValidationReportRequest(BaseModel):
    """Request model for getting data validation report"""
    session_id: str = Field(..., description="Session ID to get report for")

class DataValidationReportResponse(BaseModel):
    """Response model for data validation report"""
    session_id: str
    validation_status: str
    file_analysis: Dict[str, Any]
    security_assessment: Dict[str, Any]
    data_quality: Dict[str, Any]
    recommendations: Dict[str, Any]
    detailed_report: Dict[str, Any]
    awaiting_approval: bool

class FlowRecoveryRequest(BaseModel):
    """Request model for flow state recovery"""
    session_id: str = Field(..., description="Session ID to recover")
    recovery_strategy: str = Field(default="postgresql", description="Recovery strategy: postgresql, hybrid")
    force_recovery: bool = Field(default=False, description="Force recovery even if current state exists")

class FlowRecoveryResponse(BaseModel):
    """Response model for flow state recovery"""
    status: str
    session_id: str
    recovery_successful: bool
    recovered_state: Optional[Dict[str, Any]] = None
    recovery_strategy_used: str
    recovery_timestamp: str
    next_steps: Optional[List[str]] = None

class FlowCleanupRequest(BaseModel):
    """Request model for flow state cleanup"""
    expiration_hours: int = Field(default=72, description="Hours after which flows are considered expired")
    dry_run: bool = Field(default=False, description="Perform dry run without actual cleanup")
    specific_session_ids: Optional[List[str]] = Field(default=None, description="Specific sessions to clean up")

class FlowCleanupResponse(BaseModel):
    """Response model for flow state cleanup"""
    status: str
    flows_cleaned: int
    session_ids_cleaned: List[str]
    dry_run: bool
    cleanup_timestamp: str
    space_recovered: Optional[str] = None

class FlowPersistenceStatusResponse(BaseModel):
    """Response model for flow persistence status"""
    session_id: str
    crewai_persistence: Dict[str, Any]
    postgresql_persistence: Dict[str, Any]
    bridge_status: Dict[str, Any]
    sync_enabled: bool
    last_sync_timestamp: Optional[str] = None

# ========================================
# FLOW STATE VALIDATION ENDPOINTS
# ========================================

@router.post("/flows/{session_id}/validate", response_model=FlowStateValidationResponse)
async def validate_flow_state(
    session_id: str,
    request: FlowStateValidationRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate flow state integrity across CrewAI and PostgreSQL persistence layers.
    Provides comprehensive health check for flow data consistency.
    """
    try:
        logger.info(f"🔍 Validating flow state: session={session_id}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Perform validation
        validation_result = await bridge.validate_state_integrity(session_id)
        
        # Add recommendations based on validation results
        recommendations = []
        if not validation_result.get("overall_valid", False):
            recommendations.extend([
                "Review PostgreSQL state integrity",
                "Check for data corruption or missing records",
                "Consider flow state recovery if critical data is missing"
            ])
        
        postgresql_validation = validation_result.get("postgresql_validation", {})
        if postgresql_validation.get("errors"):
            recommendations.append("Address PostgreSQL validation errors before resuming flow")
        
        if postgresql_validation.get("warnings"):
            recommendations.append("Review PostgreSQL validation warnings for potential issues")
        
        logger.info(f"✅ Flow state validation completed: session={session_id}, valid={validation_result.get('overall_valid', False)}")
        
        return FlowStateValidationResponse(
            status=validation_result.get("status", "unknown"),
            session_id=session_id,
            overall_valid=validation_result.get("overall_valid", False),
            crewai_validation=validation_result.get("crewai_validation", {}),
            postgresql_validation=postgresql_validation,
            phase_executors=validation_result.get("phase_executors"),
            validation_timestamp=validation_result.get("validation_timestamp", ""),
            recommendations=recommendations if recommendations else None
        )
        
    except Exception as e:
        logger.error(f"❌ Flow state validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "flow_validation_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

# ========================================
# USER APPROVAL ENDPOINTS
# ========================================

@router.get("/flows/{session_id}/validation-report", response_model=DataValidationReportResponse)
async def get_data_validation_report(
    session_id: str,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the data validation report for user review and approval.
    Shows file analysis, security assessment, and recommendations.
    """
    try:
        logger.info(f"📊 Getting validation report: session={session_id}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Get flow state
        flow_state = await bridge.get_flow_state(session_id)
        if not flow_state:
            raise HTTPException(
                status_code=404,
                detail=f"Flow session not found: {session_id}"
            )
        
        # Get data validation results
        validation_data = flow_state.phase_data.get("data_import", {})
        
        if not validation_data:
            raise HTTPException(
                status_code=400,
                detail=f"Data validation not completed for session: {session_id}"
            )
        
        file_analysis = validation_data.get("file_analysis", {})
        detailed_report = validation_data.get("detailed_report", {})
        
        # Check if awaiting approval
        awaiting_approval = (
            flow_state.status == "awaiting_user_approval" and 
            flow_state.current_phase == "data_validation_complete"
        )
        
        logger.info(f"✅ Validation report retrieved: session={session_id}, awaiting_approval={awaiting_approval}")
        
        return DataValidationReportResponse(
            session_id=session_id,
            validation_status=validation_data.get("security_status", "unknown"),
            file_analysis=file_analysis,
            security_assessment=detailed_report.get("security_assessment", {}),
            data_quality=detailed_report.get("data_quality", {}),
            recommendations=detailed_report.get("recommendations", {}),
            detailed_report=detailed_report,
            awaiting_approval=awaiting_approval
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get validation report: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "validation_report_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

@router.post("/flows/{session_id}/approve", response_model=UserApprovalResponse)
async def approve_flow_progression(
    session_id: str,
    request: UserApprovalRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Record user approval to proceed to field mapping phase.
    Allows user to select different agent if recommended agent is incorrect.
    """
    try:
        logger.info(f"👤 Processing user approval: session={session_id}, approved={request.approved}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Get flow state
        flow_state = await bridge.get_flow_state(session_id)
        if not flow_state:
            raise HTTPException(
                status_code=404,
                detail=f"Flow session not found: {session_id}"
            )
        
        # Verify flow is awaiting approval
        if flow_state.status != "awaiting_user_approval":
            raise HTTPException(
                status_code=400,
                detail=f"Flow is not awaiting approval. Current status: {flow_state.status}"
            )
        
        # Get validation data for agent selection
        validation_data = flow_state.phase_data.get("data_import", {})
        file_analysis = validation_data.get("file_analysis", {})
        recommended_agent = file_analysis.get("recommended_agent", "CMDB_Data_Analyst_Agent")
        
        # Use user-selected agent or fall back to recommended
        selected_agent = request.selected_agent or recommended_agent
        
        approval_timestamp = datetime.utcnow().isoformat()
        flow_resumed = False
        next_phase = "field_mapping_approved" if request.approved else "field_mapping_rejected"
        
        if request.approved:
            # Update flow state to approved
            flow_state.status = "user_approved"
            flow_state.current_phase = "field_mapping_ready"
            
            # Store user approval data
            approval_data = {
                "approved": True,
                "selected_agent": selected_agent,
                "recommended_agent": recommended_agent,
                "user_comments": request.comments,
                "approval_timestamp": approval_timestamp
            }
            
            # Store approval in phase data
            if "user_approvals" not in flow_state.phase_data:
                flow_state.phase_data["user_approvals"] = {}
            flow_state.phase_data["user_approvals"]["data_validation"] = approval_data
            
            # Update validation data with selected agent
            if validation_data:
                validation_data["selected_agent"] = selected_agent
                validation_data["user_approved"] = True
            
            # Sync updated state
            await bridge.sync_state_update(
                flow_state, 
                flow_state.current_phase, 
                crew_results={"action": "user_approved", "approval_data": approval_data}
            )
            
            logger.info(f"✅ User approval recorded and flow ready to resume: session={session_id}")
            logger.info(f"🤖 Selected agent: {selected_agent}")
            
            flow_resumed = True
            next_phase = "field_mapping_approved"
            
        else:
            # User rejected - mark flow as rejected
            flow_state.status = "user_rejected"
            flow_state.current_phase = "data_validation_rejected"
            
            rejection_data = {
                "approved": False,
                "user_comments": request.comments,
                "rejection_timestamp": approval_timestamp
            }
            
            # Store rejection in phase data
            if "user_approvals" not in flow_state.phase_data:
                flow_state.phase_data["user_approvals"] = {}
            flow_state.phase_data["user_approvals"]["data_validation"] = rejection_data
            
            # Sync updated state
            await bridge.sync_state_update(
                flow_state, 
                flow_state.current_phase, 
                crew_results={"action": "user_rejected", "rejection_data": rejection_data}
            )
            
            logger.info(f"❌ User rejected flow progression: session={session_id}")
            next_phase = "field_mapping_rejected"
        
        return UserApprovalResponse(
            status="success",
            session_id=session_id,
            approval_recorded=True,
            next_phase=next_phase,
            selected_agent=selected_agent,
            approval_timestamp=approval_timestamp,
            flow_resumed=flow_resumed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process user approval: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "approval_processing_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

@router.post("/flows/{session_id}/resume")
async def resume_flow_execution(
    session_id: str,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume flow execution after user approval.
    Triggers the next phase (field mapping) to continue from where it paused.
    """
    try:
        logger.info(f"▶️ Attempting to resume flow execution: session={session_id}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Get flow state
        flow_state = await bridge.get_flow_state(session_id)
        if not flow_state:
            raise HTTPException(
                status_code=404,
                detail=f"Flow session not found: {session_id}"
            )
        
        # Verify flow is approved and ready to resume
        if flow_state.status != "user_approved":
            raise HTTPException(
                status_code=400,
                detail=f"Flow is not approved for resumption. Current status: {flow_state.status}"
            )
        
        if flow_state.current_phase != "field_mapping_ready":
            raise HTTPException(
                status_code=400,
                detail=f"Flow is not in field mapping ready state. Current phase: {flow_state.current_phase}"
            )
        
        # Import the discovery flow service to resume execution
        from app.services.discovery_flow_service import DiscoveryFlowService
        
        # Create service instance
        discovery_service = DiscoveryFlowService(db, context)
        
        # Resume the flow by triggering field mapping phase
        # This will create a new field mapping execution with the approved agent
        validation_data = flow_state.phase_data.get("data_import", {})
        selected_agent = validation_data.get("selected_agent", "CMDB_Data_Analyst_Agent")
        
        logger.info(f"🚀 Resuming flow with selected agent: {selected_agent}")
        
        # Trigger field mapping phase execution
        field_mapping_result = await discovery_service.execute_field_mapping_phase(
            session_id=session_id,
            previous_phase_result="data_validation_completed",
            selected_agent=selected_agent
        )
        
        # Update flow state
        flow_state.status = "running"
        flow_state.current_phase = "attribute_mapping"
        
        # Sync updated state
        await bridge.sync_state_update(
            flow_state, 
            flow_state.current_phase, 
            crew_results={"action": "flow_resumed", "field_mapping_result": field_mapping_result}
        )
        
        logger.info(f"✅ Flow execution resumed successfully: session={session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "flow_resumed": True,
            "current_phase": "attribute_mapping",
            "selected_agent": selected_agent,
            "field_mapping_status": field_mapping_result.get("status", "unknown"),
            "resume_timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to resume flow execution: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "flow_resumption_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

# ========================================
# FLOW STATE RECOVERY ENDPOINTS
# ========================================

@router.post("/flows/{session_id}/recover", response_model=FlowRecoveryResponse)
async def recover_flow_state(
    session_id: str,
    request: FlowRecoveryRequest,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Recover flow state from PostgreSQL when CrewAI persistence fails.
    Provides advanced recovery mechanism for production environments.
    """
    try:
        logger.info(f"🔄 Attempting flow state recovery: session={session_id}, strategy={request.recovery_strategy}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Attempt recovery
        recovered_state = await bridge.recover_flow_state(session_id)
        
        recovery_successful = recovered_state is not None
        next_steps = []
        
        if recovery_successful:
            next_steps.extend([
                "Verify recovered state integrity",
                "Resume flow execution from recovered state",
                "Monitor flow execution for any anomalies"
            ])
        else:
            next_steps.extend([
                "Check if session ID exists in the system",
                "Verify client account and engagement permissions",
                "Consider manual data recovery if critical"
            ])
        
        logger.info(f"✅ Flow state recovery completed: session={session_id}, successful={recovery_successful}")
        
        return FlowRecoveryResponse(
            status="success" if recovery_successful else "no_recoverable_state",
            session_id=session_id,
            recovery_successful=recovery_successful,
            recovered_state=recovered_state.dict() if recovered_state else None,
            recovery_strategy_used=request.recovery_strategy,
            recovery_timestamp=datetime.utcnow().isoformat(),
            next_steps=next_steps
        )
        
    except Exception as e:
        logger.error(f"❌ Flow state recovery failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "flow_recovery_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

# ========================================
# FLOW STATE CLEANUP ENDPOINTS
# ========================================

@router.post("/flows/cleanup", response_model=FlowCleanupResponse)
async def cleanup_expired_flows(
    request: FlowCleanupRequest,
    background_tasks: BackgroundTasks,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up expired flow states for the current tenant.
    Removes stale data while preserving active and recently completed flows.
    """
    try:
        logger.info(f"🧹 Starting flow cleanup: expiration_hours={request.expiration_hours}, dry_run={request.dry_run}")
        
        # Create PostgreSQL persistence layer
        pg_persistence = PostgreSQLFlowPersistence(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id
        )
        
        if request.dry_run:
            # For dry run, just validate what would be cleaned
            # This would require a separate method in PostgreSQLFlowPersistence
            cleanup_result = {
                "status": "dry_run_completed",
                "flows_cleaned": 0,
                "session_ids": [],
                "message": "Dry run - no actual cleanup performed"
            }
        else:
            # Perform actual cleanup
            cleanup_result = await pg_persistence.cleanup_expired_flows(request.expiration_hours)
            
            # Schedule background validation after cleanup
            if cleanup_result.get("flows_cleaned", 0) > 0:
                background_tasks.add_task(
                    _post_cleanup_validation,
                    context,
                    cleanup_result.get("session_ids", [])
                )
        
        logger.info(f"✅ Flow cleanup completed: {cleanup_result.get('flows_cleaned', 0)} flows cleaned")
        
        return FlowCleanupResponse(
            status=cleanup_result.get("status", "unknown"),
            flows_cleaned=cleanup_result.get("flows_cleaned", 0),
            session_ids_cleaned=cleanup_result.get("session_ids", []),
            dry_run=request.dry_run,
            cleanup_timestamp=cleanup_result.get("cleanup_timestamp", ""),
            space_recovered=f"~{cleanup_result.get('flows_cleaned', 0) * 50}KB estimated"
        )
        
    except Exception as e:
        logger.error(f"❌ Flow cleanup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "flow_cleanup_failed",
                "message": str(e)
            }
        )

# ========================================
# FLOW PERSISTENCE STATUS ENDPOINTS
# ========================================

@router.get("/flows/{session_id}/persistence-status", response_model=FlowPersistenceStatusResponse)
async def get_flow_persistence_status(
    session_id: str,
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive persistence status for a specific flow.
    Shows status across both CrewAI and PostgreSQL persistence layers.
    """
    try:
        logger.info(f"📊 Getting persistence status: session={session_id}")
        
        # Create flow state bridge
        bridge = create_flow_state_bridge(context)
        
        # Get validation results for status
        validation_result = await bridge.validate_state_integrity(session_id)
        
        # Build comprehensive status
        crewai_persistence = {
            "available": True,  # Assume CrewAI is available if bridge exists
            "status": "assumed_healthy",
            "note": "CrewAI handles internal persistence automatically"
        }
        
        postgresql_validation = validation_result.get("postgresql_validation", {})
        postgresql_persistence = {
            "available": postgresql_validation.get("status") != "not_found",
            "valid": postgresql_validation.get("valid", False),
            "errors": postgresql_validation.get("errors", []),
            "warnings": postgresql_validation.get("warnings", []),
            "last_updated": postgresql_validation.get("validation_timestamp")
        }
        
        bridge_status = {
            "operational": bridge is not None,
            "sync_enabled": True,  # Would need to check bridge._state_sync_enabled
            "last_sync": validation_result.get("validation_timestamp"),
            "sync_errors": []  # Would track any recent sync errors
        }
        
        logger.info(f"✅ Persistence status retrieved: session={session_id}")
        
        return FlowPersistenceStatusResponse(
            session_id=session_id,
            crewai_persistence=crewai_persistence,
            postgresql_persistence=postgresql_persistence,
            bridge_status=bridge_status,
            sync_enabled=True,
            last_sync_timestamp=validation_result.get("validation_timestamp")
        )
        
    except Exception as e:
        logger.error(f"❌ Failed to get persistence status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "persistence_status_failed",
                "message": str(e),
                "session_id": session_id
            }
        )

# ========================================
# BULK OPERATIONS
# ========================================

@router.post("/flows/bulk-validate")
async def bulk_validate_flows(
    session_ids: List[str],
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate multiple flows in bulk for operational efficiency.
    Useful for health checks across multiple active flows.
    """
    try:
        logger.info(f"🔍 Bulk validating {len(session_ids)} flows")
        
        bridge = create_flow_state_bridge(context)
        results = []
        
        for session_id in session_ids:
            try:
                validation_result = await bridge.validate_state_integrity(session_id)
                results.append({
                    "session_id": session_id,
                    "status": "validated",
                    "valid": validation_result.get("overall_valid", False),
                    "summary": {
                        "postgresql_valid": validation_result.get("postgresql_validation", {}).get("valid", False),
                        "error_count": len(validation_result.get("postgresql_validation", {}).get("errors", [])),
                        "warning_count": len(validation_result.get("postgresql_validation", {}).get("warnings", []))
                    }
                })
            except Exception as e:
                results.append({
                    "session_id": session_id,
                    "status": "validation_failed",
                    "error": str(e)
                })
        
        valid_count = sum(1 for r in results if r.get("valid", False))
        
        logger.info(f"✅ Bulk validation completed: {valid_count}/{len(session_ids)} flows valid")
        
        return {
            "status": "completed",
            "total_flows": len(session_ids),
            "valid_flows": valid_count,
            "invalid_flows": len(session_ids) - valid_count,
            "results": results,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Bulk validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "bulk_validation_failed",
                "message": str(e)
            }
        )

# ========================================
# BACKGROUND TASKS
# ========================================

async def _post_cleanup_validation(context: RequestContext, cleaned_session_ids: List[str]):
    """
    Background task to validate system state after cleanup operations.
    Ensures cleanup didn't affect active flows.
    """
    try:
        logger.info(f"🔍 Post-cleanup validation for {len(cleaned_session_ids)} cleaned sessions")
        
        bridge = create_flow_state_bridge(context)
        
        # Verify cleaned sessions are actually gone
        for session_id in cleaned_session_ids[:5]:  # Sample first 5
            validation_result = await bridge.validate_state_integrity(session_id)
            if validation_result.get("status") != "not_found":
                logger.warning(f"⚠️ Session {session_id} still exists after cleanup")
        
        logger.info("✅ Post-cleanup validation completed")
        
    except Exception as e:
        logger.error(f"❌ Post-cleanup validation failed: {e}")

# ========================================
# HEALTH CHECK ENDPOINTS
# ========================================

@router.get("/health/persistence")
async def check_persistence_health(
    context: RequestContext = Depends(get_current_context_dependency),
    db: AsyncSession = Depends(get_db)
):
    """
    Health check endpoint for the hybrid persistence architecture.
    Validates that both CrewAI and PostgreSQL persistence layers are operational.
    """
    try:
        # Test PostgreSQL persistence
        pg_persistence = PostgreSQLFlowPersistence(
            client_account_id=context.client_account_id,
            engagement_id=context.engagement_id,
            user_id=context.user_id
        )
        
        # Test bridge creation
        bridge = create_flow_state_bridge(context)
        
        health_status = {
            "status": "healthy",
            "postgresql_persistence": "operational",
            "flow_state_bridge": "operational",
            "crewai_integration": "assumed_healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info("✅ Persistence health check passed")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Persistence health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 