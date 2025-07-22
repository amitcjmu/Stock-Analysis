"""
Assessment Flow Service - Main Service Implementation

This service provides the main interface for executing assessment flows
through the CrewAI UnifiedAssessmentFlow. It follows the same patterns
as the discovery flow service and integrates with the Master Flow Orchestrator.

Key responsibilities:
- Initialize and execute UnifiedAssessmentFlow instances
- Manage assessment flow state through PostgreSQL persistence
- Handle pause/resume functionality for user input phases
- Provide status checking and flow management
- Delegate to real CrewAI agents for assessment intelligence
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.models.assessment_flow import AssessmentStatus
from app.services.crewai_flows.unified_assessment_flow import UnifiedAssessmentFlow, create_unified_assessment_flow

# from app.services.crewai_flows.persistence.postgres_store import PostgresStore  # Handled by master orchestrator

logger = logging.getLogger(__name__)


class AssessmentFlowService:
    """
    Main Assessment Flow Service that delegates to UnifiedAssessmentFlow
    
    This service provides the interface between the Master Flow Orchestrator
    and the actual CrewAI UnifiedAssessmentFlow implementation.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the assessment flow service"""
        self.db = db
        self._active_flows: Dict[str, UnifiedAssessmentFlow] = {}
        logger.info("✅ Assessment Flow Service initialized")
    
    async def create_assessment_flow(
        self,
        context: RequestContext,
        selected_application_ids: List[str],
        flow_name: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new assessment flow
        
        Args:
            context: Request context with tenant information
            selected_application_ids: Applications from Discovery inventory to assess
            flow_name: Optional human-readable name for the flow
            configuration: Optional flow configuration
            
        Returns:
            Dictionary with flow_id and initial status
        """
        try:
            # Generate unique flow ID
            flow_id = f"assess_{str(uuid.uuid4())[:8]}"
            
            logger.info(f"🚀 Creating assessment flow {flow_id} for {len(selected_application_ids)} applications")
            
            # Create the UnifiedAssessmentFlow instance
            assessment_flow = create_unified_assessment_flow(
                crewai_service=self,  # Pass self as the service
                context=context,
                selected_application_ids=selected_application_ids,
                flow_id=flow_id,
                flow_name=flow_name or f"Assessment Flow {flow_id}",
                configuration=configuration or {}
            )
            
            # Store the active flow
            self._active_flows[flow_id] = assessment_flow
            
            # Start the assessment flow in background
            logger.info(f"🎯 Starting CrewAI Assessment Flow kickoff for {flow_id}")
            
            async def run_assessment_flow():
                try:
                    # Start with initialization
                    await assessment_flow.initialize_assessment()
                    logger.info(f"✅ Assessment Flow {flow_id} initialized successfully")
                    
                except Exception as e:
                    logger.error(f"❌ Assessment Flow {flow_id} execution failed: {e}")
                    # Update flow state to failed
                    if hasattr(assessment_flow, 'state') and assessment_flow.state:
                        assessment_flow.state.status = AssessmentStatus.FAILED
                        assessment_flow.state.add_error("execution", str(e))
                        await assessment_flow.postgres_store.save_flow_state(assessment_flow.state)
            
            # Create the task but don't await it - let it run in background
            asyncio.create_task(run_assessment_flow())
            logger.info(f"🚀 Assessment Flow {flow_id} task created and running in background")
            
            return {
                "flow_id": flow_id,
                "status": "initialized",
                "selected_applications": len(selected_application_ids),
                "created_at": datetime.utcnow().isoformat(),
                "message": "Assessment flow created and running"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create assessment flow: {e}")
            raise RuntimeError(f"Assessment flow creation failed: {str(e)}")
    
    async def get_flow_status(
        self,
        flow_id: str,
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Get the current status of an assessment flow
        
        Args:
            flow_id: Assessment flow identifier
            context: Request context for tenant isolation
            
        Returns:
            Dictionary with current flow status and details
        """
        try:
            logger.info(f"📊 Getting status for assessment flow {flow_id}")
            
            # Try to get from active flows first
            if flow_id in self._active_flows:
                assessment_flow = self._active_flows[flow_id]
                if hasattr(assessment_flow, 'state') and assessment_flow.state:
                    state = assessment_flow.state
                    
                    return {
                        "flow_id": flow_id,
                        "flow_status": state.status.value if state.status else "unknown",
                        "current_phase": state.current_phase.value if state.current_phase else None,
                        "progress": state.progress,
                        "selected_applications": len(state.selected_application_ids),
                        "apps_ready_for_planning": len(state.apps_ready_for_planning) if state.apps_ready_for_planning else 0,
                        "phase_results": state.phase_results,
                        "user_input_required": state.status == AssessmentStatus.PAUSED_FOR_USER_INPUT,
                        "pause_points": state.pause_points,
                        "last_user_interaction": state.last_user_interaction.isoformat() if state.last_user_interaction else None,
                        "created_at": state.created_at.isoformat() if state.created_at else None,
                        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                        "errors": state.errors
                    }
            
            # Try to load from PostgreSQL persistence
            from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
            PostgresFlowStateStore(self.db, context)
            try:
                # This would need to be implemented to load assessment flow state
                # For now, return not found
                state = None
                if state:
                    return {
                        "flow_id": flow_id,
                        "flow_status": state.status.value if state.status else "unknown",
                        "current_phase": state.current_phase.value if state.current_phase else None,
                        "progress": state.progress,
                        "selected_applications": len(state.selected_application_ids),
                        "apps_ready_for_planning": len(state.apps_ready_for_planning) if state.apps_ready_for_planning else 0,
                        "phase_results": state.phase_results,
                        "user_input_required": state.status == AssessmentStatus.PAUSED_FOR_USER_INPUT,
                        "pause_points": state.pause_points,
                        "last_user_interaction": state.last_user_interaction.isoformat() if state.last_user_interaction else None,
                        "created_at": state.created_at.isoformat() if state.created_at else None,
                        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                        "errors": state.errors
                    }
            except Exception as e:
                logger.warning(f"Could not load flow state from persistence: {e}")
            
            # Flow not found
            return {
                "flow_id": flow_id,
                "flow_status": "not_found",
                "message": "Assessment flow not found"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get assessment flow status: {e}")
            return {
                "flow_id": flow_id,
                "flow_status": "error",
                "error": str(e)
            }
    
    async def resume_flow(
        self,
        flow_id: str,
        resume_context: Optional[Dict[str, Any]] = None,
        context: RequestContext = None
    ) -> Dict[str, Any]:
        """
        Resume a paused assessment flow with user input
        
        Args:
            flow_id: Assessment flow identifier
            resume_context: Context and user input for resuming
            context: Request context for tenant isolation
            
        Returns:
            Dictionary with resume operation result
        """
        try:
            logger.info(f"🔄 Resuming assessment flow {flow_id}")
            
            # Get or recreate the assessment flow
            assessment_flow = self._active_flows.get(flow_id)
            
            if not assessment_flow:
                logger.info(f"Assessment flow {flow_id} not in active flows, attempting to recreate")
                
                # Try to load state from persistence and recreate flow
                from app.services.crewai_flows.persistence.postgres_store import PostgresFlowStateStore
                PostgresFlowStateStore(self.db, context)
                # This would need to be implemented to load assessment flow state
                state = None
                
                if not state:
                    raise ValueError(f"Assessment flow {flow_id} not found")
                
                # Recreate the assessment flow
                assessment_flow = create_unified_assessment_flow(
                    crewai_service=self,
                    context=context,
                    selected_application_ids=state.selected_application_ids,
                    flow_id=flow_id
                )
                
                # Restore state
                assessment_flow.state = state
                self._active_flows[flow_id] = assessment_flow
            
            # Get current phase and user input
            current_phase = assessment_flow.state.current_phase
            
            # Ensure resume_context is not None
            if resume_context is None:
                resume_context = {}
                logger.info(f"🔍 resume_context was None for assessment flow {flow_id}, using empty dict")
            
            user_input = resume_context.get('user_input', {})
            
            # Resume from the current phase
            await assessment_flow.resume_from_phase(current_phase, user_input)
            
            logger.info(f"✅ Assessment flow {flow_id} resumed successfully")
            
            return {
                "flow_id": flow_id,
                "status": "resumed",
                "current_phase": current_phase.value if current_phase else None,
                "resumed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to resume assessment flow {flow_id}: {e}")
            raise RuntimeError(f"Assessment flow resume failed: {str(e)}")
    
    async def advance_flow_phase(
        self,
        flow_id: str,
        next_phase: str,
        context: RequestContext,
        phase_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Advance assessment flow to a specific phase
        
        Args:
            flow_id: Assessment flow identifier
            next_phase: Name of the phase to advance to
            context: Request context for tenant isolation
            phase_input: Optional input data for the phase
            
        Returns:
            Dictionary with advancement result
        """
        try:
            logger.info(f"⏭️ Advancing assessment flow {flow_id} to phase {next_phase}")
            
            # Get the assessment flow
            assessment_flow = self._active_flows.get(flow_id)
            if not assessment_flow:
                raise ValueError(f"Assessment flow {flow_id} not found in active flows")
            
            # Map phase names to methods
            phase_methods = {
                "architecture_minimums": assessment_flow.capture_architecture_minimums,
                "tech_debt_analysis": assessment_flow.analyze_technical_debt,
                "component_sixr_strategies": assessment_flow.determine_component_sixr_strategies,
                "app_on_page_generation": assessment_flow.generate_app_on_page,
                "finalization": assessment_flow.finalize_assessment
            }
            
            phase_method = phase_methods.get(next_phase)
            if not phase_method:
                raise ValueError(f"Unknown assessment phase: {next_phase}")
            
            # Execute the phase
            result = await phase_method("advanced_to_phase")
            
            logger.info(f"✅ Assessment flow {flow_id} advanced to {next_phase}")
            
            return {
                "flow_id": flow_id,
                "phase": next_phase,
                "status": "completed",
                "result": result,
                "advanced_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to advance assessment flow {flow_id} to {next_phase}: {e}")
            raise RuntimeError(f"Phase advancement failed: {str(e)}")
    
    async def list_active_flows(
        self,
        context: RequestContext,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        List active assessment flows for the tenant
        
        Args:
            context: Request context for tenant isolation
            limit: Maximum number of flows to return
            
        Returns:
            List of active assessment flows
        """
        try:
            logger.info(f"📋 Listing active assessment flows for tenant {context.client_account_id}")
            
            active_flows = []
            
            for flow_id, assessment_flow in list(self._active_flows.items())[:limit]:
                if hasattr(assessment_flow, 'state') and assessment_flow.state:
                    state = assessment_flow.state
                    
                    # Check tenant isolation
                    if str(state.client_account_id) == str(context.client_account_id):
                        active_flows.append({
                            "flow_id": flow_id,
                            "flow_name": getattr(state, 'flow_name', f"Assessment {flow_id}"),
                            "status": state.status.value if state.status else "unknown",
                            "current_phase": state.current_phase.value if state.current_phase else None,
                            "progress": state.progress,
                            "selected_applications": len(state.selected_application_ids),
                            "created_at": state.created_at.isoformat() if state.created_at else None,
                            "updated_at": state.updated_at.isoformat() if state.updated_at else None
                        })
            
            logger.info(f"✅ Found {len(active_flows)} active assessment flows")
            
            return active_flows
            
        except Exception as e:
            logger.error(f"❌ Failed to list active assessment flows: {e}")
            return []
    
    async def delete_flow(
        self,
        flow_id: str,
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Delete an assessment flow
        
        Args:
            flow_id: Assessment flow identifier
            context: Request context for tenant isolation
            
        Returns:
            Dictionary with deletion result
        """
        try:
            logger.info(f"🗑️ Deleting assessment flow {flow_id}")
            
            # Remove from active flows
            if flow_id in self._active_flows:
                del self._active_flows[flow_id]
                logger.info(f"Removed {flow_id} from active flows")
            
            # TODO: Implement PostgreSQL cleanup if needed
            # For now, we'll just remove from active memory
            
            return {
                "flow_id": flow_id,
                "deleted": True,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to delete assessment flow {flow_id}: {e}")
            raise RuntimeError(f"Assessment flow deletion failed: {str(e)}")