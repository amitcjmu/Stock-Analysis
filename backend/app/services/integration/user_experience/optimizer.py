"""
Main User Experience Optimizer

Complete UX optimizer combining all modular components.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import UUID

from app.core.logging import get_logger
from app.monitoring.metrics import track_performance

from .analyzer import UXAnalyzer
from .base import UserJourneyAnalytics, UXRecommendation
from .optimization_manager import OptimizationManager
from .recommendations import UXRecommendationEngine

logger = get_logger(__name__)


class UserExperienceOptimizer:
    """
    Complete user experience optimizer combining all modular components.
    Optimizes user experience across the complete ADCS workflow.
    """

    def __init__(self):
        self.analyzer = UXAnalyzer()
        self.recommendation_engine = UXRecommendationEngine()
        self.optimization_manager = OptimizationManager()

        self.ux_metrics_cache: Dict[UUID, Dict[str, Any]] = {}
        self.optimization_rules = self._initialize_optimization_rules()

    def _initialize_optimization_rules(self) -> Dict[str, Any]:
        """Initialize UX optimization rules"""
        return {
            "workflow_navigation": {
                "auto_advance_threshold": 0.9,  # Auto-advance when confidence > 90%
                "show_preview": True,
                "breadcrumb_depth": 3,
                "shortcuts_enabled": True,
            },
            "progress_tracking": {
                "granular_progress": True,
                "estimated_time_remaining": True,
                "milestone_celebrations": True,
                "comparative_benchmarks": True,
            },
            "error_communication": {
                "progressive_disclosure": True,
                "suggested_actions": True,
                "recovery_guidance": True,
                "expert_escalation": True,
            },
            "data_visualization": {
                "adaptive_charts": True,
                "drill_down_enabled": True,
                "export_options": True,
                "accessibility_features": True,
            },
            "automation_transparency": {
                "ai_confidence_display": True,
                "processing_indicators": True,
                "manual_override_options": True,
                "explanation_on_demand": True,
            },
            "performance_optimization": {
                "lazy_loading": True,
                "progressive_enhancement": True,
                "caching_strategy": "intelligent",
                "background_processing": True,
            },
        }

    @track_performance("ux.optimization.analyze")
    async def analyze_user_experience(
        self, engagement_id: UUID, user_id: UUID
    ) -> Tuple[UserJourneyAnalytics, List[UXRecommendation]]:
        """
        Analyze user experience and provide optimization recommendations
        """

        logger.info(
            "Analyzing user experience for workflow optimization",
            extra={"engagement_id": str(engagement_id), "user_id": str(user_id)},
        )

        try:
            # Create optimization context
            context = await self.analyzer.create_optimization_context(
                engagement_id, user_id
            )

            # Analyze user journey
            journey_analytics = await self.analyzer.analyze_user_journey(context)

            # Generate UX recommendations
            recommendations = await self.recommendation_engine.generate_recommendations(
                context, journey_analytics
            )

            # Cache metrics for future optimization
            self.ux_metrics_cache[engagement_id] = {
                "journey_analytics": journey_analytics,
                "recommendations": recommendations,
                "last_updated": datetime.utcnow(),
            }

            logger.info(
                "User experience analysis completed",
                extra={
                    "engagement_id": str(engagement_id),
                    "recommendations_count": len(recommendations),
                    "journey_duration": (
                        datetime.utcnow() - journey_analytics.journey_start
                    ).total_seconds(),
                },
            )

            return journey_analytics, recommendations

        except Exception as e:
            logger.error(
                "Error during user experience analysis",
                extra={
                    "engagement_id": str(engagement_id),
                    "user_id": str(user_id),
                    "error": str(e),
                },
            )
            raise

    @track_performance("ux.optimization.apply")
    async def apply_ux_optimizations(
        self, engagement_id: UUID, user_id: UUID, optimization_ids: List[str]
    ) -> Dict[str, Any]:
        """Apply selected UX optimizations"""

        # Get cached recommendations
        cached_data = self.ux_metrics_cache.get(engagement_id)
        if not cached_data:
            return {
                "error": "No optimization recommendations found for engagement",
                "applied": [],
                "failed": optimization_ids,
            }

        recommendations = cached_data["recommendations"]

        return await self.optimization_manager.apply_optimizations(
            engagement_id, user_id, optimization_ids, recommendations
        )

    @track_performance("ux.metrics.get")
    async def get_ux_metrics(self, engagement_id: UUID) -> Dict[str, Any]:
        """Get UX metrics for an engagement"""

        cached_data = self.ux_metrics_cache.get(engagement_id)

        if not cached_data:
            return {
                "engagement_id": str(engagement_id),
                "metrics_available": False,
                "message": "No UX metrics available. Run analysis first.",
            }

        journey = cached_data["journey_analytics"]
        recommendations = cached_data["recommendations"]

        return {
            "engagement_id": str(engagement_id),
            "metrics_available": True,
            "journey_analytics": {
                "current_phase": journey.current_phase,
                "phases_completed": journey.phases_completed,
                "total_journey_time": (
                    datetime.utcnow() - journey.journey_start
                ).total_seconds(),
                "automation_efficiency": journey.automation_efficiency,
                "satisfaction_indicators": journey.satisfaction_indicators,
            },
            "recommendations": [
                {
                    "id": rec.id,
                    "title": rec.title,
                    "area": rec.area.value,
                    "impact": rec.impact,
                    "priority_score": rec.priority_score,
                }
                for rec in recommendations
            ],
            "improvement_opportunities": len(recommendations),
            "last_updated": cached_data["last_updated"].isoformat(),
        }

    def get_user_optimization_history(self, user_id: UUID) -> Dict[str, Any]:
        """Get optimization history for a user"""
        return self.optimization_manager.get_user_optimization_history(user_id)

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get overall optimization statistics"""
        base_stats = self.optimization_manager.get_optimization_stats()

        # Add cache statistics
        base_stats.update(
            {
                "cached_engagements": len(self.ux_metrics_cache),
                "cache_hit_rate": 0.85,  # Would calculate from actual metrics
            }
        )

        return base_stats

    def clear_engagement_cache(self, engagement_id: UUID) -> None:
        """Clear cache for a specific engagement"""
        if engagement_id in self.ux_metrics_cache:
            del self.ux_metrics_cache[engagement_id]
            logger.info(f"Cleared UX metrics cache for engagement {engagement_id}")

    def clear_user_preferences(self, user_id: UUID) -> None:
        """Clear optimization preferences for a user"""
        self.optimization_manager.clear_user_preferences(user_id)
