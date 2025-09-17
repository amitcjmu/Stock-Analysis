"""
Utility functions for dependency analysis.

This module contains helper functions used across the dependency analysis
tools, including path finding and graph utilities.
"""

from typing import Any, Dict, List


def find_path(start: str, end: str, edges: List[Dict[str, Any]]) -> List[str]:
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


def build_adjacency_list(edges: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build adjacency list from edges"""
    adjacency = {}
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in adjacency:
            adjacency[source] = []
        adjacency[source].append(target)
    return adjacency


def calculate_graph_metrics(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate basic graph metrics"""
    node_count = len(nodes)
    edge_count = len(edges)

    # Calculate density
    max_edges = node_count * (node_count - 1) if node_count > 1 else 0
    density = edge_count / max_edges if max_edges > 0 else 0

    # Calculate degree distribution
    in_degrees = {}
    out_degrees = {}

    # Initialize all nodes with 0 degree
    for node in nodes:
        node_id = node["id"]
        in_degrees[node_id] = 0
        out_degrees[node_id] = 0

    # Count degrees from edges
    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source in out_degrees:
            out_degrees[source] += 1
        if target in in_degrees:
            in_degrees[target] += 1

    return {
        "node_count": node_count,
        "edge_count": edge_count,
        "density": density,
        "in_degrees": in_degrees,
        "out_degrees": out_degrees,
        "avg_in_degree": sum(in_degrees.values()) / node_count if node_count > 0 else 0,
        "avg_out_degree": (
            sum(out_degrees.values()) / node_count if node_count > 0 else 0
        ),
    }


def find_isolated_nodes(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> List[str]:
    """Find nodes with no connections"""
    connected_nodes = set()
    for edge in edges:
        connected_nodes.add(edge["source"])
        connected_nodes.add(edge["target"])

    isolated = []
    for node in nodes:
        if node["id"] not in connected_nodes:
            isolated.append(node["id"])

    return isolated


def group_nodes_by_attribute(
    nodes: List[Dict[str, Any]], attribute: str
) -> Dict[str, List[Dict[str, Any]]]:
    """Group nodes by a specific attribute"""
    groups = {}
    for node in nodes:
        value = node.get(attribute, "unknown")
        if value not in groups:
            groups[value] = []
        groups[value].append(node)
    return groups


def validate_graph_structure(
    nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Validate graph structure and identify issues"""
    issues = []
    node_ids = {node["id"] for node in nodes}

    # Check for edges referencing non-existent nodes
    for edge in edges:
        if edge["source"] not in node_ids:
            issues.append(f"Edge references non-existent source node: {edge['source']}")
        if edge["target"] not in node_ids:
            issues.append(f"Edge references non-existent target node: {edge['target']}")

    # Check for duplicate node IDs
    seen_ids = set()
    for node in nodes:
        node_id = node["id"]
        if node_id in seen_ids:
            issues.append(f"Duplicate node ID: {node_id}")
        seen_ids.add(node_id)

    # Check for self-loops
    self_loops = []
    for edge in edges:
        if edge["source"] == edge["target"]:
            self_loops.append(edge["id"])

    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "self_loops": self_loops,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
