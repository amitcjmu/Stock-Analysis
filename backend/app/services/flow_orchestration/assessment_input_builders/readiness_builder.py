"""
Assessment Input Builders - Readiness Builder

Mixin for building readiness assessment inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class ReadinessBuilderMixin:
    """Mixin for readiness assessment input building"""

    async def build_readiness_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for readiness assessment phase.

        Combines application metadata, technology stack info, architecture
        standards, and current environment details for readiness evaluation.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user-provided readiness criteria

        Returns:
            Structured input dictionary containing:
                - Application metadata (name, type, criticality)
                - Technology stack information
                - Architecture standards
                - Current environment details
                - User-provided readiness criteria
        """
        try:
            # Fetch context data from repository
            context_data = await self.data_repo.get_readiness_data(flow_id)

            # Extract user-provided criteria
            readiness_criteria = (user_input or {}).get("readiness_criteria", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "readiness_assessment",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "discovery_results": context_data.get("discovery_results", {}),
                    "infrastructure_count": context_data.get("infrastructure_count", 0),
                    "collected_inventory": context_data.get("collected_inventory", {}),
                },
                "readiness_criteria": {
                    "migration_strategy": readiness_criteria.get(
                        "migration_strategy", ""
                    ),
                    "target_platform": readiness_criteria.get("target_platform", ""),
                    "compliance_requirements": readiness_criteria.get(
                        "compliance_requirements", []
                    ),
                    "timeline_constraint": readiness_criteria.get(
                        "timeline_constraint", ""
                    ),
                    "budget_constraint": readiness_criteria.get(
                        "budget_constraint", ""
                    ),
                },
                "previous_phase_results": {},  # First phase, no prior results
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "readiness_assessment",
                },
            }

        except Exception as e:
            logger.error(f"Error building readiness input: {e}")
            return self._build_fallback_input(
                flow_id, "readiness_assessment", user_input
            )
