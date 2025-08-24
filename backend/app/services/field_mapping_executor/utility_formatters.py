"""
Utility Formatters
Validation, logging, and clarification formatters for field mapping operations.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


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

            lines.append("\n📊 Mapping Metrics:")
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
        lines.append("\nSummary:")
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
        """Format execution results for structured logging"""
        log_data = {
            "phase": phase_name,
            "mapping_count": len(mappings),
            "crew_execution": crew_used,
            "performance": {
                "execution_time_ms": execution_time_ms,
                "mappings_per_second": (
                    len(mappings) / (execution_time_ms / 1000.0)
                    if execution_time_ms and execution_time_ms > 0
                    else None
                ),
            },
            "quality_metrics": self._calculate_quality_metrics(
                mappings, confidence_scores
            ),
        }

        return log_data

    def _calculate_quality_metrics(
        self, mappings: Dict[str, str], confidence_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate quality metrics for logging"""
        if not confidence_scores:
            return {"average_confidence": 0.0, "quality_distribution": {}}

        scores = list(confidence_scores.values())
        high_quality = sum(1 for score in scores if score >= 0.8)
        medium_quality = sum(1 for score in scores if 0.6 <= score < 0.8)
        low_quality = sum(1 for score in scores if score < 0.6)

        return {
            "average_confidence": sum(scores) / len(scores) if scores else 0.0,
            "min_confidence": min(scores) if scores else 0.0,
            "max_confidence": max(scores) if scores else 0.0,
            "quality_distribution": {
                "high_quality": high_quality,
                "medium_quality": medium_quality,
                "low_quality": low_quality,
            },
            "unmapped_fields": sum(1 for target in mappings.values() if not target),
        }


class ClarificationFormatter:
    """Formats clarifications and suggestions for user interaction"""

    def format_clarifications(self, clarifications: List[str]) -> Dict[str, Any]:
        """Format clarifications for API response"""
        if not clarifications:
            return {
                "has_clarifications": False,
                "count": 0,
                "questions": [],
                "summary": "No clarifications needed",
            }

        return {
            "has_clarifications": True,
            "count": len(clarifications),
            "questions": clarifications,
            "summary": f"{len(clarifications)} clarification(s) needed for optimal mapping",
        }

    def format_mapping_suggestions(
        self, suggestions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format mapping suggestions for user review"""
        if not suggestions:
            return {
                "has_suggestions": False,
                "count": 0,
                "suggestions": [],
            }

        formatted_suggestions = []
        for suggestion in suggestions:
            formatted_suggestions.append(
                {
                    "source_field": suggestion.get("source_field"),
                    "suggested_targets": suggestion.get("suggested_targets", []),
                    "confidence_scores": suggestion.get("confidence_scores", {}),
                    "reasoning": suggestion.get("reasoning", ""),
                    "requires_confirmation": suggestion.get(
                        "requires_confirmation", True
                    ),
                }
            )

        return {
            "has_suggestions": True,
            "count": len(formatted_suggestions),
            "suggestions": formatted_suggestions,
            "summary": f"{len(formatted_suggestions)} mapping suggestion(s) available",
        }
