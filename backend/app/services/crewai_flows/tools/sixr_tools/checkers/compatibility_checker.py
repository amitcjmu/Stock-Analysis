"""
Compatibility Checker for Six R Strategy Tools.

Validates compatibility between component treatments within an application.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.models.assessment_flow_state import ComponentType, SixRStrategy

logger = logging.getLogger(__name__)


class CompatibilityChecker:
    """
    Validates compatibility between component treatments within an application.

    Checks for:
    - Technical compatibility between component strategies
    - Data flow and integration compatibility
    - Timing and sequencing requirements
    - Shared resource conflicts
    """

    def __init__(self):
        self.name = "compatibility_checker"
        self.description = (
            "Validates treatment compatibility between related components"
        )
        logger.info("Initialized CompatibilityChecker")

    def _run(
        self,
        component_treatments: List[Dict[str, Any]],
        application_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Check compatibility between component treatments.

        Args:
            component_treatments: List of proposed treatments for components
            application_metadata: Application details and architecture

        Returns:
            Dict with compatibility validation results
        """
        try:
            # Group treatments by component type
            treatments_by_type = {}
            for treatment in component_treatments:
                comp_type = treatment.get("component_type", "unknown")
                strategy = treatment.get("recommended_strategy", "unknown")
                treatments_by_type[comp_type] = strategy

            # Check for incompatibilities
            issues = self._check_treatment_conflicts(treatments_by_type)

            # Check data flow compatibility
            data_flow_issues = self._check_data_flow_compatibility(
                component_treatments, application_metadata
            )
            issues.extend(data_flow_issues)

            # Check timing requirements
            timing_issues = self._check_timing_requirements(component_treatments)
            issues.extend(timing_issues)

            # Generate compatibility score
            compatibility_score = self._calculate_compatibility_score(issues)

            # Generate recommendations
            recommendations = self._generate_compatibility_recommendations(
                issues, treatments_by_type
            )

            return {
                "compatible": len(issues) == 0,
                "compatibility_score": compatibility_score,
                "issues": issues,
                "recommendations": recommendations,
                "validation_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in CompatibilityChecker: {str(e)}")
            return {
                "compatible": False,
                "compatibility_score": 0.0,
                "issues": [f"Validation error: {str(e)}"],
                "error": str(e),
            }

    def _check_treatment_conflicts(
        self, treatments_by_type: Dict[str, str]
    ) -> List[str]:
        """Check for known incompatible treatment combinations"""
        issues = []

        # Define incompatible patterns
        incompatible_patterns = [
            {
                "condition": lambda t: (
                    t.get(ComponentType.FRONTEND.value) == SixRStrategy.REWRITE.value
                    and t.get(ComponentType.BACKEND.value) == SixRStrategy.RETAIN.value
                ),
                "issue": "Frontend rewrite with backend retain may cause API compatibility issues",
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.DATABASE.value) == SixRStrategy.RETIRE.value
                    and t.get(ComponentType.BACKEND.value)
                    in [SixRStrategy.RETAIN.value, SixRStrategy.REHOST.value]
                ),
                "issue": "Database retirement conflicts with retained backend components",
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.FRONTEND.value) == SixRStrategy.REHOST.value
                    and t.get(ComponentType.BACKEND.value)
                    == SixRStrategy.REARCHITECT.value
                ),
                "issue": "Rehosted frontend may not support re-architected backend patterns",
            },
            {
                "condition": lambda t: (
                    t.get(ComponentType.API.value) == SixRStrategy.RETIRE.value
                    and any(s == SixRStrategy.RETAIN.value for s in t.values())
                ),
                "issue": "API retirement impacts retained components that depend on it",
            },
        ]

        for pattern in incompatible_patterns:
            if pattern["condition"](treatments_by_type):
                issues.append(pattern["issue"])

        return issues

    def _check_data_flow_compatibility(
        self,
        component_treatments: List[Dict[str, Any]],
        application_metadata: Dict[str, Any],
    ) -> List[str]:
        """Check if data flow between components remains viable"""
        issues = []

        # Extract dependencies
        component_deps = {}
        for treatment in component_treatments:
            comp_name = treatment.get("component_name", "")
            deps = treatment.get("dependencies", [])
            component_deps[comp_name] = deps

        # Check if modernized components can still communicate with legacy ones
        for treatment in component_treatments:
            comp_name = treatment.get("component_name", "")
            strategy = treatment.get("recommended_strategy", "")

            if strategy in [SixRStrategy.REWRITE.value, SixRStrategy.REARCHITECT.value]:
                # Check dependencies
                for dep in component_deps.get(comp_name, []):
                    dep_treatment = next(
                        (
                            t
                            for t in component_treatments
                            if t.get("component_name") == dep
                        ),
                        None,
                    )
                    if (
                        dep_treatment
                        and dep_treatment.get("recommended_strategy")
                        == SixRStrategy.RETAIN.value
                    ):
                        issues.append(
                            f"Modernized component '{comp_name}' depends on retained "
                            f"component '{dep}' - interface compatibility required"
                        )

        return issues

    def _check_timing_requirements(
        self, component_treatments: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if migration timing creates conflicts"""
        issues = []

        # Count strategies that require significant downtime
        high_impact_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.RETIRE.value,
        ]

        high_impact_count = sum(
            1
            for t in component_treatments
            if t.get("recommended_strategy") in high_impact_strategies
        )

        if high_impact_count > len(component_treatments) / 2:
            issues.append(
                f"{high_impact_count} components require major changes - consider phased migration approach"
            )

        # Check for database changes with dependent components
        db_components = [
            t
            for t in component_treatments
            if t.get("component_type") == ComponentType.DATABASE.value
        ]

        for db_comp in db_components:
            if db_comp.get("recommended_strategy") != SixRStrategy.RETAIN.value:
                dependent_count = sum(
                    1
                    for t in component_treatments
                    if db_comp.get("component_name") in t.get("dependencies", [])
                )
                if dependent_count > 2:
                    issues.append(
                        f"Database changes affect {dependent_count} components - requires careful coordination"
                    )

        return issues

    def _calculate_compatibility_score(self, issues: List[str]) -> float:
        """Calculate overall compatibility score (0-100)"""
        if not issues:
            return 100.0

        # Deduct points based on issue severity
        base_score = 100.0

        for issue in issues:
            if "conflicts" in issue.lower() or "incompatible" in issue.lower():
                base_score -= 20.0  # Severe issues
            elif "requires" in issue.lower() or "careful" in issue.lower():
                base_score -= 10.0  # Moderate issues
            else:
                base_score -= 5.0  # Minor issues

        return max(0.0, base_score)

    def _generate_compatibility_recommendations(
        self, issues: List[str], treatments_by_type: Dict[str, str]
    ) -> List[str]:
        """Generate recommendations to address compatibility issues"""
        recommendations = []

        if not issues:
            recommendations.append(
                "All component treatments are compatible - proceed with confidence"
            )
            return recommendations

        # General recommendations based on issue patterns
        if any("interface compatibility" in issue for issue in issues):
            recommendations.append(
                "Implement API versioning and backwards compatibility layers"
            )
            recommendations.append(
                "Consider using API gateways or service mesh for protocol translation"
            )

        if any("phased migration" in issue for issue in issues):
            recommendations.append(
                "Develop a phased migration plan with clear milestones"
            )
            recommendations.append("Implement feature flags for gradual rollout")

        if any("database changes" in issue for issue in issues):
            recommendations.append(
                "Use database migration tools with rollback capabilities"
            )
            recommendations.append(
                "Consider database replication during transition period"
            )

        if any("conflicts" in issue for issue in issues):
            recommendations.append("Review component strategies for alignment")
            recommendations.append(
                "Consider adjusting strategies for better compatibility"
            )

        # Strategy-specific recommendations
        if (
            treatments_by_type.get(ComponentType.FRONTEND.value)
            == SixRStrategy.REWRITE.value
        ):
            recommendations.append("Implement API contracts early in frontend rewrite")

        if (
            treatments_by_type.get(ComponentType.DATABASE.value)
            == SixRStrategy.RETIRE.value
        ):
            recommendations.append(
                "Plan data migration strategy before database retirement"
            )

        return recommendations
