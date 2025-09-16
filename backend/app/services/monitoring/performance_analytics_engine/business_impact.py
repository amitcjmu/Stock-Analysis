"""
Business Impact Analysis module for Performance Analytics Engine

Calculates and models the business impact of performance changes.
"""

from typing import Dict, List, Tuple

from .base import BusinessImpactAnalysis


class BusinessImpactService:
    """Service for analyzing business impact of performance changes"""

    def __init__(self):
        # Business impact models
        self.business_impact_models = {
            "user_satisfaction": self._model_user_satisfaction_impact,
            "conversion_rate": self._model_conversion_impact,
            "user_retention": self._model_retention_impact,
            "operational_cost": self._model_cost_impact,
        }

    def calculate_business_impact(
        self, metric_name: str, performance_change: float
    ) -> BusinessImpactAnalysis:
        """Calculate business impact of performance changes"""
        user_impact = {}
        business_impact = {}
        confidence = 0.0

        # Apply business impact models
        for impact_type, model_func in self.business_impact_models.items():
            impact_value, impact_confidence = model_func(
                metric_name, performance_change
            )
            user_impact[impact_type] = impact_value
            confidence += impact_confidence

        confidence = confidence / len(self.business_impact_models)

        # Calculate aggregate business impact
        business_impact = {
            "user_experience_score_change": user_impact.get("user_satisfaction", 0),
            "estimated_conversion_impact_percent": user_impact.get(
                "conversion_rate", 0
            ),
            "estimated_retention_impact_percent": user_impact.get("user_retention", 0),
            "estimated_cost_impact_percent": user_impact.get("operational_cost", 0),
        }

        return BusinessImpactAnalysis(
            metric_name=metric_name,
            performance_change_percent=performance_change,
            estimated_user_impact=user_impact,
            estimated_business_impact=business_impact,
            confidence_level=confidence,
        )

    def calculate_business_impacts_for_trends(
        self, trends: Dict
    ) -> List[BusinessImpactAnalysis]:
        """Calculate business impacts for all significant trends"""
        business_impacts = []
        for metric_name, trend in trends.items():
            if abs(trend.change_percentage) > 5:  # Significant changes only
                impact = self.calculate_business_impact(
                    metric_name, trend.change_percentage
                )
                business_impacts.append(impact)
        return business_impacts

    def _model_user_satisfaction_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on user satisfaction"""
        # Simplified model: performance improvements have diminishing returns on satisfaction
        if metric_name.endswith("_ms"):
            # For response time metrics, negative change is good
            satisfaction_change = -performance_change * 0.3
        else:
            # For other metrics, positive change is good
            satisfaction_change = performance_change * 0.2

        return satisfaction_change, 70.0  # 70% confidence

    def _model_conversion_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on conversion rate"""
        # Research shows 100ms improvement can increase conversion by 1%
        if metric_name == "login_p95_ms":
            conversion_change = -performance_change * 0.01  # 1% per 100ms improvement
        else:
            conversion_change = performance_change * 0.005

        return conversion_change, 60.0  # 60% confidence

    def _model_retention_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on user retention"""
        # Performance has moderate impact on retention
        retention_change = performance_change * 0.1

        return retention_change, 50.0  # 50% confidence

    def _model_cost_impact(
        self, metric_name: str, performance_change: float
    ) -> Tuple[float, float]:
        """Model impact on operational costs"""
        # Better performance can reduce server costs
        if metric_name in ["cpu_usage", "memory_usage"]:
            cost_change = performance_change * 0.5  # Direct correlation
        else:
            cost_change = performance_change * 0.1  # Indirect correlation

        return cost_change, 80.0  # 80% confidence
