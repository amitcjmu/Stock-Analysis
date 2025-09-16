"""
Success criteria validation functionality.

This module handles enhanced success criteria validation for crew planning phases.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SuccessCriteriaValidationMixin:
    """Mixin for success criteria validation functionality"""

    def validate_enhanced_success_criteria(
        self, phase_name: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced success criteria validation"""
        try:
            validation_result = {
                "phase": phase_name,
                "passed": False,
                "criteria_checked": [],
                "validation_details": {},
                "recommendations": [],
                "confidence_scores": {},
            }

            # Get phase-specific criteria
            phase_criteria = self._get_phase_success_criteria(phase_name)

            for criterion, threshold in phase_criteria.items():
                validation_result["criteria_checked"].append(criterion)

                # Extract relevant value from results
                criterion_value = self._extract_criterion_value(criterion, results)
                validation_result["confidence_scores"][criterion] = criterion_value

                # Validate against threshold
                passes_criterion = criterion_value >= threshold
                validation_result["validation_details"][criterion] = {
                    "value": criterion_value,
                    "threshold": threshold,
                    "passed": passes_criterion,
                }

                if not passes_criterion:
                    recommendation = self._generate_improvement_recommendation(
                        criterion, criterion_value, threshold
                    )
                    validation_result["recommendations"].append(recommendation)

            # Overall validation result
            all_passed = all(
                details["passed"]
                for details in validation_result["validation_details"].values()
            )
            validation_result["passed"] = all_passed

            # Generate overall recommendations if needed
            if not all_passed:
                validation_result["recommendations"].append(
                    {
                        "type": "overall",
                        "message": (
                            f"Phase {phase_name} requires improvement in "
                            f"{len(validation_result['recommendations'])} areas"
                        ),
                        "priority": "medium",
                    }
                )

            logger.info(
                f"✅ Enhanced validation completed for {phase_name}: {'PASSED' if all_passed else 'NEEDS_IMPROVEMENT'}"
            )
            return validation_result

        except Exception as e:
            logger.error(f"Failed enhanced success criteria validation: {e}")
            return {"passed": False, "error": str(e)}

    def _get_phase_success_criteria(self, phase_name: str) -> Dict[str, float]:
        """Get success criteria thresholds for a phase"""
        criteria_map = {
            "field_mapping": {
                "mapping_confidence": 0.8,
                "field_coverage": 0.9,
                "semantic_accuracy": 0.75,
            },
            "data_cleansing": {
                "data_quality_score": 0.85,
                "completeness_ratio": 0.9,
                "standardization_success": 0.8,
            },
            "inventory_building": {
                "classification_accuracy": 0.8,
                "asset_completeness": 0.85,
                "cross_domain_consistency": 0.75,
            },
            "app_server_dependencies": {
                "dependency_completeness": 0.8,
                "relationship_accuracy": 0.75,
                "hosting_mapping_confidence": 0.8,
            },
            "app_app_dependencies": {
                "integration_completeness": 0.75,
                "dependency_confidence": 0.8,
                "business_flow_accuracy": 0.7,
            },
            "technical_debt": {
                "debt_assessment_completeness": 0.8,
                "modernization_recommendation_confidence": 0.75,
                "risk_assessment_accuracy": 0.8,
            },
        }
        return criteria_map.get(phase_name, {"overall_success": 0.7})

    def _extract_criterion_value(
        self, criterion: str, results: Dict[str, Any]
    ) -> float:
        """Extract criterion value from results"""
        criterion_mapping = {
            "mapping_confidence": ["field_mappings", "confidence_score"],
            "field_coverage": ["field_mappings", "coverage_ratio"],
            "data_quality_score": ["data_quality", "overall_score"],
            "classification_accuracy": ["classification", "accuracy"],
            "dependency_completeness": ["dependencies", "completeness"],
            "overall_success": ["overall", "success_score"],
        }

        try:
            if criterion in criterion_mapping:
                keys = criterion_mapping[criterion]
                value = results
                for key in keys:
                    value = value.get(key, 0.0)
                    if not isinstance(value, dict):
                        break
                return float(value) if isinstance(value, (int, float)) else 0.0
            else:
                return float(results.get(criterion, 0.0))
        except (ValueError, TypeError):
            return 0.0

    def _generate_improvement_recommendation(
        self, criterion: str, current_value: float, threshold: float
    ) -> Dict[str, Any]:
        """Generate improvement recommendation for failed criterion"""
        gap = threshold - current_value

        recommendations_map = {
            "mapping_confidence": "Review field mappings and improve semantic analysis",
            "data_quality_score": "Enhance data validation and cleansing procedures",
            "classification_accuracy": "Refine asset classification rules and patterns",
            "dependency_completeness": "Expand dependency discovery and validation",
        }

        return {
            "criterion": criterion,
            "current_value": current_value,
            "target_threshold": threshold,
            "gap": gap,
            "recommendation": recommendations_map.get(
                criterion, f"Improve {criterion} performance"
            ),
            "priority": "high" if gap > 0.2 else "medium" if gap > 0.1 else "low",
        }
