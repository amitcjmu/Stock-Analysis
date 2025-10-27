"""
Assessment Data Repository - Dependency Queries

Mixin for dependency analysis data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.canonical_applications import CanonicalApplication
from app.models.asset import Asset

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
        """Build dependency graph structure from available data."""
        return {
            "nodes": {
                "applications": [str(app.id) for app in applications],
                "servers": [str(srv.id) for srv in servers],
            },
            "edges": [],  # To be populated by agent analysis
            "metadata": {
                "app_count": len(applications),
                "server_count": len(servers),
                "inventory_types": len(inventory_data.get("by_type", [])),
            },
        }
