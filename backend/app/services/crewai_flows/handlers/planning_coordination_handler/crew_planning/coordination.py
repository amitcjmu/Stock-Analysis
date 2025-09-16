"""
Core crew coordination functionality.

This module handles the main crew coordination logic including setup,
coordination planning, and data complexity analysis.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class CrewCoordinationMixin:
    """Mixin for core crew coordination functionality"""

    def _setup_planning_coordination(self) -> Dict[str, Any]:
        """Setup cross-crew planning coordination"""
        return {
            "coordination_enabled": True,
            "planning_intelligence": True,
            "cross_crew_optimization": True,
            "coordination_strategies": {
                "sequential": {"enabled": True, "default": True},
                "parallel": {"enabled": True, "conditions": ["non_dependent_crews"]},
                "adaptive": {"enabled": True, "based_on": "data_complexity"},
            },
            "coordination_metrics": {
                "crew_dependency_graph": {
                    "field_mapping": [],
                    "data_cleansing": ["field_mapping"],
                    "inventory_building": ["field_mapping", "data_cleansing"],
                    "app_server_dependencies": ["inventory_building"],
                    "app_app_dependencies": ["inventory_building"],
                    "technical_debt": [
                        "app_server_dependencies",
                        "app_app_dependencies",
                    ],
                },
                "parallel_opportunities": [
                    {
                        "crews": ["app_server_dependencies", "app_app_dependencies"],
                        "after": "inventory_building",
                    }
                ],
            },
            "coordination_thresholds": {
                "data_size_for_parallel": 1000,
                "complexity_threshold": 0.7,
                "resource_utilization_max": 0.8,
            },
        }

    def coordinate_crew_planning(
        self, data_complexity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Coordinate planning across crews"""
        if not self.planning_coordination:
            self.planning_coordination = self._setup_planning_coordination()

        try:
            coordination_plan = {
                "coordination_strategy": "sequential",
                "crew_execution_order": [],
                "parallel_opportunities": [],
                "resource_allocation": {},
                "estimated_duration": 0,
                "coordination_intelligence": {},
            }

            # Analyze data complexity for planning decisions
            complexity_analysis = self._analyze_data_complexity(data_complexity)
            coordination_plan["coordination_intelligence"][
                "complexity_analysis"
            ] = complexity_analysis

            # Determine optimal coordination strategy
            if complexity_analysis["enables_parallel_execution"]:
                coordination_plan["coordination_strategy"] = "adaptive"
                coordination_plan["parallel_opportunities"] = (
                    self.planning_coordination["coordination_metrics"][
                        "parallel_opportunities"
                    ]
                )

            # Build execution order based on dependency graph
            dependency_graph = self.planning_coordination["coordination_metrics"][
                "crew_dependency_graph"
            ]
            execution_order = self._build_execution_order(dependency_graph)
            coordination_plan["crew_execution_order"] = execution_order

            # Allocate resources based on crew requirements
            resource_allocation = self._allocate_crew_resources(complexity_analysis)
            coordination_plan["resource_allocation"] = resource_allocation

            # Estimate total duration
            coordination_plan["estimated_duration"] = (
                self._estimate_coordination_duration(coordination_plan)
            )

            logger.info(
                f"🎯 Crew planning coordination completed - Strategy: {coordination_plan['coordination_strategy']}"
            )
            return {"success": True, "coordination_plan": coordination_plan}

        except Exception as e:
            logger.error(f"Failed to coordinate crew planning: {e}")
            return {"success": False, "reason": f"error: {str(e)}"}

    def _analyze_data_complexity(
        self, data_characteristics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze data complexity for dynamic planning"""
        try:
            data_size = data_characteristics.get("record_count", 0)
            field_count = data_characteristics.get("field_count", 0)
            data_quality = data_characteristics.get("data_quality_score", 0.5)

            complexity_analysis = {
                "overall_complexity": "medium",
                "complexity_factors": {
                    "data_size": (
                        "small"
                        if data_size < 1000
                        else "medium" if data_size < 10000 else "large"
                    ),
                    "field_complexity": (
                        "simple"
                        if field_count < 10
                        else "moderate" if field_count < 50 else "complex"
                    ),
                    "data_quality": (
                        "high"
                        if data_quality > 0.8
                        else "medium" if data_quality > 0.5 else "low"
                    ),
                },
                "recommended_strategies": [],
                "enables_parallel_execution": False,
                "requires_enhanced_validation": False,
            }

            # Determine overall complexity
            complexity_score = 0
            if complexity_analysis["complexity_factors"]["data_size"] == "large":
                complexity_score += 0.4
            if (
                complexity_analysis["complexity_factors"]["field_complexity"]
                == "complex"
            ):
                complexity_score += 0.3
            if complexity_analysis["complexity_factors"]["data_quality"] == "low":
                complexity_score += 0.3

            if complexity_score > 0.7:
                complexity_analysis["overall_complexity"] = "high"
                complexity_analysis["requires_enhanced_validation"] = True
            elif complexity_score < 0.3:
                complexity_analysis["overall_complexity"] = "low"
                complexity_analysis["enables_parallel_execution"] = True

            # Generate strategy recommendations
            if complexity_analysis["enables_parallel_execution"]:
                complexity_analysis["recommended_strategies"].append(
                    "parallel_execution"
                )
            if complexity_analysis["requires_enhanced_validation"]:
                complexity_analysis["recommended_strategies"].append(
                    "enhanced_validation"
                )
            if complexity_analysis["overall_complexity"] == "high":
                complexity_analysis["recommended_strategies"].append(
                    "incremental_processing"
                )

            return complexity_analysis

        except Exception as e:
            logger.error(f"Failed to analyze data complexity: {e}")
            return {"overall_complexity": "medium", "error": str(e)}

    def create_dynamic_plan(
        self, complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create dynamic plan based on complexity analysis"""
        try:
            dynamic_plan = {
                "plan_type": "dynamic",
                "adaptation_triggers": [],
                "crew_configurations": {},
                "success_criteria": {},
                "fallback_strategies": [],
            }

            # Configure crews based on complexity
            for crew_name in [
                "field_mapping",
                "data_cleansing",
                "inventory_building",
                "app_server_dependencies",
                "app_app_dependencies",
                "technical_debt",
            ]:
                crew_config = {
                    "timeout_seconds": 300,
                    "retry_attempts": 1,
                    "enhanced_validation": False,
                    "parallel_eligible": False,
                }

                # Adjust configuration based on complexity
                if complexity_analysis["overall_complexity"] == "high":
                    crew_config["timeout_seconds"] = 600
                    crew_config["retry_attempts"] = 2
                    crew_config["enhanced_validation"] = True
                elif complexity_analysis["overall_complexity"] == "low":
                    crew_config["timeout_seconds"] = 180
                    crew_config["parallel_eligible"] = True

                dynamic_plan["crew_configurations"][crew_name] = crew_config

            # Set adaptation triggers
            dynamic_plan["adaptation_triggers"] = [
                {"trigger": "crew_failure", "action": "retry_with_enhanced_config"},
                {
                    "trigger": "low_confidence_results",
                    "action": "increase_validation_threshold",
                },
                {
                    "trigger": "performance_degradation",
                    "action": "switch_to_sequential",
                },
            ]

            # Define success criteria based on complexity
            base_confidence = (
                0.8 if complexity_analysis["overall_complexity"] == "high" else 0.7
            )
            dynamic_plan["success_criteria"] = {
                "field_mapping_confidence": base_confidence,
                "data_quality_score": base_confidence,
                "classification_accuracy": base_confidence,
                "dependency_completeness": base_confidence - 0.1,
            }

            logger.info(
                f"📋 Dynamic plan created for {complexity_analysis['overall_complexity']} complexity"
            )
            return {"success": True, "dynamic_plan": dynamic_plan}

        except Exception as e:
            logger.error(f"Failed to create dynamic plan: {e}")
            return {"success": False, "reason": f"error: {str(e)}"}
