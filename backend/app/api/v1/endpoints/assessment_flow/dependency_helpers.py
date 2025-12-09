"""
Helper functions for dependency analysis endpoints.

Extracted from dependency_endpoints.py for modularization compliance.
"""

from typing import Any, Dict


def build_empty_dependency_response(flow_id: str) -> Dict[str, Any]:
    """
    Build empty dependency response when no applications are selected.

    Args:
        flow_id: Child flow UUID

    Returns:
        Dict with empty graph structure
    """
    return {
        "flow_id": flow_id,
        "app_server_dependencies": [],
        "app_app_dependencies": [],
        "applications": [],
        "dependency_graph": {
            "nodes": [],
            "edges": [],
            "metadata": {
                "dependency_count": 0,
                "node_count": 0,
                "app_count": 0,
                "server_count": 0,
            },
        },
        "agent_results": None,
        "message": "No applications selected for assessment",
    }


def populate_application_dependencies(
    filtered_apps: list[Dict[str, Any]], all_deps: list[Dict[str, Any]]
) -> None:
    """
    Populate dependencies field on applications for frontend table display.

    Modifies filtered_apps in-place to add:
    - dependencies: Comma-separated string of dependency IDs
    - dependency_names: Comma-separated string of dependency names

    Args:
        filtered_apps: List of application metadata dicts (modified in-place)
        all_deps: List of all dependency records
    """
    for app in filtered_apps:
        app_id = app["id"]
        dep_ids = []
        dep_names = []

        # Collect ALL dependencies (server, database, application, network, etc.)
        for dep in all_deps:
            if dep.get("source_app_id") == app_id:
                target_info = dep.get("target_info", {})
                target_id = target_info.get("id")
                target_name = target_info.get("name")
                if target_id:
                    dep_ids.append(target_id)
                    if target_name:
                        dep_names.append(target_name)

        # Set dependencies as comma-separated string (or None if no deps)
        app["dependencies"] = ",".join([str(d) for d in dep_ids]) if dep_ids else None
        # Add dependency_names for display in frontend table
        app["dependency_names"] = ",".join(dep_names) if dep_names else None


def build_dependency_graph(
    filtered_apps: list[Dict[str, Any]], all_deps: list[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Construct dependency graph from application and dependency data.

    Builds graph structure with nodes (applications, servers, databases, etc.)
    and edges (dependencies between assets).

    Args:
        filtered_apps: List of selected application metadata
        all_deps: List of all dependency records

    Returns:
        Dict with:
        - nodes: List of graph nodes with type, name, metadata
        - edges: List of directed edges (source -> target)
        - metadata: Graph statistics (counts)
    """
    nodes = []
    edges = []
    node_ids = set()

    # Add source application nodes from filtered_apps
    for app in filtered_apps:
        app_id = app["id"]
        if app_id not in node_ids:
            nodes.append(
                {
                    "id": app_id,
                    "name": app.get("application_name") or app.get("name"),
                    "type": "application",
                    "business_criticality": app.get("business_criticality"),
                }
            )
            node_ids.add(app_id)

    # Add source application nodes from dependencies (in case not in filtered_apps)
    for dep in all_deps:
        source_id = dep.get("source_app_id")
        if source_id and source_id not in node_ids:
            nodes.append(
                {
                    "id": source_id,
                    "name": dep.get("source_app_name"),
                    "type": "application",
                }
            )
            node_ids.add(source_id)

    # Add target asset nodes and edges from all_deps (unified query)
    for dep in all_deps:
        target_info = dep.get("target_info", {})
        target_id = target_info.get("id")
        target_type = target_info.get("type", "unknown")

        # Add target node if not already present
        if target_id and target_id not in node_ids:
            node_data = {
                "id": target_id,
                "name": target_info.get("name"),
                "type": target_type,
            }

            # Add type-specific fields
            if target_type == "server":
                node_data["hostname"] = target_info.get("hostname")
            elif target_type in ("application", "database"):
                node_data["application_name"] = target_info.get("application_name")

            nodes.append(node_data)
            node_ids.add(target_id)

        # Add edge
        edges.append(
            {
                "source": dep.get("source_app_id"),
                "target": target_id,
                "type": dep.get("dependency_type", "unknown"),
                "source_name": dep.get("source_app_name"),
                "target_name": target_info.get("name"),
            }
        )

    # Count node types
    app_count = sum(1 for n in nodes if n["type"] == "application")
    server_count = sum(1 for n in nodes if n["type"] == "server")

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "dependency_count": len(edges),
            "node_count": len(nodes),
            "app_count": app_count,
            "server_count": server_count,
        },
    }
