"""
Assessment Input Builders - Recommendation Builder

Mixin for building recommendation generation inputs.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class RecommendationBuilderMixin:
    """Mixin for recommendation generation input building"""

    async def build_recommendation_input(
        self, flow_id: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build input for recommendation generation phase.

        Aggregates results from all previous phases along with business objectives,
        timeline constraints, and budget constraints for final recommendations.

        Args:
            flow_id: Assessment flow UUID
            user_input: Optional user preferences for recommendations

        Returns:
            Structured input dictionary containing:
                - Results from all previous phases
                - Business objectives
                - Timeline constraints
                - Budget constraints
                - User preferences
        """
        try:
            # Fetch recommendation data (includes all phase results)
            context_data = await self.data_repo.get_recommendation_data(flow_id)

            # Extract user preferences
            user_preferences = (user_input or {}).get("preferences", {})

            # Build structured input
            return {
                "flow_id": flow_id,
                "client_account_id": str(self.data_repo.client_account_id),
                "engagement_id": str(self.data_repo.engagement_id),
                "phase_name": "recommendation_generation",
                "user_input": user_input or {},
                "context_data": {
                    "applications": context_data.get("applications", []),
                    "business_objectives": context_data.get("business_objectives", []),
                    "timeline_constraints": context_data.get(
                        "timeline_constraints", {}
                    ),
                    "budget_constraints": context_data.get("budget_constraints", {}),
                },
                "user_preferences": {
                    "preferred_strategy": user_preferences.get(
                        "preferred_strategy", ""
                    ),
                    "target_cloud": user_preferences.get("target_cloud", ""),
                    "automation_level": user_preferences.get(
                        "automation_level", "high"
                    ),
                    "prioritization": user_preferences.get(
                        "prioritization", "business_value"
                    ),
                },
                "previous_phase_results": context_data.get("all_phase_results", {}),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "phase_version": "1.0.0",
                    "builder": "recommendation_generation",
                },
            }

        except Exception as e:
            logger.error(f"Error building recommendation input: {e}")
            return self._build_fallback_input(
                flow_id, "recommendation_generation", user_input
            )
