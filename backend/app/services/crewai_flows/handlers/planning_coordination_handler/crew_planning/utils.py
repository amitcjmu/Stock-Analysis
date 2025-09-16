"""
Crew planning utility functions.

This module contains utility functions for crew planning including
execution order building, resource allocation, and duration estimation.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CrewPlanningUtilsMixin:
    """Mixin for crew planning utility functions"""

    def _build_execution_order(
        self, dependency_graph: Dict[str, List[str]]
    ) -> List[str]:
        """Build execution order based on dependency graph"""
        # Topological sort implementation
        order = []
        visited = set()
        temp_visited = set()

        def visit(node):
            if node in temp_visited:
                # Circular dependency detected, handle gracefully
                return
            if node in visited:
                return

            temp_visited.add(node)
            for dependency in dependency_graph.get(node, []):
                visit(dependency)
            temp_visited.remove(node)
            visited.add(node)
            order.append(node)

        for node in dependency_graph.keys():
            if node not in visited:
                visit(node)

        return order[::-1]  # Reverse for correct execution order

    def _allocate_crew_resources(
        self, complexity_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Allocate resources to crews based on complexity"""
        base_allocation = {
            "field_mapping": {"cpu_cores": 2, "memory_gb": 4, "priority": "high"},
            "data_cleansing": {"cpu_cores": 2, "memory_gb": 6, "priority": "high"},
            "inventory_building": {
                "cpu_cores": 3,
                "memory_gb": 8,
                "priority": "medium",
            },
            "app_server_dependencies": {
                "cpu_cores": 2,
                "memory_gb": 4,
                "priority": "medium",
            },
            "app_app_dependencies": {
                "cpu_cores": 2,
                "memory_gb": 4,
                "priority": "medium",
            },
            "technical_debt": {"cpu_cores": 2, "memory_gb": 6, "priority": "low"},
        }

        # Adjust allocation based on complexity
        complexity_multiplier = {"low": 0.8, "medium": 1.0, "high": 1.5}

        multiplier = complexity_multiplier.get(
            complexity_analysis.get("overall_complexity", "medium"), 1.0
        )

        adjusted_allocation = {}
        for crew, resources in base_allocation.items():
            adjusted_allocation[crew] = {
                "cpu_cores": max(1, int(resources["cpu_cores"] * multiplier)),
                "memory_gb": max(2, int(resources["memory_gb"] * multiplier)),
                "priority": resources["priority"],
            }

        return adjusted_allocation

    def _estimate_coordination_duration(self, coordination_plan: Dict[str, Any]) -> int:
        """Estimate coordination duration in seconds"""
        base_duration_per_crew = 180  # 3 minutes per crew
        crew_count = len(coordination_plan.get("crew_execution_order", []))

        # Parallel execution reduces duration
        if coordination_plan["coordination_strategy"] == "adaptive":
            # Assume 30% reduction with parallel execution
            return int(base_duration_per_crew * crew_count * 0.7)

        return base_duration_per_crew * crew_count

    def get_crew_planning_summary(self) -> Dict[str, Any]:
        """Get summary of current crew planning configuration"""
        summary = {
            "coordination_enabled": False,
            "active_strategies": [],
            "dependency_graph_size": 0,
            "parallel_opportunities": 0,
            "resource_allocation_active": False,
        }

        if hasattr(self, "planning_coordination") and self.planning_coordination:
            summary["coordination_enabled"] = self.planning_coordination.get(
                "coordination_enabled", False
            )
            summary["active_strategies"] = [
                strategy
                for strategy, config in self.planning_coordination.get(
                    "coordination_strategies", {}
                ).items()
                if config.get("enabled", False)
            ]

            dependency_graph = self.planning_coordination.get(
                "coordination_metrics", {}
            ).get("crew_dependency_graph", {})
            summary["dependency_graph_size"] = len(dependency_graph)

            parallel_opps = self.planning_coordination.get(
                "coordination_metrics", {}
            ).get("parallel_opportunities", [])
            summary["parallel_opportunities"] = len(parallel_opps)

            summary["resource_allocation_active"] = True

        return summary

    def validate_crew_dependencies(
        self, dependency_graph: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Validate crew dependency graph for cycles and issues"""
        validation_result = {
            "valid": True,
            "issues": [],
            "circular_dependencies": [],
            "orphaned_crews": [],
            "recommendations": [],
        }

        # Check for circular dependencies
        visited = set()
        rec_stack = set()

        def has_cycle(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                return cycle
            if node in visited:
                return None

            visited.add(node)
            rec_stack.add(node)

            for neighbor in dependency_graph.get(node, []):
                cycle = has_cycle(neighbor, path + [node])
                if cycle:
                    return cycle

            rec_stack.remove(node)
            return None

        all_nodes = set(dependency_graph.keys())
        for dependent in dependency_graph.values():
            all_nodes.update(dependent)

        for node in all_nodes:
            if node not in visited:
                cycle = has_cycle(node, [])
                if cycle:
                    validation_result["circular_dependencies"].append(cycle)
                    validation_result["valid"] = False

        # Check for orphaned crews (referenced but not defined)
        defined_crews = set(dependency_graph.keys())
        referenced_crews = set()
        for deps in dependency_graph.values():
            referenced_crews.update(deps)

        orphaned = referenced_crews - defined_crews
        if orphaned:
            validation_result["orphaned_crews"] = list(orphaned)
            validation_result["issues"].append(
                f"Orphaned crews found: {', '.join(orphaned)}"
            )

        # Generate recommendations
        if validation_result["circular_dependencies"]:
            validation_result["recommendations"].append(
                "Resolve circular dependencies by reviewing crew relationships"
            )
        if validation_result["orphaned_crews"]:
            validation_result["recommendations"].append(
                "Add missing crew definitions or remove invalid references"
            )
        if validation_result["valid"]:
            validation_result["recommendations"].append(
                "Dependency graph is valid and ready for execution"
            )

        return validation_result
