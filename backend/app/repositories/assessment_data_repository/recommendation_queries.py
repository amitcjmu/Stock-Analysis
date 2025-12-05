"""
Assessment Data Repository - Recommendation Queries

Mixin for recommendation generation data fetching.
Per ADR-024: All queries include tenant scoping.
"""

from typing import Any, Dict, List, Set
from uuid import UUID

from sqlalchemy import select

from app.core.logging import get_logger
from app.models.assessment_flow import AssessmentFlow

logger = get_logger(__name__)


class RecommendationQueriesMixin:
    """Mixin for recommendation generation data queries"""

    async def _get_existing_sixr_decision_app_ids(self, flow_id: str) -> Set[str]:
        """
        Get application IDs that already have 6R decisions for this flow.

        Used to filter out applications during retry operations to avoid
        regenerating recommendations for apps that already succeeded.

        Decisions are stored in phase_results JSONB at:
        phase_results['recommendation_generation']['results']['recommendation_generation']['applications']

        Args:
            flow_id: Assessment flow UUID

        Returns:
            Set of application IDs (as strings) with existing 6R decisions
        """
        try:
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            # Query AssessmentFlow to get phase_results
            stmt = select(AssessmentFlow.phase_results).where(
                AssessmentFlow.id == flow_uuid,
                AssessmentFlow.client_account_id == self.client_account_id,
                AssessmentFlow.engagement_id == self.engagement_id,
            )
            result = await self.db.execute(stmt)
            phase_results = result.scalar_one_or_none()

            if not phase_results:
                logger.info(f"[RETRY-FIX] No phase_results found for flow_id={flow_id}")
                return set()

            # Navigate nested structure defensively to find applications with 6R decisions
            # Structure: recommendation_generation -> results -> recommendation_generation -> applications
            # Qodo Bot: More defensive null handling with `or {}`
            recommendation_gen = (
                phase_results.get("recommendation_generation", {}) or {}
            )
            results_data = recommendation_gen.get("results", {}) or {}
            inner_rec_gen = results_data.get("recommendation_generation", {}) or {}
            applications = inner_rec_gen.get("applications", []) or []

            # Qodo Bot: Accept either 'six_r_strategy' or 'overall_strategy' to detect completed apps
            def has_strategy(app: Dict[str, Any]) -> bool:
                strat = app.get("six_r_strategy") or app.get("overall_strategy")
                return isinstance(strat, str) and len(strat.strip()) > 0

            # Extract application IDs that have a valid 6R strategy
            existing_app_ids = {
                str(app.get("application_id"))
                for app in applications
                if app.get("application_id") and has_strategy(app)
            }

            logger.info(
                f"[RETRY-FIX] Found {len(existing_app_ids)} existing 6R decisions "
                f"in phase_results for flow_id={flow_id}"
            )
            return existing_app_ids

        except Exception as e:
            logger.warning(
                f"[RETRY-FIX] Error fetching existing 6R decisions from phase_results: {e}"
            )
            return set()

    async def _get_selected_app_ids_with_fallbacks(self, flow: Any) -> list:
        """
        [ISSUE-999] Get selected application IDs with multiple fallback strategies.

        Extracted to reduce cyclomatic complexity of get_recommendation_data.

        Fallback order:
        1. selected_canonical_application_ids (new field)
        2. application_asset_groups canonical_application_id
        3. Resolve selected_asset_ids via AssessmentApplicationResolver

        Returns:
            List of selected canonical application IDs as strings
        """
        # Primary: Use selected_canonical_application_ids (new field)
        selected_app_ids: List[str] = flow.selected_canonical_application_ids or []

        # Fallback 1: Try application_asset_groups if new field is empty
        if not selected_app_ids and flow.application_asset_groups:
            selected_app_ids = [
                group.get("canonical_application_id")
                for group in flow.application_asset_groups
                if group.get("canonical_application_id")
            ]

        # Fallback 2: Resolve selected_asset_ids to canonical applications
        if not selected_app_ids and (
            flow.selected_asset_ids or flow.selected_application_ids
        ):
            asset_ids = flow.selected_asset_ids or flow.selected_application_ids
            logger.info(
                f"[ISSUE-999] Resolving {len(asset_ids)} selected_asset_ids "
                "to canonical applications"
            )
            try:
                from app.services.assessment.application_resolver import (
                    AssessmentApplicationResolver,
                )

                resolver = AssessmentApplicationResolver(
                    db=self.db,
                    client_account_id=self.client_account_id,
                    engagement_id=self.engagement_id,
                )

                # Get collection_flow_id from flow metadata if available
                collection_flow_id = None
                if hasattr(flow, "flow_metadata") and flow.flow_metadata:
                    source_collection = flow.flow_metadata.get("source_collection", {})
                    coll_id = source_collection.get("collection_flow_id")
                    if coll_id:
                        collection_flow_id = (
                            UUID(coll_id) if isinstance(coll_id, str) else coll_id
                        )

                # Resolve assets to canonical applications
                application_groups = await resolver.resolve_assets_to_applications(
                    asset_ids=[
                        UUID(aid) if isinstance(aid, str) else aid for aid in asset_ids
                    ],
                    collection_flow_id=collection_flow_id,
                )

                # Extract canonical_application_ids from resolved groups
                selected_app_ids = [
                    str(group.canonical_application_id)
                    for group in application_groups
                    if group.canonical_application_id
                ]
                logger.info(
                    f"[ISSUE-999] Resolved {len(asset_ids)} assets to "
                    f"{len(selected_app_ids)} canonical applications"
                )
            except Exception as e:
                logger.warning(
                    f"[ISSUE-999] Failed to resolve assets to applications: {e}"
                )

        return selected_app_ids

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

            # ISSUE-999: Get selected application IDs using helper with fallbacks
            selected_app_ids = await self._get_selected_app_ids_with_fallbacks(flow)

            logger.info(
                f"[ISSUE-999] Retrieved {len(selected_app_ids)} selected application IDs "
                f"for recommendation generation"
            )

            # RETRY-FIX: Filter out applications that already have 6R decisions
            # This ensures retry operations only process failed applications
            existing_decision_app_ids = await self._get_existing_sixr_decision_app_ids(
                flow_id
            )
            apps_with_decisions_count = 0
            if existing_decision_app_ids and selected_app_ids:
                original_count = len(selected_app_ids)
                selected_app_ids = [
                    app_id
                    for app_id in selected_app_ids
                    if str(app_id) not in existing_decision_app_ids
                ]
                apps_with_decisions_count = original_count - len(selected_app_ids)
                if apps_with_decisions_count > 0:
                    logger.info(
                        f"[RETRY-FIX] Filtered out {apps_with_decisions_count} apps with existing 6R "
                        f"decisions, {len(selected_app_ids)} remaining for processing"
                    )

            # Get applications filtered by selected IDs
            applications = []
            app_assets_map = {}
            apps_not_found = []

            if selected_app_ids:
                applications = await self._get_selected_applications(selected_app_ids)
                found_app_ids = {str(app.id) for app in applications}
                apps_not_found = [
                    app_id
                    for app_id in selected_app_ids
                    if str(app_id) not in found_app_ids
                ]

                if apps_not_found:
                    logger.warning(
                        f"[RETRY-FIX] {len(apps_not_found)} selected apps not found in "
                        f"canonical_applications table: {apps_not_found}"
                    )

                # Fetch comprehensive asset data for each application
                if applications:
                    app_assets_map = await self._get_applications_with_assets(
                        [str(app.id) for app in applications]
                    )
            elif apps_with_decisions_count > 0:
                # All apps were filtered out because they have decisions - return empty
                # to signal that retry is not needed (all apps already completed)
                logger.info(
                    f"[RETRY-FIX] All {apps_with_decisions_count} selected apps already have "
                    f"6R decisions - no retry needed for flow_id={flow_id}"
                )
            else:
                # No selected apps at all - this shouldn't happen normally
                logger.warning(
                    f"[ISSUE-999] No selected_canonical_application_ids found "
                    f"for flow_id={flow_id}"
                )

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
                # RETRY-FIX: Metadata about filtering and data issues
                "_meta": {
                    "apps_with_existing_decisions": apps_with_decisions_count,
                    "apps_not_found_in_db": apps_not_found,
                    "apps_to_process": len(serialized_apps),
                    "all_apps_completed": (
                        apps_with_decisions_count > 0 and len(serialized_apps) == 0
                    ),
                    "has_missing_apps": len(apps_not_found) > 0,
                },
            }

        except Exception as e:
            logger.error(
                f"[ISSUE-999] Error fetching recommendation data: {e}", exc_info=True
            )
            return self._empty_recommendation_data()
