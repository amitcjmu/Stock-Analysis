"""
Resource Planning Service for Planning Flow.

Provides business logic for resource pools, allocations, and skill gap analysis.
6R-based estimation logic is in sixr_estimation.py module.
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.schemas.planning.resource import (
    ResourcePlanningResponse,
    ResourceMetrics,
)
from app.services.planning.sixr_estimation import estimate_resources_from_6r
from app.services.planning.resource_service.enrichment import (
    enrich_wave_data_with_6r_strategies,
)
from app.services.planning.resource_service.helpers import (
    transform_pools_to_teams,
    calculate_metrics,
    generate_recommendations,
    get_upcoming_needs,
)

logger = logging.getLogger(__name__)


class ResourceService:
    """Service for resource planning operations with 6R-based estimation."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize resource service with database session and context.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        # Per migration 115, tenant IDs are UUIDs - NEVER convert to integers
        client_account_id = context.client_account_id
        engagement_id = context.engagement_id

        self.client_account_uuid = (
            (
                UUID(client_account_id)
                if isinstance(client_account_id, str)
                else client_account_id
            )
            if client_account_id
            else None
        )

        self.engagement_uuid = (
            (UUID(engagement_id) if isinstance(engagement_id, str) else engagement_id)
            if engagement_id
            else None
        )

        # Initialize repository with tenant scoping
        self.planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=self.client_account_uuid,
            engagement_id=self.engagement_uuid,
        )

    async def _get_wave_plan_data(
        self, planning_flow_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """
        Retrieve wave_plan_data from planning_flows table.

        Args:
            planning_flow_id: Optional specific planning flow UUID

        Returns:
            wave_plan_data dict or empty dict if not found
        """
        from app.models.planning import PlanningFlow

        conditions = [
            PlanningFlow.client_account_id == self.client_account_uuid,
            PlanningFlow.engagement_id == self.engagement_uuid,
        ]

        if planning_flow_id:
            conditions.append(PlanningFlow.planning_flow_id == planning_flow_id)

        stmt = (
            select(PlanningFlow)
            .where(and_(*conditions))
            .order_by(PlanningFlow.created_at.desc())
            .limit(1)
        )

        result = await self.db.execute(stmt)
        planning_flow = result.scalar_one_or_none()

        if planning_flow and planning_flow.wave_plan_data:
            # Enrich wave_plan_data with 6R strategies from assessment phase_results
            enriched_data = await enrich_wave_data_with_6r_strategies(
                self.db,
                planning_flow.wave_plan_data,
                self.client_account_uuid,
                self.engagement_uuid,
            )
            return enriched_data
        return {}

    async def get_resources_for_planning(
        self, planning_flow_id: Optional[UUID] = None
    ) -> ResourcePlanningResponse:
        """
        Get aggregated resource planning data for UI display.

        If planning_flow_id is provided and wave data exists, uses 6R-based
        estimation from wave applications. Falls back to resource_pools table
        if configured manually.

        Args:
            planning_flow_id: Optional planning flow UUID for 6R estimation

        Returns:
            ResourcePlanningResponse with teams, metrics, recommendations, needs
        """
        try:
            logger.info(
                f"Retrieving resource planning data for engagement: "
                f"{self.engagement_uuid}"
            )

            # First, try 6R-based estimation from wave_plan_data
            if planning_flow_id:
                wave_plan_data = await self._get_wave_plan_data(planning_flow_id)
                if wave_plan_data.get("waves"):
                    logger.info(
                        f"Using 6R-based estimation for "
                        f"{len(wave_plan_data['waves'])} waves"
                    )
                    estimation = estimate_resources_from_6r(wave_plan_data)
                    return ResourcePlanningResponse(
                        teams=estimation["teams"],
                        metrics=estimation["metrics"],
                        recommendations=estimation["recommendations"],
                        upcoming_needs=estimation["upcoming_needs"],
                    )

            # Fall back to resource_pools table (manual configuration)
            resource_pools, allocations = await self._fetch_resource_pools(
                planning_flow_id
            )

            # If no pools, try to get wave data without specific flow ID
            if not resource_pools:
                wave_plan_data = await self._get_wave_plan_data(None)
                if wave_plan_data.get("waves"):
                    logger.info(
                        "No resource pools - using 6R estimation from latest wave data"
                    )
                    estimation = estimate_resources_from_6r(wave_plan_data)
                    return ResourcePlanningResponse(
                        teams=estimation["teams"],
                        metrics=estimation["metrics"],
                        recommendations=estimation["recommendations"],
                        upcoming_needs=estimation["upcoming_needs"],
                    )

            # Transform resource pools to teams
            teams = transform_pools_to_teams(resource_pools, allocations)

            # Calculate metrics
            metrics = calculate_metrics(resource_pools, allocations)

            # Generate recommendations
            recommendations = generate_recommendations(resource_pools, allocations)

            # Get upcoming needs (skill gaps)
            upcoming_needs = await get_upcoming_needs(self.db, self.planning_repo)

            return ResourcePlanningResponse(
                teams=teams,
                metrics=metrics,
                recommendations=recommendations,
                upcoming_needs=upcoming_needs,
            )

        except Exception as e:
            logger.error(f"Error retrieving resource planning data: {e}")
            # Return empty state on error (no mock data)
            return ResourcePlanningResponse(
                teams=[],
                metrics=ResourceMetrics(
                    total_teams=0,
                    total_resources=0,
                    average_utilization=0.0,
                    skill_coverage={},
                ),
                recommendations=[],
                upcoming_needs=[],
            )

    async def _fetch_resource_pools(self, planning_flow_id: Optional[UUID]):
        """
        Fetch resource pools and allocations from database.

        Args:
            planning_flow_id: Optional planning flow UUID

        Returns:
            Tuple of (resource_pools, allocations)
        """
        resource_pools = []
        allocations = []

        try:
            resource_pools = await self.planning_repo.list_resource_pools(
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
                is_active=True,
            )
            if planning_flow_id:
                allocations = (
                    await self.planning_repo.list_allocations_by_planning_flow(
                        planning_flow_id=planning_flow_id,
                        client_account_id=self.client_account_uuid,
                        engagement_id=self.engagement_uuid,
                    )
                )
        except Exception as pool_error:
            logger.warning(
                f"Resource pools query failed (using 6R estimation): {pool_error}"
            )

        return resource_pools, allocations
