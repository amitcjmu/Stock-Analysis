"""
Impact Calculator Tool - Calculates business impact of data gaps
"""

import logging
from typing import Any, Dict, List

from app.services.tools.base_tool import AsyncBaseDiscoveryTool
from app.services.tools.registry import ToolMetadata

from .constants import BASE_EFFORT_HOURS

logger = logging.getLogger(__name__)


class ImpactCalculatorTool(AsyncBaseDiscoveryTool):
    """Calculates business impact of data gaps"""

    name: str = "impact_calculator"
    description: str = (
        "Calculate business and technical impact of missing critical attributes"
    )

    @classmethod
    def tool_metadata(cls) -> ToolMetadata:
        """Return metadata for tool registration"""
        return ToolMetadata(
            name="impact_calculator",
            description="Calculate business and technical impact of missing critical attributes",
            tool_class=cls,
            categories=["gap_analysis", "impact_analysis"],
            required_params=["gaps", "migration_context"],
            optional_params=[],
            context_aware=True,
            async_tool=True,
        )

    async def arun(
        self, gaps: List[Dict[str, Any]], migration_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate impact of gaps on migration planning and execution"""
        try:
            self.log_with_context("info", f"Calculating impact for {len(gaps)} gaps")

            impact_results = {
                "migration_confidence_impact": {},
                "timeline_impact": {},
                "cost_impact": {},
                "risk_assessment": {},
                "strategy_viability": {},
                "recommendations": [],
            }

            # Calculate confidence impact per strategy
            for strategy in [
                "rehost",
                "replatform",
                "refactor",
                "repurchase",
                "retire",
                "retain",
            ]:
                impact_results["migration_confidence_impact"][
                    strategy
                ] = self._calculate_strategy_confidence(gaps, strategy)

            # Calculate timeline impact
            impact_results["timeline_impact"] = self._calculate_timeline_impact(
                gaps, migration_context
            )

            # Calculate cost impact
            impact_results["cost_impact"] = self._calculate_cost_impact(
                gaps, migration_context
            )

            # Assess risks
            impact_results["risk_assessment"] = self._assess_migration_risks(
                gaps, migration_context
            )

            # Determine strategy viability
            impact_results["strategy_viability"] = self._assess_strategy_viability(
                impact_results["migration_confidence_impact"]
            )

            # Generate recommendations
            impact_results["recommendations"] = self._generate_impact_recommendations(
                impact_results
            )

            self.log_with_context("info", "Impact calculation completed")
            return impact_results

        except Exception as e:
            self.log_with_context("error", f"Error in impact calculation: {e}")
            return {"error": str(e)}

    def _calculate_strategy_confidence(
        self, gaps: List[Dict[str, Any]], strategy: str
    ) -> Dict[str, Any]:
        """Calculate confidence impact for a specific migration strategy"""
        base_confidence = 100.0
        critical_gaps = 0
        high_gaps = 0

        for gap in gaps:
            if strategy in gap.get("affects_strategies", []):
                if gap["priority"] == "critical":
                    base_confidence -= 15
                    critical_gaps += 1
                elif gap["priority"] == "high":
                    base_confidence -= 10
                    high_gaps += 1
                elif gap["priority"] == "medium":
                    base_confidence -= 5
                else:
                    base_confidence -= 2

        return {
            "confidence_score": max(0, base_confidence),
            "critical_gaps_affecting": critical_gaps,
            "high_gaps_affecting": high_gaps,
            "recommendation_viable": base_confidence >= 60,
        }

    def _calculate_timeline_impact(
        self, gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate impact on migration timeline"""
        total_collection_hours = 0
        blocking_gaps = []

        for gap in gaps:
            hours = BASE_EFFORT_HOURS.get(gap.get("collection_difficulty", "medium"), 8)
            total_collection_hours += hours

            if gap["priority"] == "critical":
                blocking_gaps.append(gap["attribute"])

        # Calculate delay in weeks (assuming 40-hour work week, 2 people)
        estimated_delay_weeks = total_collection_hours / (40 * 2)

        return {
            "estimated_collection_hours": total_collection_hours,
            "estimated_delay_weeks": round(estimated_delay_weeks, 1),
            "blocking_gaps": blocking_gaps,
            "timeline_risk": (
                "high"
                if blocking_gaps
                else "medium"
                if estimated_delay_weeks > 2
                else "low"
            ),
            "mitigation": (
                "Parallel collection activities recommended"
                if estimated_delay_weeks > 1
                else "Standard process"
            ),
        }

    def _calculate_cost_impact(
        self, gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate cost impact of gaps"""
        hourly_rate = context.get("hourly_rate", 150)  # Default hourly rate

        collection_hours = 0
        rework_risk_hours = 0

        for gap in gaps:
            # Collection cost
            collection_hours += BASE_EFFORT_HOURS.get(
                gap.get("collection_difficulty", "medium"), 8
            )

            # Risk of rework if gap not addressed
            if gap["priority"] in ["critical", "high"]:
                rework_risk_hours += 40  # Potential rework hours

        collection_cost = collection_hours * hourly_rate
        potential_rework_cost = rework_risk_hours * hourly_rate * 0.3  # 30% probability

        return {
            "data_collection_cost": collection_cost,
            "potential_rework_cost": potential_rework_cost,
            "total_cost_impact": collection_cost + potential_rework_cost,
            "roi_justification": "Investing in data collection reduces migration risks and rework",
            "cost_optimization": "Automate easy/medium difficulty collections to reduce costs",
        }

    def _assess_migration_risks(
        self, gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess migration risks due to gaps"""
        risks = {
            "technical_risks": [],
            "business_risks": [],
            "compliance_risks": [],
            "operational_risks": [],
        }

        for gap in gaps:
            if gap["attribute"] in [
                "technology_stack",
                "application_dependencies",
                "database_dependencies",
            ]:
                risks["technical_risks"].append(
                    {
                        "risk": f"Unknown {gap['attribute']} may lead to incompatible migration approach",
                        "severity": (
                            "high" if gap["priority"] == "critical" else "medium"
                        ),
                    }
                )

            if gap["attribute"] in ["criticality_level", "owner", "cost_center"]:
                risks["business_risks"].append(
                    {
                        "risk": f"Missing {gap['attribute']} affects business prioritization",
                        "severity": "medium",
                    }
                )

            if gap["attribute"] in ["data_classification", "compliance_scope"]:
                risks["compliance_risks"].append(
                    {
                        "risk": f"Unknown {gap['attribute']} may violate compliance requirements",
                        "severity": "high",
                    }
                )

            if gap["attribute"] in ["backup_strategy", "monitoring_status"]:
                risks["operational_risks"].append(
                    {
                        "risk": f"Missing {gap['attribute']} impacts operational continuity",
                        "severity": "medium",
                    }
                )

        # Overall risk level
        total_risks = sum(len(r) for r in risks.values())
        high_severity_risks = sum(
            1
            for r_list in risks.values()
            for r in r_list
            if r.get("severity") == "high"
        )

        overall_risk = (
            "high"
            if high_severity_risks > 2
            else "medium"
            if total_risks > 5
            else "low"
        )

        return {
            **risks,
            "total_risks_identified": total_risks,
            "high_severity_risks": high_severity_risks,
            "overall_risk_level": overall_risk,
            "risk_mitigation_priority": "Address compliance and technical risks first",
        }

    def _assess_strategy_viability(
        self, confidence_scores: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess viability of each migration strategy based on confidence"""
        viability = {}

        for strategy, scores in confidence_scores.items():
            confidence = scores["confidence_score"]

            if confidence >= 80:
                status = "recommended"
                action = "Proceed with confidence"
            elif confidence >= 60:
                status = "viable_with_gaps"
                action = "Address critical gaps before proceeding"
            elif confidence >= 40:
                status = "risky"
                action = "Significant gap closure required"
            else:
                status = "not_recommended"
                action = "Major data collection effort needed"

            viability[strategy] = {
                "status": status,
                "confidence": confidence,
                "action": action,
                "gaps_to_address": scores["critical_gaps_affecting"]
                + scores["high_gaps_affecting"],
            }

        # Identify best strategy
        best_strategy = max(
            confidence_scores.items(), key=lambda x: x[1]["confidence_score"]
        )[0]

        return {
            "strategy_status": viability,
            "recommended_strategy": best_strategy,
            "alternative_strategies": [
                s
                for s, v in viability.items()
                if v["status"] in ["recommended", "viable_with_gaps"]
                and s != best_strategy
            ],
        }

    def _generate_impact_recommendations(
        self, impact_results: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on impact analysis"""
        recommendations = []

        # Timeline recommendations
        if impact_results["timeline_impact"]["timeline_risk"] == "high":
            recommendations.append(
                "URGENT: Address blocking gaps immediately to prevent migration delays. "
                "Consider dedicated gap resolution sprint."
            )

        # Cost recommendations
        if impact_results["cost_impact"]["total_cost_impact"] > 50000:
            recommendations.append(
                "Consider phased gap resolution to spread costs. "
                "Prioritize gaps affecting recommended migration strategy."
            )

        # Risk recommendations
        if impact_results["risk_assessment"]["overall_risk_level"] == "high":
            recommendations.append(
                "High risk profile detected. Implement risk mitigation plan "
                "focusing on compliance and technical gaps first."
            )

        # Strategy recommendations
        best_strategy = impact_results["strategy_viability"]["recommended_strategy"]
        if (
            impact_results["migration_confidence_impact"][best_strategy][
                "confidence_score"
            ]
            < 80
        ):
            recommendations.append(
                f"Recommended strategy '{best_strategy}' has reduced confidence. "
                f"Focus gap resolution on attributes affecting this strategy."
            )

        return recommendations
