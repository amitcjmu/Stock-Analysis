"""
State validation and utility functions for field mapping operations.

This module contains state validation, preparation, and utility functions
separated from the main FieldMappingExecutor to improve maintainability.
"""

import logging
from typing import Any, Dict

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState

from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class StateValidator:
    """Handles state validation for field mapping operations."""

    @staticmethod
    def validate_execution_state(state: UnifiedDiscoveryFlowState) -> None:
        """Validate that the state has required data for field mapping."""
        # Check for raw_data (sample data)
        if not state.raw_data:
            raise ValidationError("No sample data available for field mapping")

        # Check for detected_columns in metadata
        if not state.metadata.get("detected_columns"):
            raise ValidationError("No detected columns available for field mapping")

        logger.debug(f"State validation passed for flow {state.flow_id}")


class PhaseUtils:
    """Utility functions for phase management."""

    @staticmethod
    def determine_next_phase(
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
    ) -> str:
        """Determine the next phase based on execution results."""
        # Check if clarifications are needed
        if rules_results.get("clarifications"):
            return "clarification_needed"

        # Check if validation failed critically
        if validation_results.get("critical_errors"):
            return "validation_failed"

        # Check if transformation failed
        if not transformation_results.get("success", False):
            return "transformation_failed"

        # Otherwise proceed to next phase
        return "data_transformation"


class StorageUtils:
    """Utility functions for storage operations."""

    def __init__(
        self, storage_manager: Any, client_account_id: str, engagement_id: str
    ):
        """Initialize storage utilities."""
        self.storage_manager = storage_manager
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_engagement_requirements(self) -> Dict[str, Any]:
        """Get engagement-specific requirements for field mapping."""
        try:
            if not self.storage_manager:
                return {}

            # Get from storage manager
            requirements = await self.storage_manager.get_engagement_metadata(
                self.client_account_id, self.engagement_id
            )
            return requirements.get("field_mapping_requirements", {})
        except Exception as e:
            logger.warning(f"Could not retrieve engagement requirements: {str(e)}")
            return {}

    async def get_client_preferences(self) -> Dict[str, Any]:
        """Get client-specific preferences for field mapping."""
        try:
            if not self.storage_manager:
                return {}

            # Get from storage manager
            preferences = await self.storage_manager.get_client_preferences(
                self.client_account_id
            )
            return preferences.get("field_mapping_preferences", {})
        except Exception as e:
            logger.warning(f"Could not retrieve client preferences: {str(e)}")
            return {}
