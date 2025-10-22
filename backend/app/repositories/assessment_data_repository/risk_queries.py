"""
Assessment Data Repository - Risk Queries

Mixin for risk assessment data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.canonical_applications import CanonicalApplication

logger = get_logger(__name__)


class RiskQueriesMixin:
    """Mixin for risk assessment data queries"""

    async def get_risk_data(self, flow_id: str) -> Dict[str, Any]:
        """
        Fetch data for risk assessment phase.

        Aggregates results from readiness, complexity, and dependency phases
        along with business impact data for comprehensive risk evaluation.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - readiness_results: Results from readiness phase
                - complexity_results: Results from complexity phase
                - dependency_results: Results from dependency phase
                - applications: Application details with criticality
                - business_impact_data: Business criticality indicators
        """
        try:
            # Get assessment flow to extract phase results
            flow = await self._get_assessment_flow(flow_id)
            if not flow:
                logger.warning(f"Assessment flow not found for risk data: {flow_id}")
                return self._empty_risk_data()

            # Extract prior phase results from flow state
            readiness_results = self._extract_phase_results(
                flow, "readiness_assessment"
            )
            complexity_results = self._extract_phase_results(
                flow, "complexity_analysis"
            )
            dependency_results = self._extract_phase_results(
                flow, "dependency_analysis"
            )

            # Get applications with business criticality
            applications = await self._get_applications()

            # Calculate business impact indicators
            business_impact = await self._calculate_business_impact(applications)

            return {
                "readiness_results": readiness_results,
                "complexity_results": complexity_results,
                "dependency_results": dependency_results,
                "applications": [
                    self._serialize_application(app) for app in applications
                ],
                "business_impact_data": business_impact,
                "engagement_id": str(self.engagement_id),
            }

        except Exception as e:
            logger.error(f"Error fetching risk data: {e}")
            return self._empty_risk_data()

    async def _calculate_business_impact(
        self, applications: List[CanonicalApplication]
    ) -> Dict[str, Any]:
        """Calculate business impact indicators from application data."""
        criticality_counts = {}
        for app in applications:
            crit = app.business_criticality or "Medium"
            criticality_counts[crit] = criticality_counts.get(crit, 0) + 1

        return {
            "criticality_distribution": criticality_counts,
            "high_criticality_count": criticality_counts.get("High", 0),
            "total_applications": len(applications),
        }
