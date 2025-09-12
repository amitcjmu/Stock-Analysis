"""
Control and management fields for Unified Discovery Flow State.
Contains flow control, status, integration, and enterprise features.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ControlFieldsMixin(BaseModel):
    """Mixin containing control and management fields for UnifiedDiscoveryFlowState"""

    # ========================================
    # FLOW CONTROL AND STATUS
    # ========================================
    status: str = (
        "running"  # running, completed, failed, paused, waiting_for_approval, waiting_for_user_approval
    )
    progress_percentage: float = 0.0
    estimated_remaining_time: str = "Calculating..."

    # Processing statistics
    records_processed: int = 0
    records_total: int = 0
    records_valid: int = 0
    records_failed: int = 0
    total_insights: int = 0
    total_clarifications: int = 0

    # User approval and interaction
    awaiting_user_approval: bool = False
    user_approval_received: bool = False
    user_approval_data: Dict[str, Any] = Field(default_factory=dict)

    # Success criteria tracking for validation
    success_criteria: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "field_mapping": {
                "field_mappings_confidence": 0.8,
                "unmapped_fields_threshold": 0.1,
                "validation_passed": False,
            },
            "data_cleansing": {
                "data_quality_score": 0.85,
                "standardization_complete": False,
                "validation_passed": False,
            },
            "asset_inventory": {
                "asset_classification_complete": False,
                "cross_domain_validation": False,
                "classification_confidence": 0.9,
            },
            "dependency_analysis": {
                "dependency_relationships_mapped": False,
                "topology_validated": False,
                "dependency_confidence": 0.8,
            },
            "tech_debt_analysis": {
                "debt_assessment_complete": False,
                "six_r_recommendations_ready": False,
                "risk_analysis_complete": False,
            },
        }
    )

    # ========================================
    # CREWAI INTEGRATION
    # ========================================

    # Memory and knowledge management
    shared_memory_id: str = ""
    shared_memory_reference: Any = None
    knowledge_base_refs: List[str] = Field(default_factory=list)

    # Planning and coordination
    overall_plan: Dict[str, Any] = Field(default_factory=dict)
    crew_coordination: Dict[str, Any] = Field(default_factory=dict)
    agent_assignments: Dict[str, List[str]] = Field(default_factory=dict)

    # Agent performance and collaboration
    agent_performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    collaboration_activities: List[Dict[str, Any]] = Field(default_factory=list)
    memory_analytics: Dict[str, Any] = Field(default_factory=dict)
    knowledge_base_status: Dict[str, Any] = Field(default_factory=dict)

    # ========================================
    # ERROR HANDLING AND LOGGING
    # ========================================
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    workflow_log: List[Dict[str, Any]] = Field(default_factory=list)

    # Agent insights and clarifications
    agent_insights: List[Dict[str, Any]] = Field(default_factory=list)
    clarification_questions: List[Dict[str, Any]] = Field(default_factory=list)
    agent_results: Dict[str, Any] = Field(default_factory=dict)

    # Agent confidence tracking and coordination
    agent_confidences: Dict[str, float] = Field(default_factory=dict)
    user_clarifications: List[Dict[str, Any]] = Field(default_factory=list)
    crew_escalations: List[Dict[str, Any]] = Field(default_factory=list)

    # ========================================
    # TIMESTAMPS
    # ========================================
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time_seconds: float = 0.0

    # Pause/Resume related timestamps
    paused_at: Optional[str] = None
    resumed_at: Optional[str] = None
    pause_reason: Optional[str] = None

    # ========================================
    # DATABASE INTEGRATION
    # ========================================
    database_assets_created: List[str] = Field(default_factory=list)
    database_integration_status: str = (
        "pending"  # pending, in_progress, completed, failed
    )

    # Final integration results
    discovery_summary: Dict[str, Any] = Field(default_factory=dict)
    assessment_flow_package: Dict[str, Any] = Field(default_factory=dict)
    final_result: str = (
        ""  # Track final result of flow (e.g., "awaiting_user_approval_in_attribute_mapping")
    )

    # ========================================
    # ENTERPRISE FEATURES
    # ========================================

    # Learning and privacy controls
    learning_scope: str = "engagement"  # engagement, client, global, disabled
    cross_client_learning_enabled: bool = False
    learning_data_sharing_consent: bool = False
    learning_audit_trail: List[Dict[str, Any]] = Field(default_factory=list)
    memory_isolation_level: str = "strict"  # strict, moderate, open
    data_residency_requirements: Dict[str, Any] = Field(default_factory=dict)
