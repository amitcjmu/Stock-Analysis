"""
Assessment Flow Report Generation Helper

This module contains helper methods for generating assessment reports
and "App on a Page" summaries used by the UnifiedAssessmentFlow class.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.models.assessment_flow import AssessmentFlowState

logger = logging.getLogger(__name__)


class ReportGenerationHelper:
    """Helper class for report generation operations."""

    def __init__(self, flow_state: AssessmentFlowState):
        self.flow_state = flow_state

    async def generate_app_on_page_data(
        self,
        application_data: Dict[str, Any],
        tech_debt_analysis: Dict[str, Any],
        sixr_decisions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive "App on a Page" assessment data."""
        try:
            app_id = application_data.get("application_id")
            app_name = application_data.get("application_name", "Unknown Application")

            logger.info(f"Generating App on a Page for {app_name}")

            # Build the comprehensive assessment
            app_on_page = {
                "application_id": app_id,
                "application_name": app_name,
                "assessment_metadata": {
                    "assessment_flow_id": self.flow_state.flow_id,
                    "engagement_id": self.flow_state.engagement_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "assessment_version": "1.0",
                },
                # Application overview
                "application_overview": {
                    "description": application_data.get("description", ""),
                    "technology_stack": application_data.get("technology_stack", []),
                    "business_criticality": application_data.get(
                        "business_criticality", "medium"
                    ),
                    "complexity_score": application_data.get("complexity_score", 0.0),
                    "user_count": application_data.get("user_count", "unknown"),
                    "data_sensitivity": application_data.get(
                        "data_sensitivity", "medium"
                    ),
                },
                # Technical debt assessment
                "technical_debt": self._format_tech_debt_summary(tech_debt_analysis),
                # 6R strategy recommendations
                "sixr_recommendations": self._format_sixr_summary(sixr_decisions),
                # Architecture assessment
                "architecture_assessment": self._generate_architecture_assessment(
                    application_data
                ),
                # Migration roadmap
                "migration_roadmap": self._generate_migration_roadmap(sixr_decisions),
                # Risk assessment
                "risk_assessment": self._generate_risk_assessment(
                    application_data, tech_debt_analysis, sixr_decisions
                ),
                # Cost and effort estimates
                "cost_effort_estimates": self._generate_cost_estimates(sixr_decisions),
                # Recommendations and next steps
                "recommendations": self._generate_recommendations(
                    application_data, tech_debt_analysis, sixr_decisions
                ),
            }

            logger.info(f"Successfully generated App on a Page for {app_name}")
            return app_on_page

        except Exception as e:
            logger.error(f"Failed to generate App on a Page: {str(e)}")
            return {
                "error": f"Failed to generate assessment: {str(e)}",
                "application_id": application_data.get("application_id"),
                "application_name": application_data.get("application_name", "Unknown"),
            }

    async def generate_assessment_summary(self) -> Dict[str, Any]:
        """Generate overall assessment summary across all applications."""
        try:
            logger.info("Generating overall assessment summary")

            summary = {
                "assessment_metadata": {
                    "flow_id": self.flow_state.flow_id,
                    "engagement_id": self.flow_state.engagement_id,
                    "client_account_id": self.flow_state.client_account_id,
                    "generated_at": datetime.utcnow().isoformat(),
                    "overall_progress": self.flow_state.overall_progress,
                    "current_phase": self.flow_state.current_phase,
                },
                # High-level statistics
                "portfolio_statistics": {
                    "total_applications": len(self.flow_state.application_components),
                    "total_components": sum(
                        len(app.get("components", []))
                        for app in self.flow_state.application_components
                    ),
                    "total_sixr_decisions": len(self.flow_state.sixr_decisions),
                    "architecture_standards_count": len(
                        self.flow_state.architecture_standards
                    ),
                },
                # Strategy distribution across portfolio
                "strategy_distribution": self._calculate_portfolio_strategy_distribution(),
                # Risk profile
                "risk_profile": self._calculate_portfolio_risk_profile(),
                # Effort estimates
                "effort_estimates": self._calculate_portfolio_effort_estimates(),
                # Key insights and recommendations
                "key_insights": self._generate_portfolio_insights(),
                # Next steps for planning
                "planning_readiness": self._assess_planning_readiness(),
            }

            logger.info("Successfully generated assessment summary")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate assessment summary: {str(e)}")
            return {
                "error": f"Failed to generate summary: {str(e)}",
                "flow_id": self.flow_state.flow_id,
            }

    def _format_tech_debt_summary(
        self, tech_debt_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format technical debt analysis for App on a Page."""
        return {
            "overall_score": tech_debt_analysis.get("overall_score", 0.0),
            "debt_categories": tech_debt_analysis.get("categories", {}),
            "critical_issues": tech_debt_analysis.get("critical_issues", []),
            "remediation_priority": tech_debt_analysis.get("priority_items", []),
            "estimated_remediation_effort": tech_debt_analysis.get(
                "remediation_effort", "unknown"
            ),
        }

    def _format_sixr_summary(
        self, sixr_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format 6R decisions for App on a Page."""
        if not sixr_decisions:
            return {"strategies": [], "distribution": {}, "confidence": 0.0}

        strategies = []
        distribution = {}
        total_confidence = 0.0

        for decision in sixr_decisions:
            strategy = decision.get("sixr_strategy")
            if strategy:
                distribution[strategy] = distribution.get(strategy, 0) + 1
                total_confidence += decision.get("confidence", 0.0)

                strategies.append(
                    {
                        "component": decision.get("component_name"),
                        "strategy": strategy,
                        "confidence": decision.get("confidence"),
                        "reasoning": (
                            decision.get("reasoning", "")[:200] + "..."
                            if len(decision.get("reasoning", "")) > 200
                            else decision.get("reasoning", "")
                        ),
                        "estimated_effort": decision.get("estimated_effort"),
                        "risk_level": decision.get("risk_level"),
                    }
                )

        avg_confidence = (
            total_confidence / len(sixr_decisions) if sixr_decisions else 0.0
        )

        return {
            "strategies": strategies,
            "distribution": distribution,
            "average_confidence": avg_confidence,
            "total_decisions": len(sixr_decisions),
        }

    def _generate_architecture_assessment(
        self, application_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate architecture assessment section."""
        return {
            "current_architecture": {
                "pattern": application_data.get("architecture_pattern", "monolithic"),
                "scalability": application_data.get("scalability_rating", "medium"),
                "maintainability": application_data.get(
                    "maintainability_rating", "medium"
                ),
                "performance": application_data.get("performance_rating", "medium"),
            },
            "cloud_readiness": {
                "score": application_data.get("cloud_readiness_score", 5.0),
                "blockers": application_data.get("cloud_readiness_blockers", []),
                "enablers": application_data.get("cloud_readiness_enablers", []),
            },
            "modernization_opportunities": application_data.get(
                "modernization_opportunities", []
            ),
        }

    def _generate_migration_roadmap(
        self, sixr_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate migration roadmap based on 6R decisions."""
        phases = {"phase_1": [], "phase_2": [], "phase_3": []}

        # Simple phasing logic based on risk and dependencies
        for decision in sixr_decisions:
            risk = decision.get("risk_level", "medium")
            strategy = decision.get("sixr_strategy")

            if strategy == "rehost" or risk == "low":
                phases["phase_1"].append(decision.get("component_name"))
            elif risk == "medium":
                phases["phase_2"].append(decision.get("component_name"))
            else:
                phases["phase_3"].append(decision.get("component_name"))

        return {
            "phases": phases,
            "estimated_duration": "6-12 months",  # Placeholder
            "dependencies": [],
            "critical_path": phases["phase_3"],
        }

    def _generate_risk_assessment(
        self,
        application_data: Dict[str, Any],
        tech_debt_analysis: Dict[str, Any],
        sixr_decisions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive risk assessment."""
        high_risk_decisions = [
            d for d in sixr_decisions if d.get("risk_level") == "high"
        ]

        return {
            "overall_risk": "medium",  # Should be calculated
            "risk_factors": [
                "Technical debt score above threshold",
                "Complex component dependencies",
                "High business criticality",
            ],
            "high_risk_components": [
                d.get("component_name") for d in high_risk_decisions
            ],
            "mitigation_strategies": [
                "Implement comprehensive testing strategy",
                "Plan for gradual rollout",
                "Establish rollback procedures",
            ],
        }

    def _generate_cost_estimates(
        self, sixr_decisions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate cost and effort estimates."""
        effort_mapping = {"low": 1, "medium": 3, "high": 5, "very_high": 8}

        total_effort = 0
        for decision in sixr_decisions:
            effort = decision.get("estimated_effort", "medium")
            total_effort += effort_mapping.get(effort, 3)

        return {
            "estimated_effort_weeks": total_effort,
            "estimated_cost_range": f"${total_effort * 10000}-${total_effort * 20000}",
            "effort_breakdown": {
                strategy: sum(
                    effort_mapping.get(d.get("estimated_effort", "medium"), 3)
                    for d in sixr_decisions
                    if d.get("sixr_strategy") == strategy
                )
                for strategy in set(
                    d.get("sixr_strategy")
                    for d in sixr_decisions
                    if d.get("sixr_strategy")
                )
            },
        }

    def _generate_recommendations(
        self,
        application_data: Dict[str, Any],
        tech_debt_analysis: Dict[str, Any],
        sixr_decisions: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Add tech debt recommendations
        debt_score = tech_debt_analysis.get("overall_score", 0.0)
        if debt_score > 7.0:
            recommendations.append("Address critical technical debt before migration")

        # Add strategy-specific recommendations
        strategy_dist = {}
        for decision in sixr_decisions:
            strategy = decision.get("sixr_strategy")
            if strategy:
                strategy_dist[strategy] = strategy_dist.get(strategy, 0) + 1

        if strategy_dist.get("rebuild", 0) > 0:
            recommendations.append(
                "Consider modern architecture patterns for rebuild components"
            )

        if strategy_dist.get("retain", 0) > len(sixr_decisions) * 0.5:
            recommendations.append(
                "Review retain decisions to ensure migration opportunities aren't missed"
            )

        recommendations.extend(
            [
                "Establish comprehensive testing strategy",
                "Plan for user training and change management",
                "Implement monitoring and observability early",
            ]
        )

        return recommendations

    def _calculate_portfolio_strategy_distribution(self) -> Dict[str, Any]:
        """Calculate strategy distribution across the entire portfolio."""
        # Implementation for portfolio-level calculations
        return {}

    def _calculate_portfolio_risk_profile(self) -> Dict[str, Any]:
        """Calculate risk profile across the entire portfolio."""
        return {"overall_risk": "medium", "risk_factors": []}

    def _calculate_portfolio_effort_estimates(self) -> Dict[str, Any]:
        """Calculate effort estimates across the entire portfolio."""
        return {"total_effort_weeks": 0, "total_cost_estimate": "$0"}

    def _generate_portfolio_insights(self) -> List[str]:
        """Generate insights across the entire portfolio."""
        return ["Portfolio analysis insights would go here"]

    def _assess_planning_readiness(self) -> Dict[str, Any]:
        """Assess readiness for planning phase."""
        return {
            "ready_for_planning": True,
            "blocking_issues": [],
            "recommendations_before_planning": [],
        }
