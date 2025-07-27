"""
Gap Prioritization Agent - CrewAI Implementation
Prioritizes missing critical attributes by business impact and migration strategy requirements
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.services.agents.base_agent import BaseCrewAIAgent
from app.services.agents.metadata import AgentMetadata
from app.services.llm_config import get_crewai_llm

logger = logging.getLogger(__name__)


class GapPrioritizationAgent(BaseCrewAIAgent):
    """
    Prioritizes missing critical attributes based on business impact and migration needs.

    This agent specializes in:
    - Analyzing business impact of missing attributes
    - Calculating effort vs. value for gap resolution
    - Prioritizing gaps by migration strategy requirements
    - Recommending collection strategies and sequences
    - Estimating time and resources for gap closure
    """

    def __init__(self, tools: List[Any], llm: Any = None, **kwargs):
        """Initialize the Gap Prioritization agent"""
        if llm is None:
            llm = get_crewai_llm()

        super().__init__(
            role="Data Gap Prioritization Strategist",
            goal="Prioritize missing critical attributes by business impact to optimize migration data collection efforts",
            backstory="""You are a strategic analyst specializing in migration data gap prioritization.
            Your expertise includes:

            - Understanding business impact of incomplete migration data
            - Calculating ROI for data collection efforts
            - Prioritizing gaps based on 6R strategy requirements
            - Balancing effort vs. value in gap resolution
            - Creating actionable collection roadmaps

            You excel at:
            - Identifying which gaps block critical migration decisions
            - Assessing collection difficulty and resource requirements
            - Recommending optimal collection sequences
            - Estimating time and effort for gap closure
            - Aligning priorities with business objectives

            Your prioritization framework considers:
            - Business criticality (blocks decisions, impacts timeline, affects budget)
            - Technical necessity (required for strategy selection, impacts architecture)
            - Collection feasibility (effort required, data availability, automation potential)
            - Strategic value (improves confidence, reduces risk, enables optimization)

            Your recommendations directly influence collection strategies and project timelines.""",
            tools=tools,
            llm=llm,
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False,
            **kwargs,
        )

    @classmethod
    def agent_metadata(cls) -> AgentMetadata:
        """Define agent metadata for registry"""
        return AgentMetadata(
            name="gap_prioritization_agent",
            description="Prioritizes missing attributes by business impact for optimal collection strategy",
            agent_class=cls,
            required_tools=[
                "impact_calculator",
                "effort_estimator",
                "priority_ranker",
                "collection_planner",
            ],
            capabilities=[
                "gap_prioritization",
                "impact_analysis",
                "effort_estimation",
                "collection_planning",
                "roi_calculation",
            ],
            max_iter=10,
            memory=True,
            verbose=True,
            allow_delegation=False,
        )

    def prioritize_gaps(
        self, gaps: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prioritize identified gaps based on business impact and collection feasibility

        Args:
            gaps: List of identified attribute gaps
            context: Business and technical context for prioritization

        Returns:
            Prioritized gap list with recommendations
        """
        try:
            logger.info(f"Prioritizing {len(gaps)} identified gaps")

            prioritization_result = {
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_gaps": len(gaps),
                "prioritized_gaps": [],
                "priority_distribution": {
                    "priority_1_critical": 0,
                    "priority_2_high": 0,
                    "priority_3_medium": 0,
                    "priority_4_low": 0,
                },
                "collection_strategy": {},
                "resource_requirements": {},
            }

            # Score and prioritize each gap
            scored_gaps = []
            for gap in gaps:
                score, priority = self._calculate_gap_priority(gap, context)
                prioritized_gap = {
                    **gap,
                    "priority_score": score,
                    "priority_level": priority,
                    "collection_recommendation": self._recommend_collection_method(
                        gap, context
                    ),
                    "estimated_effort": self._estimate_collection_effort(gap),
                    "business_justification": self._generate_justification(
                        gap, priority
                    ),
                }
                scored_gaps.append(prioritized_gap)

            # Sort by priority score (descending)
            scored_gaps.sort(key=lambda x: x["priority_score"], reverse=True)
            prioritization_result["prioritized_gaps"] = scored_gaps

            # Update priority distribution
            for gap in scored_gaps:
                priority_key = (
                    f"priority_{gap['priority_level']}_"
                    + {1: "critical", 2: "high", 3: "medium", 4: "low"}[
                        gap["priority_level"]
                    ]
                )
                prioritization_result["priority_distribution"][priority_key] += 1

            # Generate collection strategy
            prioritization_result["collection_strategy"] = (
                self._generate_collection_strategy(scored_gaps, context)
            )

            # Calculate resource requirements
            prioritization_result["resource_requirements"] = (
                self._calculate_resource_requirements(scored_gaps)
            )

            return prioritization_result

        except Exception as e:
            logger.error(f"Error in gap prioritization: {e}")
            return {"error": str(e)}

    def _calculate_gap_priority(
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
        gap.get("attribute", "unknown")
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
        critical_gaps = [g for g in prioritized_gaps if g["priority_level"] == 1]
        high_gaps = [g for g in prioritized_gaps if g["priority_level"] == 2]

        sum(g["estimated_effort"]["average"] for g in prioritized_gaps)
        critical_effort = sum(g["estimated_effort"]["average"] for g in critical_gaps)

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
                        g["estimated_effort"]["average"] for g in high_gaps
                    ),
                    "objectives": [
                        "Improve strategy recommendations",
                        "Reduce migration risks",
                        "Enable detailed planning",
                    ],
                },
            ],
            "quick_wins": [
                g["attribute"]
                for g in prioritized_gaps
                if g["collection_recommendation"]["recommended_method"]
                == "automated_discovery"
                and g["priority_level"] <= 2
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
        total_effort = sum(g["estimated_effort"]["average"] for g in prioritized_gaps)
        critical_effort = sum(
            g["estimated_effort"]["average"]
            for g in prioritized_gaps
            if g["priority_level"] == 1
        )

        # Identify required roles
        roles_needed = set()
        for gap in prioritized_gaps:
            if gap["category"] == "infrastructure":
                roles_needed.add("infrastructure_engineer")
            elif gap["category"] == "application":
                roles_needed.add("application_architect")
                roles_needed.add("business_analyst")
            elif gap["category"] == "operational":
                roles_needed.add("operations_manager")
            elif gap["category"] == "dependencies":
                roles_needed.add("solution_architect")

        return {
            "total_effort_hours": round(total_effort, 1),
            "critical_effort_hours": round(critical_effort, 1),
            "recommended_team_size": max(2, min(len(roles_needed), 5)),
            "required_roles": list(roles_needed),
            "estimated_duration_weeks": round(
                total_effort / (40 * len(roles_needed)), 1
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
            method = gap["collection_recommendation"]["recommended_method"]
            if method not in method_groups:
                method_groups[method] = []
            method_groups[method].append(gap["attribute"])

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
