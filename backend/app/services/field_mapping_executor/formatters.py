"""
Field Mapping Formatters
Output formatting and response creation for field mapping results.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class MappingResponseFormatter:
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

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat()


class ValidationResultsFormatter:
    """Formats validation results for display and logging"""

    def format_validation_summary(self, validation_results: Dict[str, Any]) -> str:
        """Create human-readable validation summary"""
        if not validation_results:
            return "No validation results available"

        lines = []
        lines.append("=== Field Mapping Validation Summary ===")

        # Overall status
        overall_valid = validation_results.get("overall_valid", False)
        status = "✅ PASSED" if overall_valid else "❌ FAILED"
        lines.append(f"Overall Status: {status}")

        # Error summary
        errors = validation_results.get("errors", [])
        warnings = validation_results.get("warnings", [])

        if errors:
            lines.append(f"\n🚨 Errors ({len(errors)}):")
            for error in errors:
                lines.append(f"  • {error}")

        if warnings:
            lines.append(f"\n⚠️ Warnings ({len(warnings)}):")
            for warning in warnings:
                lines.append(f"  • {warning}")

        # Mapping quality metrics
        if "cleaned_mappings" in validation_results:
            mappings = validation_results["cleaned_mappings"]
            confidence_validation = validation_results.get("confidence_validation", {})

            lines.append(f"\n📊 Mapping Metrics:")
            lines.append(f"  • Total mappings: {len(mappings)}")

            if confidence_validation and "metrics" in confidence_validation:
                metrics = confidence_validation["metrics"]
                lines.append(
                    f"  • Average confidence: {metrics.get('average_confidence', 0):.2f}"
                )
                lines.append(
                    f"  • High confidence fields: {metrics.get('high_confidence_count', 0)}"
                )
                lines.append(
                    f"  • Low confidence fields: {metrics.get('low_confidence_count', 0)}"
                )

        # Data quality metrics
        if "data_quality_validation" in validation_results:
            dq = validation_results["data_quality_validation"]
            if "quality_score" in dq:
                lines.append(f"  • Data quality score: {dq['quality_score']:.2f}")

        return "\n".join(lines)

    def format_confidence_breakdown(self, confidence_scores: Dict[str, float]) -> str:
        """Create confidence score breakdown"""
        if not confidence_scores:
            return "No confidence scores available"

        lines = []
        lines.append("=== Confidence Score Breakdown ===")

        # Sort by confidence (highest first)
        sorted_scores = sorted(
            confidence_scores.items(), key=lambda x: x[1], reverse=True
        )

        for field, score in sorted_scores:
            confidence_icon = "🟢" if score >= 0.8 else "🟡" if score >= 0.6 else "🔴"
            lines.append(f"{confidence_icon} {field}: {score:.2f}")

        # Summary statistics
        scores = list(confidence_scores.values())
        lines.append(f"\nSummary:")
        lines.append(f"  • Average: {sum(scores) / len(scores):.2f}")
        lines.append(f"  • Minimum: {min(scores):.2f}")
        lines.append(f"  • Maximum: {max(scores):.2f}")
        lines.append(
            f"  • High confidence (≥0.8): {sum(1 for s in scores if s >= 0.8)}"
        )
        lines.append(f"  • Low confidence (<0.6): {sum(1 for s in scores if s < 0.6)}")

        return "\n".join(lines)


class LoggingFormatter:
    """Formats mapping results for structured logging"""

    def format_execution_log(
        self,
        phase_name: str,
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
        execution_time_ms: Optional[float] = None,
        crew_used: bool = False,
    ) -> Dict[str, Any]:
        """Format execution details for structured logging"""
        scores = list(confidence_scores.values()) if confidence_scores else []

        log_entry = {
            "event": "field_mapping_execution",
            "phase": phase_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "total_fields": len(mappings),
                "avg_confidence": sum(scores) / len(scores) if scores else 0.0,
                "min_confidence": min(scores) if scores else 0.0,
                "max_confidence": max(scores) if scores else 0.0,
                "high_confidence_count": sum(1 for s in scores if s >= 0.8),
                "low_confidence_count": sum(1 for s in scores if s < 0.6),
            },
            "execution": {
                "crew_used": crew_used,
                "execution_time_ms": execution_time_ms,
                "method": "crew_ai" if crew_used else "fallback",
            },
        }

        # Add field details (limited for log size)
        if len(mappings) <= 20:  # Only include details for small mapping sets
            log_entry["mappings"] = [
                {
                    "source": source,
                    "target": target,
                    "confidence": confidence_scores.get(source, 0.0),
                }
                for source, target in mappings.items()
            ]

        return log_entry

    def format_error_log(
        self,
        phase_name: str,
        error_message: str,
        error_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Format error details for structured logging"""
        log_entry = {
            "event": "field_mapping_error",
            "phase": phase_name,
            "timestamp": datetime.utcnow().isoformat(),
            "error": {
                "type": error_type,
                "message": error_message,
            },
        }

        if context:
            log_entry["context"] = context

        return log_entry


class ClarificationFormatter:
    """Formats clarification questions and responses"""

    def format_clarifications(
        self,
        clarifications: List[str],
        mappings: Dict[str, str],
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        """Format clarification questions with context"""
        formatted_clarifications = []

        for i, clarification in enumerate(clarifications, 1):
            formatted_clarifications.append(
                {
                    "id": f"clarification_{i}",
                    "question": clarification,
                    "priority": (
                        "high" if "required" in clarification.lower() else "normal"
                    ),
                    "category": self._categorize_clarification(clarification),
                }
            )

        return {
            "clarifications": formatted_clarifications,
            "total_questions": len(clarifications),
            "context": {
                "total_mappings": len(mappings),
                "avg_confidence": (
                    sum(confidence_scores.values()) / len(confidence_scores)
                    if confidence_scores
                    else 0.0
                ),
                "low_confidence_fields": [
                    field for field, score in confidence_scores.items() if score < 0.6
                ],
            },
        }

    def _categorize_clarification(self, clarification: str) -> str:
        """Categorize clarification question by type"""
        clarification_lower = clarification.lower()

        if "required" in clarification_lower or "missing" in clarification_lower:
            return "missing_required"
        elif "confidence" in clarification_lower or "review" in clarification_lower:
            return "confidence_review"
        elif "data quality" in clarification_lower:
            return "data_quality"
        else:
            return "general"


# Factory functions
def create_response_formatter() -> MappingResponseFormatter:
    """Create a mapping response formatter"""
    return MappingResponseFormatter()


def create_validation_formatter() -> ValidationResultsFormatter:
    """Create a validation results formatter"""
    return ValidationResultsFormatter()


def create_logging_formatter() -> LoggingFormatter:
    """Create a logging formatter"""
    return LoggingFormatter()


def create_clarification_formatter() -> ClarificationFormatter:
    """Create a clarification formatter"""
    return ClarificationFormatter()
