"""
Business Value Calculator - CrewAI Tool Implementation

Calculates business value and impact of migration strategies.

Factors include:
- Business criticality and revenue impact
- User experience improvements
- Operational efficiency gains
- Risk reduction benefits
- Compliance and security improvements
"""

import logging
from typing import Any, Dict, List

from app.models.assessment_flow_state import SixRStrategy

logger = logging.getLogger(__name__)


class BusinessValueCalculator:
    """
    Calculates business value and impact of migration strategies.

    Factors include:
    - Business criticality and revenue impact
    - User experience improvements
    - Operational efficiency gains
    - Risk reduction benefits
    - Compliance and security improvements
    """

    def __init__(self):
        self.name = "business_value_calculator"
        self.description = "Assesses business impact and value of migration strategies"
        logger.info("Initialized BusinessValueCalculator")

    def _run(
        self,
        application_metadata: Dict[str, Any],
        sixr_strategy: str,
        tech_debt_score: float,
    ) -> Dict[str, Any]:
        """
        Calculate business value for a migration strategy.

        Args:
            application_metadata: Application business context
            sixr_strategy: Chosen 6R strategy
            tech_debt_score: Current technical debt score

        Returns:
            Dict with business value metrics and recommendations
        """
        try:
            # Extract business context
            criticality = application_metadata.get("business_criticality", "medium")
            user_count = application_metadata.get("user_count", 100)
            revenue_impact = application_metadata.get("revenue_impact", "medium")
            compliance_required = application_metadata.get("compliance_required", False)

            # Calculate base business value
            base_value = self._calculate_base_value(
                criticality, user_count, revenue_impact
            )

            # Calculate strategy-specific value
            strategy_value = self._calculate_strategy_value(
                sixr_strategy, tech_debt_score
            )

            # Calculate risk reduction value
            risk_value = self._calculate_risk_reduction_value(
                tech_debt_score, compliance_required, sixr_strategy
            )

            # Calculate operational value
            operational_value = self._calculate_operational_value(sixr_strategy)

            # Calculate total business value
            total_value = (
                base_value + strategy_value + risk_value + operational_value
            ) / 4

            # Generate business case elements
            business_case = self._generate_business_case(
                sixr_strategy,
                total_value,
                criticality,
                tech_debt_score,
                compliance_required,
            )

            # Calculate ROI metrics
            roi_metrics = self._calculate_roi_metrics(
                sixr_strategy, total_value, tech_debt_score
            )

            return {
                "business_value_score": total_value,
                "value_components": {
                    "base_business_value": base_value,
                    "strategy_value": strategy_value,
                    "risk_reduction_value": risk_value,
                    "operational_value": operational_value,
                },
                "business_case": business_case,
                "roi_metrics": roi_metrics,
                "priority_recommendation": self._get_priority_recommendation(
                    total_value
                ),
                "value_realization_timeline": self._get_value_timeline(sixr_strategy),
            }

        except Exception as e:
            logger.error(f"Error in BusinessValueCalculator: {str(e)}")
            return {
                "business_value_score": 50.0,
                "error": str(e),
                "business_case": ["Unable to calculate business value due to error"],
            }

    def _calculate_base_value(
        self, criticality: str, user_count: int, revenue_impact: str
    ) -> float:
        """Calculate base business value from application attributes"""

        # Criticality scoring
        criticality_scores = {
            "critical": 100.0,
            "high": 80.0,
            "medium": 50.0,
            "low": 20.0,
        }
        crit_score = criticality_scores.get(criticality.lower(), 50.0)

        # User impact scoring
        if user_count > 10000:
            user_score = 100.0
        elif user_count > 1000:
            user_score = 80.0
        elif user_count > 100:
            user_score = 60.0
        else:
            user_score = 40.0

        # Revenue impact scoring
        revenue_scores = {"high": 100.0, "medium": 60.0, "low": 30.0, "none": 10.0}
        rev_score = revenue_scores.get(revenue_impact.lower(), 50.0)

        # Weighted average
        return crit_score * 0.4 + user_score * 0.3 + rev_score * 0.3

    def _calculate_strategy_value(
        self, sixr_strategy: str, tech_debt_score: float
    ) -> float:
        """Calculate value specific to the chosen strategy"""

        strategy_values = {
            SixRStrategy.REWRITE.value: {
                "base": 90.0,  # High transformation value
                "debt_multiplier": 1.5,  # More valuable for high debt
            },
            SixRStrategy.REARCHITECT.value: {"base": 80.0, "debt_multiplier": 1.3},
            SixRStrategy.REFACTOR.value: {"base": 70.0, "debt_multiplier": 1.2},
            SixRStrategy.REPLATFORM.value: {"base": 60.0, "debt_multiplier": 1.0},
            SixRStrategy.REHOST.value: {"base": 40.0, "debt_multiplier": 0.8},
            SixRStrategy.RETAIN.value: {"base": 20.0, "debt_multiplier": 0.5},
        }

        strategy_config = strategy_values.get(
            sixr_strategy, {"base": 50.0, "debt_multiplier": 1.0}
        )

        # Adjust value based on technical debt
        debt_factor = (tech_debt_score / 100.0) * strategy_config["debt_multiplier"]

        return strategy_config["base"] * (1 + debt_factor * 0.5)

    def _calculate_risk_reduction_value(
        self, tech_debt_score: float, compliance_required: bool, sixr_strategy: str
    ) -> float:
        """Calculate value from risk reduction"""

        base_risk_value = 0.0

        # Technical debt risk reduction
        if tech_debt_score > 70:
            if sixr_strategy in [
                SixRStrategy.REWRITE.value,
                SixRStrategy.REARCHITECT.value,
            ]:
                base_risk_value += 80.0  # Major risk reduction
            elif sixr_strategy == SixRStrategy.REFACTOR.value:
                base_risk_value += 60.0  # Moderate risk reduction
            else:
                base_risk_value += 30.0  # Some risk reduction

        # Compliance risk reduction
        if compliance_required:
            if sixr_strategy in [
                SixRStrategy.REWRITE.value,
                SixRStrategy.REARCHITECT.value,
            ]:
                base_risk_value += 40.0  # Full compliance opportunity
            else:
                base_risk_value += 20.0  # Partial compliance improvement

        # Security risk reduction
        modernization_strategies = [
            SixRStrategy.REWRITE.value,
            SixRStrategy.REARCHITECT.value,
            SixRStrategy.REFACTOR.value,
        ]
        if sixr_strategy in modernization_strategies:
            base_risk_value += 30.0  # Security improvements

        return min(100.0, base_risk_value)

    def _calculate_operational_value(self, sixr_strategy: str) -> float:
        """Calculate operational efficiency value"""

        operational_values = {
            SixRStrategy.REWRITE.value: 90.0,  # Maximum efficiency gains
            SixRStrategy.REARCHITECT.value: 85.0,  # High efficiency gains
            SixRStrategy.REFACTOR.value: 70.0,  # Good efficiency gains
            SixRStrategy.REPLATFORM.value: 80.0,  # Platform benefits
            SixRStrategy.REHOST.value: 50.0,  # Cloud cost benefits
            SixRStrategy.REPURCHASE.value: 95.0,  # SaaS operational benefits
            SixRStrategy.RETIRE.value: 100.0,  # Eliminate maintenance
            SixRStrategy.RETAIN.value: 10.0,  # Minimal gains
        }

        return operational_values.get(sixr_strategy, 50.0)

    def _generate_business_case(
        self,
        sixr_strategy: str,
        total_value: float,
        criticality: str,
        tech_debt_score: float,
        compliance_required: bool,
    ) -> List[str]:
        """Generate business case points"""

        business_case = []

        # Value-based case
        if total_value > 80:
            business_case.append("High business value justifies migration investment")
        elif total_value > 60:
            business_case.append("Solid business value supports migration effort")
        else:
            business_case.append(
                "Moderate business value - evaluate against other priorities"
            )

        # Strategy-specific benefits
        strategy_benefits = {
            SixRStrategy.REWRITE.value: "Complete modernization enables digital transformation",
            SixRStrategy.REARCHITECT.value: "Architecture improvements enable scalability and agility",
            SixRStrategy.REFACTOR.value: "Code improvements reduce maintenance costs",
            SixRStrategy.REPLATFORM.value: "Cloud platform benefits improve operational efficiency",
            SixRStrategy.REHOST.value: "Quick cloud migration provides immediate cost benefits",
            SixRStrategy.RETAIN.value: "Minimal disruption preserves stability",
        }

        benefit = strategy_benefits.get(sixr_strategy)
        if benefit:
            business_case.append(benefit)

        # Risk mitigation
        if tech_debt_score > 70:
            business_case.append(
                f"Addresses critical technical debt (score: {tech_debt_score:.1f})"
            )

        # Compliance
        if compliance_required:
            business_case.append("Enables compliance with regulatory requirements")

        # Criticality
        if criticality.lower() == "critical":
            business_case.append(
                "Critical business application requires modernization for continuity"
            )

        return business_case

    def _calculate_roi_metrics(
        self, sixr_strategy: str, total_value: float, tech_debt_score: float
    ) -> Dict[str, Any]:
        """Calculate ROI metrics for the migration"""

        # Estimate costs based on strategy
        cost_factors = {
            SixRStrategy.REWRITE.value: 1.0,
            SixRStrategy.REARCHITECT.value: 0.8,
            SixRStrategy.REFACTOR.value: 0.6,
            SixRStrategy.REPLATFORM.value: 0.4,
            SixRStrategy.REHOST.value: 0.2,
            SixRStrategy.RETAIN.value: 0.05,
        }

        relative_cost = cost_factors.get(sixr_strategy, 0.5)

        # Estimate payback period
        if total_value > 80 and relative_cost < 0.5:
            payback_months = 12
        elif total_value > 60:
            payback_months = 18
        else:
            payback_months = 24

        # Calculate 3-year ROI
        annual_value = total_value * 12  # Simplified annual value
        total_cost = relative_cost * 1000  # Simplified cost model
        three_year_value = annual_value * 3
        roi_percentage = ((three_year_value - total_cost) / total_cost) * 100

        return {
            "estimated_payback_months": payback_months,
            "three_year_roi_percentage": round(roi_percentage, 1),
            "annual_value_score": round(annual_value, 1),
            "relative_cost_factor": relative_cost,
            "cost_avoidance_factors": (
                [
                    "Reduced maintenance costs",
                    "Avoided security breach risks",
                    "Eliminated technical debt interest",
                ]
                if tech_debt_score > 50
                else ["Minimal cost avoidance"]
            ),
        }

    def _get_priority_recommendation(self, total_value: float) -> str:
        """Get priority recommendation based on value"""

        if total_value >= 80:
            return (
                "HIGH PRIORITY - Significant business value justifies immediate action"
            )
        elif total_value >= 60:
            return "MEDIUM PRIORITY - Good candidate for migration wave 1-2"
        elif total_value >= 40:
            return "LOW PRIORITY - Consider for later migration waves"
        else:
            return "MINIMAL PRIORITY - Evaluate alternatives to migration"

    def _get_value_timeline(self, sixr_strategy: str) -> Dict[str, str]:
        """Get value realization timeline"""

        timelines = {
            SixRStrategy.REWRITE.value: {
                "initial_value": "12-18 months",
                "full_value": "18-24 months",
                "value_type": "Transformational",
            },
            SixRStrategy.REARCHITECT.value: {
                "initial_value": "6-12 months",
                "full_value": "12-18 months",
                "value_type": "Architectural",
            },
            SixRStrategy.REFACTOR.value: {
                "initial_value": "3-6 months",
                "full_value": "6-12 months",
                "value_type": "Incremental",
            },
            SixRStrategy.REPLATFORM.value: {
                "initial_value": "1-3 months",
                "full_value": "3-6 months",
                "value_type": "Platform",
            },
            SixRStrategy.REHOST.value: {
                "initial_value": "< 1 month",
                "full_value": "1-3 months",
                "value_type": "Infrastructure",
            },
            SixRStrategy.RETAIN.value: {
                "initial_value": "N/A",
                "full_value": "N/A",
                "value_type": "None",
            },
        }

        return timelines.get(
            sixr_strategy,
            {
                "initial_value": "3-6 months",
                "full_value": "6-12 months",
                "value_type": "Standard",
            },
        )
