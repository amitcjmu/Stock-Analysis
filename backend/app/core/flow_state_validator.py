"""
Validates flow state integrity and structure
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Base exception for validation operations"""

    pass


class FlowStateValidator:
    """
    Ensures flow state consistency and validity
    """

    REQUIRED_FIELDS = [
        "flow_id",
        "current_phase",
        "phase_completion",
        "client_account_id",
    ]

    VALID_PHASES = [
        "initialization",
        "data_import",
        "field_mapping",
        "data_cleansing",
        "asset_creation",
        "asset_inventory",
        "dependency_analysis",
        "tech_debt_analysis",
        "completed",
    ]

    VALID_STATUSES = [
        "running",
        "paused",
        "completed",
        "failed",
        "waiting_for_user",
        "waiting_for_approval",
        "waiting_for_user_approval",
    ]

    PHASE_DEPENDENCIES = {
        "initialization": [],
        "data_import": ["initialization"],
        "field_mapping": ["data_import"],
        "data_cleansing": ["field_mapping"],
        "asset_creation": ["data_cleansing"],
        "asset_inventory": ["asset_creation"],
        "dependency_analysis": ["asset_inventory"],
        "tech_debt_analysis": ["dependency_analysis"],
        "completed": ["tech_debt_analysis"],
    }

    @staticmethod
    def validate_state_structure(state: Dict[str, Any]) -> List[str]:
        """
        Validate state structure and return list of errors
        """
        errors = []

        # Check required fields
        for field in FlowStateValidator.REQUIRED_FIELDS:
            if field not in state:
                errors.append(f"Missing required field: {field}")

        # Validate flow_id
        if "flow_id" in state:
            flow_id = state["flow_id"]
            if not flow_id or not isinstance(flow_id, str):
                errors.append("flow_id must be a non-empty string")

        # Validate current_phase
        if "current_phase" in state:
            phase = state["current_phase"]
            if phase not in FlowStateValidator.VALID_PHASES:
                errors.append(
                    f"Invalid current_phase: {phase}. Must be one of {FlowStateValidator.VALID_PHASES}"
                )

        # Validate status
        if "status" in state:
            status = state["status"]
            if status not in FlowStateValidator.VALID_STATUSES:
                errors.append(
                    f"Invalid status: {status}. Must be one of {FlowStateValidator.VALID_STATUSES}"
                )

        # Validate progress_percentage
        if "progress_percentage" in state:
            progress = state["progress_percentage"]
            if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
                errors.append("progress_percentage must be a number between 0 and 100")

        # Validate phase completion consistency
        if "phases_completed" in state and "current_phase" in state:
            completed_phases = state["phases_completed"]
            current_phase = state["current_phase"]

            if isinstance(completed_phases, list) and current_phase in completed_phases:
                errors.append("Current phase is marked as completed")

        # Validate phase_completion structure
        if "phase_completion" in state:
            phase_completion = state["phase_completion"]
            if isinstance(phase_completion, dict):
                for phase, completed in phase_completion.items():
                    if phase not in FlowStateValidator.VALID_PHASES:
                        errors.append(f"Unknown phase in phase_completion: {phase}")
                    if not isinstance(completed, bool):
                        errors.append(f"phase_completion[{phase}] must be boolean")

        # Validate timestamps
        timestamp_fields = ["created_at", "updated_at", "started_at", "completed_at"]
        for field in timestamp_fields:
            if field in state and state[field]:
                try:
                    datetime.fromisoformat(state[field].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    errors.append(f"Invalid timestamp format for {field}")

        # Validate JSON serializable
        try:
            json.dumps(state, default=str)
        except TypeError as e:
            errors.append(f"State not JSON serializable: {e}")

        return errors

    @staticmethod
    def validate_phase_transition(
        current_state: Dict[str, Any], new_phase: str
    ) -> bool:
        """
        Validate if phase transition is allowed
        """
        if new_phase not in FlowStateValidator.VALID_PHASES:
            return False

        current_phase = current_state.get("current_phase")
        if not current_phase:
            return new_phase == "initialization"

        # Check if dependencies are met
        dependencies = FlowStateValidator.PHASE_DEPENDENCIES.get(new_phase, [])
        phase_completion = current_state.get("phase_completion", {})

        for dep_phase in dependencies:
            if not phase_completion.get(dep_phase, False):
                logger.warning(f"Phase transition blocked: {dep_phase} not completed")
                return False

        return True

    @staticmethod
    def validate_data_consistency(state: Dict[str, Any]) -> List[str]:
        """
        Validate data consistency across different state components
        """
        errors = []
        current_phase = state.get("current_phase")

        # Validate raw_data presence for early phases
        if current_phase in ["data_import", "field_mapping"] and not state.get(
            "raw_data"
        ):
            errors.append(f"raw_data required for phase {current_phase}")

        # Validate field_mappings for processing phases
        if current_phase in ["data_cleansing", "asset_creation"] and not state.get(
            "field_mappings"
        ):
            errors.append(f"field_mappings required for phase {current_phase}")

        # Validate cleaned_data for asset phases
        if current_phase in [
            "asset_inventory",
            "dependency_analysis",
        ] and not state.get("cleaned_data"):
            errors.append(f"cleaned_data required for phase {current_phase}")

        # Validate asset_inventory for dependency analysis
        if current_phase == "dependency_analysis" and not state.get("asset_inventory"):
            errors.append("asset_inventory required for dependency_analysis phase")

        # Check completion status consistency
        if state.get("status") == "completed":
            required_phases = [
                "data_import",
                "field_mapping",
                "data_cleansing",
                "asset_inventory",
            ]
            phase_completion = state.get("phase_completion", {})

            for phase in required_phases:
                if not phase_completion.get(phase, False):
                    errors.append(f"Flow marked completed but {phase} not completed")

        # Check progress consistency
        progress = state.get("progress_percentage", 0)
        if state.get("status") == "completed" and progress < 100:
            errors.append("Flow marked completed but progress < 100%")

        if state.get("status") == "failed" and progress == 100:
            errors.append("Flow marked failed but progress = 100%")

        return errors

    @staticmethod
    def validate_agent_data(state: Dict[str, Any]) -> List[str]:
        """
        Validate agent-specific data structures
        """
        errors = []

        # Validate agent_confidences
        if "agent_confidences" in state:
            confidences = state["agent_confidences"]
            if isinstance(confidences, dict):
                for agent, confidence in confidences.items():
                    if (
                        not isinstance(confidence, (int, float))
                        or confidence < 0
                        or confidence > 1
                    ):
                        errors.append(
                            f"Invalid confidence for {agent}: must be between 0 and 1"
                        )

        # Validate agent_insights structure
        if "agent_insights" in state:
            insights = state["agent_insights"]
            if isinstance(insights, list):
                for i, insight in enumerate(insights):
                    if not isinstance(insight, dict):
                        errors.append(f"agent_insights[{i}] must be a dictionary")
                    elif "agent_id" not in insight:
                        errors.append(f"agent_insights[{i}] missing agent_id")

        # Validate user_clarifications structure
        if "user_clarifications" in state:
            clarifications = state["user_clarifications"]
            if isinstance(clarifications, list):
                for i, clarification in enumerate(clarifications):
                    if not isinstance(clarification, dict):
                        errors.append(f"user_clarifications[{i}] must be a dictionary")

        return errors

    @staticmethod
    def validate_enterprise_data(state: Dict[str, Any]) -> List[str]:
        """
        Validate enterprise-specific data structures
        """
        errors = []

        # Validate UUID format for enterprise fields
        uuid_fields = ["client_account_id", "engagement_id", "user_id"]
        for field in uuid_fields:
            if field in state and state[field]:
                value = state[field]
                if isinstance(value, str) and value not in ["", "system", "anonymous"]:
                    try:
                        import uuid

                        uuid.UUID(value)
                    except ValueError:
                        errors.append(f"Invalid UUID format for {field}: {value}")

        # Validate learning_scope
        if "learning_scope" in state:
            scope = state["learning_scope"]
            valid_scopes = ["engagement", "client", "global", "disabled"]
            if scope not in valid_scopes:
                errors.append(
                    f"Invalid learning_scope: {scope}. Must be one of {valid_scopes}"
                )

        # Validate memory_isolation_level
        if "memory_isolation_level" in state:
            level = state["memory_isolation_level"]
            valid_levels = ["strict", "moderate", "open"]
            if level not in valid_levels:
                errors.append(
                    f"Invalid memory_isolation_level: {level}. Must be one of {valid_levels}"
                )

        return errors

    @classmethod
    def validate_complete_state(cls, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform complete validation of state and return comprehensive results
        """
        start_time = datetime.utcnow()

        # Collect all validation errors
        structure_errors = cls.validate_state_structure(state)
        consistency_errors = cls.validate_data_consistency(state)
        agent_errors = cls.validate_agent_data(state)
        enterprise_errors = cls.validate_enterprise_data(state)

        all_errors = (
            structure_errors + consistency_errors + agent_errors + enterprise_errors
        )

        # Generate warnings for non-critical issues
        warnings = []

        # Check for deprecated fields
        # session_id deprecated warning removed - session_id fully eliminated

        # Check for empty optional collections
        optional_collections = [
            "agent_insights",
            "user_clarifications",
            "errors",
            "warnings",
        ]
        for field in optional_collections:
            if (
                field in state
                and isinstance(state[field], list)
                and len(state[field]) == 0
            ):
                warnings.append(f"Empty {field} collection")

        # Performance warnings
        if "workflow_log" in state and isinstance(state["workflow_log"], list):
            if len(state["workflow_log"]) > 1000:
                warnings.append("workflow_log is very large (>1000 entries)")

        validation_time = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "valid": len(all_errors) == 0,
            "errors": all_errors,
            "warnings": warnings,
            "validation_time_seconds": validation_time,
            "validated_at": start_time.isoformat(),
            "state_summary": {
                "flow_id": state.get("flow_id"),
                "current_phase": state.get("current_phase"),
                "status": state.get("status"),
                "progress_percentage": state.get("progress_percentage"),
                "errors_count": len(state.get("errors", [])),
                "warnings_count": len(state.get("warnings", [])),
            },
        }

        if not result["valid"]:
            logger.warning(
                f"State validation failed for flow {state.get('flow_id')}: {len(all_errors)} errors"
            )
        else:
            logger.info(f"State validation passed for flow {state.get('flow_id')}")

        return result


# Utility functions for common validation scenarios


def validate_state_for_phase_transition(
    state: Dict[str, Any], target_phase: str
) -> bool:
    """Quick validation for phase transitions"""
    validator = FlowStateValidator()

    # Basic structure validation
    structure_errors = validator.validate_state_structure(state)
    if structure_errors:
        return False

    # Phase transition validation
    return validator.validate_phase_transition(state, target_phase)


def validate_minimal_state(state: Dict[str, Any]) -> bool:
    """Minimal validation for performance-critical paths"""
    required_fields = ["flow_id", "current_phase", "status"]

    for field in required_fields:
        if field not in state or not state[field]:
            return False

    return state["current_phase"] in FlowStateValidator.VALID_PHASES


def get_validation_summary(state: Dict[str, Any]) -> str:
    """Get a human-readable validation summary"""
    validator = FlowStateValidator()
    result = validator.validate_complete_state(state)

    if result["valid"]:
        return f"✅ State valid - Flow {state.get('flow_id')} in {state.get('current_phase')} phase"
    else:
        error_count = len(result["errors"])
        warning_count = len(result["warnings"])
        return f"❌ State invalid - {error_count} errors, {warning_count} warnings"
