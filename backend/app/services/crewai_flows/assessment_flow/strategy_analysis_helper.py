"""
Assessment Flow Strategy Analysis Helper

This module contains helper methods for 6R strategy analysis and decision-making
used by the UnifiedAssessmentFlow class.
"""

import logging
from typing import Any, Dict

from app.models.assessment_flow import AssessmentFlowState, InMemorySixRDecision

logger = logging.getLogger(__name__)


class StrategyAnalysisHelper:
    """Helper class for 6R strategy analysis operations."""

    def __init__(self, flow_state: AssessmentFlowState):
        self.flow_state = flow_state

    def get_strategy_distribution(self) -> Dict[str, int]:
        """Get distribution of 6R strategies across all decisions."""
        try:
            distribution = {}

            for decision in self.flow_state.sixr_decisions:
                strategy = decision.sixr_strategy
                distribution[strategy] = distribution.get(strategy, 0) + 1

            logger.debug(f"Strategy distribution: {distribution}")
            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate strategy distribution: {str(e)}")
            return {}

    def analyze_component_for_sixr(
        self, component: Dict[str, Any], application_context: Dict[str, Any]
    ) -> InMemorySixRDecision:
        """Analyze a component and recommend a 6R strategy."""
        try:
            # Ensure unique component ID with application context
            app_id = application_context.get("application_id", "unknown-app")
            raw_id = component.get("component_id") or component.get("name") or "unknown"
            component_id = (
                str(raw_id) if component.get("component_id") else f"{app_id}:{raw_id}"
            )
            component_name = component.get("name", "Unknown Component")

            # Simple strategy decision logic (should be enhanced with actual AI/ML)
            strategy, confidence, reasoning = self._determine_strategy(
                component, application_context
            )

            decision = InMemorySixRDecision(
                component_id=component_id,
                component_name=component_name,
                sixr_strategy=strategy,
                confidence=confidence,
                reasoning=reasoning,
                dependencies=component.get("dependencies", []),
                estimated_effort=self._estimate_effort(component, strategy),
                risk_level=self._assess_risk_level(component, strategy),
            )

            logger.info(
                f"Analyzed component {component_name}: {strategy} "
                f"(confidence: {confidence:.2f})"
            )

            return decision

        except Exception as e:
            logger.error(
                f"Failed to analyze component {component.get('name')}: {str(e)}"
            )
            # Return a safe default decision
            return InMemorySixRDecision(
                component_id=component.get("component_id", "unknown"),
                component_name=component.get("name", "Unknown Component"),
                sixr_strategy="retain",
                confidence=0.1,
                reasoning=f"Analysis failed: {str(e)}. Defaulting to retain for safety.",
                risk_level="high",
            )

    def _determine_strategy(
        self, component: Dict[str, Any], application_context: Dict[str, Any]
    ) -> tuple[str, float, str]:
        """Determine the best 6R strategy for a component."""
        try:
            component_type = component.get("type", "").lower()
            technology = component.get("technology", "").lower()
            complexity_score = component.get("complexity_score", 5.0)
            business_criticality = application_context.get(
                "business_criticality", "medium"
            ).lower()

            # Simple decision tree logic (replace with ML model in production)
            if "database" in component_type:
                if "legacy" in technology or complexity_score > 8.0:
                    return (
                        "refactor",
                        0.8,
                        "Legacy database requires refactoring for cloud compatibility",
                    )
                elif business_criticality == "high":
                    return (
                        "rehost",
                        0.7,
                        "High criticality database should be rehosted first",
                    )
                else:
                    return (
                        "rearchitect",
                        0.6,
                        "Database can benefit from cloud-native rearchitecting",
                    )

            elif "web_server" in component_type or "app_server" in component_type:
                if complexity_score < 4.0:
                    return (
                        "rehost",
                        0.9,
                        "Simple server component suitable for direct rehosting",
                    )
                elif complexity_score < 7.0:
                    return (
                        "refactor",
                        0.8,
                        "Moderate complexity server requires refactoring",
                    )
                else:
                    return (
                        "rebuild",
                        0.7,
                        "Complex server component benefits from rebuilding",
                    )

            elif "cache" in component_type:
                return (
                    "replace",
                    0.9,
                    "Cache systems can typically be replaced with cloud services",
                )

            elif "monitoring" in component_type or "logging" in component_type:
                return (
                    "replace",
                    0.85,
                    "Observability tools should be replaced with cloud-native solutions",
                )

            else:
                # Default strategy based on complexity
                if complexity_score < 3.0:
                    return (
                        "rehost",
                        0.6,
                        "Low complexity component suitable for rehosting",
                    )
                elif complexity_score < 6.0:
                    return (
                        "refactor",
                        0.5,
                        "Medium complexity component may need refactoring",
                    )
                else:
                    return (
                        "retain",
                        0.4,
                        "High complexity component may need to be retained",
                    )

        except Exception as e:
            logger.warning(f"Error in strategy determination: {str(e)}")
            return "retain", 0.1, f"Strategy analysis failed: {str(e)}"

    def _estimate_effort(self, component: Dict[str, Any], strategy: str) -> str:
        """Estimate the effort required for the chosen strategy."""
        try:
            complexity_score = component.get("complexity_score", 5.0)

            # Base effort mapping
            effort_mapping = {
                "rehost": "low",
                "refactor": "medium",
                "rearchitect": "high",
                "rebuild": "high",
                "replace": "medium",
                "retain": "minimal",
            }

            base_effort = effort_mapping.get(strategy, "medium")

            # Adjust based on complexity
            if complexity_score > 8.0:
                if base_effort == "low":
                    return "medium"
                elif base_effort == "medium":
                    return "high"
                elif base_effort == "high":
                    return "very_high"

            return base_effort

        except Exception as e:
            logger.warning(f"Error estimating effort: {str(e)}")
            return "unknown"

    def _assess_risk_level(self, component: Dict[str, Any], strategy: str) -> str:
        """Assess the risk level for the chosen strategy."""
        try:
            complexity_score = component.get("complexity_score", 5.0)
            component_type = component.get("type", "").lower()

            # Base risk mapping
            risk_mapping = {
                "rehost": "low",
                "refactor": "medium",
                "rearchitect": "high",
                "rebuild": "high",
                "replace": "medium",
                "retain": "low",
            }

            base_risk = risk_mapping.get(strategy, "medium")

            # Adjust for critical components
            if "database" in component_type and strategy in ["rearchitect", "rebuild"]:
                return "high"

            # Adjust for complexity
            if complexity_score > 8.0 and strategy != "retain":
                if base_risk == "low":
                    return "medium"
                elif base_risk == "medium":
                    return "high"

            return base_risk

        except Exception as e:
            logger.warning(f"Error assessing risk: {str(e)}")
            return "medium"

    def validate_strategy_coherence(self) -> Dict[str, Any]:
        """Validate that all 6R decisions make sense together."""
        try:
            decisions = self.flow_state.sixr_decisions

            validation_results = {
                "is_coherent": True,
                "warnings": [],
                "recommendations": [],
                "strategy_stats": self.get_strategy_distribution(),
            }

            # Check for potential issues
            total_decisions = len(decisions)
            if total_decisions == 0:
                validation_results["warnings"].append("No 6R decisions found")
                validation_results["is_coherent"] = False
                return validation_results

            distribution = validation_results["strategy_stats"]

            # Check for excessive retain strategies
            retain_percentage = (distribution.get("retain", 0) / total_decisions) * 100
            if retain_percentage > 60:
                validation_results["warnings"].append(
                    f"High percentage of 'retain' decisions ({retain_percentage:.1f}%) "
                    "may indicate missed migration opportunities"
                )

            # Check for lack of diversity in strategies
            if len(distribution) == 1:
                validation_results["warnings"].append(
                    "All components assigned same strategy - consider more nuanced analysis"
                )

            # Check for high-risk combinations
            high_risk_count = sum(1 for d in decisions if d.risk_level == "high")
            high_risk_percentage = (high_risk_count / total_decisions) * 100
            if high_risk_percentage > 40:
                validation_results["warnings"].append(
                    f"High percentage of high-risk decisions ({high_risk_percentage:.1f}%) "
                    "may require additional planning and validation"
                )

            logger.info(
                f"Strategy coherence validation completed with {len(validation_results['warnings'])} warnings"
            )
            return validation_results

        except Exception as e:
            logger.error(f"Failed to validate strategy coherence: {str(e)}")
            return {
                "is_coherent": False,
                "warnings": [f"Validation failed: {str(e)}"],
                "recommendations": [],
                "strategy_stats": {},
            }
