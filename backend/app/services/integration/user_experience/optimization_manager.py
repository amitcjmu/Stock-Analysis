"""
Optimization Manager

Manages application and tracking of UX optimizations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from .base import UXRecommendation

logger = logging.getLogger(__name__)


class OptimizationManager:
    """Manages UX optimization application and tracking"""

    def __init__(self):
        self.user_preferences: Dict[UUID, Dict[str, Any]] = {}

    async def apply_optimizations(
        self,
        engagement_id: UUID,
        user_id: UUID,
        optimization_ids: List[str],
        cached_recommendations: List[UXRecommendation],
    ) -> Dict[str, Any]:
        """Apply selected UX optimizations"""

        logger.info(
            "Applying UX optimizations",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id),
                "optimization_ids": optimization_ids,
            },
        )

        applied_optimizations = []
        failed_optimizations = []

        for opt_id in optimization_ids:
            try:
                # Find recommendation
                recommendation = next(
                    (r for r in cached_recommendations if r.id == opt_id), None
                )
                if not recommendation:
                    failed_optimizations.append(
                        {"id": opt_id, "reason": "Recommendation not found"}
                    )
                    continue

                # Apply optimization based on area
                success = await self._apply_single_optimization(
                    engagement_id, user_id, recommendation
                )

                if success:
                    applied_optimizations.append(
                        {
                            "id": opt_id,
                            "title": recommendation.title,
                            "area": recommendation.area.value,
                        }
                    )
                else:
                    failed_optimizations.append(
                        {"id": opt_id, "reason": "Implementation failed"}
                    )

            except Exception as e:
                failed_optimizations.append({"id": opt_id, "reason": str(e)})

        return {
            "applied": applied_optimizations,
            "failed": failed_optimizations,
            "engagement_id": str(engagement_id),
        }

    async def _apply_single_optimization(
        self, engagement_id: UUID, user_id: UUID, recommendation: UXRecommendation
    ) -> bool:
        """Apply a specific optimization"""

        # This would implement actual optimization application
        # For now, return success for demonstration

        logger.info(
            f"Applying optimization: {recommendation.title}",
            extra={
                "engagement_id": str(engagement_id),
                "user_id": str(user_id),
                "optimization_area": recommendation.area.value,
            },
        )

        # Store user preference if applicable
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {}

        self.user_preferences[user_id][recommendation.id] = {
            "applied_at": datetime.utcnow(),
            "area": recommendation.area.value,
            "expected_improvement": recommendation.expected_improvement,
        }

        return True

    def get_user_optimization_history(self, user_id: UUID) -> Dict[str, Any]:
        """Get optimization history for a user"""

        user_prefs = self.user_preferences.get(user_id, {})

        return {
            "user_id": str(user_id),
            "total_optimizations": len(user_prefs),
            "optimization_history": [
                {
                    "optimization_id": opt_id,
                    "area": details["area"],
                    "applied_at": details["applied_at"].isoformat(),
                    "expected_improvement": details["expected_improvement"],
                }
                for opt_id, details in user_prefs.items()
            ],
        }

    def clear_user_preferences(self, user_id: UUID) -> None:
        """Clear optimization preferences for a user"""
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
            logger.info(f"Cleared optimization preferences for user {user_id}")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get overall optimization statistics"""

        total_users = len(self.user_preferences)
        total_optimizations = sum(
            len(prefs) for prefs in self.user_preferences.values()
        )

        # Count by optimization area
        area_counts = {}
        for user_prefs in self.user_preferences.values():
            for details in user_prefs.values():
                area = details["area"]
                area_counts[area] = area_counts.get(area, 0) + 1

        return {
            "total_users_with_optimizations": total_users,
            "total_optimizations_applied": total_optimizations,
            "average_optimizations_per_user": (
                total_optimizations / total_users if total_users > 0 else 0
            ),
            "optimization_by_area": area_counts,
        }
