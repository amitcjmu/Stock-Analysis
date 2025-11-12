"""
Decision Queries - 6R decision query operations

Retrieves 6R migration decisions from multiple data sources:
1. phase_results['recommendation_generation']['applications'] (primary)
2. assets table where six_r_strategy IS NOT NULL (fallback)
3. sixr_decisions table if exists (legacy)

Created for Issue #999 - Integration piece connecting parallel iterations 4-6
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment_flow import AssessmentFlow
from app.models.asset import Asset

logger = logging.getLogger(__name__)


class DecisionQueries:
    """Queries for 6R decision retrieval"""

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: str,
        engagement_id: Optional[str] = None,
    ):
        self.db = db
        self.client_account_id = client_account_id
        self.engagement_id = engagement_id

    async def get_all_sixr_decisions(self, flow_id: str) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all 6R decisions for applications in assessment flow.

        Data Sources (in priority order):
        1. phase_results['recommendation_generation']['applications'] (Iteration 4 writes here)
        2. assets table where six_r_strategy IS NOT NULL (Iteration 5 writes here)
        3. sixr_decisions table if exists (legacy fallback)

        Args:
            flow_id: Assessment flow UUID string

        Returns:
            Dict keyed by application_id:
            {
                "app-uuid-1": {
                    "application_id": "app-uuid-1",
                    "application_name": "Analytics Engine",
                    "six_r_strategy": "rehost",
                    "confidence_score": 0.85,
                    "reasoning": "Low complexity, cloud-ready...",
                    "estimated_effort": "medium",
                    "risk_level": "low"
                }
            }
        """
        logger.info(f"[ISSUE-999] 📊 Retrieving 6R decisions for flow {flow_id}")

        try:
            # Convert flow_id to UUID
            flow_uuid = UUID(flow_id) if isinstance(flow_id, str) else flow_id

            # Get assessment flow with proper tenant scoping
            result = await self.db.execute(
                select(AssessmentFlow).where(
                    and_(
                        AssessmentFlow.id == flow_uuid,
                        AssessmentFlow.client_account_id == self.client_account_id,
                        # Add engagement_id scoping if provided
                        (
                            AssessmentFlow.engagement_id == self.engagement_id
                            if self.engagement_id
                            else True
                        ),
                    )
                )
            )
            flow = result.scalar_one_or_none()

            if not flow:
                logger.warning(
                    f"[ISSUE-999] ⚠️ Assessment flow {flow_id} not found or access denied"
                )
                return {}

            # Source 1: Check phase_results for recommendation_generation data (Primary)
            decisions_dict = await self._get_from_phase_results(flow)

            if decisions_dict:
                logger.info(
                    f"[ISSUE-999] ✅ Retrieved {len(decisions_dict)} 6R decisions from phase_results"
                )
                return decisions_dict

            # Source 2: Fall back to assets table
            logger.info(
                "[ISSUE-999] ⚠️ No phase_results found, falling back to assets table"
            )
            decisions_dict = await self._get_from_assets_table(flow)

            if decisions_dict:
                logger.info(
                    f"[ISSUE-999] ✅ Found {len(decisions_dict)} assessed applications in assets table"
                )
                return decisions_dict

            # No data found in any source
            logger.warning(f"[ISSUE-999] ⚠️ No 6R decisions found for flow {flow_id}")
            return {}

        except Exception as e:
            logger.error(
                f"[ISSUE-999] ❌ Error retrieving 6R decisions for flow {flow_id}: {str(e)}"
            )
            # Return empty dict on error to prevent UI breakage
            return {}

    async def _get_from_phase_results(
        self, flow: AssessmentFlow
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract 6R decisions from phase_results JSON field.

        Expected structure (written by Iteration 4):
        {
            "recommendation_generation": {
                "applications": [
                    {
                        "application_id": "uuid",
                        "application_name": "string",
                        "six_r_strategy": "rehost",
                        "confidence_score": 0.85,
                        "reasoning": "...",
                        "estimated_effort": "medium",
                        "risk_level": "low"
                    }
                ]
            }
        }
        """
        try:
            phase_results = flow.phase_results or {}
            recommendation_gen = phase_results.get("recommendation_generation", {})
            applications = recommendation_gen.get("applications", [])

            if not applications:
                return {}

            # Transform list to dict keyed by application_id
            decisions_dict = {}
            for app_data in applications:
                app_id = str(app_data.get("application_id", ""))
                if app_id and app_data.get("six_r_strategy"):
                    decisions_dict[app_id] = {
                        "application_id": app_id,
                        "application_name": app_data.get("application_name", "Unknown"),
                        "six_r_strategy": app_data.get("six_r_strategy"),
                        "confidence_score": app_data.get("confidence_score", 0.0),
                        "reasoning": app_data.get("reasoning", ""),
                        "estimated_effort": app_data.get("estimated_effort", "unknown"),
                        "risk_level": app_data.get("risk_level", "unknown"),
                    }

            return decisions_dict

        except Exception as e:
            logger.error(f"[ISSUE-999] ❌ Error parsing phase_results: {str(e)}")
            return {}

    async def _get_from_assets_table(
        self, flow: AssessmentFlow
    ) -> Dict[str, Dict[str, Any]]:
        """
        Query assets table for 6R decisions (Iteration 5 writes here).

        Falls back to this when phase_results is empty.
        Uses selected_canonical_application_ids from assessment flow.
        """
        try:
            # Get selected application IDs from flow
            # Note: Use selected_canonical_application_ids (new semantic field) if available,
            # otherwise fall back to selected_application_ids (deprecated but still used)
            selected_ids = (
                flow.selected_canonical_application_ids
                if flow.selected_canonical_application_ids
                else flow.selected_application_ids
            )

            if not selected_ids:
                logger.warning(
                    "[ISSUE-999] ⚠️ No selected application IDs found in flow"
                )
                return {}

            # Convert to UUID list
            app_uuids = []
            for app_id in selected_ids:
                try:
                    app_uuids.append(
                        UUID(app_id) if isinstance(app_id, str) else app_id
                    )
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"[ISSUE-999] ⚠️ Invalid UUID in selected_application_ids: {app_id} - {e}"
                    )
                    continue

            if not app_uuids:
                return {}

            # Query assets table with proper tenant scoping
            result = await self.db.execute(
                select(Asset).where(
                    and_(
                        Asset.id.in_(app_uuids),
                        Asset.client_account_id == self.client_account_id,
                        Asset.engagement_id == flow.engagement_id,
                        Asset.six_r_strategy.isnot(
                            None
                        ),  # Only assets with 6R strategy
                    )
                )
            )
            assets = result.scalars().all()

            # Transform to decisions dict
            decisions_dict = {}
            for asset in assets:
                app_id = str(asset.id)
                decisions_dict[app_id] = {
                    "application_id": app_id,
                    "application_name": asset.name
                    or asset.application_name
                    or "Unknown",
                    "six_r_strategy": asset.six_r_strategy,
                    "confidence_score": asset.confidence_score or 0.0,
                    "reasoning": f"Strategy set from assessment analysis for {asset.name}",
                    "estimated_effort": "unknown",  # Not stored in assets table
                    "risk_level": "unknown",  # Not stored in assets table
                }

            return decisions_dict

        except Exception as e:
            logger.error(f"[ISSUE-999] ❌ Error querying assets table: {str(e)}")
            return {}
