"""
Core field definitions for Unified Discovery Flow State.
Contains identification, flow state management, and phase-specific data fields.
"""

import uuid
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class CoreFieldsMixin(BaseModel):
    """Mixin containing core fields for UnifiedDiscoveryFlowState"""

    # ========================================
    # CORE IDENTIFICATION (Required)
    # ========================================
    flow_id: str = ""  # Primary identifier from CrewAI Flow - NEVER generate our own
    client_account_id: str = ""
    engagement_id: str = ""
    user_id: str = ""
    master_flow_id: Optional[str] = None  # Links to master flow orchestrator record

    # ========================================
    # CREWAI FLOW STATE MANAGEMENT
    # ========================================
    current_phase: str = "initialization"
    phase_completion: Dict[str, bool] = Field(
        default_factory=lambda: {
            "data_import": False,
            "field_mapping": False,
            "data_cleansing": False,
            "asset_creation": False,
            "asset_inventory": False,
            "dependency_analysis": False,
            "tech_debt_analysis": False,
        }
    )
    crew_status: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Phase managers for hierarchical coordination
    phase_managers: Dict[str, str] = Field(
        default_factory=lambda: {
            "field_mapping": "CMDB Field Mapping Coordination Manager",
            "data_cleansing": "Data Quality Assurance Manager",
            "asset_inventory": "IT Asset Inventory Manager",
            "dependency_analysis": "Application Dependency Manager",
            "tech_debt_analysis": "Technical Debt Assessment Manager",
        }
    )

    # Agent collaboration mapping
    agent_collaboration_map: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "field_mapping": [
                "Schema Structure Expert",
                "Attribute Mapping Specialist",
                "Knowledge Management Coordinator",
            ],
            "data_cleansing": [
                "Data Validation Expert",
                "Data Standardization Specialist",
                "Quality Metrics Analyst",
            ],
            "asset_inventory": [
                "Server Classification Expert",
                "Application Discovery Expert",
                "Device Classification Expert",
            ],
            "dependency_analysis": [
                "Hosting Relationship Expert",
                "Integration Pattern Expert",
                "Migration Impact Analyst",
            ],
            "tech_debt_analysis": [
                "Legacy Technology Analyst",
                "Modernization Strategy Expert",
                "Risk Assessment Specialist",
            ],
        }
    )

    # ========================================
    # PHASE-SPECIFIC DATA
    # ========================================

    # Input data
    raw_data: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    data_source_type: str = "cmdb"

    # Phase execution data storage
    phase_data: Dict[str, Any] = Field(default_factory=dict)

    # Field mapping results
    field_mappings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "mappings": {},
            "confidence_scores": {},
            "unmapped_fields": [],
            "validation_results": {},
            "agent_insights": {},
        }
    )
    field_mapping_confidence: float = Field(
        default=0.0, description="Overall confidence score for field mappings (0-1)"
    )

    # Backward compatibility field for field mapping execution tracking
    # Note: This duplicates phase_completion["field_mapping"] but maintained for compatibility
    field_mapping_executed: bool = Field(
        default=False,
        description="Tracks if field mapping has been executed (backward compatibility)",
    )

    # Data validation results (from DataImportValidationAgent)
    data_validation_results: Dict[str, Any] = Field(default_factory=dict)

    # Validation results - used by phase handlers for storing validation outputs
    validation_results: Dict[str, Any] = Field(default_factory=dict)

    # Data cleansing results
    cleaned_data: List[Dict[str, Any]] = Field(default_factory=list)
    data_quality_metrics: Dict[str, Any] = Field(default_factory=dict)
    data_cleansing_results: Dict[str, Any] = Field(default_factory=dict)

    # Asset creation results
    asset_creation_results: Dict[str, Any] = Field(default_factory=dict)

    # Asset inventory results
    asset_inventory: Dict[str, Any] = Field(
        default_factory=lambda: {
            "servers": [],
            "applications": [],
            "devices": [],
            "classification_metadata": {},
            "total_assets": 0,
            "classification_confidence": {},
        }
    )

    # Dependency analysis results
    dependencies: Dict[str, Any] = Field(
        default_factory=lambda: {
            "app_server_dependencies": {
                "hosting_relationships": [],
                "resource_mappings": [],
                "topology_insights": {},
            },
            "app_app_dependencies": {
                "communication_patterns": [],
                "api_dependencies": [],
                "integration_complexity": {},
                "dependency_graph": {"nodes": [], "edges": []},
            },
        }
    )

    # Dependency analysis results (agent output)
    dependency_analysis: Dict[str, Any] = Field(default_factory=dict)

    # Technical debt analysis results
    technical_debt: Dict[str, Any] = Field(
        default_factory=lambda: {
            "debt_scores": {},
            "modernization_recommendations": [],
            "risk_assessments": {},
            "six_r_preparation": {},
        }
    )

    # Tech debt analysis results (agent output)
    tech_debt_analysis: Dict[str, Any] = Field(default_factory=dict)

    # ========================================
    # FIELD VALIDATORS FOR UUID HANDLING
    # ========================================

    @field_validator(
        "flow_id",
        "client_account_id",
        "engagement_id",
        "user_id",
        "master_flow_id",
        mode="before",
    )
    @classmethod
    def validate_uuid_fields(cls, value: Union[uuid.UUID, str, None]) -> str:
        """
        Convert UUID fields to strings during model instantiation.
        This ensures compatibility when instantiating from dictionaries containing UUID objects.
        """
        if value is None:
            return ""
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value) if value else ""
