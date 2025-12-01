"""
CrewAI tool implementations for dependency analysis.

This module contains the actual CrewAI tool classes that agents can use
to perform dependency analysis, graph building, and migration wave planning.
"""

import json
from typing import Any, Dict

from .base import BaseTool, CREWAI_TOOLS_AVAILABLE, logger
from .analyzer import DependencyAnalyzer


# Tool classes - defined conditionally to reduce complexity
class DependencyAnalysisTool(BaseTool if CREWAI_TOOLS_AVAILABLE else object):
    """Tool for comprehensive dependency analysis"""

    name: str = "dependency_analyzer"
    description: str = """
    Analyze dependencies between assets including network, configuration, data, and service dependencies.
    Identifies bottlenecks, circular dependencies, and critical paths.

    Input: List of asset dictionaries
    Output: Comprehensive dependency analysis with graph, insights, and migration recommendations
    """

    def __init__(self, context_info: Dict[str, Any]):
        if CREWAI_TOOLS_AVAILABLE:
            super().__init__()
        self._context_info = context_info

    def _run(self, analysis_request: str) -> str:
        """Analyze dependencies between assets"""
        try:
            request = json.loads(analysis_request)
            # Bug #1094 Fix: Handle both formats - list directly or dict with "assets" key
            # Agents may pass assets as a list directly instead of wrapped in {"assets": [...]}
            if isinstance(request, list):
                assets = request
            elif isinstance(request, dict) and "assets" in request:
                assets = request["assets"]
            else:
                # Qodo Bot feedback: Log warning for unexpected format but don't break workflow
                logger.warning(
                    f"⚠️ Unexpected dependency analysis input format: {type(request).__name__}. "
                    "Expected list or dict with 'assets' key. Processing with empty list."
                )
                assets = []

            result = DependencyAnalyzer.analyze_dependencies(assets, self._context_info)
            return json.dumps(result)

        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            return json.dumps(
                {"error": str(e), "dependency_graph": {"nodes": [], "edges": []}}
            )


class DependencyGraphBuilderTool(BaseTool if CREWAI_TOOLS_AVAILABLE else object):
    """Tool for building visual dependency graphs"""

    name: str = "dependency_graph_builder"
    description: str = """
    Build a visual dependency graph from analyzed dependencies.
    Creates nodes for assets and edges for dependencies with confidence scores.

    Input: Dictionary with assets and dependency analysis results
    Output: Graph structure with nodes, edges, and layout information
    """

    def __init__(self, context_info: Dict[str, Any]):
        if CREWAI_TOOLS_AVAILABLE:
            super().__init__()
        self._context_info = context_info

    def _run(self, graph_request: str) -> str:
        """Build dependency graph visualization data"""
        try:
            request = json.loads(graph_request)

            # Bug #1094 Fix: Handle list input format
            if isinstance(request, list):
                # List of assets passed directly
                assets = request
                analysis = DependencyAnalyzer.analyze_dependencies(assets)
                graph = analysis.get("dependency_graph", {})
            elif "dependency_graph" in request:
                # If we already have analysis results, extract the graph
                graph = request["dependency_graph"]
            elif isinstance(request, dict) and "assets" in request:
                # Build graph from assets in dict format
                assets = request["assets"]
                analysis = DependencyAnalyzer.analyze_dependencies(assets)
                graph = analysis.get("dependency_graph", {})
            else:
                # Qodo Bot feedback: Log warning for unexpected format but don't break workflow
                logger.warning(
                    f"⚠️ Unexpected graph_request format: {type(request).__name__}. "
                    "Expected list, dict with 'assets', or dict with 'dependency_graph'. Processing empty."
                )
                graph = {"nodes": [], "edges": []}

            # Add visualization hints
            graph["layout"] = "hierarchical"  # or "force-directed"
            graph["visualization_ready"] = True

            return json.dumps(graph)

        except Exception as e:
            logger.error(f"❌ Graph building failed: {e}")
            return json.dumps({"error": str(e), "nodes": [], "edges": []})


class MigrationWavePlannerTool(BaseTool if CREWAI_TOOLS_AVAILABLE else object):
    """Tool for planning migration waves based on dependencies"""

    name: str = "migration_wave_planner"
    description: str = """
    Plan migration waves based on dependency analysis.
    Groups assets that should be migrated together to minimize disruption.

    Input: Dependency analysis results with graph and critical paths
    Output: Migration wave plan with asset groups and sequencing
    """

    def __init__(self, context_info: Dict[str, Any]):
        if CREWAI_TOOLS_AVAILABLE:
            super().__init__()
        self._context_info = context_info

    def _run(self, planning_request: str) -> str:
        """Plan migration waves based on dependencies"""
        try:
            request = json.loads(planning_request)
            dependency_graph = request.get("dependency_graph", {})
            bottlenecks = request.get("bottlenecks", [])
            circular_deps = request.get("circular_dependencies", [])

            waves = []

            # Wave 1: Independent assets (no dependencies)
            nodes = dependency_graph.get("nodes", [])
            edges = dependency_graph.get("edges", [])

            dependent_nodes = set()
            for edge in edges:
                dependent_nodes.add(edge["source"])
                dependent_nodes.add(edge["target"])

            independent = [n for n in nodes if n["id"] not in dependent_nodes]
            if independent:
                waves.append(
                    {
                        "wave": 1,
                        "name": "Independent Components",
                        "assets": [n["label"] for n in independent],
                        "asset_count": len(independent),
                        "risk": "low",
                        "strategy": "Can be migrated in parallel",
                    }
                )

            # Wave 2: Low-dependency assets
            low_dep = [
                n
                for n in nodes
                if n["id"] in dependent_nodes
                and n["id"] not in [b["node_id"] for b in bottlenecks]
            ]
            if low_dep:
                waves.append(
                    {
                        "wave": 2,
                        "name": "Low Dependency Components",
                        "assets": [n["label"] for n in low_dep[:10]],  # Limit to 10
                        "asset_count": len(low_dep),
                        "risk": "medium",
                        "strategy": "Migrate with dependency validation",
                    }
                )

            # Wave 3: Critical/bottleneck assets
            if bottlenecks:
                waves.append(
                    {
                        "wave": 3,
                        "name": "Critical Dependencies",
                        "assets": [b["node_name"] for b in bottlenecks[:5]],
                        "asset_count": len(bottlenecks),
                        "risk": "high",
                        "strategy": "Requires careful planning and testing",
                    }
                )

            # Wave 4: Circular dependencies (migrate together)
            if circular_deps:
                waves.append(
                    {
                        "wave": 4,
                        "name": "Circular Dependency Groups",
                        "assets": [f"Group {i+1}" for i in range(len(circular_deps))],
                        "asset_count": len(circular_deps) * 2,  # Assuming pairs
                        "risk": "high",
                        "strategy": "Must be migrated as atomic units",
                    }
                )

            return json.dumps(
                {
                    "migration_waves": waves,
                    "total_waves": len(waves),
                    "estimated_duration": f"{len(waves) * 2} weeks",
                    "risk_assessment": (
                        "high" if bottlenecks or circular_deps else "medium"
                    ),
                }
            )

        except Exception as e:
            logger.error(f"❌ Wave planning failed: {e}")
            return json.dumps({"error": str(e), "migration_waves": []})


# Dummy classes for when CrewAI is not available
class DummyDependencyAnalysisTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass


class DummyDependencyGraphBuilderTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass


class DummyMigrationWavePlannerTool:
    def __init__(self, context_info: Dict[str, Any]):
        pass
