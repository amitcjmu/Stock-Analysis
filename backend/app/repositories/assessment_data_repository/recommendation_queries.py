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

        ISSUE-999: Now filters applications by selected_canonical_application_ids
        from assessment flow for per-application 6R strategy generation.

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Dictionary containing:
                - all_phase_results: Results from all previous phases
                - applications: Application details (FILTERED by selected IDs)
                - selected_application_ids: List of selected canonical app IDs
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

            # ISSUE-999: Get selected application IDs from flow
            # Use selected_canonical_application_ids (new field) with fallback to legacy field
            selected_app_ids = flow.selected_canonical_application_ids or []

            # Fallback: Try application_asset_groups if new field is empty
            if not selected_app_ids and flow.application_asset_groups:
                selected_app_ids = [
                    group.get("canonical_application_id")
                    for group in flow.application_asset_groups
                    if group.get("canonical_application_id")
                ]

            logger.info(
                f"[ISSUE-999] Retrieved {len(selected_app_ids)} selected application IDs "
                f"for recommendation generation"
            )

            # Get applications filtered by selected IDs
            if selected_app_ids:
                applications = await self._get_selected_applications(selected_app_ids)
                # Fetch comprehensive asset data for each application
                app_assets_map = await self._get_applications_with_assets(
                    selected_app_ids
                )
            else:
                # Fallback: Get all applications if no selection
                logger.warning(
                    f"[ISSUE-999] No selected_canonical_application_ids found, "
                    f"using all applications (flow_id={flow_id})"
                )
                applications = await self._get_applications()
                # For fallback, also fetch assets
                app_ids = [app.id for app in applications]
                app_assets_map = await self._get_applications_with_assets(app_ids)

            # Get business constraints (from flow metadata or defaults)
            business_constraints = self._extract_business_constraints(flow)

            # Serialize applications with comprehensive asset data
            serialized_apps = []
            for app in applications:
                assets = app_assets_map.get(str(app.id), [])
                serialized_apps.append(self._serialize_application(app, assets))

            return {
                "all_phase_results": all_phase_results,
                "applications": serialized_apps,
                "selected_application_ids": [
                    str(app_id) for app_id in selected_app_ids
                ],
                "business_objectives": business_constraints.get("objectives", []),
                "timeline_constraints": business_constraints.get("timeline", {}),
                "budget_constraints": business_constraints.get("budget", {}),
                "engagement_id": str(self.engagement_id),
                "flow_id": str(flow_id),
            }

        except Exception as e:
            logger.error(
                f"[ISSUE-999] Error fetching recommendation data: {e}", exc_info=True
            )
            return self._empty_recommendation_data()
