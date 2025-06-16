"""
Enhanced CrewAI Flow Service
Integrates the simplified CrewAI Flow implementation with our existing system
Following CrewAI best practices while maintaining backward compatibility
"""

import logging
import asyncio
import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.schemas.flow_schemas import DiscoveryFlowState as LegacyDiscoveryFlowState
from app.services.crewai_flows.enhanced_discovery_flow import (
    create_enhanced_discovery_flow,
    EnhancedDiscoveryFlow,
    DiscoveryFlowState as EnhancedDiscoveryFlowState,
    CREWAI_FLOW_AVAILABLE
)

logger = logging.getLogger(__name__)

class EnhancedCrewAIFlowService:
    """
    Enhanced CrewAI Flow Service that uses the simplified Flow implementation.
    
    Key improvements:
    - Uses native CrewAI Flow patterns with @start/@listen decorators
    - Automatic state persistence with @persist decorator
    - Simplified control transfer between workflow steps
    - Better error handling and recovery
    - Maintains backward compatibility with existing API
    """
    
    def __init__(self, db: AsyncSession):
        from app.services.workflow_state_service import WorkflowStateService
        
        self.db = db
        self.state_service = WorkflowStateService(self.db)
        self.service_available = CREWAI_FLOW_AVAILABLE
        
        # Active flows tracking (for monitoring and management)
        self._active_flows: Dict[str, EnhancedDiscoveryFlow] = {}
        self._flow_creation_lock = asyncio.Lock()
        
        # Initialize agents (reuse existing logic)
        self.agents = self._initialize_agents()
        
        logger.info("Enhanced CrewAI Flow Service initialized")
        if not self.service_available:
            logger.warning("CrewAI Flow not available - using fallback mode")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize agents (reuse existing agent initialization logic)."""
        # This would typically reuse the existing agent initialization
        # For now, return empty dict to indicate fallback mode
        return {}
    
    async def initiate_enhanced_discovery_workflow(
        self,
        data_source: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Initiate a discovery workflow using the enhanced CrewAI Flow.
        
        This method provides the same interface as the legacy service but uses
        the simplified CrewAI Flow implementation internally.
        """
        try:
            # Parse and validate input data (reuse existing logic)
            file_data = data_source.get("file_data")
            if not file_data:
                raise ValueError("file_data is required for analysis")
            
            # Handle different input formats
            if isinstance(file_data, str):
                # Handle base64 or JSON string
                try:
                    if file_data.strip().startswith('['):
                        parsed_data = json.loads(file_data)
                    else:
                        # Assume base64 encoded CSV
                        import base64
                        import csv
                        import io
                        decoded = base64.b64decode(file_data).decode('utf-8')
                        string_io = io.StringIO(decoded)
                        parsed_data = list(csv.DictReader(string_io))
                except Exception as e:
                    raise ValueError(f"Invalid file_data format: {str(e)}")
            elif isinstance(file_data, list):
                parsed_data = file_data
            else:
                raise ValueError("file_data must be a list or string")
            
            metadata = data_source.get("metadata", {})
            cmdb_data = {"file_data": parsed_data, "metadata": metadata}
            
            # Generate session ID
            session_id = context.session_id or str(uuid.uuid4())
            
            # Create the enhanced flow
            async with self._flow_creation_lock:
                flow = create_enhanced_discovery_flow(
                    session_id=session_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    user_id=context.user_id or "anonymous",
                    cmdb_data=cmdb_data,
                    metadata=metadata,
                    crewai_service=self,
                    context=context
                )
                
                # Store the active flow for monitoring
                self._active_flows[session_id] = flow
            
            # Start the workflow in the background
            asyncio.create_task(self._run_enhanced_workflow_background(flow, context))
            
            # Return initial state in legacy format for backward compatibility
            initial_state = self._convert_to_legacy_format(flow.state)
            
            logger.info(f"Enhanced discovery workflow initiated for session: {session_id}")
            return initial_state
            
        except Exception as e:
            logger.error(f"Failed to initiate enhanced discovery workflow: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to start enhanced workflow: {str(e)}"
            }
    
    async def _run_enhanced_workflow_background(
        self,
        flow: EnhancedDiscoveryFlow,
        context: RequestContext
    ):
        """Run the enhanced workflow in the background."""
        session_id = flow.state.session_id
        
        try:
            logger.info(f"Starting enhanced workflow execution for session: {session_id}")
            
            # Execute the flow using CrewAI's kickoff method
            if CREWAI_FLOW_AVAILABLE:
                # Use native CrewAI Flow execution
                result = await asyncio.to_thread(flow.kickoff)
                logger.info(f"Enhanced workflow completed for session: {session_id}")
            else:
                # Fallback: manually execute the flow steps
                logger.info("Using fallback workflow execution")
                result = await self._execute_fallback_workflow(flow)
            
            # Update persistent state
            if self.state_service:
                legacy_state = self._convert_to_legacy_format(flow.state)
                await self.state_service.update_workflow_state(
                    session_id=session_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    status=flow.state.status,
                    current_phase=flow.state.current_phase,
                    state_data=legacy_state
                )
            
        except Exception as e:
            logger.error(f"Enhanced workflow failed for session {session_id}: {e}", exc_info=True)
            
            # Update state with error
            flow.state.status = "failed"
            flow.state.current_phase = "error"
            flow.state.add_error("workflow_execution", str(e))
            
            if self.state_service:
                legacy_state = self._convert_to_legacy_format(flow.state)
                await self.state_service.update_workflow_state(
                    session_id=session_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id,
                    status="failed",
                    current_phase="error",
                    state_data=legacy_state
                )
        finally:
            # Clean up active flow tracking
            if session_id in self._active_flows:
                del self._active_flows[session_id]
    
    async def _execute_fallback_workflow(self, flow: EnhancedDiscoveryFlow) -> str:
        """Execute workflow manually when CrewAI Flow is not available."""
        try:
            # Execute each step manually
            result = flow.initialize_discovery()
            result = flow.validate_data_quality(result)
            result = flow.map_source_fields(result)
            result = flow.classify_and_strategize(result)
            result = flow.analyze_relationships(result)
            result = flow.complete_discovery(result)
            
            return result
        except Exception as e:
            logger.error(f"Fallback workflow execution failed: {e}")
            raise
    
    def _convert_to_legacy_format(self, enhanced_state: EnhancedDiscoveryFlowState) -> Dict[str, Any]:
        """Convert enhanced state to legacy format for backward compatibility."""
        return {
            "flow_id": enhanced_state.session_id,
            "session_id": enhanced_state.session_id,
            "client_account_id": enhanced_state.client_account_id,
            "engagement_id": enhanced_state.engagement_id,
            "user_id": enhanced_state.user_id,
            "import_session_id": enhanced_state.session_id,
            "status": enhanced_state.status,
            "current_phase": enhanced_state.current_phase,
            "workflow_phases": list(enhanced_state.phases_completed.keys()),
            "phase_progress": {phase: (100.0 if completed else 0.0) for phase, completed in enhanced_state.phases_completed.items()},
            
            # Phase completion flags
            "data_source_analysis_complete": True,  # Always true in enhanced version
            "data_validation_complete": enhanced_state.phases_completed.get("data_validation", False),
            "field_mapping_complete": enhanced_state.phases_completed.get("field_mapping", False),
            "asset_classification_complete": enhanced_state.phases_completed.get("asset_classification", False),
            "dependency_analysis_complete": enhanced_state.phases_completed.get("dependency_analysis", False),
            "database_integration_complete": enhanced_state.phases_completed.get("database_integration", False),
            "completion_complete": enhanced_state.status == "completed",
            
            # Results
            "validated_structure": enhanced_state.results.get("data_validation", {}),
            "processed_data": {"cmdb_data": enhanced_state.cmdb_data},
            "suggested_field_mappings": enhanced_state.results.get("field_mapping", {}).get("mappings", {}),
            "asset_classifications": enhanced_state.results.get("asset_classification", {}).get("classifications", []),
            "agent_insights": enhanced_state.agent_insights,
            
            # Status and logging
            "status_message": f"Enhanced workflow: {enhanced_state.current_phase}",
            "workflow_log": [
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Enhanced workflow in phase: {enhanced_state.current_phase}",
                    "phase": enhanced_state.current_phase,
                    "extra_data": {
                        "progress_percentage": enhanced_state.progress_percentage,
                        "errors": enhanced_state.errors,
                        "warnings": enhanced_state.warnings
                    }
                }
            ]
        }
    
    async def get_enhanced_flow_state_by_session(
        self,
        session_id: str,
        context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """Get flow state by session ID, checking both active flows and persistent storage."""
        
        # First check active flows
        if session_id in self._active_flows:
            flow = self._active_flows[session_id]
            return self._convert_to_legacy_format(flow.state)
        
        # Fall back to persistent storage
        if self.state_service:
            workflow_state = await self.state_service.get_workflow_state_by_session_id(
                session_id=session_id,
                client_account_id=context.client_account_id,
                engagement_id=context.engagement_id
            )
            
            if workflow_state:
                return workflow_state.state_data
        
        return None
    
    def get_active_flows_summary(self) -> Dict[str, Any]:
        """Get summary of all active enhanced flows."""
        active_flows = []
        
        for session_id, flow in self._active_flows.items():
            flow_summary = {
                "session_id": session_id,
                "current_phase": flow.state.current_phase,
                "status": flow.state.status,
                "progress_percentage": flow.state.progress_percentage,
                "started_at": flow.state.started_at.isoformat() if flow.state.started_at else None,
                "total_errors": len(flow.state.errors),
                "phases_completed": flow.state.phases_completed
            }
            active_flows.append(flow_summary)
        
        return {
            "service_type": "enhanced_crewai_flow",
            "total_active_flows": len(self._active_flows),
            "crewai_flow_available": CREWAI_FLOW_AVAILABLE,
            "active_flows": active_flows
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the enhanced service."""
        return {
            "service_name": "enhanced_crewai_flow_service",
            "status": "healthy" if self.service_available else "degraded",
            "crewai_flow_available": CREWAI_FLOW_AVAILABLE,
            "active_flows": len(self._active_flows),
            "features": [
                "native_crewai_flows",
                "automatic_state_persistence",
                "simplified_control_transfer",
                "enhanced_error_handling",
                "backward_compatibility"
            ],
            "capabilities": {
                "declarative_flow_control": CREWAI_FLOW_AVAILABLE,
                "automatic_persistence": CREWAI_FLOW_AVAILABLE,
                "fallback_execution": True,
                "legacy_compatibility": True
            }
        }

# Factory function for dependency injection
def create_enhanced_crewai_flow_service(db: AsyncSession) -> EnhancedCrewAIFlowService:
    """Create an instance of the Enhanced CrewAI Flow Service."""
    return EnhancedCrewAIFlowService(db) 