"""
Discovery Flow State Model
Enhanced state management for Discovery Flow with CrewAI best practices
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field

class DiscoveryFlowState(BaseModel):
    """Enhanced state for Discovery Flow with CrewAI best practices"""
    
    # Flow identification
    session_id: str = ""
    client_account_id: str = ""
    engagement_id: str = ""
    user_id: str = ""
    flow_fingerprint: str = ""
    
    # Planning and coordination
    overall_plan: Dict[str, Any] = {}
    crew_coordination: Dict[str, Any] = {}
    agent_assignments: Dict[str, List[str]] = {}
    
    # Memory references
    shared_memory_id: str = ""
    knowledge_base_refs: List[str] = []
    
    # Phase tracking with manager oversight
    current_phase: str = "initialization"
    phase_managers: Dict[str, str] = {}
    crew_status: Dict[str, Dict[str, Any]] = {}
    agent_collaboration_map: Dict[str, List[str]] = {}
    
    # Input data
    raw_data: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    data_source_type: str = "cmdb"
    
    # Data processing results with provenance
    field_mappings: Dict[str, Any] = {
        "mappings": {},
        "confidence_scores": {},
        "unmapped_fields": [],
        "validation_results": {},
        "agent_insights": {}
    }
    
    cleaned_data: List[Dict[str, Any]] = []
    data_quality_metrics: Dict[str, Any] = {}
    
    asset_inventory: Dict[str, List[Dict[str, Any]]] = {
        "servers": [],
        "applications": [],
        "devices": [],
        "classification_metadata": {}
    }
    
    app_server_dependencies: Dict[str, Any] = {
        "hosting_relationships": [],
        "resource_mappings": [],
        "topology_insights": {}
    }
    
    app_app_dependencies: Dict[str, Any] = {
        "communication_patterns": [],
        "api_dependencies": [],
        "integration_complexity": {}
    }
    
    technical_debt_assessment: Dict[str, Any] = {
        "debt_scores": {},
        "modernization_recommendations": [],
        "risk_assessments": {},
        "six_r_preparation": {}
    }
    
    # Final integration for Assessment Flow
    discovery_summary: Dict[str, Any] = {}
    assessment_flow_package: Dict[str, Any] = {}
    
    # Error tracking
    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    started_at: str = ""
    completed_at: str = "" 