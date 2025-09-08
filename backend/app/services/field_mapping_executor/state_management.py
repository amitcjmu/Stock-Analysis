"""
Field Mapping Executor - State Management Module

This module handles state validation and management operations
for field mapping execution.
"""

import logging
from typing import Any, Dict

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class StateManager:
    """Handles state validation and management for field mapping execution."""

    def __init__(
        self, client_account_id: str = "unknown", engagement_id: str = "unknown"
    ):
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    def validate_execution_state(self, state: UnifiedDiscoveryFlowState) -> None:
        """Validate that the state has required data for field mapping."""
        # Check for raw_data (sample data)
        if not state.raw_data:
            raise ValidationError("No sample data available for field mapping")

        # Check for detected_columns in metadata
        if not state.metadata.get("detected_columns"):
            raise ValidationError("No detected columns available for field mapping")

        logger.debug(f"State validation passed for flow {state.flow_id}")

    def determine_next_phase(
        self,
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
    ) -> str:
        """
        Determine the next phase based on execution results.

        Args:
            validation_results: Results from mapping validation
            rules_results: Results from business rules application
            transformation_results: Results from transformation and persistence

        Returns:
            Next phase name as string
        """
        try:
            # Check if there are critical validation errors
            if not validation_results.get("valid", True):
                critical_errors = validation_results.get("critical_errors", [])
                if critical_errors:
                    logger.warning(
                        f"Critical validation errors found: {critical_errors}"
                    )
                    return "field_mapping"  # Stay in current phase for correction

            # Check if clarifications are needed
            clarifications_needed = rules_results.get("clarifications_needed", [])
            if clarifications_needed:
                logger.info(
                    f"Clarifications needed: {len(clarifications_needed)} items"
                )
                return "questionnaire"  # Move to questionnaire for clarifications

            # Check transformation success
            if not transformation_results.get("success", False):
                logger.warning("Transformation failed, staying in field mapping phase")
                return "field_mapping"

            # All checks passed, proceed to next phase
            logger.info(
                "Field mapping completed successfully, proceeding to data cleansing"
            )
            return "data_cleansing"

        except Exception as e:
            logger.error(f"Error determining next phase: {str(e)}")
            # Default to staying in current phase if error occurs
            return "field_mapping"

    async def get_engagement_requirements(self) -> Dict[str, Any]:
        """Get engagement-specific requirements for field mapping."""
        # This is a placeholder implementation
        # In a real implementation, this would fetch from database or configuration
        return {
            "required_fields": ["hostname", "ip", "os", "environment"],
            "optional_fields": ["owner", "application", "cpu", "memory", "storage"],
            "validation_rules": {
                "hostname": {"required": True, "pattern": r"^[a-zA-Z0-9\-\.]+$"},
                "ip": {"required": True, "pattern": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"},
                "environment": {
                    "required": True,
                    "values": ["Production", "Staging", "Development"],
                },
            },
        }

    async def get_client_preferences(self) -> Dict[str, Any]:
        """Get client-specific preferences for field mapping."""
        # This is a placeholder implementation
        # In a real implementation, this would fetch from client configuration
        return {
            "mapping_strategy": "conservative",  # conservative, aggressive, balanced
            "confidence_threshold": 0.8,
            "auto_approve_threshold": 0.95,
            "field_naming_convention": "snake_case",
            "custom_field_mappings": {},
            "preferred_data_sources": [
                "hostname",
                "ip_address",
                "operating_system",
                "environment_type",
            ],
        }
