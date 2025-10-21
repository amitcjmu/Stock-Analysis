"""
Assessment Input Builders - Dependency Builder

Mixin for building dependency analysis inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class DependencyBuilderMixin:
    """Mixin for dependency analysis input building"""

    async def build_dependency_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for dependency analysis phase.

        Includes application dependencies, infrastructure dependencies,
        data dependencies, and integration dependencies.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user-provided dependency information

        Returns:
            Structured input dictionary containing:
                - Application dependencies
                - Infrastructure dependencies
                - Data dependencies
                - Integration dependencies
                - User-provided dependency information
        """
        try:
            # Fetch context data from repository
            context_data = await self.data_repo.get_dependency_data(flow_id)

            # Extract user-provided dependency info
            dependency_info = (user_input or {}).get("dependency_info", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "dependency_analysis",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "infrastructure": context_data.get("infrastructure", []),
                    "dependency_graph": context_data.get("dependency_graph", {}),
                    "collected_inventory": context_data.get("collected_inventory", {}),
                },
                "dependency_info": {
                    "known_dependencies": dependency_info.get("known_dependencies", []),
                    "external_systems": dependency_info.get("external_systems", []),
                    "data_flows": dependency_info.get("data_flows", []),
                    "integration_protocols": dependency_info.get(
                        "integration_protocols", []
                    ),
                },
                "previous_phase_results": {
                    # Results from readiness and complexity will be added by execution engine
                    "readiness_assessment": {},
                    "complexity_analysis": {},
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "dependency_analysis",
                },
            }

        except Exception as e:
            logger.error(f"Error building dependency input: {e}")
            return self._build_fallback_input(
                flow_id, "dependency_analysis", user_input
            )
