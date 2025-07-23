"""
Business Context Analysis Optimization - B2.4
ADCS AI Analysis & Intelligence Service

Questionnaire targeting and optimization logic.

Built by: Agent Team B2 (AI Analysis & Intelligence)
"""

import logging
from typing import Any, Dict, List, Optional

from .enums import BusinessDomain, StakeholderRole
from .models import BusinessContext, QuestionnaireTarget

logger = logging.getLogger(__name__)


class QuestionnaireOptimizer:
    """Handles questionnaire targeting and optimization logic"""

    def __init__(self, domain_configurations: Dict[BusinessDomain, Dict[str, Any]]):
        """Initialize with domain configurations"""
        self.domain_configurations = domain_configurations

    def create_questionnaire_target(
        self,
        gap: Dict[str, Any],
        business_context: BusinessContext,
        available_stakeholders: List[Dict[str, Any]],
    ) -> Optional[QuestionnaireTarget]:
        """Create a questionnaire target for a specific gap"""
        try:
            gap_category = gap.get("category", "general")
            gap_priority = gap.get("priority", 3)

            # Determine appropriate stakeholders
            target_stakeholders = self._determine_target_stakeholders(
                gap_category, business_context
            )

            # Filter by available stakeholders
            available_roles = [
                StakeholderRole(s.get("role", "").lower().replace(" ", "_"))
                for s in available_stakeholders
                if s.get("role")
            ]
            target_stakeholders = [
                role for role in target_stakeholders if role in available_roles
            ]

            if not target_stakeholders:
                return None

            # Determine complexity and effort
            complexity = self._determine_question_complexity(gap, business_context)
            effort_minutes = self._estimate_effort_minutes(
                gap, complexity, business_context
            )

            return QuestionnaireTarget(
                target_stakeholders=target_stakeholders,
                priority_level=self._map_gap_priority(gap_priority),
                complexity_level=complexity,
                estimated_effort_minutes=effort_minutes,
                business_justification=gap.get(
                    "business_justification", "Required for migration planning"
                ),
                success_metrics=[
                    f"Fill {gap.get('attribute_name', 'missing')} data gap",
                    "Improve 6R strategy confidence",
                    "Enable accurate migration planning",
                ],
            )

        except Exception as e:
            logger.error(f"Error creating questionnaire target: {e}")
            return None

    def optimize_delivery_sequence(
        self, targets: List[QuestionnaireTarget], business_context: BusinessContext
    ) -> List[Dict[str, Any]]:
        """Optimize questionnaire delivery sequence"""
        # Sort by priority and complexity
        sorted_targets = sorted(
            targets,
            key=lambda t: (
                {"critical": 1, "high": 2, "medium": 3, "low": 4}[t.priority_level],
                {"basic": 1, "intermediate": 2, "advanced": 3}[t.complexity_level],
            ),
        )

        sequence = []
        for i, target in enumerate(sorted_targets):
            sequence.append(
                {
                    "sequence_order": i + 1,
                    "target_id": f"target_{i+1}",
                    "stakeholders": [role.value for role in target.target_stakeholders],
                    "priority": target.priority_level,
                    "estimated_duration": target.estimated_effort_minutes,
                    "dependencies": [],  # Could be enhanced with actual dependencies
                    "recommended_timing": self._calculate_optimal_timing(
                        i, business_context
                    ),
                }
            )

        return sequence

    def generate_communication_strategy(
        self, targets: List[QuestionnaireTarget], business_context: BusinessContext
    ) -> Dict[str, Any]:
        """Generate stakeholder communication strategy"""
        try:
            return {
                "communication_channels": {
                    "primary": business_context.cultural_factors.get(
                        "communication_style", "email"
                    ),
                    "secondary": ["teams_meeting", "slack"],
                    "escalation": "management_review",
                },
                "messaging_framework": {
                    "business_justification": "Critical for migration success and risk reduction",
                    "time_commitment": "Minimal time investment for maximum migration value",
                    "value_proposition": "Your expertise directly improves migration outcomes",
                    "urgency_level": business_context.resource_constraints.get(
                        "time_constraints", "medium"
                    ),
                },
                "stakeholder_customization": {
                    "technical_stakeholders": "Focus on technical accuracy and migration feasibility",
                    "business_stakeholders": "Emphasize business value and risk mitigation",
                    "executive_stakeholders": "Highlight strategic importance and ROI",
                },
                "follow_up_strategy": {
                    "reminder_cadence": "3_day_intervals",
                    "escalation_threshold": "7_days_no_response",
                    "completion_recognition": "public_acknowledgment",
                },
            }

        except Exception as e:
            logger.error(f"Error generating communication strategy: {e}")
            return {"communication_channels": {"primary": "email"}}

    def calculate_effort_estimates(
        self, targets: List[QuestionnaireTarget], business_context: BusinessContext
    ) -> Dict[str, Any]:
        """Calculate effort and timeline estimates"""
        try:
            total_minutes = sum(target.estimated_effort_minutes for target in targets)

            # Account for organizational factors
            efficiency_factor = 1.0
            if business_context.cultural_factors.get("collaboration_level") == "high":
                efficiency_factor *= 0.9
            if (
                business_context.resource_constraints.get("stakeholder_availability")
                == "limited"
            ):
                efficiency_factor *= 1.3

            adjusted_minutes = total_minutes * efficiency_factor
            total_days = max(
                7, int(adjusted_minutes / 60 / 2)
            )  # Assuming 2 hours per day max

            return {
                "total_minutes": int(adjusted_minutes),
                "total_days": total_days,
                "stakeholder_workload": self._calculate_stakeholder_workload(targets),
                "milestones": self._generate_timeline_milestones(total_days),
            }

        except Exception as e:
            logger.error(f"Error calculating effort estimates: {e}")
            return {"total_minutes": 0, "total_days": 7, "stakeholder_workload": {}}

    def identify_primary_stakeholders(
        self, business_context: BusinessContext
    ) -> List[str]:
        """Identify primary stakeholders based on business context"""
        domain = business_context.organization_profile.get(
            "domain", BusinessDomain.GENERAL
        )
        domain_config = self.domain_configurations.get(domain, {})

        primary_roles = domain_config.get(
            "stakeholder_priority", [StakeholderRole.BUSINESS_OWNER]
        )
        return [role.value for role in primary_roles[:3]]  # Top 3 primary stakeholders

    def assess_capacity_constraints(
        self, business_context: BusinessContext
    ) -> Dict[str, Any]:
        """Assess stakeholder capacity constraints"""
        return {
            "overall_availability": business_context.resource_constraints.get(
                "stakeholder_availability", "medium"
            ),
            "competing_priorities": business_context.resource_constraints.get(
                "competing_priorities", "medium"
            ),
            "seasonal_factors": business_context.resource_constraints.get(
                "seasonal_factors", []
            ),
            "workload_distribution": "balanced",  # Could be enhanced with actual data
            "capacity_risk_level": "medium",
        }

    def define_escalation_paths(
        self, business_context: BusinessContext
    ) -> List[Dict[str, Any]]:
        """Define escalation paths for questionnaire non-completion"""
        return [
            {
                "level": 1,
                "trigger": "3_days_overdue",
                "action": "automated_reminder",
                "escalation_to": "direct_manager",
            },
            {
                "level": 2,
                "trigger": "7_days_overdue",
                "action": "manager_intervention",
                "escalation_to": "project_manager",
            },
            {
                "level": 3,
                "trigger": "14_days_overdue",
                "action": "executive_review",
                "escalation_to": "c_level_sponsor",
            },
        ]

    def calculate_target_response_rate(
        self, business_context: BusinessContext
    ) -> float:
        """Calculate target response rate based on context"""
        base_rate = 75.0

        # Adjust based on organizational factors
        if business_context.cultural_factors.get("collaboration_level") == "high":
            base_rate += 10
        if (
            business_context.resource_constraints.get("stakeholder_availability")
            == "limited"
        ):
            base_rate -= 15
        if business_context.organization_profile.get("change_readiness") == "high":
            base_rate += 5

        return max(50.0, min(95.0, base_rate))

    def define_quality_thresholds(
        self, business_context: BusinessContext
    ) -> Dict[str, float]:
        """Define quality thresholds for responses"""
        domain = business_context.organization_profile.get(
            "domain", BusinessDomain.GENERAL
        )
        domain_config = self.domain_configurations.get(domain, {})

        base_threshold = 75.0
        if domain_config.get("question_complexity") == "high":
            base_threshold = 80.0

        return {
            "minimum_completeness": base_threshold,
            "minimum_accuracy": base_threshold + 5,
            "minimum_relevance": base_threshold - 5,
            "overall_quality": base_threshold,
        }

    def identify_targeting_risks(
        self, business_context: BusinessContext
    ) -> List[Dict[str, Any]]:
        """Identify risks in questionnaire targeting"""
        risks = []

        if (
            business_context.resource_constraints.get("stakeholder_availability")
            == "limited"
        ):
            risks.append(
                {
                    "risk": "Low stakeholder availability",
                    "impact": "medium",
                    "mitigation": "Flexible scheduling and async collection methods",
                }
            )

        if business_context.cultural_factors.get("change_tolerance") == "low":
            risks.append(
                {
                    "risk": "Change resistance",
                    "impact": "high",
                    "mitigation": "Enhanced communication and executive sponsorship",
                }
            )

        return risks

    def assess_overall_complexity(self, business_context: BusinessContext) -> str:
        """Assess overall complexity level for the business context"""
        domain = business_context.organization_profile.get(
            "domain", BusinessDomain.GENERAL
        )
        domain_config = self.domain_configurations.get(domain, {})

        base_complexity = domain_config.get("question_complexity", "medium")
        org_size = business_context.organization_profile.get("size")

        # Import here to avoid circular dependency
        from .enums import OrganizationSize

        if (
            org_size in [OrganizationSize.LARGE, OrganizationSize.ENTERPRISE]
            and base_complexity == "high"
        ):
            return "advanced"
        elif base_complexity == "high" or org_size == OrganizationSize.ENTERPRISE:
            return "intermediate"
        else:
            return "basic"

    def target_to_dict(self, target: QuestionnaireTarget) -> Dict[str, Any]:
        """Convert QuestionnaireTarget to dictionary"""
        return {
            "target_stakeholders": [role.value for role in target.target_stakeholders],
            "priority_level": target.priority_level,
            "complexity_level": target.complexity_level,
            "estimated_effort_minutes": target.estimated_effort_minutes,
            "business_justification": target.business_justification,
            "success_metrics": target.success_metrics,
        }

    def _determine_target_stakeholders(
        self, gap_category: str, business_context: BusinessContext
    ) -> List[StakeholderRole]:
        """Determine appropriate stakeholders for a gap category"""
        stakeholder_mapping = {
            "infrastructure": [
                StakeholderRole.INFRASTRUCTURE_ENGINEER,
                StakeholderRole.OPERATIONS_MANAGER,
                StakeholderRole.NETWORK_ADMINISTRATOR,
            ],
            "application": [
                StakeholderRole.APPLICATION_ARCHITECT,
                StakeholderRole.BUSINESS_OWNER,
                StakeholderRole.PROJECT_MANAGER,
            ],
            "operational": [
                StakeholderRole.OPERATIONS_MANAGER,
                StakeholderRole.BUSINESS_OWNER,
                StakeholderRole.PROJECT_MANAGER,
            ],
            "dependencies": [
                StakeholderRole.APPLICATION_ARCHITECT,
                StakeholderRole.INFRASTRUCTURE_ENGINEER,
                StakeholderRole.BUSINESS_OWNER,
            ],
            "security": [
                StakeholderRole.SECURITY_OFFICER,
                StakeholderRole.COMPLIANCE_MANAGER,
            ],
            "compliance": [
                StakeholderRole.COMPLIANCE_MANAGER,
                StakeholderRole.SECURITY_OFFICER,
                StakeholderRole.BUSINESS_OWNER,
            ],
        }

        return stakeholder_mapping.get(gap_category, [StakeholderRole.BUSINESS_OWNER])

    def _determine_question_complexity(
        self, gap: Dict[str, Any], business_context: BusinessContext
    ) -> str:
        """Determine appropriate question complexity level"""
        domain = business_context.organization_profile.get(
            "domain", BusinessDomain.GENERAL
        )
        domain_config = self.domain_configurations.get(domain, {})
        base_complexity = domain_config.get("question_complexity", "medium")

        # Adjust based on gap characteristics
        if gap.get("priority", 3) == 1:  # Critical gaps need detailed questions
            return "advanced"
        elif gap.get("technical_depth") == "high":
            return "advanced"
        elif base_complexity == "high":
            return "intermediate"
        else:
            return "basic"

    def _estimate_effort_minutes(
        self, gap: Dict[str, Any], complexity: str, business_context: BusinessContext
    ) -> int:
        """Estimate effort required in minutes"""
        base_minutes = {"basic": 10, "intermediate": 20, "advanced": 35}

        effort = base_minutes.get(complexity, 15)

        # Adjust for organizational factors
        if business_context.cultural_factors.get("communication_style") == "detailed":
            effort += 5
        if business_context.resource_constraints.get("time_constraints") == "high":
            effort -= 5

        return max(5, effort)

    def _map_gap_priority(self, gap_priority: int) -> str:
        """Map gap priority to questionnaire priority"""
        mapping = {1: "critical", 2: "high", 3: "medium", 4: "low"}
        return mapping.get(gap_priority, "medium")

    def _calculate_optimal_timing(
        self, sequence_index: int, business_context: BusinessContext
    ) -> str:
        """Calculate optimal timing for questionnaire delivery"""
        # Simple timing calculation - could be enhanced
        days_offset = sequence_index * 2  # 2-day intervals
        return f"Day {days_offset + 1}"

    def _calculate_stakeholder_workload(
        self, targets: List[QuestionnaireTarget]
    ) -> Dict[str, int]:
        """Calculate workload per stakeholder role"""
        workload = {}

        for target in targets:
            minutes_per_stakeholder = target.estimated_effort_minutes / len(
                target.target_stakeholders
            )
            for stakeholder in target.target_stakeholders:
                workload[stakeholder.value] = (
                    workload.get(stakeholder.value, 0) + minutes_per_stakeholder
                )

        return {k: int(v) for k, v in workload.items()}

    def _generate_timeline_milestones(self, total_days: int) -> List[Dict[str, Any]]:
        """Generate timeline milestones"""
        milestones = []

        quarter_days = total_days // 4
        milestones.extend(
            [
                {"day": quarter_days, "milestone": "25% questionnaires completed"},
                {"day": quarter_days * 2, "milestone": "50% questionnaires completed"},
                {"day": quarter_days * 3, "milestone": "75% questionnaires completed"},
                {"day": total_days, "milestone": "All questionnaires completed"},
            ]
        )

        return milestones
