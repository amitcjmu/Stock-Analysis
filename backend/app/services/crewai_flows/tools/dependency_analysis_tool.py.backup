"""
Dependency Analysis Tools for Discovery Flow

Provides comprehensive tools for persistent agents to analyze dependencies,
build dependency graphs, and identify communication patterns between assets.
"""

import json
import logging
from typing import Any, Dict, List
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Import CrewAI tools
try:
    from crewai.tools import BaseTool

    CREWAI_TOOLS_AVAILABLE = True
except ImportError:
    CREWAI_TOOLS_AVAILABLE = False

    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass


class DependencyAnalyzer:
    """Core dependency analysis logic"""

    @staticmethod
    def analyze_dependencies(
        assets: List[Dict[str, Any]], context_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Analyze dependencies between assets based on various indicators

        Args:
            assets: List of asset records with potential dependency information
            context_info: Optional context with client/engagement info

        Returns:
            Comprehensive dependency analysis results
        """
        try:
            logger.info(f"🔍 Analyzing dependencies for {len(assets)} assets")

            if not assets:
                return DependencyAnalyzer._create_empty_analysis()

            # Extract different types of dependencies
            network_deps = DependencyAnalyzer._analyze_network_dependencies(assets)
            config_deps = DependencyAnalyzer._analyze_configuration_dependencies(assets)
            data_deps = DependencyAnalyzer._analyze_data_dependencies(assets)
            service_deps = DependencyAnalyzer._analyze_service_dependencies(assets)

            # Build comprehensive dependency graph
            dependency_graph = DependencyAnalyzer._build_dependency_graph(
                assets, network_deps, config_deps, data_deps, service_deps
            )

            # Identify critical paths and bottlenecks
            critical_analysis = DependencyAnalyzer._analyze_critical_paths(
                dependency_graph
            )

            # Generate migration insights
            migration_insights = DependencyAnalyzer._generate_migration_insights(
                dependency_graph, critical_analysis
            )

            return {
                "total_assets": len(assets),
                "dependency_graph": dependency_graph,
                "network_dependencies": network_deps,
                "configuration_dependencies": config_deps,
                "data_dependencies": data_deps,
                "service_dependencies": service_deps,
                "critical_paths": critical_analysis["critical_paths"],
                "bottlenecks": critical_analysis["bottlenecks"],
                "circular_dependencies": critical_analysis["circular_dependencies"],
                "migration_insights": migration_insights,
                "analysis_timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Dependency analysis failed: {e}")
            return DependencyAnalyzer._create_empty_analysis(error=str(e))

    @staticmethod
    def _create_empty_analysis(error: str = None) -> Dict[str, Any]:
        """Create empty analysis result"""
        return {
            "total_assets": 0,
            "dependency_graph": {"nodes": [], "edges": []},
            "network_dependencies": [],
            "configuration_dependencies": [],
            "data_dependencies": [],
            "service_dependencies": [],
            "critical_paths": [],
            "bottlenecks": [],
            "circular_dependencies": [],
            "migration_insights": [],
            "error": error,
        }

    @staticmethod
    def _analyze_network_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze network-based dependencies (IP, ports, URLs)"""
        dependencies = []

        for asset in assets:
            # Check for network connections in various fields
            connections = []

            # Check IP addresses
            if asset.get("ip_address"):
                connections.append(
                    {"type": "ip", "value": asset["ip_address"], "protocol": "tcp/ip"}
                )

            # Check for connection strings in custom attributes
            custom_attrs = asset.get("custom_attributes", {})
            if isinstance(custom_attrs, dict):
                for key, value in custom_attrs.items():
                    if "connection" in key.lower() or "endpoint" in key.lower():
                        connections.append(
                            {
                                "type": "endpoint",
                                "value": str(value),
                                "protocol": "unknown",
                            }
                        )

            # Check dependencies field
            deps = asset.get("dependencies", [])
            if isinstance(deps, list):
                for dep in deps:
                    connections.append(
                        {"type": "explicit", "value": str(dep), "protocol": "unknown"}
                    )

            if connections:
                dependencies.append(
                    {
                        "asset_id": str(asset.get("id", uuid.uuid4())),
                        "asset_name": asset.get("name", "Unknown"),
                        "connections": connections,
                        "connection_count": len(connections),
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_configuration_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze configuration-based dependencies"""
        dependencies = []

        for asset in assets:
            config_deps = []

            # Check for database connections
            if asset.get("asset_type") == "database":
                config_deps.append(
                    {
                        "type": "database",
                        "role": "provider",
                        "service": asset.get("name", "Unknown DB"),
                    }
                )
            elif asset.get("asset_type") == "application":
                # Applications depend on databases
                tech_stack = asset.get("technology_stack", "")
                if (
                    "sql" in str(tech_stack).lower()
                    or "database" in str(tech_stack).lower()
                ):
                    config_deps.append(
                        {
                            "type": "database",
                            "role": "consumer",
                            "requirement": "database_connection",
                        }
                    )

            # Check for API dependencies
            if "api" in str(asset.get("name", "")).lower():
                config_deps.append(
                    {
                        "type": "api",
                        "role": (
                            "provider"
                            if "server" in str(asset.get("asset_type", "")).lower()
                            else "consumer"
                        ),
                    }
                )

            if config_deps:
                dependencies.append(
                    {
                        "asset_id": str(asset.get("id", uuid.uuid4())),
                        "asset_name": asset.get("name", "Unknown"),
                        "configuration_dependencies": config_deps,
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_data_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze data flow dependencies"""
        dependencies = []

        # Group assets by type
        databases = [a for a in assets if a.get("asset_type") == "database"]
        applications = [a for a in assets if a.get("asset_type") == "application"]

        # Analyze data flow patterns
        for app in applications:
            data_flows = []

            # Check if app reads/writes to databases
            for db in databases:
                if DependencyAnalyzer._is_likely_connected(app, db):
                    data_flows.append(
                        {
                            "source": db.get("name", "Unknown DB"),
                            "target": app.get("name", "Unknown App"),
                            "flow_type": "read_write",
                            "confidence": 0.7,
                        }
                    )

            if data_flows:
                dependencies.append(
                    {
                        "asset_id": str(app.get("id", uuid.uuid4())),
                        "asset_name": app.get("name", "Unknown"),
                        "data_flows": data_flows,
                    }
                )

        return dependencies

    @staticmethod
    def _analyze_service_dependencies(
        assets: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Analyze service-level dependencies"""
        dependencies = []

        for asset in assets:
            services = []

            # Check for load balancer dependencies
            if asset.get("asset_type") == "load_balancer":
                services.append(
                    {
                        "type": "load_balancer",
                        "role": "traffic_distributor",
                        "criticality": "high",
                    }
                )

            # Check for security group dependencies
            if asset.get("asset_type") == "security_group":
                services.append(
                    {
                        "type": "security",
                        "role": "access_control",
                        "criticality": "high",
                    }
                )

            # Check environment-based dependencies
            env = asset.get("environment", "").lower()
            if env in ["production", "prod"]:
                services.append(
                    {
                        "type": "environment",
                        "role": "production_service",
                        "criticality": "critical",
                    }
                )

            if services:
                dependencies.append(
                    {
                        "asset_id": str(asset.get("id", uuid.uuid4())),
                        "asset_name": asset.get("name", "Unknown"),
                        "service_dependencies": services,
                    }
                )

        return dependencies

    @staticmethod
    def _is_likely_connected(app: Dict[str, Any], db: Dict[str, Any]) -> bool:
        """Determine if an application is likely connected to a database"""
        # Check explicit dependencies
        app_deps = app.get("dependencies", [])
        if isinstance(app_deps, list):
            for dep in app_deps:
                if db.get("name") in str(dep) or db.get("id") in str(dep):
                    return True

        # Check by environment
        if app.get("environment") == db.get("environment"):
            return True

        # Check by department/owner
        if app.get("department") == db.get("department") and app.get("department"):
            return True

        return False

    @staticmethod
    def _build_dependency_graph(
        assets: List[Dict[str, Any]],
        network_deps: List[Dict[str, Any]],
        config_deps: List[Dict[str, Any]],
        data_deps: List[Dict[str, Any]],
        service_deps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build comprehensive dependency graph"""
        nodes = []
        edges = []
        edge_id = 0

        # Create nodes for all assets
        for asset in assets:
            nodes.append(
                {
                    "id": str(asset.get("id", uuid.uuid4())),
                    "label": asset.get("name", "Unknown"),
                    "type": asset.get("asset_type", "unknown"),
                    "environment": asset.get("environment", "unknown"),
                    "criticality": asset.get("business_criticality", "medium"),
                    "metadata": {
                        "department": asset.get("department"),
                        "owner": asset.get("business_owner"),
                        "technology": asset.get("technology_stack"),
                    },
                }
            )

        # Create edges from dependencies

        # Process data dependencies (most reliable)
        for dep in data_deps:
            source_id = dep["asset_id"]
            for flow in dep.get("data_flows", []):
                # Find target asset by name
                target_asset = next(
                    (a for a in assets if a.get("name") == flow["source"]), None
                )
                if target_asset:
                    edge_id += 1
                    edges.append(
                        {
                            "id": f"edge_{edge_id}",
                            "source": str(target_asset.get("id", uuid.uuid4())),
                            "target": source_id,
                            "type": "data_flow",
                            "label": flow["flow_type"],
                            "confidence": flow["confidence"],
                        }
                    )

        # Process network dependencies
        for dep in network_deps:
            source_id = dep["asset_id"]
            for conn in dep.get("connections", []):
                if conn["type"] == "explicit":
                    # Try to find target asset
                    target_name = conn["value"]
                    target_asset = next(
                        (a for a in assets if target_name in a.get("name", "")), None
                    )
                    if target_asset:
                        edge_id += 1
                        edges.append(
                            {
                                "id": f"edge_{edge_id}",
                                "source": source_id,
                                "target": str(target_asset.get("id", uuid.uuid4())),
                                "type": "network",
                                "label": "network_connection",
                                "confidence": 0.8,
                            }
                        )

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "density": (
                len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0
            ),
        }

    @staticmethod
    def _analyze_critical_paths(dependency_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Identify critical paths and bottlenecks in the dependency graph"""
        nodes = dependency_graph.get("nodes", [])
        edges = dependency_graph.get("edges", [])

        # Count incoming and outgoing edges for each node
        edge_counts = {}
        for node in nodes:
            node_id = node["id"]
            incoming = sum(1 for e in edges if e["target"] == node_id)
            outgoing = sum(1 for e in edges if e["source"] == node_id)
            edge_counts[node_id] = {
                "incoming": incoming,
                "outgoing": outgoing,
                "total": incoming + outgoing,
                "node": node,
            }

        # Identify bottlenecks (nodes with high connectivity)
        bottlenecks = []
        for node_id, counts in edge_counts.items():
            if counts["total"] > 3:  # Threshold for bottleneck
                bottlenecks.append(
                    {
                        "node_id": node_id,
                        "node_name": counts["node"]["label"],
                        "incoming_connections": counts["incoming"],
                        "outgoing_connections": counts["outgoing"],
                        "total_connections": counts["total"],
                        "risk_level": "high" if counts["total"] > 5 else "medium",
                    }
                )

        # Detect circular dependencies
        circular_deps = DependencyAnalyzer._detect_circular_dependencies(edges)

        # Identify critical paths (chains of dependencies)
        critical_paths = DependencyAnalyzer._find_critical_paths(nodes, edges)

        return {
            "bottlenecks": sorted(
                bottlenecks, key=lambda x: x["total_connections"], reverse=True
            ),
            "circular_dependencies": circular_deps,
            "critical_paths": critical_paths,
        }

    @staticmethod
    def _detect_circular_dependencies(
        edges: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detect circular dependencies in the graph"""
        circular = []
        adjacency = {}

        # Build adjacency list
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source not in adjacency:
                adjacency[source] = []
            adjacency[source].append(target)

        # Simple cycle detection (for pairs)
        for source, targets in adjacency.items():
            for target in targets:
                if target in adjacency and source in adjacency[target]:
                    cycle = sorted([source, target])
                    cycle_key = f"{cycle[0]}-{cycle[1]}"
                    if not any(c["cycle_id"] == cycle_key for c in circular):
                        circular.append(
                            {
                                "cycle_id": cycle_key,
                                "nodes": cycle,
                                "type": "bidirectional",
                                "severity": "high",
                            }
                        )

        return circular

    @staticmethod
    def _find_critical_paths(
        nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find critical dependency paths"""
        paths = []

        # Find nodes with no incoming edges (potential start points)
        node_ids = {n["id"] for n in nodes}
        targets = {e["target"] for e in edges}
        sources = {e["source"] for e in edges}

        start_nodes = node_ids - targets  # Nodes with no incoming edges
        end_nodes = node_ids - sources  # Nodes with no outgoing edges

        # Build simple paths from start to end nodes
        for start in start_nodes:
            for end in end_nodes:
                if start != end:
                    path = DependencyAnalyzer._find_path(start, end, edges)
                    if path and len(path) > 2:  # Only include paths with 3+ nodes
                        start_node = next((n for n in nodes if n["id"] == start), {})
                        end_node = next((n for n in nodes if n["id"] == end), {})
                        paths.append(
                            {
                                "path_id": f"path_{len(paths) + 1}",
                                "start": start_node.get("label", "Unknown"),
                                "end": end_node.get("label", "Unknown"),
                                "length": len(path),
                                "nodes": path,
                                "criticality": "high" if len(path) > 4 else "medium",
                            }
                        )

        return paths[:5]  # Return top 5 critical paths

    @staticmethod
    def _find_path(start: str, end: str, edges: List[Dict[str, Any]]) -> List[str]:
        """Find a path between two nodes (simple BFS)"""
        if start == end:
            return [start]

        adjacency = {}
        for edge in edges:
            if edge["source"] not in adjacency:
                adjacency[edge["source"]] = []
            adjacency[edge["source"]].append(edge["target"])

        queue = [(start, [start])]
        visited = {start}

        while queue:
            node, path = queue.pop(0)

            if node in adjacency:
                for neighbor in adjacency[node]:
                    if neighbor == end:
                        return path + [neighbor]
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, path + [neighbor]))

        return []

    @staticmethod
    def _generate_migration_insights(
        dependency_graph: Dict[str, Any], critical_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate migration insights based on dependency analysis"""
        insights = []

        # Insight about bottlenecks
        bottlenecks = critical_analysis.get("bottlenecks", [])
        if bottlenecks:
            top_bottleneck = bottlenecks[0]
            insights.append(
                {
                    "type": "bottleneck",
                    "severity": "high",
                    "message": (
                        f"{top_bottleneck['node_name']} is a critical bottleneck with "
                        f"{top_bottleneck['total_connections']} dependencies"
                    ),
                    "recommendation": "Consider migrating this component early with careful planning",
                    "affected_assets": [top_bottleneck["node_name"]],
                }
            )

        # Insight about circular dependencies
        circular = critical_analysis.get("circular_dependencies", [])
        if circular:
            insights.append(
                {
                    "type": "circular_dependency",
                    "severity": "high",
                    "message": f"Found {len(circular)} circular dependencies that need resolution",
                    "recommendation": "Migrate circular dependent components together as a unit",
                    "affected_assets": [c["nodes"] for c in circular],
                }
            )

        # Insight about isolated components
        node_count = dependency_graph.get("node_count", 0)
        if node_count > 0:
            density = dependency_graph.get("density", 0)
            if density < 0.1:
                insights.append(
                    {
                        "type": "low_coupling",
                        "severity": "low",
                        "message": "System has low coupling, which is good for migration",
                        "recommendation": "Components can be migrated independently",
                        "affected_assets": [],
                    }
                )
            elif density > 0.5:
                insights.append(
                    {
                        "type": "high_coupling",
                        "severity": "high",
                        "message": "System has high coupling, requiring careful migration planning",
                        "recommendation": "Consider wave-based migration with dependency groups",
                        "affected_assets": [],
                    }
                )

        # Insight about critical paths
        paths = critical_analysis.get("critical_paths", [])
        if paths:
            longest_path = max(paths, key=lambda x: x["length"]) if paths else None
            if longest_path:
                insights.append(
                    {
                        "type": "critical_path",
                        "severity": "medium",
                        "message": f"Longest dependency chain has {longest_path['length']} components",
                        "recommendation": "Test end-to-end functionality after each migration step",
                        "affected_assets": [longest_path["start"], longest_path["end"]],
                    }
                )

        return insights


def create_dependency_analysis_tools(context_info: Dict[str, Any]) -> List:
    """
    Create tools for agents to analyze dependencies and build dependency graphs

    Args:
        context_info: Dictionary containing client_account_id, engagement_id, flow_id

    Returns:
        List of dependency analysis tools
    """
    logger.info("🔧 Creating dependency analysis tools for persistent agents")

    if not CREWAI_TOOLS_AVAILABLE:
        logger.warning("⚠️ CrewAI tools not available - returning empty list")
        return []

    try:
        tools = []

        # Use factory functions to create tools
        analyzer = _create_dependency_analysis_tool(context_info)
        tools.append(analyzer)

        graph_builder = _create_dependency_graph_builder_tool(context_info)
        tools.append(graph_builder)

        wave_planner = _create_migration_wave_planner_tool(context_info)
        tools.append(wave_planner)

        logger.info(f"✅ Created {len(tools)} dependency analysis tools")
        return tools
    except Exception as e:
        logger.error(f"❌ Failed to create dependency analysis tools: {e}")
        return []


# Factory functions to create tools
def _create_dependency_analysis_tool(context_info: Dict[str, Any]):
    """Create dependency analysis tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyDependencyAnalysisTool(context_info)
    return DependencyAnalysisTool(context_info)


def _create_dependency_graph_builder_tool(context_info: Dict[str, Any]):
    """Create dependency graph builder tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyDependencyGraphBuilderTool(context_info)
    return DependencyGraphBuilderTool(context_info)


def _create_migration_wave_planner_tool(context_info: Dict[str, Any]):
    """Create migration wave planner tool"""
    if not CREWAI_TOOLS_AVAILABLE:
        return DummyMigrationWavePlannerTool(context_info)
    return MigrationWavePlannerTool(context_info)


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
            assets = request.get("assets", [])

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

            # If we already have analysis results, extract the graph
            if "dependency_graph" in request:
                graph = request["dependency_graph"]
            else:
                # Build graph from assets
                assets = request.get("assets", [])
                analysis = DependencyAnalyzer.analyze_dependencies(assets)
                graph = analysis.get("dependency_graph", {})

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
