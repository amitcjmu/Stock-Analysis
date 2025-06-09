"""
Pydantic schemas for Agentic Flow State Management.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime

class DiscoveryFlowState(BaseModel):
    """Represents the state of a single discovery workflow run."""
    session_id: str
    client_account_id: str
    engagement_id: str
    user_id: str
    import_session_id: str
    current_phase: str = "initialization"
    workflow_phases: List[str] = Field(default_factory=lambda: [
        "initialization", "data_source_analysis", "data_validation", "field_mapping", 
        "asset_classification", "dependency_analysis", "database_integration", "completion"
    ])
    phase_progress: Dict[str, float] = Field(default_factory=dict)
    # Flags to track completion of each phase
    data_source_analysis_complete: bool = False
    data_validation_complete: bool = False
    field_mapping_complete: bool = False
    asset_classification_complete: bool = False
    dependency_analysis_complete: bool = False
    database_integration_complete: bool = False
    completion_complete: bool = False
    # Data artifacts from the workflow
    validated_structure: Dict[str, Any] = {}
    processed_data: Dict[str, Any] = {}
    suggested_field_mappings: Dict[str, str] = {}
    asset_classifications: List[Dict[str, Any]] = []
    agent_insights: Dict[str, Any] = {}

    # New fields for logging and status
    status_message: Optional[str] = None
    workflow_log: List[Dict[str, Any]] = Field(default_factory=list)

    def log_entry(self, message: str, phase: str = None, extra_data: Dict = None):
        """Adds a log entry to the workflow state."""
        self.workflow_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            "phase": phase or self.current_phase,
            "extra_data": extra_data or {}
        }) 