"""
JSONB Data Update Operations.

Provides operations for updating JSONB fields in planning flows
(wave_plan_data, resource_allocation_data, timeline_data, cost_estimation_data).
"""

import logging
import uuid
from typing import Any, Dict, Optional

from app.models.planning import PlanningFlow

logger = logging.getLogger(__name__)


class JsonbOperationsMixin:
    """Mixin for JSONB data update operations."""

    # ===========================
    # JSONB Data Updates
    # ===========================

    async def save_wave_plan_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        wave_plan_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save wave planning results.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
            wave_plan_data: Wave plan JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            wave_plan_data=wave_plan_data,
        )

    async def save_resource_allocation_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        resource_allocation_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save resource allocation data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
            resource_allocation_data: Resource allocation JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            resource_allocation_data=resource_allocation_data,
        )

    async def save_timeline_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        timeline_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save timeline data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
            timeline_data: Timeline JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            timeline_data=timeline_data,
        )

    async def save_cost_estimation_data(
        self,
        planning_flow_id: uuid.UUID,
        client_account_id: uuid.UUID,
        engagement_id: uuid.UUID,
        cost_estimation_data: Dict[str, Any],
    ) -> Optional[PlanningFlow]:
        """
        Save cost estimation data.

        Args:
            planning_flow_id: Planning flow UUID
            client_account_id: Client account UUID (per migration 115)
            engagement_id: Engagement UUID (per migration 115)
            cost_estimation_data: Cost estimation JSONB data

        Returns:
            Updated PlanningFlow or None if not found
        """
        return await self.update_planning_flow(
            planning_flow_id=planning_flow_id,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
            cost_estimation_data=cost_estimation_data,
        )
