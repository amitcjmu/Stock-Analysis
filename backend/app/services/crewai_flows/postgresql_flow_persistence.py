"""
PostgreSQL Flow Persistence Layer
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Custom persistence layer that bridges CrewAI Flow state with PostgreSQL.
Migrating from WorkflowState to DiscoveryFlow V2 architecture.

This addresses the gap between CrewAI's built-in SQLite persistence and our
PostgreSQL multi-tenant enterprise requirements.
"""

import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, and_, or_, func, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import AsyncSessionLocal
from app.core.context import RequestContext

# V2 Discovery Flow imports (target architecture)
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset
from app.services.discovery_flow_service import DiscoveryFlowService
from app.repositories.discovery_flow_repository import DiscoveryFlowRepository

# Legacy imports for backward compatibility
from app.models.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

logger = logging.getLogger(__name__)

class PostgreSQLFlowPersistence:
    """
    ⚠️ LEGACY COMPATIBILITY LAYER - Use DiscoveryFlowService for new development
    
    Custom persistence layer that bridges CrewAI Flow state with PostgreSQL.
    
    Provides hybrid persistence strategy:
    1. CrewAI @persist() handles flow execution state and continuity
    2. This layer handles enterprise requirements (multi-tenancy, analytics, recovery)
    
    Key Features:
    - Multi-tenant flow isolation by client_account_id and engagement_id
    - Flow state validation and integrity checks
    - Advanced recovery and reconstruction capabilities
    - Performance monitoring and analytics integration
    - Seamless integration with V2 DiscoveryFlow models
    """
    
    def __init__(self, client_account_id: str, engagement_id: str, user_id: Optional[str] = None):
        """Initialize PostgreSQL persistence layer with tenant context"""
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id
        self.user_id = user_id or "system"
        
        # Convert string UUIDs to UUID objects for database operations
        try:
            self.client_uuid = uuid.UUID(client_account_id)
            self.engagement_uuid = uuid.UUID(engagement_id)
            self.user_uuid = uuid.UUID(user_id) if user_id and user_id != "system" else None
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid UUID format in persistence layer: {e}")
            raise ValueError(f"Invalid UUID format: {e}")
    
    async def persist_flow_initialization(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """
        Persist flow initialization to V2 DiscoveryFlow table.
        ⚠️ LEGACY METHOD - Use DiscoveryFlowService.create_discovery_flow() for new development
        """
        try:
            logger.info(f"🔄 [LEGACY] Persisting flow initialization using V2 architecture: {state.flow_id}")
            
            async with AsyncSessionLocal() as db_session:
                # Create mock context for V2 service
                from app.core.context import RequestContext
                context = RequestContext(
                    client_account_id=self.client_uuid,
                    engagement_id=self.engagement_uuid,
                    user_id=self.user_id or "system"
                )
                
                # Use V2 Discovery Flow Service
                flow_service = DiscoveryFlowService(db_session, context)
                
                # Create V2 discovery flow
                flow = await flow_service.create_discovery_flow(
                    flow_id=state.flow_id,
                    raw_data=state.raw_data or [],
                    metadata={
                        "legacy_migration": True,
                        "original_session_id": state.session_id,
                        "crewai_state": state.dict()
                    },
                    user_id=self.user_id
                )
                
                logger.info(f"✅ [LEGACY] Flow initialization persisted using V2: flow_id={flow.flow_id}")
                
                return {
                    "status": "success",
                    "flow_id": str(flow.flow_id),
                    "legacy_session_id": state.session_id,  # For backward compatibility
                    "persisted_at": datetime.utcnow().isoformat(),
                    "migration_note": "Persisted using V2 DiscoveryFlow architecture"
                }
                
        except Exception as e:
            logger.error(f"❌ [LEGACY] Failed to persist flow initialization: {e}")
            raise
    
    async def update_workflow_state(self, state: UnifiedDiscoveryFlowState) -> Dict[str, Any]:
        """
        Update V2 DiscoveryFlow with current flow state.
        ⚠️ LEGACY METHOD - Use DiscoveryFlowService.update_phase_completion() for new development
        """
        try:
            logger.info(f"🔄 [LEGACY] Updating flow state using V2 architecture: {state.flow_id}")
            
            async with AsyncSessionLocal() as db_session:
                # Create mock context for V2 service
                from app.core.context import RequestContext
                context = RequestContext(
                    client_account_id=self.client_uuid,
                    engagement_id=self.engagement_uuid,
                    user_id=self.user_id or "system"
                )
                
                # Use V2 Discovery Flow Service
                flow_service = DiscoveryFlowService(db_session, context)
                
                # Update flow with current phase if available
                if state.current_phase and state.current_phase != "initialization":
                    flow = await flow_service.update_phase_completion(
                        flow_id=state.flow_id,
                        phase=state.current_phase,
                        phase_data={
                            "status": state.status,
                            "progress": state.progress_percentage,
                            "crew_status": state.crew_status,
                            "legacy_data": state.dict()
                        },
                        crew_status=state.crew_status,
                        agent_insights=state.agent_insights or []
                    )
                else:
                    # Just get the flow for response
                    flow = await flow_service.get_flow_by_id(state.flow_id)
                
                if not flow:
                    logger.warning(f"⚠️ [LEGACY] No V2 flow found for ID: {state.flow_id}")
                    return {"status": "not_found", "flow_id": state.flow_id}
                
                logger.info(f"✅ [LEGACY] Flow state updated using V2: flow_id={flow.flow_id}, progress={flow.progress_percentage}%")
                
                return {
                    "status": "success",
                    "flow_id": str(flow.flow_id),
                    "legacy_session_id": state.session_id,  # For backward compatibility
                    "updated_at": datetime.utcnow().isoformat(),
                    "progress_percentage": flow.progress_percentage,
                    "current_phase": flow.get_next_phase() or "completed"
                }
                
        except Exception as e:
            logger.error(f"❌ [LEGACY] Failed to update flow state: {e}")
            return {"status": "error", "error": str(e)}

    async def persist_phase_completion(self, state: UnifiedDiscoveryFlowState, phase: str, crew_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Persist phase completion using V2 architecture
        ⚠️ LEGACY METHOD - Use DiscoveryFlowService.update_phase_completion() directly
        """
        try:
            logger.info(f"🔄 [LEGACY] Persisting phase completion using V2: {state.flow_id}, phase: {phase}")
            
            async with AsyncSessionLocal() as db_session:
                # Create mock context for V2 service
                from app.core.context import RequestContext
                context = RequestContext(
                    client_account_id=self.client_uuid,
                    engagement_id=self.engagement_uuid,
                    user_id=self.user_id or "system"
                )
                
                # Use V2 Discovery Flow Service
                flow_service = DiscoveryFlowService(db_session, context)
                
                # Update phase completion
                flow = await flow_service.update_phase_completion(
                    flow_id=state.flow_id,
                    phase=phase,
                    phase_data=crew_results,
                    crew_status=state.crew_status,
                    agent_insights=state.agent_insights or []
                )
                
                logger.info(f"✅ [LEGACY] Phase completion persisted using V2: {phase}, progress: {flow.progress_percentage}%")
                
                return {
                    "status": "success",
                    "flow_id": str(flow.flow_id),
                    "phase": phase,
                    "progress_percentage": flow.progress_percentage,
                    "next_phase": flow.get_next_phase(),
                    "persisted_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ [LEGACY] Failed to persist phase completion: {e}")
            return {"status": "error", "error": str(e)}
    
    async def restore_flow_state(self, session_id: str) -> Optional[UnifiedDiscoveryFlowState]:
        """
        Restore flow state from PostgreSQL for resumption.
        Provides fallback when CrewAI persistence is unavailable.
        """
        try:
            async with AsyncSessionLocal() as db_session:
                # Get workflow state with extensions
                stmt = select(WorkflowState).options(
                    selectinload(WorkflowState.crewai_extensions)
                ).where(
                    and_(
                        WorkflowState.session_id == uuid.UUID(session_id),
                        WorkflowState.client_account_id == self.client_uuid,
                        WorkflowState.engagement_id == self.engagement_uuid
                    )
                )
                
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    logger.warning(f"No workflow state found for session: {session_id}")
                    return None
                
                # Reconstruct UnifiedDiscoveryFlowState from database
                restored_state = UnifiedDiscoveryFlowState(
                    session_id=str(workflow.session_id),
                    flow_id=str(workflow.flow_id) if workflow.flow_id else str(uuid.uuid4()),
                    client_account_id=str(workflow.client_account_id),
                    engagement_id=str(workflow.engagement_id),
                    user_id=str(workflow.user_id) if workflow.user_id else self.user_id,
                    
                    # Flow state
                    current_phase=workflow.current_phase or "initialization",
                    status=workflow.status or "running",
                    progress_percentage=workflow.progress_percentage or 0.0,
                    phase_completion=workflow.phase_completion or {},
                    crew_status=workflow.crew_status or {},
                    
                    # Data state
                    raw_data=workflow.raw_data or [],
                    field_mappings=workflow.field_mappings or {},
                    cleaned_data=workflow.cleaned_data or [],
                    asset_inventory=workflow.asset_inventory or {},
                    dependencies=workflow.dependencies or {},
                    technical_debt=workflow.technical_debt or {},
                    
                    # Metadata
                    agent_insights=workflow.agent_insights or [],
                    success_criteria=workflow.success_criteria or {},
                    errors=workflow.errors or [],
                    warnings=workflow.warnings or [],
                    workflow_log=workflow.workflow_log or [],
                    
                    # Timestamps
                    started_at=workflow.started_at.isoformat() if workflow.started_at else datetime.utcnow().isoformat(),
                    created_at=workflow.created_at.isoformat() if workflow.created_at else datetime.utcnow().isoformat(),
                    updated_at=workflow.updated_at.isoformat() if workflow.updated_at else datetime.utcnow().isoformat(),
                    completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None
                )
                
                logger.info(f"✅ Flow state restored from PostgreSQL: session={session_id}")
                
                return restored_state
                
        except Exception as e:
            logger.error(f"❌ Failed to restore flow state: {e}")
            return None
    
    async def validate_flow_integrity(self, session_id: str) -> Dict[str, Any]:
        """
        Validate flow state integrity and detect corruption.
        Comprehensive health check for flow data consistency.
        """
        try:
            async with AsyncSessionLocal() as db_session:
                # Get workflow state
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.session_id == uuid.UUID(session_id),
                        WorkflowState.client_account_id == self.client_uuid,
                        WorkflowState.engagement_id == self.engagement_uuid
                    )
                )
                
                result = await db_session.execute(stmt)
                workflow = result.scalar_one_or_none()
                
                if not workflow:
                    return {
                        "status": "not_found",
                        "session_id": session_id,
                        "valid": False,
                        "errors": ["Workflow state not found"]
                    }
                
                validation_errors = []
                warnings = []
                
                # 1. Basic data integrity checks
                if not workflow.current_phase:
                    validation_errors.append("Missing current_phase")
                
                if workflow.progress_percentage < 0 or workflow.progress_percentage > 100:
                    validation_errors.append(f"Invalid progress_percentage: {workflow.progress_percentage}")
                
                if not workflow.status or workflow.status not in ['running', 'paused', 'completed', 'failed']:
                    validation_errors.append(f"Invalid status: {workflow.status}")
                
                # 2. Phase consistency checks
                phase_completion = workflow.phase_completion or {}
                completed_phases = [phase for phase, completed in phase_completion.items() if completed]
                
                if workflow.current_phase in completed_phases:
                    warnings.append(f"Current phase '{workflow.current_phase}' is marked as completed")
                
                # 3. Data consistency checks
                if workflow.current_phase in ['data_cleansing', 'asset_inventory'] and not workflow.field_mappings:
                    warnings.append("Field mappings missing for current phase")
                
                if workflow.current_phase in ['asset_inventory', 'dependency_analysis'] and not workflow.cleaned_data:
                    warnings.append("Cleaned data missing for current phase")
                
                # 4. Timestamp consistency
                if workflow.completed_at and workflow.status != 'completed':
                    validation_errors.append("Completed timestamp set but status is not 'completed'")
                
                if workflow.updated_at < workflow.created_at:
                    validation_errors.append("Updated timestamp is before created timestamp")
                
                is_valid = len(validation_errors) == 0
                
                logger.info(f"✅ Flow integrity validation completed: session={session_id}, valid={is_valid}, errors={len(validation_errors)}, warnings={len(warnings)}")
                
                return {
                    "status": "validated",
                    "session_id": session_id,
                    "valid": is_valid,
                    "errors": validation_errors,
                    "warnings": warnings,
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "flow_details": {
                        "current_phase": workflow.current_phase,
                        "status": workflow.status,
                        "progress_percentage": workflow.progress_percentage,
                        "completed_phases": completed_phases
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Flow integrity validation failed: {e}")
            return {
                "status": "error",
                "session_id": session_id,
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    async def cleanup_expired_flows(self, expiration_hours: int = 72) -> Dict[str, Any]:
        """
        Clean up expired flows for this tenant context.
        Removes flows older than expiration_hours that are not completed.
        """
        try:
            expiration_time = datetime.utcnow() - timedelta(hours=expiration_hours)
            
            async with AsyncSessionLocal() as db_session:
                # Find expired flows
                stmt = select(WorkflowState).where(
                    and_(
                        WorkflowState.client_account_id == self.client_uuid,
                        WorkflowState.engagement_id == self.engagement_uuid,
                        WorkflowState.updated_at < expiration_time,
                        WorkflowState.status.in_(['running', 'paused', 'failed'])
                    )
                )
                
                result = await db_session.execute(stmt)
                expired_flows = result.scalars().all()
                
                if not expired_flows:
                    return {
                        "status": "success",
                        "flows_cleaned": 0,
                        "message": "No expired flows found"
                    }
                
                # Delete expired flows and their extensions
                session_ids = [flow.session_id for flow in expired_flows]
                
                # Delete CrewAI extensions first (foreign key constraint)
                await db_session.execute(
                    delete(CrewAIFlowStateExtensions).where(
                        CrewAIFlowStateExtensions.session_id.in_(session_ids)
                    )
                )
                
                # Delete workflow states
                await db_session.execute(
                    delete(WorkflowState).where(
                        WorkflowState.session_id.in_(session_ids)
                    )
                )
                
                await db_session.commit()
                
                logger.info(f"✅ Cleaned up {len(expired_flows)} expired flows for tenant {self.client_account_id}/{self.engagement_id}")
                
                return {
                    "status": "success",
                    "flows_cleaned": len(expired_flows),
                    "session_ids": [str(sid) for sid in session_ids],
                    "expiration_hours": expiration_hours,
                    "cleanup_timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup expired flows: {e}")
            raise
    
    # Private helper methods
    
    async def _update_crewai_extensions(self, db_session: AsyncSession, state: UnifiedDiscoveryFlowState):
        """Update CrewAI extensions with latest collaboration data"""
        try:
            collaboration_entry = {
                "event": "state_update",
                "timestamp": datetime.utcnow().isoformat(),
                "phase": state.current_phase,
                "progress": state.progress_percentage,
                "crew_status": state.crew_status
            }
            
            # Get existing extensions
            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.session_id == uuid.UUID(state.session_id)
            )
            result = await db_session.execute(stmt)
            extensions = result.scalar_one_or_none()
            
            if extensions:
                # Update existing collaboration log
                collaboration_log = extensions.agent_collaboration_log or []
                collaboration_log.append(collaboration_entry)
                
                # Keep only last 100 entries to prevent bloat
                if len(collaboration_log) > 100:
                    collaboration_log = collaboration_log[-100:]
                
                # Update flow persistence data
                flow_persistence_data = extensions.flow_persistence_data or {}
                flow_persistence_data["last_state_snapshot"] = state.dict()
                flow_persistence_data["last_updated"] = datetime.utcnow().isoformat()
                
                # Update extensions
                stmt = update(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.session_id == uuid.UUID(state.session_id)
                ).values(
                    agent_collaboration_log=collaboration_log,
                    flow_persistence_data=flow_persistence_data,
                    updated_at=datetime.utcnow()
                )
                
                await db_session.execute(stmt)
            
        except Exception as e:
            logger.warning(f"Failed to update CrewAI extensions: {e}")
    
    async def _log_phase_completion(self, db_session: AsyncSession, session_id: str, phase: str, crew_results: Dict[str, Any]):
        """Log phase completion in CrewAI extensions"""
        try:
            completion_entry = {
                "event": "phase_completion",
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase,
                "crew_results_summary": {
                    "status": crew_results.get("status"),
                    "assets_processed": crew_results.get("assets_processed", 0),
                    "errors": len(crew_results.get("errors", [])),
                    "warnings": len(crew_results.get("warnings", []))
                }
            }
            
            # Update phase execution times
            stmt = select(CrewAIFlowStateExtensions).where(
                CrewAIFlowStateExtensions.session_id == uuid.UUID(session_id)
            )
            result = await db_session.execute(stmt)
            extensions = result.scalar_one_or_none()
            
            if extensions:
                # Update collaboration log
                collaboration_log = extensions.agent_collaboration_log or []
                collaboration_log.append(completion_entry)
                
                # Update phase execution times
                phase_times = extensions.phase_execution_times or {}
                phase_times[phase] = {
                    "completed_at": datetime.utcnow().isoformat(),
                    "duration_seconds": crew_results.get("execution_time_seconds", 0)
                }
                
                # Update extensions
                stmt = update(CrewAIFlowStateExtensions).where(
                    CrewAIFlowStateExtensions.session_id == uuid.UUID(session_id)
                ).values(
                    agent_collaboration_log=collaboration_log,
                    phase_execution_times=phase_times,
                    updated_at=datetime.utcnow()
                )
                
                await db_session.execute(stmt)
            
        except Exception as e:
            logger.warning(f"Failed to log phase completion: {e}") 