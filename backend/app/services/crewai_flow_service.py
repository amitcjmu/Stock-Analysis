"""
CrewAI Flow Service
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
from app.services.crewai_flows.discovery_flow import (
    create_discovery_flow,
    DiscoveryFlow,
    DiscoveryFlowState,
    CREWAI_FLOW_AVAILABLE
)

logger = logging.getLogger(__name__)

class CrewAIFlowService:
    """
    CrewAI Flow Service that uses the simplified Flow implementation.
    
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
        self._active_flows: Dict[str, DiscoveryFlow] = {}
        self._flow_creation_lock = asyncio.Lock()
        
        # Initialize agents (reuse existing logic)
        self.agents = self._initialize_agents()
        
        logger.info("CrewAI Flow Service initialized")
        if not self.service_available:
            logger.warning("CrewAI Flow not available - using fallback mode")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize agents (reuse existing agent initialization logic)."""
        # This would typically reuse the existing agent initialization
        # For now, return empty dict to indicate fallback mode
        return {}
    
    async def initiate_discovery_workflow(
        self,
        data_source: Dict[str, Any],
        context: RequestContext
    ) -> Dict[str, Any]:
        """
        Initiate a discovery workflow using the CrewAI Flow.
        
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
            
            # Create the flow
            async with self._flow_creation_lock:
                flow = create_discovery_flow(
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
            asyncio.create_task(self._run_workflow_background(flow, context))
            
            # Return initial state in legacy format for backward compatibility
            initial_state = self._convert_to_legacy_format(flow.state)
            
            logger.info(f"Discovery workflow initiated for session: {session_id}")
            return initial_state
            
        except Exception as e:
            logger.error(f"Failed to initiate discovery workflow: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Failed to start workflow: {str(e)}"
            }
    
    async def _run_workflow_background(
        self,
        flow: DiscoveryFlow,
        context: RequestContext
    ):
        """Run the workflow in the background."""
        session_id = flow.state.session_id
        
        try:
            logger.info(f"Starting workflow execution for session: {session_id}")
            
            # Execute the flow using CrewAI's kickoff method
            if CREWAI_FLOW_AVAILABLE:
                # Use native CrewAI Flow execution
                result = await asyncio.to_thread(flow.kickoff)
                logger.info(f"Workflow completed for session: {session_id}")
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
            logger.error(f"Workflow failed for session {session_id}: {e}", exc_info=True)
            
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
    
    async def _execute_fallback_workflow(self, flow: DiscoveryFlow) -> str:
        """Execute workflow manually when CrewAI Flow is not available."""
        try:
            # Execute each step manually
            result = flow.initialize_discovery()
            result = flow.validate_data_quality(result)
            result = flow.map_source_fields(result)
            result = flow.classify_assets(result)
            result = flow.analyze_dependencies(result)
            result = flow.finalize_discovery(result)
            
            return result
        except Exception as e:
            logger.error(f"Fallback workflow execution failed: {e}")
            raise
    
    def _convert_to_legacy_format(self, flow_state: DiscoveryFlowState) -> Dict[str, Any]:
        """Convert flow state to legacy format for backward compatibility."""
        return {
            "session_id": flow_state.session_id,
            "client_account_id": flow_state.client_account_id,
            "engagement_id": flow_state.engagement_id,
            "user_id": flow_state.user_id,
            "status": flow_state.status,
            "current_phase": flow_state.current_phase,
            "phases_completed": flow_state.phases_completed,
            "results": flow_state.results,
            "errors": flow_state.errors,
            "metadata": flow_state.metadata,
            "created_at": flow_state.created_at.isoformat() if flow_state.created_at else None,
            "updated_at": flow_state.updated_at.isoformat() if flow_state.updated_at else None,
            
            # Legacy fields for compatibility
            "data_validation": {
                "status": "completed" if flow_state.phases_completed.get("data_validation") else "pending",
                "results": flow_state.results.get("data_validation", {})
            },
            "field_mapping": {
                "status": "completed" if flow_state.phases_completed.get("field_mapping") else "pending",
                "results": flow_state.results.get("field_mapping", {})
            },
            "asset_classification": {
                "status": "completed" if flow_state.phases_completed.get("asset_classification") else "pending",
                "results": flow_state.results.get("asset_classification", {})
            },
            "dependency_analysis": {
                "status": "completed" if flow_state.phases_completed.get("dependency_analysis") else "pending",
                "results": flow_state.results.get("dependency_analysis", {})
            },
            "database_integration": {
                "status": "completed" if flow_state.phases_completed.get("database_integration") else "pending",
                "results": flow_state.results.get("database_integration", {})
            }
        }
    
    async def get_flow_state_by_session(
        self,
        session_id: str,
        context: RequestContext
    ) -> Optional[Dict[str, Any]]:
        """Get flow state by session ID."""
        try:
            # Check active flows first
            if session_id in self._active_flows:
                flow = self._active_flows[session_id]
                return self._convert_to_legacy_format(flow.state)
            
            # Fall back to persistent state
            if self.state_service:
                state = await self.state_service.get_workflow_state(
                    session_id=session_id,
                    client_account_id=context.client_account_id,
                    engagement_id=context.engagement_id
                )
                return state.state_data if state else None
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get flow state for session {session_id}: {e}")
            return None
    
    def get_active_flows_summary(self) -> Dict[str, Any]:
        """Get summary of active flows for monitoring."""
        return {
            "total_active_flows": len(self._active_flows),
            "active_sessions": list(self._active_flows.keys()),
            "flows_by_status": {
                status: len([f for f in self._active_flows.values() if f.state.status == status])
                for status in ["running", "completed", "failed", "pending"]
            },
            "service_available": self.service_available,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get service health status."""
        return {
            "service_name": "CrewAI Flow Service",
            "status": "healthy" if self.service_available else "degraded",
            "crewai_flow_available": CREWAI_FLOW_AVAILABLE,
            "active_flows": len(self._active_flows),
            "features": {
                "native_flow_execution": CREWAI_FLOW_AVAILABLE,
                "fallback_execution": True,
                "state_persistence": self.state_service is not None,
                "background_processing": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }


def create_crewai_flow_service(db: AsyncSession) -> CrewAIFlowService:
    """Factory function to create CrewAI Flow Service."""
    return CrewAIFlowService(db) 