"""
Unified Discovery Flow State Model
Single source of truth for Discovery Flow state following CrewAI Flow documentation patterns.
Consolidates all competing state model implementations into one unified model.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UUIDEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles UUID objects"""

    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_uuid_to_str(value: Any) -> str:
    """Safely convert UUID or string to string"""
    if isinstance(value, uuid.UUID):
        return str(value)
    elif isinstance(value, str):
        return value
    elif value is None:
        return ""
    else:
        return str(value)


class UnifiedDiscoveryFlowState(BaseModel):
    """
    Single source of truth for Discovery Flow state.
    Follows CrewAI Flow documentation patterns from:
    https://docs.crewai.com/guides/flows/mastering-flow-state

    Consolidates all previous implementations:
    - backend/app/services/crewai_flows/models/flow_state.py
    - backend/app/schemas/flow_schemas.py
    - backend/app/schemas/flow_schemas_new.py
    - Multiple frontend state interfaces
    """

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

    # Data validation results (from DataImportValidationAgent)
    data_validation_results: Dict[str, Any] = Field(default_factory=dict)

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
    # FLOW CONTROL AND STATUS
    # ========================================
    status: str = "running"  # running, completed, failed, paused, waiting_for_approval, waiting_for_user_approval
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
    shared_memory_reference: Optional[Any] = None
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
    final_result: str = ""  # Track final result of flow (e.g., "awaiting_user_approval_in_attribute_mapping")

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

    # ========================================
    # HELPER METHODS
    # ========================================

    def add_error(self, phase: str, error: str, details: Optional[Dict] = None):
        """Add error to the flow state with proper tracking"""
        error_entry = {
            "phase": phase,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
        }
        self.errors.append(error_entry)
        self.updated_at = datetime.utcnow().isoformat()

    def add_warning(self, message: str, phase: Optional[str] = None):
        """Add warning to the flow state"""
        warning_message = f"[{phase or self.current_phase}] {message}"
        self.warnings.append(warning_message)
        self.updated_at = datetime.utcnow().isoformat()

    def log_entry(
        self,
        message: str,
        phase: Optional[str] = None,
        extra_data: Optional[Dict] = None,
    ):
        """Add log entry to the workflow state"""
        self.workflow_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message,
                "phase": phase or self.current_phase,
                "extra_data": extra_data or {},
            }
        )
        self.updated_at = datetime.utcnow().isoformat()

    def mark_phase_complete(self, phase: str, results: Optional[Dict[str, Any]] = None):
        """Mark a phase as completed with results"""
        self.phase_completion[phase] = True
        if results:
            self.agent_results[phase] = results

        # Update success criteria
        if phase in self.success_criteria:
            self.success_criteria[phase]["validation_passed"] = True

        self.updated_at = datetime.utcnow().isoformat()
        self.log_entry(f"Phase {phase} completed successfully", phase)

    def update_progress(self):
        """Calculate and update overall progress based on phase completion"""
        completed_phases = sum(
            1 for completed in self.phase_completion.values() if completed
        )
        total_phases = len(self.phase_completion)

        if total_phases > 0:
            self.progress_percentage = (completed_phases / total_phases) * 100.0
        else:
            self.progress_percentage = 0.0

        self.updated_at = datetime.utcnow().isoformat()

    def validate_phase_success(self, phase: str) -> Dict[str, Any]:
        """Validate success criteria for a specific phase"""
        if phase not in self.success_criteria:
            return {
                "phase": phase,
                "success": False,
                "details": {},
                "recommendations": [f"Unknown phase: {phase}"],
            }

        criteria = self.success_criteria[phase]

        if phase == "field_mapping":
            mappings_count = len(self.field_mappings.get("mappings", {}))
            unmapped_count = len(self.field_mappings.get("unmapped_fields", []))
            total_fields = mappings_count + unmapped_count

            success = (
                mappings_count > 0
                and (unmapped_count / max(total_fields, 1))
                <= criteria.get("unmapped_fields_threshold", 0.1)
                and criteria.get("validation_passed", False)
            )

            return {
                "phase": phase,
                "success": success,
                "details": {
                    "mapped_fields": mappings_count,
                    "unmapped_fields": unmapped_count,
                    "mapping_percentage": (mappings_count / max(total_fields, 1)) * 100,
                },
            }

        elif phase == "data_cleansing":
            cleaned_count = len(self.cleaned_data)
            quality_score = self.data_quality_metrics.get("overall_score", 0)

            success = (
                cleaned_count > 0
                and quality_score >= criteria.get("data_quality_score", 0.85)
                and criteria.get("validation_passed", False)
            )

            return {
                "phase": phase,
                "success": success,
                "details": {
                    "cleaned_records": cleaned_count,
                    "quality_score": quality_score,
                },
            }

        elif phase == "asset_inventory":
            total_assets = self.asset_inventory.get("total_assets", 0)
            classification_complete = criteria.get(
                "asset_classification_complete", False
            )

            success = (
                total_assets > 0
                and classification_complete
                and criteria.get("cross_domain_validation", False)
            )

            return {
                "phase": phase,
                "success": success,
                "details": {
                    "total_assets": total_assets,
                    "classification_complete": classification_complete,
                },
            }

        elif phase == "dependency_analysis":
            app_server_deps = len(
                self.dependencies.get("app_server_dependencies", {}).get(
                    "hosting_relationships", []
                )
            )
            app_app_deps = len(
                self.dependencies.get("app_app_dependencies", {}).get(
                    "communication_patterns", []
                )
            )

            success = (
                (app_server_deps > 0 or app_app_deps > 0)
                and criteria.get("dependency_relationships_mapped", False)
                and criteria.get("topology_validated", False)
            )

            return {
                "phase": phase,
                "success": success,
                "details": {
                    "app_server_dependencies": app_server_deps,
                    "app_app_dependencies": app_app_deps,
                },
            }

        elif phase == "tech_debt_analysis":
            debt_scores = len(self.technical_debt.get("debt_scores", {}))
            recommendations = len(
                self.technical_debt.get("modernization_recommendations", [])
            )

            success = (
                debt_scores > 0
                and recommendations > 0
                and criteria.get("debt_assessment_complete", False)
                and criteria.get("six_r_recommendations_ready", False)
            )

            return {
                "phase": phase,
                "success": success,
                "details": {
                    "debt_assessments": debt_scores,
                    "modernization_recommendations": recommendations,
                },
            }

        # Default case
        return {
            "phase": phase,
            "success": criteria.get("validation_passed", False),
            "details": {},
        }

    def get_current_phase_status(self) -> Dict[str, Any]:
        """Get detailed status of the current phase"""
        return {
            "phase": self.current_phase,
            "progress": self.progress_percentage,
            "status": self.status,
            "crew_status": self.crew_status.get(self.current_phase, {}),
            "success_criteria": self.success_criteria.get(self.current_phase, {}),
            "validation": self.validate_phase_success(self.current_phase),
        }

    def is_ready_for_next_phase(self, next_phase: str) -> bool:
        """Check if flow is ready to proceed to the next phase"""
        # Define phase dependencies
        phase_dependencies = {
            "field_mapping": [],  # No dependencies
            "data_cleansing": ["field_mapping"],
            "asset_inventory": ["data_cleansing"],
            "dependency_analysis": ["asset_inventory"],
            "tech_debt_analysis": ["dependency_analysis"],
        }

        dependencies = phase_dependencies.get(next_phase, [])

        # Check if all dependency phases are completed successfully
        for dep_phase in dependencies:
            if not self.phase_completion.get(dep_phase, False):
                return False

            validation = self.validate_phase_success(dep_phase)
            if not validation.get("success", False):
                return False

        return True

    def finalize_flow(self) -> Dict[str, Any]:
        """Finalize the discovery flow and prepare summary"""
        if self.status != "completed":
            self.status = "completed"
            self.completed_at = datetime.utcnow().isoformat()

        # Generate comprehensive summary
        self.discovery_summary = {
            "flow_id": self.flow_id,
            "total_duration_seconds": self._calculate_duration(),
            "phases_completed": self.phase_completion,
            "total_assets_processed": self.asset_inventory.get("total_assets", 0),
            "total_dependencies_identified": (
                len(
                    self.dependencies.get("app_server_dependencies", {}).get(
                        "hosting_relationships", []
                    )
                )
                + len(
                    self.dependencies.get("app_app_dependencies", {}).get(
                        "communication_patterns", []
                    )
                )
            ),
            "data_quality_score": self.data_quality_metrics.get("overall_score", 0),
            "technical_debt_items": len(self.technical_debt.get("debt_scores", {})),
            "agent_insights_count": len(self.agent_insights),
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
        }

        # Prepare assessment flow package
        self.assessment_flow_package = {
            "assets": self.asset_inventory,
            "dependencies": self.dependencies,
            "technical_debt": self.technical_debt,
            "data_quality": self.data_quality_metrics,
            "field_mappings": self.field_mappings,
            "metadata": self.metadata,
            "discovery_summary": self.discovery_summary,
        }

        self.updated_at = datetime.utcnow().isoformat()

        return self.discovery_summary

    def _calculate_duration(self) -> float:
        """Calculate flow duration in seconds"""
        if not self.started_at:
            return 0.0

        start_time = datetime.fromisoformat(self.started_at.replace("Z", "+00:00"))
        end_time = datetime.utcnow()

        if self.completed_at:
            end_time = datetime.fromisoformat(self.completed_at.replace("Z", "+00:00"))

        return (end_time - start_time).total_seconds()

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to ensure UUID serialization safety"""
        data = super().model_dump(**kwargs)

        # Recursively convert any UUID objects to strings
        def convert_uuids(obj):
            if isinstance(obj, dict):
                return {k: convert_uuids(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_uuids(item) for item in obj]
            elif isinstance(obj, uuid.UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj

        return convert_uuids(data)

    def to_json_safe_dict(self) -> Dict[str, Any]:
        """Convert to JSON-safe dictionary with UUID handling"""
        return self.model_dump()

    def safe_json_dumps(self) -> str:
        """Safely serialize to JSON with UUID handling"""
        return json.dumps(self.model_dump(), cls=UUIDEncoder, default=str)

    def get_llm(self):
        """Get the LLM instance for CrewAI agents."""
        try:
            from app.services.llm_config import get_crewai_llm

            llm = get_crewai_llm()
            return llm
        except ImportError:
            # Return a mock LLM for fallback
            class MockLLM:
                def __init__(self):
                    self.model_name = "mock"

                def invoke(self, prompt):
                    return "Mock response"

            return MockLLM()
