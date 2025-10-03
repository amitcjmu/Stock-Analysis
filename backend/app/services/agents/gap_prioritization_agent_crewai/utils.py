"""
Gap Prioritization Agent - Utility Methods Module
Contains helper methods for gap analysis and resource estimation.
"""

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class UtilsMixin:
    """Mixin for utility methods"""

    def _calculate_gap_priority(  # noqa: C901
        self, gap: Dict[str, Any], context: Dict[str, Any]
    ) -> Tuple[float, int]:
        """Calculate priority score and level for a gap"""
        score = 0.0

        # Business impact scoring (0-40 points)
        impact = gap.get("business_impact", "medium")
        if impact == "critical":
            score += 40
        elif impact == "high":
            score += 30
        elif impact == "medium":
            score += 20
        else:
            score += 10

        # Strategy relevance scoring (0-30 points)
        affected_strategies = gap.get("affects_strategies", [])
        primary_strategy = context.get("primary_migration_strategy", "rehost")

        if primary_strategy in affected_strategies:
            score += 30
        elif len(affected_strategies) > 3:
            score += 25
        elif len(affected_strategies) > 1:
            score += 15
        else:
            score += 5

        # Decision blocking scoring (0-20 points)
        if gap.get("blocks_decision", False):
            score += 20
        elif gap.get("impacts_timeline", False):
            score += 15
        elif gap.get("affects_budget", False):
            score += 10
        else:
            score += 5

        # Collection feasibility scoring (0-10 points, inverse)
        difficulty = gap.get("collection_difficulty", "medium")
        if difficulty == "easy":
            score += 10
        elif difficulty == "medium":
            score += 7
        elif difficulty == "hard":
            score += 4
        else:  # very_hard
            score += 2

        # Determine priority level based on score
        if score >= 80:
            priority = 1  # Critical
        elif score >= 60:
            priority = 2  # High
        elif score >= 40:
            priority = 3  # Medium
        else:
            priority = 4  # Low

        return score, priority

    def _recommend_collection_method(
        self, gap: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recommend collection method for a gap"""
        category = gap.get("category", "unknown")
        automation_tier = context.get("automation_tier", "tier_2")

        # Base recommendations by category
        collection_methods = {
            "infrastructure": {
                "primary": "automated_discovery",
                "fallback": "infrastructure_survey",
                "tools": ["discovery_agent", "cmdb_import", "cloud_api"],
            },
            "application": {
                "primary": "sme_interview",
                "fallback": "application_questionnaire",
                "tools": ["app_profiler", "code_analyzer", "dependency_scanner"],
            },
            "operational": {
                "primary": "operational_survey",
                "fallback": "manual_documentation",
                "tools": ["monitoring_api", "ticketing_integration", "cost_reports"],
            },
            "dependencies": {
                "primary": "dependency_analysis",
                "fallback": "architecture_review",
                "tools": ["network_scanner", "flow_analyzer", "integration_mapper"],
            },
        }

        method_config = collection_methods.get(
            category,
            {
                "primary": "manual_collection",
                "fallback": "stakeholder_interview",
                "tools": ["manual_forms"],
            },
        )

        # Adjust based on automation tier
        if automation_tier in ["tier_3", "tier_4"]:
            # More manual methods for lower automation tiers
            method_config["primary"] = method_config["fallback"]

        return {
            "recommended_method": method_config["primary"],
            "alternative_method": method_config["fallback"],
            "available_tools": method_config["tools"],
            "automation_feasible": automation_tier in ["tier_1", "tier_2"],
            "requires_manual_input": category in ["application", "operational"],
        }

    def _estimate_collection_effort(self, gap: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate effort required to collect missing attribute"""
        difficulty = gap.get("collection_difficulty", "medium")
        category = gap.get("category", "unknown")

        # Base effort estimates (in hours)
        effort_matrix = {
            "easy": {"min": 0.5, "max": 2, "avg": 1},
            "medium": {"min": 2, "max": 8, "avg": 4},
            "hard": {"min": 8, "max": 24, "avg": 16},
            "very_hard": {"min": 24, "max": 80, "avg": 40},
        }

        base_effort = effort_matrix.get(difficulty, effort_matrix["medium"])

        # Adjust for category complexity
        category_multipliers = {
            "infrastructure": 0.8,  # Usually more automated
            "application": 1.2,  # Requires more human input
            "operational": 1.0,  # Standard effort
            "dependencies": 1.5,  # Most complex to gather
        }

        multiplier = category_multipliers.get(category, 1.0)

        return {
            "estimated_hours": {
                "minimum": base_effort["min"] * multiplier,
                "maximum": base_effort["max"] * multiplier,
                "average": base_effort["avg"] * multiplier,
            },
            "confidence_level": "medium",
            "factors_considered": [
                f"Collection difficulty: {difficulty}",
                f"Attribute category: {category}",
                "Availability of automation tools",
                "Required stakeholder involvement",
            ],
        }

    def _generate_justification(self, gap: Dict[str, Any], priority: int) -> str:
        """Generate business justification for gap priority"""
        attribute = gap.get("attribute", "unknown")
        impact = gap.get("business_impact", "medium")
        strategies = gap.get("affects_strategies", [])

        justifications = {
            1: f"CRITICAL: Missing '{attribute}' blocks migration strategy selection. "
            f"This {impact}-impact attribute affects {len(strategies)} migration strategies "
            f"({', '.join(strategies)}). Immediate collection required to proceed with migration planning.",
            2: f"HIGH: Missing '{attribute}' significantly reduces migration confidence. "
            f"This {impact}-impact attribute is essential for {', '.join(strategies)} strategies. "
            f"Collection recommended within current sprint to maintain project timeline.",
            3: f"MEDIUM: Missing '{attribute}' impacts migration optimization opportunities. "
            f"While not blocking, this attribute improves accuracy for {', '.join(strategies)} strategies. "
            f"Schedule collection based on resource availability.",
            4: f"LOW: Missing '{attribute}' provides additional context but is not critical. "
            f"Consider collecting if resources permit or combine with other data gathering activities.",
        }

        return justifications.get(priority, justifications[4])

    def _generate_collection_strategy(
        self, prioritized_gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate overall collection strategy"""
        critical_gaps = [g for g in prioritized_gaps if g.get("priority_level") == 1]
        high_gaps = [g for g in prioritized_gaps if g.get("priority_level") == 2]

        # Safely calculate critical effort with default values
        critical_effort = 0
        for gap in critical_gaps:
            effort = gap.get("estimated_effort", {})
            avg_effort = effort.get("average", 0) or 0
            critical_effort += avg_effort

        strategy = {
            "approach": "phased_collection",
            "phases": [
                {
                    "phase": 1,
                    "name": "Critical Gap Resolution",
                    "gaps_count": len(critical_gaps),
                    "estimated_duration_hours": critical_effort,
                    "objectives": [
                        "Unblock migration strategy selection",
                        "Enable confidence scoring",
                        "Support go/no-go decisions",
                    ],
                },
                {
                    "phase": 2,
                    "name": "High Priority Collection",
                    "gaps_count": len(high_gaps),
                    "estimated_duration_hours": sum(
                        g.get("estimated_effort", {}).get("average", 0) or 0
                        for g in high_gaps
                    ),
                    "objectives": [
                        "Improve strategy recommendations",
                        "Reduce migration risks",
                        "Enable detailed planning",
                    ],
                },
            ],
            "quick_wins": [
                g.get("attribute", "")
                for g in prioritized_gaps
                if g.get("collection_recommendation", {}).get("recommended_method")
                == "automated_discovery"
                and g.get("priority_level", 99) <= 2
            ][:5],
            "parallel_activities": self._identify_parallel_activities(prioritized_gaps),
            "success_metrics": [
                f"Close {len(critical_gaps)} critical gaps",
                "Achieve >85% critical attribute coverage",
                "Improve migration confidence score by >20%",
            ],
        }

        return strategy

    def _calculate_resource_requirements(
        self, prioritized_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate resource requirements for gap closure"""
        # Safely calculate total effort with default values
        total_effort = 0
        critical_effort = 0
        for gap in prioritized_gaps:
            effort = gap.get("estimated_effort", {})
            avg_effort = effort.get("average", 0) or 0
            total_effort += avg_effort

            if gap.get("priority_level") == 1:
                critical_effort += avg_effort

        # Identify required roles
        roles_needed = set()
        for gap in prioritized_gaps:
            category = gap.get("category", "")
            if category == "infrastructure":
                roles_needed.add("infrastructure_engineer")
            elif category == "application":
                roles_needed.add("application_architect")
                roles_needed.add("business_analyst")
            elif category == "operational":
                roles_needed.add("operations_manager")
            elif category == "dependencies":
                roles_needed.add("solution_architect")

        return {
            "total_effort_hours": round(total_effort, 1),
            "critical_effort_hours": round(critical_effort, 1),
            "recommended_team_size": max(2, min(len(roles_needed), 5)),
            "required_roles": list(roles_needed),
            "estimated_duration_weeks": round(
                total_effort / (40 * len(roles_needed)) if roles_needed else 0, 1
            ),
            "resource_allocation": {
                "automated_collection": "30%",
                "manual_collection": "50%",
                "validation_review": "20%",
            },
        }

    def _identify_parallel_activities(
        self, prioritized_gaps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify activities that can be done in parallel"""
        parallel_activities = []

        # Group by collection method
        method_groups = {}
        for gap in prioritized_gaps[:10]:  # Focus on top 10 gaps
            method = gap.get("collection_recommendation", {}).get("recommended_method")
            if method:
                if method not in method_groups:
                    method_groups[method] = []
                method_groups[method].append(gap.get("attribute", "unknown"))

        for method, attributes in method_groups.items():
            if len(attributes) > 1:
                parallel_activities.append(
                    {
                        "activity": f"Batch {method}",
                        "attributes": attributes,
                        "efficiency_gain": f"{len(attributes)*15}% time saving",
                    }
                )

        return parallel_activities
