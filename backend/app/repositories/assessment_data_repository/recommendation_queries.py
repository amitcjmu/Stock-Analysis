"""
Assessment Data Repository - Recommendation Queries

Mixin for recommendation generation data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict

from app.core.logging import get_logger

logger = get_logger(__name__)


class RecommendationQueriesMixin:
    """Mixin for recommendation generation data queries"""

    async def get_recommendation_data(self, flow_id: str) -> Dict[str, Any]:
        """
        Fetch data for recommendation generation phase.

        Aggregates results from all previous phases along with business objectives,
        timeline constraints, and budget constraints for final recommendations.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - all_phase_results: Results from all previous phases
                - applications: Application details
                - business_objectives: Business goals and constraints
                - timeline_constraints: Project timeline data
                - budget_constraints: Budget limitations
        """
        try:
            # Get assessment flow with all phase results
            flow = await self._get_assessment_flow(flow_id)
            if not flow:
                logger.warning(
                    f"Assessment flow not found for recommendations: {flow_id}"
                )
                return self._empty_recommendation_data()

            # Extract all phase results
            all_phase_results = {
                "readiness": self._extract_phase_results(flow, "readiness_assessment"),
                "complexity": self._extract_phase_results(flow, "complexity_analysis"),
                "dependency": self._extract_phase_results(flow, "dependency_analysis"),
                "tech_debt": self._extract_phase_results(flow, "tech_debt_assessment"),
                "risk": self._extract_phase_results(flow, "risk_assessment"),
            }

            # Get applications
            applications = await self._get_applications()

            # Get business constraints (from flow metadata or defaults)
            business_constraints = self._extract_business_constraints(flow)

            return {
                "all_phase_results": all_phase_results,
                "applications": [
                    self._serialize_application(app) for app in applications
                ],
                "business_objectives": business_constraints.get("objectives", []),
                "timeline_constraints": business_constraints.get("timeline", {}),
                "budget_constraints": business_constraints.get("budget", {}),
                "engagement_id": str(self.engagement_id),
                "flow_id": str(flow_id),
            }

        except Exception as e:
            logger.error(f"Error fetching recommendation data: {e}")
            return self._empty_recommendation_data()
