"""
Recommendation Validation Tool for 6R Migration Strategy Analysis.
Validates 6R recommendations for accuracy and feasibility.
"""

from typing import Any, Dict, List

from ..core.base import BaseTool, BaseModel, Field, logger, json


class RecommendationValidationInput(BaseModel):
    """Input schema for recommendation validation tool."""

    recommendation: Dict[str, Any] = Field(
        ..., description="6R recommendation to validate"
    )
    application_context: Dict[str, Any] = Field(..., description="Application context")
    validation_criteria: List[str] = Field(
        default=[], description="Specific validation criteria"
    )


class RecommendationValidationTool(BaseTool):
    """Tool for validating 6R recommendations."""

    name: str = "recommendation_validation_tool"
    description: str = "Validate 6R recommendations for accuracy and feasibility"
    args_schema: type[BaseModel] = RecommendationValidationInput

    def _run(
        self,
        recommendation: Dict[str, Any],
        application_context: Dict[str, Any],
        validation_criteria: List[str] = [],
    ) -> str:
        """Validate a 6R recommendation."""
        try:
            validation_result = {
                "overall_status": "approved",
                "confidence_score": 0.8,
                "validation_checks": [],
                "warnings": [],
                "recommendations": [],
                "implementation_readiness": "ready",
            }

            # Validate strategy alignment
            strategy = recommendation.get("recommended_strategy", "")
            confidence = recommendation.get("confidence_score", 0.0)

            # Check confidence threshold
            if confidence < 0.6:
                validation_result["warnings"].append(
                    "Low confidence score - consider gathering more information"
                )
                validation_result["overall_status"] = "needs_review"

            # Strategy-specific validation
            if strategy == "retire":
                if application_context.get("business_criticality") == "high":
                    validation_result["warnings"].append(
                        "Retire recommendation for high-criticality application needs careful review"
                    )

            elif strategy == "rearchitect":
                if application_context.get("migration_urgency", 5) > 7:
                    validation_result["warnings"].append(
                        "Rearchitect strategy conflicts with high urgency requirements"
                    )

            elif strategy == "rewrite":
                if application_context.get("innovation_priority", 5) < 6:
                    validation_result["warnings"].append(
                        "Rewrite strategy requires high innovation priority and commitment"
                    )

            # Technical feasibility checks
            tech_complexity = application_context.get("technical_complexity", 5)
            if tech_complexity > 8 and strategy in [
                "refactor",
                "rearchitect",
                "rewrite",
            ]:
                validation_result["warnings"].append(
                    "High technical complexity may increase implementation risk"
                )

            # Business alignment checks
            business_value = application_context.get("business_value", 5)
            if business_value > 7 and strategy == "retire":
                validation_result["overall_status"] = "needs_revision"
                validation_result["warnings"].append(
                    "High business value conflicts with retire recommendation"
                )

            # Set final status
            if len(validation_result["warnings"]) > 2:
                validation_result["overall_status"] = "needs_review"

            if validation_result["overall_status"] == "needs_revision":
                validation_result["implementation_readiness"] = "blocked"
            elif validation_result["overall_status"] == "needs_review":
                validation_result["implementation_readiness"] = "conditional"

            return json.dumps(validation_result, indent=2)

        except Exception as e:
            logger.error(f"Recommendation validation failed: {e}")
            return json.dumps({"error": str(e), "status": "failed"})
