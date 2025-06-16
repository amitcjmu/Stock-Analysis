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
    shared_memory_reference: Any = None  # Direct reference to shared memory instance
    knowledge_base_refs: List[str] = []
    
    # Enhanced Phase tracking with manager oversight
    current_phase: str = "initialization"
    phase_managers: Dict[str, str] = Field(default_factory=lambda: {
        "field_mapping": "Field Mapping Manager",
        "data_cleansing": "Data Quality Manager",
        "inventory_building": "Inventory Manager", 
        "app_server_dependencies": "Dependency Manager",
        "app_app_dependencies": "Integration Manager",
        "technical_debt": "Technical Debt Manager"
    })
    crew_status: Dict[str, Dict[str, Any]] = {}
    agent_collaboration_map: Dict[str, List[str]] = Field(default_factory=lambda: {
        "field_mapping": ["Schema Analysis Expert", "Attribute Mapping Specialist"],
        "data_cleansing": ["Data Validation Expert", "Data Standardization Specialist"],
        "inventory_building": ["Server Classification Expert", "Application Discovery Expert", "Device Classification Expert"],
        "app_server_dependencies": ["Hosting Relationship Expert", "Migration Impact Analyst"],
        "app_app_dependencies": ["Integration Pattern Expert", "Business Flow Analyst"],
        "technical_debt": ["Legacy Systems Analyst", "Modernization Expert", "Risk Assessment Specialist"]
    })
    
    # Success criteria tracking for enhanced validation
    success_criteria: Dict[str, Dict[str, Any]] = Field(default_factory=lambda: {
        "field_mapping": {"field_mappings_confidence": 0.8, "unmapped_fields_threshold": 0.1, "validation_passed": True},
        "data_cleansing": {"data_quality_score": 0.85, "standardization_complete": True, "validation_passed": True},
        "inventory_building": {"asset_classification_complete": True, "cross_domain_validation": True, "classification_confidence": 0.9},
        "app_server_dependencies": {"hosting_relationships_mapped": True, "topology_validated": True, "dependency_confidence": 0.8},
        "app_app_dependencies": {"communication_patterns_mapped": True, "api_dependencies_identified": True, "integration_analysis_complete": True},
        "technical_debt": {"debt_assessment_complete": True, "six_r_recommendations_ready": True, "risk_analysis_complete": True}
    })
    
    # Phase completion tracking for flow control
    phase_completion: Dict[str, bool] = Field(default_factory=lambda: {
        "field_mapping": False, "data_cleansing": False, "inventory_building": False,
        "app_server_dependencies": False, "app_app_dependencies": False, "technical_debt": False
    })
    
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