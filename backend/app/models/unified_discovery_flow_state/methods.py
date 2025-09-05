"""
Method implementations for Unified Discovery Flow State.
Contains all helper methods, validation logic, and flow control methods.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .utils import UUIDEncoder


class FlowStateMethods:
    """Mixin containing all methods for UnifiedDiscoveryFlowState"""

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

    @property
    def completed_phases(self) -> List[str]:
        """
        Get list of completed phase names.
        This property provides backward compatibility for code that expects a 'completed_phases' attribute.
        """
        return [
            phase for phase, completed in self.phase_completion.items() if completed
        ]

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
