"""
Mapping Response Formatters
Specialized formatters for field mapping responses and suggestions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseFormatter:
    """Base class for formatters"""

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format data for output

        Args:
            data: Data to format

        Returns:
            Formatted data
        """
        raise NotImplementedError


class MappingResponseFormatter(BaseFormatter):
    """Formats field mapping responses in standardized format"""

    def __init__(self):
        self.default_confidence = 0.7

    def create_mapping_response(
        self,
        mappings: Dict[str, str],
        confidence_scores: Optional[Dict[str, float]] = None,
        validation_results: Optional[Dict[str, Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create standardized mapping response

        Args:
            mappings: Field mappings dictionary
            confidence_scores: Optional confidence scores per field
            validation_results: Optional validation results
            execution_metadata: Optional execution metadata

        Returns:
            Standardized mapping response dictionary
        """
        confidence_scores = confidence_scores or {}

        # Ensure all mappings have confidence scores
        for field in mappings:
            if field not in confidence_scores:
                confidence_scores[field] = self.default_confidence

        # Calculate overall metrics
        total_fields = len(mappings)
        mapped_fields = len([k for k, v in mappings.items() if v])
        avg_confidence = (
            sum(confidence_scores.values()) / len(confidence_scores)
            if confidence_scores
            else self.default_confidence
        )

        # Create validation results if not provided
        if validation_results is None:
            validation_results = {
                "total_fields": total_fields,
                "mapped_fields": mapped_fields,
                "mapping_confidence": avg_confidence,
                "fallback_used": False,
            }

        # Create execution metadata if not provided
        if execution_metadata is None:
            execution_metadata = {
                "timestamp": self._get_timestamp(),
                "method": "field_mapping_executor",
            }

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "validation_results": validation_results,
            "crew_execution": execution_metadata.get("crew_used", False),
            "execution_metadata": execution_metadata,
        }

    def create_mapping_response_with_details(
        self,
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
        mapping_details: Optional[Dict[str, Dict[str, Any]]] = None,
        validation_results: Optional[Dict[str, Any]] = None,
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create detailed mapping response with per-field details

        Args:
            mappings: Field mappings dictionary
            confidence_scores: Confidence scores per field
            mapping_details: Optional detailed information per field
            validation_results: Optional validation results
            execution_metadata: Optional execution metadata

        Returns:
            Detailed mapping response dictionary
        """
        # Create mapping details if not provided
        if mapping_details is None:
            mapping_details = {}
            for source, target in mappings.items():
                confidence = confidence_scores.get(source, self.default_confidence)
                mapping_details[source] = {
                    "target": target,
                    "confidence": confidence,
                    "reasoning": f"Mapped with {confidence*100:.0f}% confidence",
                }

        # Create base response
        response = self.create_mapping_response(
            mappings, confidence_scores, validation_results, execution_metadata
        )

        # Add detailed information
        response["mapping_details"] = mapping_details

        return response

    def create_suggestions_response(
        self,
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
        clarifications: List[str],
        execution_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create response for mapping suggestions (used in suggestions-only mode)

        Args:
            mappings: Suggested field mappings
            confidence_scores: Confidence scores per mapping
            clarifications: List of clarification questions
            execution_metadata: Optional execution metadata

        Returns:
            Suggestions response dictionary
        """
        if execution_metadata is None:
            execution_metadata = {
                "timestamp": self._get_timestamp(),
                "method": "suggestions_only",
                "crew_used": False,
            }

        return {
            "mappings": mappings,
            "confidence_scores": confidence_scores,
            "clarifications": clarifications,
            "suggestions_generated": True,
            "execution_metadata": execution_metadata,
        }

    def create_error_response(
        self,
        error_message: str,
        error_type: str = "MappingError",
        partial_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create error response for failed mapping operations

        Args:
            error_message: Error description
            error_type: Type of error
            partial_results: Any partial results if available

        Returns:
            Error response dictionary
        """
        response = {
            "status": "error",
            "error": {
                "type": error_type,
                "message": error_message,
                "timestamp": self._get_timestamp(),
            },
            "mappings": {},
            "confidence_scores": {},
            "execution_metadata": {
                "timestamp": self._get_timestamp(),
                "method": "error_response",
                "success": False,
            },
        }

        # Include partial results if available
        if partial_results:
            response["partial_results"] = partial_results

        return response

    async def format_response(
        self,
        parsed_mappings: Dict[str, Any],
        validation_results: Dict[str, Any],
        rules_results: Dict[str, Any],
        transformation_results: Dict[str, Any],
        flow_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format the final response for the field mapping phase.
        This method provides compatibility with the base executor interface.
        """
        try:
            # Extract mappings from parsed structure
            if isinstance(parsed_mappings.get("mappings"), list):
                mappings = {}
                confidence_scores = {}
                for mapping in parsed_mappings["mappings"]:
                    if isinstance(mapping, dict):
                        source = mapping.get("source_field", "")
                        target = mapping.get("target_field", "")
                        confidence = mapping.get("confidence", 0.7)
                        if source and target:
                            mappings[source] = target
                            confidence_scores[source] = confidence
            else:
                mappings = parsed_mappings.get("mappings", {})
                confidence_scores = parsed_mappings.get("confidence_scores", {})

            # Create execution metadata from flow context and results
            execution_metadata = {
                "timestamp": self._get_timestamp(),
                "method": "modular_field_mapping_executor",
                "flow_id": flow_context.get("flow_id"),
                "engagement_id": flow_context.get("engagement_id"),
                "client_account_id": flow_context.get("client_account_id"),
                "phase": flow_context.get("current_phase", "field_mapping"),
                "crew_used": not transformation_results.get("message", "").startswith(
                    "Transformation skipped"
                ),
                "validation_passed": validation_results.get("overall_valid", False),
                "rules_applied": rules_results.get("rules_applied", 0),
                "transformation_success": transformation_results.get("success", False),
            }

            # Create comprehensive response
            response = self.create_mapping_response(
                mappings=mappings,
                confidence_scores=confidence_scores,
                validation_results=validation_results,
                execution_metadata=execution_metadata,
            )

            # Add additional context from all processing stages
            response["parsing_results"] = parsed_mappings
            response["rules_results"] = rules_results
            response["transformation_results"] = transformation_results
            response["success"] = validation_results.get(
                "overall_valid", False
            ) and transformation_results.get("success", False)

            # Add clarifications from various sources
            all_clarifications = []
            if parsed_mappings.get("clarifications"):
                all_clarifications.extend(parsed_mappings["clarifications"])
            if rules_results.get("clarifications"):
                all_clarifications.extend(rules_results["clarifications"])
            response["clarifications"] = all_clarifications

            return response

        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            # Return error response
            return self.create_error_response(
                error_message=f"Response formatting failed: {e}",
                error_type="FormattingError",
                partial_results={
                    "parsed_mappings": parsed_mappings,
                    "validation_results": validation_results,
                    "rules_results": rules_results,
                    "transformation_results": transformation_results,
                },
            )

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()
