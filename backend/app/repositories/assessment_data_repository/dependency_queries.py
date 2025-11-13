"""
Assessment Data Repository - Dependency Queries

Mixin for dependency analysis data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.core.logging import get_logger
from app.models.canonical_applications import CanonicalApplication
from app.models.asset import Asset, AssetDependency

logger = get_logger(__name__)


class DependencyQueriesMixin:
    """Mixin for dependency analysis data queries"""

    async def get_dependency_data(self, flow_id: str) -> Dict[str, Any]:
        """
        Fetch data for dependency analysis phase.

        Retrieves application dependencies, infrastructure dependencies,
        data dependencies, and integration dependencies.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - applications: Application details
                - infrastructure_dependencies: Server/infrastructure relationships
                - data_dependencies: Data flow dependencies
                - integration_dependencies: Integration points
        """
        try:
            # Get applications
            applications = await self._get_applications()

            # Get infrastructure data for dependency mapping
            servers = await self._get_servers()

            # Get collected inventory for dependency inference
            inventory_data = await self._get_collected_inventory()

            # Build dependency graph data
            dependency_graph = await self._build_dependency_graph(
                applications, servers, inventory_data
            )

            return {
                "applications": [
                    self._serialize_application(app) for app in applications
                ],
                "infrastructure": [self._serialize_server(srv) for srv in servers],
                "dependency_graph": dependency_graph,
                "collected_inventory": inventory_data,
                "engagement_id": str(self.engagement_id),
            }

        except Exception as e:
            logger.error(f"Error fetching dependency data: {e}")
            return self._empty_dependency_data()

    async def _build_dependency_graph(
        self,
        applications: List[CanonicalApplication],
        servers: List[Asset],
        inventory_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build dependency graph structure with actual edges from asset_dependencies.

        Fetches real dependency relationships from the database and constructs
        a D3.js-compatible graph structure with nodes and edges.

        Args:
            applications: List of canonical applications
            servers: List of server assets
            inventory_data: Additional inventory context

        Returns:
            Dictionary with:
                - nodes: List of node objects with id, name, and type
                - edges: List of edge objects with source, target, and type
                - metadata: Summary statistics including dependency_count
        """
        # Build nodes list with human-readable names
        nodes = []

        # Add application nodes
        for app in applications:
            nodes.append(
                {
                    "id": str(app.id),
                    "name": app.canonical_name or f"App-{app.id}",
                    "type": "application",
                    "business_criticality": app.business_criticality,
                }
            )

        # Add server nodes
        for srv in servers:
            nodes.append(
                {
                    "id": str(srv.id),
                    "name": srv.name
                    or srv.asset_name
                    or srv.hostname
                    or f"Server-{srv.id}",
                    "type": "server",
                    "hostname": srv.hostname,
                }
            )

        # Fetch actual dependencies from asset_dependencies table
        edges = []
        try:
            # Create aliases for source and target assets
            SourceAsset = aliased(Asset)
            TargetAsset = aliased(Asset)

            # Query asset_dependencies with tenant scoping via joined Asset tables
            query = (
                select(
                    AssetDependency.asset_id,
                    AssetDependency.depends_on_asset_id,
                    AssetDependency.dependency_type,
                    AssetDependency.confidence_score,
                    SourceAsset.name.label("source_name"),
                    SourceAsset.asset_type.label("source_type"),
                    TargetAsset.name.label("target_name"),
                    TargetAsset.asset_type.label("target_type"),
                )
                .select_from(AssetDependency)
                .join(SourceAsset, SourceAsset.id == AssetDependency.asset_id)
                .join(
                    TargetAsset, TargetAsset.id == AssetDependency.depends_on_asset_id
                )
                .where(
                    SourceAsset.client_account_id == self.client_account_id,
                    SourceAsset.engagement_id == self.engagement_id,
                    TargetAsset.client_account_id == self.client_account_id,
                    TargetAsset.engagement_id == self.engagement_id,
                )
            )

            # Filter to only include dependencies involving selected applications/servers
            # Optimize: filter in database instead of Python for performance
            all_node_ids = {app.id for app in applications} | {
                srv.id for srv in servers
            }

            # Add WHERE clause to filter dependencies at database level
            query = query.where(
                AssetDependency.asset_id.in_(all_node_ids),
                AssetDependency.depends_on_asset_id.in_(all_node_ids),
            )

            result = await self.db.execute(query)
            rows = result.all()

            # All rows are now guaranteed to be in our selected nodes (database filtered)
            for row in rows:
                edges.append(
                    {
                        "source": str(row.asset_id),
                        "target": str(row.depends_on_asset_id),
                        "type": row.dependency_type,
                        "confidence_score": row.confidence_score or 1.0,
                        "source_name": row.source_name,
                        "target_name": row.target_name,
                    }
                )

            logger.info(
                f"Built dependency graph: {len(nodes)} nodes, {len(edges)} edges "
                f"(client={self.client_account_id}, engagement={self.engagement_id})"
            )

        except Exception as e:
            logger.error(f"Error fetching dependency edges: {e}")
            # Continue with empty edges rather than failing

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "app_count": len(applications),
                "server_count": len(servers),
                "inventory_types": len(inventory_data.get("by_type", [])),
                "dependency_count": len(edges),
                "node_count": len(nodes),
            },
        }
