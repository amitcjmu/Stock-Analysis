"""
Field Mapping Executor - Business Logic Module

This module contains business logic and helper functions for field mapping execution,
including response parsing, validation, business rules, and formatting.
"""

import logging
from typing import Any, Dict

from app.schemas.unified_discovery_flow_state import UnifiedDiscoveryFlowState
from .exceptions import MappingParseError, TransformationError, ValidationError

logger = logging.getLogger(__name__)


class BusinessLogicManager:
    """Handles business logic operations for field mapping execution."""

    def __init__(
        self,
        parser=None,
        validator=None,
        rules_engine=None,
        formatter=None,
        transformer=None,
    ):
        self.parser = parser
        self.validator = validator
        self.rules_engine = rules_engine
        self.formatter = formatter
        self.transformer = transformer

    async def parse_agent_response(
        self, agent_response: str, state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Parse the agent response to extract field mappings."""
        try:
            if not self.parser:
                raise MappingParseError("No parser available")

            parsed_mappings = await self.parser.parse_response(
                agent_response, {"flow_id": str(state.flow_id)}
            )

            logger.info(
                f"Parsed {len(parsed_mappings.get('mappings', []))} mappings for flow {state.flow_id}"
            )
            return parsed_mappings

        except Exception as e:
            logger.error(
                f"Failed to parse agent response for flow {state.flow_id}: {str(e)}"
            )
            raise MappingParseError(f"Failed to parse agent response: {str(e)}") from e

    async def validate_mappings(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Validate the parsed field mappings."""
        try:
            if not self.validator:
                raise ValidationError("No validator available")

            validation_results = await self.validator.validate_mappings(
                parsed_mappings, {"flow_id": str(state.flow_id)}
            )

            logger.info(
                f"Validation completed for flow {state.flow_id}: "
                f"Valid: {validation_results.get('valid', False)}"
            )
            return validation_results

        except Exception as e:
            logger.error(
                f"Mapping validation failed for flow {state.flow_id}: {str(e)}"
            )
            raise ValidationError(f"Mapping validation failed: {str(e)}") from e

    async def apply_business_rules(
        self, parsed_mappings: Dict[str, Any], state: UnifiedDiscoveryFlowState
    ) -> Dict[str, Any]:
        """Apply business rules and check for clarifications needed."""
        try:
            if not self.rules_engine:
                # Return default response if no rules engine
                return {
                    "rules_applied": [],
                    "clarifications_needed": [],
                    "confidence_adjustments": {},
                }

            rules_results = await self.rules_engine.apply_rules(
                parsed_mappings, {"flow_id": str(state.flow_id)}
            )

            logger.info(
                f"Business rules applied for flow {state.flow_id}: "
                f"{len(rules_results.get('clarifications_needed', []))} clarifications needed"
            )
            return rules_results

        except Exception as e:
            logger.error(
                f"Business rules application failed for flow {state.flow_id}: {str(e)}"
            )
            # Return safe default instead of raising exception
            return {
                "rules_applied": [],
                "clarifications_needed": [],
                "confidence_adjustments": {},
                "error": str(e),
            }

    async def transform_and_persist(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
        db_session: Any,
    ) -> Dict[str, Any]:
        """Transform and persist the field mappings."""
        try:
            if not self.transformer:
                raise TransformationError("No transformer available")

            transformation_results = await self.transformer.transform_and_persist(
                parsed_mappings, validation_results, state, db_session
            )

            logger.info(
                f"Transformation completed for flow {state.flow_id}: "
                f"{transformation_results.get('mappings_persisted', 0)} mappings persisted"
            )
            return transformation_results

        except Exception as e:
            logger.error(f"Transformation failed for flow {state.flow_id}: {str(e)}")
            raise TransformationError(f"Transformation failed: {str(e)}") from e

    async def format_response(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
        state: UnifiedDiscoveryFlowState,
    ) -> Dict[str, Any]:
        """Format the final response for the field mapping execution."""
        try:
            if not self.formatter:
                # Return basic response if no formatter
                return {
                    "status": "completed",
                    "flow_id": str(state.flow_id),
                    "mappings": parsed_mappings.get("mappings", []),
                    "validation": validation_results,
                    "rules": rules_results,
                    "transformation": transformation_results,
                    "next_phase": self._determine_next_phase(
                        validation_results, rules_results, transformation_results
                    ),
                }

            response = await self.formatter.format_response(
                {
                    "mappings": parsed_mappings,
                    "validation": validation_results,
                    "rules": rules_results,
                    "transformation": transformation_results,
                    "flow_id": str(state.flow_id),
                }
            )

            # Add next phase determination
            response["next_phase"] = self._determine_next_phase(
                validation_results, rules_results, transformation_results
            )

            logger.info(f"Response formatted for flow {state.flow_id}")
            return response

        except Exception as e:
            logger.error(
                f"Response formatting failed for flow {state.flow_id}: {str(e)}"
            )
            # Return safe fallback response
            return {
                "status": "error",
                "flow_id": str(state.flow_id),
                "error": f"Response formatting failed: {str(e)}",
                "next_phase": "field_mapping",  # Stay in current phase on error
            }

    def _determine_next_phase(
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
