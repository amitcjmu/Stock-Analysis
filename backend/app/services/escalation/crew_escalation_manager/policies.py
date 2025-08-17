"""
Escalation policies and rules for collaboration strategies and decision-making.
"""

from typing import Dict, Any, List

from .base import logger


class EscalationPolicyManager:
    """
    Manages escalation policies, collaboration strategies, and decision rules.
    """

    def __init__(
        self,
        collaboration_strategies: Dict[str, Dict[str, str]],
        delegation_patterns: Dict[str, Dict[str, str]],
    ):
        """Initialize with collaboration strategies and delegation patterns."""
        self.collaboration_strategies = collaboration_strategies
        self.delegation_patterns = delegation_patterns

    def determine_collaboration_strategy(
        self, page: str, agent_id: str, collaboration_type: str
    ) -> Dict[str, Any]:
        """
        Determine collaboration strategy for Ponder More functionality.

        Args:
            page: The page context
            agent_id: The agent identifier
            collaboration_type: Type of collaboration requested

        Returns:
            Dict[str, Any]: Complete collaboration strategy configuration
        """
        from .triggers import EscalationTriggerManager

        # Get base strategy configuration
        base_strategy = self.collaboration_strategies.get(
            collaboration_type, self.collaboration_strategies["cross_agent"]
        )

        # Create temporary trigger manager for crew determination
        # Note: This is a bit of coupling, but necessary for the existing interface
        crew_mappings = self._get_default_crew_mappings()
        trigger_manager = EscalationTriggerManager(crew_mappings)

        # Determine primary crew
        primary_crew = trigger_manager.determine_crew_for_page_agent(page, agent_id)

        # Determine additional crews based on collaboration type
        additional_crews = self._determine_additional_crews(
            page, collaboration_type, primary_crew
        )

        strategy = {
            "primary_crew": primary_crew,
            "additional_crews": additional_crews,
            "pattern": base_strategy["pattern"],
            "description": base_strategy["description"],
            "collaboration_type": collaboration_type,
            "expected_outcomes": self._get_expected_outcomes(page, collaboration_type),
            "delegation_strategy": self._determine_delegation_strategy(
                collaboration_type
            ),
            "resource_requirements": self._calculate_resource_requirements(
                len(additional_crews) + 1
            ),
            "estimated_duration": self._estimate_collaboration_duration(
                collaboration_type, len(additional_crews)
            ),
        }

        logger.info(
            f"🤝 Collaboration strategy: {strategy['pattern']} with {len(additional_crews)} additional crews"
        )
        return strategy

    def _get_default_crew_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get default crew mappings for temporary trigger manager."""
        return {
            "field_mapping": {
                "attribute_mapping_agent": "field_mapping_crew",
                "data_validation_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
            },
            "asset_inventory": {
                "asset_inventory_agent": "asset_intelligence_crew",
                "data_cleansing_agent": "data_quality_crew",
                "asset_classification_expert": "asset_intelligence_crew",
                "business_context_analyst": "asset_intelligence_crew",
                "environment_specialist": "asset_intelligence_crew",
            },
            "dependencies": {
                "dependency_analysis_agent": "dependency_analysis_crew",
                "asset_inventory_agent": "asset_intelligence_crew",
                "network_architecture_specialist": "dependency_analysis_crew",
                "application_integration_expert": "dependency_analysis_crew",
                "infrastructure_dependencies_analyst": "dependency_analysis_crew",
            },
            "tech_debt": {
                "tech_debt_analysis_agent": "tech_debt_analysis_crew",
                "dependency_analysis_agent": "dependency_analysis_crew",
                "legacy_modernization_expert": "tech_debt_analysis_crew",
                "cloud_migration_strategist": "tech_debt_analysis_crew",
                "risk_assessment_specialist": "tech_debt_analysis_crew",
            },
        }

    def _determine_additional_crews(
        self, page: str, collaboration_type: str, primary_crew: str
    ) -> List[str]:
        """Determine additional crews based on collaboration type and page."""
        additional_crews = []

        if collaboration_type == "expert_panel":
            # Add complementary crews for expert panel
            if page == "dependencies":
                additional_crews = [
                    "asset_intelligence_crew",
                    "tech_debt_analysis_crew",
                ]
            elif page == "asset_inventory":
                additional_crews = ["dependency_analysis_crew", "field_mapping_crew"]
            elif page == "tech_debt":
                additional_crews = [
                    "dependency_analysis_crew",
                    "asset_intelligence_crew",
                ]
            elif page == "field_mapping":
                additional_crews = ["asset_intelligence_crew", "data_quality_crew"]

        elif collaboration_type == "full_crew":
            # Add all relevant crews for full collaboration
            additional_crews = [
                "asset_intelligence_crew",
                "dependency_analysis_crew",
                "tech_debt_analysis_crew",
                "field_mapping_crew",
                "data_quality_crew",
            ]
            # Remove primary crew from additional crews
            additional_crews = [c for c in additional_crews if c != primary_crew]

        elif collaboration_type == "cross_agent":
            # Add 1-2 complementary crews for cross-agent collaboration
            crew_relationships = {
                "asset_intelligence_crew": ["dependency_analysis_crew"],
                "dependency_analysis_crew": [
                    "asset_intelligence_crew",
                    "tech_debt_analysis_crew",
                ],
                "tech_debt_analysis_crew": ["dependency_analysis_crew"],
                "field_mapping_crew": ["asset_intelligence_crew"],
                "data_quality_crew": ["field_mapping_crew"],
            }
            additional_crews = crew_relationships.get(primary_crew, [])

        return additional_crews

    def _determine_delegation_strategy(self, collaboration_type: str) -> str:
        """Determine the delegation strategy based on collaboration type."""
        delegation_mapping = {
            "cross_agent": "parallel_delegation",
            "expert_panel": "sequential_delegation",
            "full_crew": "hierarchical_delegation",
        }
        return delegation_mapping.get(collaboration_type, "parallel_delegation")

    def _get_expected_outcomes(self, page: str, collaboration_type: str) -> List[str]:
        """Get expected outcomes based on page and collaboration type."""
        base_outcomes = {
            "field_mapping": [
                "Enhanced field mapping accuracy",
                "Identification of complex mapping patterns",
                "Data quality improvement recommendations",
            ],
            "asset_inventory": [
                "Comprehensive asset classification",
                "Business criticality assessment",
                "Environment and dependency insights",
            ],
            "dependencies": [
                "Complete dependency mapping",
                "Critical path identification",
                "Migration risk assessment",
            ],
            "tech_debt": [
                "Modernization strategy recommendations",
                "6R strategy optimization",
                "Technical debt prioritization",
            ],
        }

        outcomes = base_outcomes.get(page, ["Enhanced analysis results"])

        # Add collaboration-specific outcomes
        if collaboration_type == "expert_panel":
            outcomes.extend(
                [
                    "Expert validation and refinement",
                    "Multi-perspective analysis",
                    "Consensus-based recommendations",
                ]
            )
        elif collaboration_type == "full_crew":
            outcomes.extend(
                [
                    "Cross-domain insights",
                    "Comprehensive risk analysis",
                    "Holistic migration recommendations",
                    "Integrated solution design",
                ]
            )
        elif collaboration_type == "cross_agent":
            outcomes.extend(
                [
                    "Cross-functional validation",
                    "Parallel analysis efficiency",
                    "Rapid insight generation",
                ]
            )

        return outcomes

    def _calculate_resource_requirements(self, crew_count: int) -> Dict[str, Any]:
        """Calculate resource requirements based on crew count."""
        base_cpu = 0.5  # Base CPU per crew
        base_memory = 512  # Base memory in MB per crew

        return {
            "estimated_cpu": crew_count * base_cpu,
            "estimated_memory_mb": crew_count * base_memory,
            "concurrent_crews": min(crew_count, 3),  # Limit concurrent execution
            "resource_tier": (
                "low" if crew_count <= 2 else "medium" if crew_count <= 4 else "high"
            ),
        }

    def _estimate_collaboration_duration(
        self, collaboration_type: str, additional_crew_count: int
    ) -> Dict[str, int]:
        """Estimate collaboration duration based on type and crew count."""
        base_duration = {
            "cross_agent": 5,  # 5 minutes base
            "expert_panel": 8,  # 8 minutes base
            "full_crew": 12,  # 12 minutes base
        }

        base_time = base_duration.get(collaboration_type, 5)
        additional_time = additional_crew_count * 2  # 2 minutes per additional crew

        total_minutes = base_time + additional_time

        return {
            "estimated_minutes": total_minutes,
            "min_minutes": max(3, total_minutes - 2),
            "max_minutes": total_minutes + 5,
        }

    def validate_collaboration_strategy(self, strategy: Dict[str, Any]) -> bool:
        """
        Validate a collaboration strategy configuration.

        Args:
            strategy: The collaboration strategy to validate

        Returns:
            bool: Whether the strategy is valid
        """
        required_fields = [
            "primary_crew",
            "additional_crews",
            "pattern",
            "description",
            "collaboration_type",
        ]

        for field in required_fields:
            if field not in strategy:
                logger.error(
                    f"Missing required field '{field}' in collaboration strategy"
                )
                return False

        # Validate collaboration type
        if strategy["collaboration_type"] not in self.collaboration_strategies:
            logger.error(
                f"Invalid collaboration type: {strategy['collaboration_type']}"
            )
            return False

        # Validate that primary crew is not in additional crews
        if strategy["primary_crew"] in strategy["additional_crews"]:
            logger.error("Primary crew cannot be in additional crews list")
            return False

        # Validate crew count limits
        total_crews = len(strategy["additional_crews"]) + 1
        if total_crews > 6:
            logger.warning(f"High crew count ({total_crews}) may impact performance")

        logger.debug(
            f"Collaboration strategy validated: {strategy['collaboration_type']}"
        )
        return True

    def get_policy_recommendations(
        self, page: str, context: Dict[str, Any]
    ) -> List[str]:
        """Get policy recommendations based on page and context."""
        recommendations = []

        # Analyze context for policy recommendations
        page_data = context.get("page_data", {})
        assets = page_data.get("assets", [])

        # General recommendations based on asset count
        if len(assets) > 20:
            recommendations.append(
                "Consider full_crew collaboration for comprehensive analysis"
            )
        elif len(assets) > 10:
            recommendations.append(
                "Expert_panel collaboration recommended for thorough review"
            )
        else:
            recommendations.append(
                "Cross_agent collaboration sufficient for current scope"
            )

        # Page-specific recommendations
        if page == "dependencies" and any(
            asset.get("dependencies", []) for asset in assets
        ):
            recommendations.append(
                "Sequential delegation recommended for dependency analysis"
            )

        if page == "tech_debt" and len(assets) > 5:
            recommendations.append(
                "Hierarchical delegation for complex modernization decisions"
            )

        if page == "field_mapping" and page_data.get("unmapped_fields", []):
            recommendations.append(
                "Parallel delegation for efficient field mapping coverage"
            )

        return recommendations


# Export for use in other modules
__all__ = ["EscalationPolicyManager"]
