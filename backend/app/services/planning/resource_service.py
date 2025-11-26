"""
Resource Planning Service for Planning Flow.

Provides business logic for resource pools, allocations, and skill gap analysis.
Aggregates data from repository layer for UI display.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.schemas.planning.resource import (
    ResourcePlanningResponse,
    ResourceTeam,
    TeamAssignment,
    ResourceMetrics,
    ResourceRecommendation,
    UpcomingNeed,
)

logger = logging.getLogger(__name__)


class ResourceService:
    """Service for resource planning operations."""

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
        from uuid import UUID

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

    async def get_resources_for_planning(
        self, planning_flow_id: UUID = None
    ) -> ResourcePlanningResponse:
        """
        Get aggregated resource planning data for UI display.

        Args:
            planning_flow_id: Optional planning flow UUID to filter by

        Returns:
            ResourcePlanningResponse with teams, metrics, recommendations, and upcoming needs
        """
        try:
            logger.info(
                f"Retrieving resource planning data for engagement: {self.engagement_id}"
            )

            # Get resource pools (multi-tenant scoped)
            resource_pools = await self.planning_repo.list_resource_pools(
                client_account_id=self.client_account_id,
                engagement_id=self.engagement_id,
                is_active=True,
            )

            # Get resource allocations if planning_flow_id provided
            allocations = []
            if planning_flow_id:
                allocations = (
                    await self.planning_repo.list_allocations_by_planning_flow(
                        planning_flow_id=planning_flow_id,
                        client_account_id=self.client_account_id,
                        engagement_id=self.engagement_id,
                    )
                )

            # Transform resource pools to teams
            teams = self._transform_pools_to_teams(resource_pools, allocations)

            # Calculate metrics
            metrics = self._calculate_metrics(resource_pools, allocations)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                resource_pools, allocations
            )

            # Get upcoming needs (skill gaps)
            upcoming_needs = await self._get_upcoming_needs()

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

    def _transform_pools_to_teams(
        self, resource_pools: List, allocations: List
    ) -> List[ResourceTeam]:
        """
        Transform resource pools to team display format.

        Args:
            resource_pools: List of ResourcePool instances
            allocations: List of ResourceAllocation instances

        Returns:
            List of ResourceTeam schemas
        """
        teams = []

        # Group allocations by pool
        allocations_by_pool = {}
        for allocation in allocations:
            pool_id = str(allocation.resource_pool_id)
            if pool_id not in allocations_by_pool:
                allocations_by_pool[pool_id] = []
            allocations_by_pool[pool_id].append(allocation)

        for pool in resource_pools:
            pool_id = str(pool.id)

            # Get assignments for this pool
            pool_allocations = allocations_by_pool.get(pool_id, [])
            assignments = [
                TeamAssignment(
                    project=f"Wave {i+1}",  # Simplified - would map to actual wave names
                    allocation=float(alloc.allocation_percentage or 0.0),
                    start_date=alloc.allocation_start_date.strftime("%Y-%m-%d"),
                    end_date=alloc.allocation_end_date.strftime("%Y-%m-%d"),
                )
                for i, alloc in enumerate(pool_allocations)
            ]

            # Calculate availability (simplified)
            availability = (
                (
                    float(pool.available_capacity_hours)
                    / float(pool.total_capacity_hours)
                )
                * 100.0
                if pool.total_capacity_hours > 0
                else 0.0
            )

            teams.append(
                ResourceTeam(
                    id=pool_id,
                    name=pool.pool_name,
                    size=int(
                        pool.total_capacity_hours / 160
                    ),  # Assume 160 hours/month per resource
                    skills=pool.skills if isinstance(pool.skills, list) else [],
                    availability=round(availability, 2),
                    utilization=round(float(pool.utilization_percentage), 2),
                    assignments=assignments,
                )
            )

        return teams

    def _calculate_metrics(
        self, resource_pools: List, allocations: List
    ) -> ResourceMetrics:
        """
        Calculate resource metrics.

        Args:
            resource_pools: List of ResourcePool instances
            allocations: List of ResourceAllocation instances

        Returns:
            ResourceMetrics schema
        """
        if not resource_pools:
            return ResourceMetrics(
                total_teams=0,
                total_resources=0,
                average_utilization=0.0,
                skill_coverage={},
            )

        # Calculate total resources (assuming 160 hours/month per resource)
        total_resources = sum(
            int(pool.total_capacity_hours / 160) for pool in resource_pools
        )

        # Calculate average utilization
        total_utilization = sum(
            float(pool.utilization_percentage) for pool in resource_pools
        )
        average_utilization = (
            round(total_utilization / len(resource_pools), 2) if resource_pools else 0.0
        )

        # Calculate skill coverage (simplified - would integrate with skill gap analysis)
        skill_coverage = {}
        all_skills = set()
        for pool in resource_pools:
            if isinstance(pool.skills, list):
                all_skills.update(pool.skills)

        # Mock skill coverage percentages (would be calculated from actual skill requirements)
        for skill in all_skills:
            pools_with_skill = sum(
                1
                for pool in resource_pools
                if isinstance(pool.skills, list) and skill in pool.skills
            )
            coverage = (pools_with_skill / len(resource_pools)) * 100
            skill_coverage[skill] = round(coverage, 2)

        return ResourceMetrics(
            total_teams=len(resource_pools),
            total_resources=total_resources,
            average_utilization=average_utilization,
            skill_coverage=skill_coverage,
        )

    def _generate_recommendations(
        self, resource_pools: List, allocations: List
    ) -> List[ResourceRecommendation]:
        """
        Generate resource recommendations based on current state.

        Args:
            resource_pools: List of ResourcePool instances
            allocations: List of ResourceAllocation instances

        Returns:
            List of ResourceRecommendation schemas
        """
        recommendations = []

        # Check for high utilization
        for pool in resource_pools:
            utilization = float(pool.utilization_percentage)
            if utilization > 90:
                recommendations.append(
                    ResourceRecommendation(
                        type="capacity",
                        description=f"{pool.pool_name} is at {utilization}% utilization. "
                        f"Consider adding capacity to prevent burnout.",
                        impact="High",
                    )
                )
            elif utilization < 50:
                recommendations.append(
                    ResourceRecommendation(
                        type="optimization",
                        description=f"{pool.pool_name} has available capacity ({100-utilization}%). "
                        f"Can be allocated to additional tasks.",
                        impact="Low",
                    )
                )

        # Add general planning recommendation if allocations exist
        if allocations:
            recommendations.append(
                ResourceRecommendation(
                    type="planning",
                    description="Review resource allocations across waves to ensure balanced distribution.",
                    impact="Medium",
                )
            )

        return recommendations

    async def _get_upcoming_needs(self) -> List[UpcomingNeed]:
        """
        Get upcoming resource needs from skill gap analysis.

        Returns:
            List of UpcomingNeed schemas
        """
        # This would integrate with resource_skills table to get actual skill gaps
        # For now, return empty list (no mock data)
        try:
            # Get skill gaps from resource_skills table
            # Future implementation: query resource_skills with has_gap=True
            return []
        except Exception as e:
            logger.error(f"Error retrieving upcoming needs: {e}")
            return []
