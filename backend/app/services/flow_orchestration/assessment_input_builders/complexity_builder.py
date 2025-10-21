"""
Assessment Input Builders - Complexity Builder

Mixin for building complexity analysis inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class ComplexityBuilderMixin:
    """Mixin for complexity analysis input building"""

    async def build_complexity_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for complexity analysis phase.

        Includes component inventory, integration points, customization level,
        and technology stack complexity for detailed complexity assessment.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user-provided complexity factors

        Returns:
            Structured input dictionary containing:
                - Component inventory
                - Integration points
                - Customization level
                - Technology stack complexity
                - User-provided complexity factors
        """
        try:
            # Fetch context data from repository
            context_data = await self.data_repo.get_complexity_data(flow_id)

            # Extract user-provided factors
            complexity_factors = (user_input or {}).get("complexity_factors", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "complexity_analysis",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "inventory_by_type": context_data.get("inventory_by_type", {}),
                    "complexity_indicators": context_data.get(
                        "complexity_indicators", {}
                    ),
                    "total_applications": context_data.get("total_applications", 0),
                },
                "complexity_factors": {
                    "integration_count": complexity_factors.get("integration_count", 0),
                    "customization_level": complexity_factors.get(
                        "customization_level", "low"
                    ),
                    "data_volume": complexity_factors.get("data_volume", "small"),
                    "user_base_size": complexity_factors.get("user_base_size", 0),
                    "transaction_volume": complexity_factors.get(
                        "transaction_volume", "low"
                    ),
                },
                "previous_phase_results": {
                    # Results from readiness phase will be added by execution engine
                    "readiness_assessment": {}
                },
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "complexity_analysis",
                },
            }

        except Exception as e:
            logger.error(f"Error building complexity input: {e}")
            return self._build_fallback_input(
                flow_id, "complexity_analysis", user_input
            )
