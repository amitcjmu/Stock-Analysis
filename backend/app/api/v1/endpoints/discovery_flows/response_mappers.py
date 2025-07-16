"""
Flow Response Mappers

This module provides standardized response formatting and data transformation
for discovery flow API endpoints.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DiscoveryFlowResponse(BaseModel):
    """Standardized discovery flow response model"""
    flow_id: str
    data_import_id: Optional[str] = None
    status: str
    type: str = "discovery"
    current_phase: Optional[str] = None
    next_phase: Optional[str] = None
    phases_completed: List[str] = Field(default_factory=list)
    progress: float = 0.0
    progress_percentage: float = 0.0
    client_account_id: str
    engagement_id: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    flow_name: Optional[str] = None
    flow_description: Optional[str] = None
    can_resume: bool = False


class DiscoveryFlowStatusResponse(BaseModel):
    """Detailed discovery flow status response"""
    flow_id: str
    data_import_id: Optional[str] = None
    status: str
    type: str = "discovery"
    client_account_id: str
    engagement_id: str
    current_phase: Optional[str] = None
    progress_percentage: float = 0.0
    awaiting_user_approval: bool = False
    progress: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    crewai_status: str
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    phase_completion: Dict[str, bool] = Field(default_factory=dict)
    field_mappings: Dict[str, Any] = Field(default_factory=dict)
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    import_metadata: Dict[str, Any] = Field(default_factory=dict)
    last_updated: str


class FlowInitializeResponse(BaseModel):
    """Flow initialization response"""
    flow_id: str
    status: str
    type: str = "discovery"
    client_account_id: str
    engagement_id: str
    message: str
    next_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FlowOperationResponse(BaseModel):
    """Generic flow operation response"""
    success: bool
    flow_id: str
    status: str
    message: str
    next_phase: Optional[str] = None
    current_phase: Optional[str] = None
    method: Optional[str] = None


class ResponseMappers:
    """Utility class for response data transformation and standardization"""
    
    @staticmethod
    def map_flow_to_response(flow, context=None) -> Dict[str, Any]:
        """Convert a DiscoveryFlow model to standardized response format"""
        try:
            # Get current phase from flow state
            current_phase = flow.current_phase
            if not current_phase and flow.crewai_state_data:
                current_phase = flow.crewai_state_data.get("current_phase", "field_mapping")
            
            # Build phase completion list
            phases_completed = []
            if flow.data_import_completed:
                phases_completed.append("data_import")
            if flow.field_mapping_completed:
                phases_completed.append("field_mapping")
            if flow.data_cleansing_completed:
                phases_completed.append("data_cleansing")
            if flow.asset_inventory_completed:
                phases_completed.append("asset_inventory")
            if flow.dependency_analysis_completed:
                phases_completed.append("dependency_analysis")
            if flow.tech_debt_assessment_completed:
                phases_completed.append("tech_debt_assessment")
            
            return {
                "flow_id": str(flow.flow_id),
                "data_import_id": str(flow.data_import_id) if flow.data_import_id else str(flow.flow_id),
                "status": flow.status,
                "type": "discovery",
                "current_phase": current_phase or "field_mapping",
                "next_phase": None,  # Could be calculated based on phase completion
                "phases_completed": phases_completed,
                "progress": flow.progress_percentage or 0,
                "progress_percentage": flow.progress_percentage or 0,
                "client_account_id": str(flow.client_account_id),
                "engagement_id": str(flow.engagement_id),
                "created_at": flow.created_at.isoformat() if flow.created_at else "",
                "updated_at": flow.updated_at.isoformat() if flow.updated_at else "",
                "metadata": flow.flow_state or {},
                "error": None,
                "flow_name": flow.flow_name,
                "flow_description": flow.description if hasattr(flow, 'description') else None,
                "can_resume": flow.status in ['initialized', 'paused', 'waiting_for_approval']
            }
        except Exception as e:
            logger.error(f"Error mapping flow to response: {e}")
            return {
                "flow_id": str(flow.flow_id) if hasattr(flow, 'flow_id') else "unknown",
                "status": "error",
                "type": "discovery",
                "error": str(e),
                "metadata": {}
            }
    
    @staticmethod
    async def map_flow_to_status_response(flow, extensions=None, context=None, db=None) -> Dict[str, Any]:
        """Convert a DiscoveryFlow model to detailed status response format"""
        try:
            # Calculate current phase from completion flags
            current_phase = "unknown"
            steps_completed = 0
            
            if not flow.data_import_completed:
                current_phase = "data_import"
            elif not flow.field_mapping_completed:
                current_phase = "field_mapping"
                steps_completed = 1
            elif not flow.data_cleansing_completed:
                current_phase = "data_cleansing"
                steps_completed = 2
            elif not flow.asset_inventory_completed:
                current_phase = "asset_inventory"
                steps_completed = 3
            elif not flow.dependency_analysis_completed:
                current_phase = "dependency_analysis"
                steps_completed = 4
            elif not flow.tech_debt_assessment_completed:
                current_phase = "tech_debt_assessment"
                steps_completed = 5
            else:
                current_phase = "completed"
                steps_completed = 6
            
            # Extract agent insights from discovery_flows table first
            agent_insights = []
            if flow.crewai_state_data and "agent_insights" in flow.crewai_state_data:
                agent_insights = flow.crewai_state_data["agent_insights"]
            
            # Get awaiting_user_approval from discovery_flows table JSONB
            awaiting_approval = False
            if flow.crewai_state_data:
                awaiting_approval = flow.crewai_state_data.get("awaiting_user_approval", False)
            
            actual_status = flow.status
            actual_progress = flow.progress_percentage
            actual_current_phase = flow.current_phase or current_phase
            
            if extensions and extensions.flow_persistence_data:
                # Get additional state from master table if available
                persistence_data = extensions.flow_persistence_data
                
                # Only use master table insights if not found in child table
                if not agent_insights and "agent_insights" in persistence_data:
                    agent_insights = persistence_data.get("agent_insights", [])
                
                # Update phase completion from persistence data
                if "phase_completion" in persistence_data:
                    phase_completion = persistence_data["phase_completion"]
                    steps_completed = len([p for p in phase_completion.values() if p])
            
            # Use actual values from persistence data if available
            final_status = actual_status
            
            # Preserve special statuses like waiting_for_approval
            if final_status == "active" and not awaiting_approval:
                final_status = "processing"
            
            # Build phase completion from discovery_flows table
            phase_completion = {
                "data_import": flow.data_import_completed,
                "field_mapping": flow.field_mapping_completed,
                "data_cleansing": flow.data_cleansing_completed,
                "asset_inventory": flow.asset_inventory_completed,
                "dependency_analysis": flow.dependency_analysis_completed,
                "tech_debt_assessment": flow.tech_debt_assessment_completed
            }
            
            # Calculate actual progress based on completed phases
            completed_phases = sum(1 for v in phase_completion.values() if v)
            total_phases = 6
            
            # If we're in field mapping phase and have data imported, ensure minimum progress
            if flow.data_import_completed and actual_current_phase in ["field_mapping", "attribute_mapping"]:
                # At least 1 phase complete (data import) + partial progress for field mapping
                min_progress = (1.0 / total_phases) * 100  # 16.7% for data import
                if not flow.field_mapping_completed:
                    min_progress += (0.5 / total_phases) * 100  # Add 8.3% for in-progress field mapping
                actual_progress = max(actual_progress, min_progress)
            elif completed_phases > 0:
                # Calculate progress based on completed phases
                calculated_progress = (completed_phases / total_phases) * 100
                actual_progress = max(actual_progress, calculated_progress)
            
            # Override with persistence data if available
            if extensions and extensions.flow_persistence_data and "phase_completion" in extensions.flow_persistence_data:
                phase_completion.update(extensions.flow_persistence_data["phase_completion"])
            
            # Extract field mappings from CrewAI state extensions
            field_mappings = {}
            if extensions and extensions.flow_persistence_data:
                field_mappings = extensions.flow_persistence_data.get("field_mappings", {})
            
            # Also check discovery_flows table JSONB for field mappings
            if not field_mappings and flow.crewai_state_data:
                field_mappings = flow.crewai_state_data.get("field_mappings", {})
            
            # Fetch actual import data if we have a data_import_id and db session
            raw_data = []
            import_metadata = {}
            actual_field_mappings = field_mappings
            
            if flow.data_import_id and db:
                try:
                    # Import the service and get import data
                    from app.services.data_import import ImportStorageHandler
                    import_handler = ImportStorageHandler(db, context.client_account_id if context else "system")
                    
                    # Get the import data
                    import_data = await import_handler.get_import_data(str(flow.data_import_id))
                    
                    if import_data and import_data.get("success"):
                        raw_data = import_data.get("data", [])
                        import_metadata = import_data.get("import_metadata", {})
                        logger.info(f"✅ Retrieved {len(raw_data)} import records for flow {flow.flow_id}")
                    
                    # Also get field mappings from the data import system
                    from sqlalchemy import select
                    from app.models.data_import.mapping import ImportFieldMapping
                    
                    mapping_stmt = select(ImportFieldMapping).where(
                        ImportFieldMapping.data_import_id == flow.data_import_id
                    )
                    mapping_result = await db.execute(mapping_stmt)
                    mappings = mapping_result.scalars().all()
                    
                    if mappings:
                        # Convert database field mappings to dict format
                        db_field_mappings = {}
                        for mapping in mappings:
                            db_field_mappings[mapping.source_field] = {
                                "target_field": mapping.target_field,
                                "confidence": mapping.confidence,
                                "is_approved": mapping.is_approved,
                                "is_critical": getattr(mapping, 'is_critical', False)
                            }
                        
                        # Use database field mappings if we have them and they're more complete
                        if db_field_mappings and (not actual_field_mappings or len(db_field_mappings) > len(actual_field_mappings)):
                            actual_field_mappings = db_field_mappings
                            logger.info(f"✅ Retrieved {len(db_field_mappings)} field mappings from database for flow {flow.flow_id}")
                    
                except Exception as import_error:
                    logger.warning(f"Failed to retrieve import data for flow {flow.flow_id}: {import_error}")
                    # Continue with empty data rather than failing completely
            
            return {
                "flow_id": str(flow.flow_id),
                "data_import_id": str(flow.data_import_id) if flow.data_import_id else str(flow.flow_id),
                "status": final_status,
                "type": "discovery",
                "current_phase": actual_current_phase,
                "progress_percentage": actual_progress,
                "awaiting_user_approval": awaiting_approval,
                "client_account_id": str(flow.client_account_id),
                "engagement_id": str(flow.engagement_id),
                "progress": {
                    "current_phase": actual_current_phase,
                    "completion_percentage": actual_progress,
                    "steps_completed": steps_completed,
                    "total_steps": 6
                },
                "metadata": {},
                "crewai_status": final_status,
                "agent_insights": agent_insights,
                "phase_completion": phase_completion,
                "field_mappings": actual_field_mappings,
                "raw_data": raw_data,
                "import_metadata": import_metadata,
                "last_updated": flow.updated_at.isoformat() if flow.updated_at else ""
            }
        except Exception as e:
            logger.error(f"Error mapping flow to status response: {e}")
            return {
                "flow_id": str(flow.flow_id) if hasattr(flow, 'flow_id') else "unknown",
                "status": "error",
                "type": "discovery",
                "error": str(e),
                "metadata": {},
                "field_mappings": {},
                "raw_data": [],
                "import_metadata": {}
            }
    
    @staticmethod
    def map_state_dict_to_status_response(flow_id: str, state_dict: Dict[str, Any], context=None) -> Dict[str, Any]:
        """Convert flow state dict to status response format"""
        try:
            progress_percentage = float(state_dict.get("progress_percentage", 0))
            current_phase = state_dict.get("current_phase", "unknown")
            status = state_dict.get("status", "running")
            
            # Preserve special statuses, only override if generic
            if progress_percentage >= 100 and status not in ["paused", "waiting_for_approval", "waiting_for_user_approval"]:
                status = "completed"
            elif status in ["running", "active", "initialized"] and status not in ["paused", "waiting_for_approval", "waiting_for_user_approval"]:
                status = "processing"
            
            # Use context values for client_account_id and engagement_id since state_dict is just the persistence data
            return {
                "flow_id": flow_id,
                "data_import_id": flow_id,  # Use flow_id as data_import_id for compatibility
                "status": status,
                "type": "discovery",
                "client_account_id": str(context.client_account_id) if context else "",
                "engagement_id": str(context.engagement_id) if context else "",
                "current_phase": current_phase,
                "progress_percentage": progress_percentage,
                "progress": {
                    "current_phase": current_phase,
                    "completion_percentage": progress_percentage,
                    "steps_completed": len([p for p in state_dict.get("phase_completion", {}).values() if p]),
                    "total_steps": 6
                },
                "metadata": state_dict.get("metadata", {}),
                "crewai_status": "active" if status == "processing" else status,
                "agent_insights": state_dict.get("agent_insights", []),
                "phase_completion": state_dict.get("phase_completion", {}),
                "field_mappings": state_dict.get("field_mappings", {}),
                "raw_data": state_dict.get("raw_data", []),
                "import_metadata": state_dict.get("import_metadata", {}),
                "awaiting_user_approval": state_dict.get("awaiting_user_approval", False),
                "last_updated": state_dict.get("updated_at", "")
            }
        except Exception as e:
            logger.error(f"Error mapping state dict to status response: {e}")
            return {
                "flow_id": flow_id,
                "status": "error",
                "type": "discovery",
                "error": str(e),
                "metadata": {}
            }
    
    @staticmethod
    def map_orchestrator_result_to_status_response(flow_id: str, result: Dict[str, Any], context=None) -> Dict[str, Any]:
        """Convert orchestrator result to status response format"""
        try:
            progress_percentage = float(result.get("progress_percentage", 0))
            return {
                "flow_id": flow_id,
                "data_import_id": flow_id,
                "status": result.get("status", "unknown"),
                "type": "discovery",
                "client_account_id": str(result.get("client_account_id", context.client_account_id if context else "")),
                "engagement_id": str(result.get("engagement_id", context.engagement_id if context else "")),
                "progress": {
                    "current_phase": result.get("current_phase", "unknown"),
                    "completion_percentage": progress_percentage,
                    "steps_completed": int(progress_percentage / 20),  # 5 phases = 20% each
                    "total_steps": 5
                },
                "metadata": result.get("metadata", {}),
                "crewai_status": result.get("crewai_status", "unknown"),
                "agent_insights": result.get("agent_insights", [])
            }
        except Exception as e:
            logger.error(f"Error mapping orchestrator result to status response: {e}")
            return {
                "flow_id": flow_id,
                "status": "error",
                "type": "discovery",
                "error": str(e),
                "metadata": {}
            }
    
    @staticmethod
    def create_error_response(flow_id: str, error: str, status_code: int = 500) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "flow_id": flow_id,
            "status": "error",
            "type": "discovery",
            "error": error,
            "error_code": status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {}
        }
    
    @staticmethod
    def create_success_response(flow_id: str, message: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized success response"""
        response = {
            "success": True,
            "flow_id": flow_id,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        if data:
            response.update(data)
        return response