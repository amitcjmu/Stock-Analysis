"""
Resource allocation and optimization functionality.

This module handles resource allocation optimization for crew coordination.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ResourceAllocationMixin:
    """Mixin for resource allocation functionality"""

    def _setup_resource_allocation(self) -> Dict[str, Any]:
        """Setup resource allocation management"""
        return {
            "allocation_enabled": True,
            "optimization_strategies": {
                "balanced": {"cpu_weight": 0.5, "memory_weight": 0.5},
                "cpu_optimized": {"cpu_weight": 0.7, "memory_weight": 0.3},
                "memory_optimized": {"cpu_weight": 0.3, "memory_weight": 0.7},
            },
            "resource_constraints": {
                "max_cpu_cores": 16,
                "max_memory_gb": 64,
                "max_concurrent_crews": 6,
            },
            "allocation_history": [],
        }

    def optimize_resource_allocation(
        self, crew_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize resource allocation for crews"""
        if not self.resource_allocation:
            self.resource_allocation = self._setup_resource_allocation()

        try:
            optimization_result = {
                "optimized": True,
                "allocations": {},
                "total_resources": {"cpu_cores": 0, "memory_gb": 0},
                "optimization_strategy": "balanced",
                "efficiency_score": 0.0,
            }

            # Get resource constraints
            constraints = self.resource_allocation["resource_constraints"]
            max_cpu = constraints["max_cpu_cores"]
            max_memory = constraints["max_memory_gb"]

            # Calculate base allocations
            crew_count = len(crew_requirements.get("crews", []))
            if crew_count == 0:
                return optimization_result

            base_cpu_per_crew = max_cpu // crew_count
            base_memory_per_crew = max_memory // crew_count

            # Optimize allocations based on crew characteristics
            for crew_name, requirements in crew_requirements.get("crews", {}).items():
                complexity = requirements.get("complexity", "medium")
                priority = requirements.get("priority", "medium")

                # Adjust allocation based on complexity
                cpu_multiplier = 1.0
                memory_multiplier = 1.0

                if complexity == "high":
                    cpu_multiplier = 1.5
                    memory_multiplier = 1.3
                elif complexity == "low":
                    cpu_multiplier = 0.8
                    memory_multiplier = 0.8

                # Adjust based on priority
                if priority == "high":
                    cpu_multiplier *= 1.2
                    memory_multiplier *= 1.2
                elif priority == "low":
                    cpu_multiplier *= 0.9
                    memory_multiplier *= 0.9

                allocated_cpu = min(
                    max(1, int(base_cpu_per_crew * cpu_multiplier)),
                    max_cpu // 2,  # No crew gets more than half
                )
                allocated_memory = min(
                    max(2, int(base_memory_per_crew * memory_multiplier)),
                    max_memory // 2,
                )

                optimization_result["allocations"][crew_name] = {
                    "cpu_cores": allocated_cpu,
                    "memory_gb": allocated_memory,
                    "priority": priority,
                    "estimated_duration": self._estimate_crew_duration(
                        crew_name, allocated_cpu, allocated_memory
                    ),
                }

                optimization_result["total_resources"]["cpu_cores"] += allocated_cpu
                optimization_result["total_resources"]["memory_gb"] += allocated_memory

            # Calculate efficiency score
            cpu_utilization = (
                optimization_result["total_resources"]["cpu_cores"] / max_cpu
            )
            memory_utilization = (
                optimization_result["total_resources"]["memory_gb"] / max_memory
            )
            optimization_result["efficiency_score"] = (
                cpu_utilization + memory_utilization
            ) / 2

            # Record allocation history
            self.resource_allocation["allocation_history"].append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "allocations": optimization_result["allocations"],
                    "efficiency_score": optimization_result["efficiency_score"],
                }
            )

            logger.info(
                f"💻 Resource allocation optimized - Efficiency: {optimization_result['efficiency_score']:.2f}"
            )
            return optimization_result

        except Exception as e:
            logger.error(f"Failed to optimize resource allocation: {e}")
            return {"optimized": False, "error": str(e)}

    def _estimate_crew_duration(
        self, crew_name: str, cpu_cores: int, memory_gb: int
    ) -> int:
        """Estimate crew execution duration based on allocated resources"""
        base_durations = {
            "field_mapping": 180,
            "data_cleansing": 240,
            "inventory_building": 300,
            "app_server_dependencies": 200,
            "app_app_dependencies": 220,
            "technical_debt": 260,
        }

        base_duration = base_durations.get(crew_name, 200)

        # Adjust based on resources (more resources = faster execution)
        resource_factor = (cpu_cores + memory_gb / 4) / 6  # Normalized resource factor
        adjusted_duration = int(base_duration / max(resource_factor, 0.5))

        return adjusted_duration

    def get_resource_utilization_report(self) -> Dict[str, Any]:
        """Generate resource utilization report"""
        if (
            not self.resource_allocation
            or not self.resource_allocation["allocation_history"]
        ):
            return {"error": "No allocation history available"}

        history = self.resource_allocation["allocation_history"]
        latest_allocation = history[-1] if history else {}

        report = {
            "current_utilization": {
                "cpu_cores": 0,
                "memory_gb": 0,
                "efficiency_score": latest_allocation.get("efficiency_score", 0.0),
            },
            "allocation_breakdown": {},
            "recommendations": [],
            "constraints": self.resource_allocation["resource_constraints"],
        }

        # Calculate current utilization
        for crew_name, allocation in latest_allocation.get("allocations", {}).items():
            report["current_utilization"]["cpu_cores"] += allocation.get("cpu_cores", 0)
            report["current_utilization"]["memory_gb"] += allocation.get("memory_gb", 0)
            report["allocation_breakdown"][crew_name] = allocation

        # Generate recommendations
        efficiency = latest_allocation.get("efficiency_score", 0.0)
        if efficiency < 0.6:
            report["recommendations"].append(
                "Resource utilization is low - consider reducing allocations or increasing parallelism"
            )
        elif efficiency > 0.9:
            report["recommendations"].append(
                "Resource utilization is very high - consider adding more resources or sequential execution"
            )
        else:
            report["recommendations"].append("Resource utilization is optimal")

        return report
