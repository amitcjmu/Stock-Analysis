"""
Wave Planning Service for Planning Flow

Generates wave plans for migration applications based on assessment data.
This is the initial implementation that generates basic wave plans.
Future enhancement: Integrate with CrewAI agents for intelligent wave optimization.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository

logger = logging.getLogger(__name__)


class WavePlanningService:
    """Service for generating wave plans for migration applications."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context

        # Convert client_account_id and engagement_id to integers
        # Handle placeholder UUIDs from development/testing contexts
        client_account_id = context.client_account_id
        if isinstance(client_account_id, str):
            client_account_id_int = (
                1 if "1111111" in client_account_id else int(client_account_id)
            )
        else:
            client_account_id_int = int(client_account_id)

        engagement_id = context.engagement_id
        if isinstance(engagement_id, str):
            engagement_id_int = 1 if "2222222" in engagement_id else int(engagement_id)
        else:
            engagement_id_int = int(engagement_id)

        # Store integer versions for use in execute_wave_planning
        self.client_account_id_int = client_account_id_int
        self.engagement_id_int = engagement_id_int

        self.planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_id_int,
            engagement_id=engagement_id_int,
        )

    async def execute_wave_planning(
        self, planning_flow_id: UUID, planning_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute wave planning for the given planning flow.

        Args:
            planning_flow_id: UUID of the planning flow
            planning_config: Configuration for wave planning

        Returns:
            Dict containing wave plan data
        """
        try:
            logger.info(
                f"Starting wave planning execution for flow: {planning_flow_id}"
            )

            # Update phase status to in_progress
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_id_int,
                engagement_id=self.engagement_id_int,
                current_phase="wave_planning",
                phase_status="in_progress",
            )

            # Get planning flow to access selected applications
            planning_flow = await self.planning_repo.get_planning_flow_by_id(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_id_int,
                engagement_id=self.engagement_id_int,
            )

            if not planning_flow:
                raise ValueError(f"Planning flow not found: {planning_flow_id}")

            # Get configuration parameters
            max_apps_per_wave = planning_config.get("max_apps_per_wave", 50)
            wave_duration_days = planning_config.get("wave_duration_limit_days", 90)

            # Generate wave plan
            wave_plan = self._generate_wave_plan(
                selected_app_count=len(planning_flow.selected_applications or []),
                max_apps_per_wave=max_apps_per_wave,
                wave_duration_days=wave_duration_days,
            )

            # Update planning flow with wave plan data
            await self.planning_repo.save_wave_plan_data(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_id_int,
                engagement_id=self.engagement_id_int,
                wave_plan_data=wave_plan,
            )

            # Update phase status to completed
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_id_int,
                engagement_id=self.engagement_id_int,
                current_phase="wave_planning",
                phase_status="completed",
            )

            await self.db.commit()

            logger.info(
                f"Wave planning completed successfully for flow: {planning_flow_id}"
            )

            return {
                "status": "success",
                "wave_plan": wave_plan,
                "message": "Wave planning completed successfully",
            }

        except Exception as e:
            logger.error(
                f"Wave planning failed for flow {planning_flow_id}: {str(e)}",
                exc_info=True,
            )
            # Update phase status to failed
            try:
                await self.planning_repo.update_phase_status(
                    planning_flow_id=planning_flow_id,
                    client_account_id=self.client_account_id_int,
                    engagement_id=self.engagement_id_int,
                    current_phase="wave_planning",
                    phase_status="failed",
                )
                await self.db.commit()
            except Exception as update_error:
                logger.error(
                    f"Failed to update phase status after error: {update_error}"
                )

            return {
                "status": "failed",
                "error": str(e),
                "message": "Wave planning failed",
            }

    def _generate_wave_plan(
        self, selected_app_count: int, max_apps_per_wave: int, wave_duration_days: int
    ) -> Dict[str, Any]:
        """
        Generate a wave plan based on application count and constraints.

        This is a simple implementation that groups applications into waves.
        Future enhancement: Use CrewAI agents for intelligent grouping based on:
        - Application dependencies
        - Migration complexity
        - Business criticality
        - Resource availability

        Args:
            selected_app_count: Number of applications to migrate
            max_apps_per_wave: Maximum applications per wave
            wave_duration_days: Duration of each wave in days

        Returns:
            Dict containing wave plan with waves, groups, and summary
        """
        # Calculate number of waves needed
        wave_count = max(
            1, (selected_app_count + max_apps_per_wave - 1) // max_apps_per_wave
        )

        waves = []
        start_date = datetime.now(timezone.utc)

        for wave_num in range(1, wave_count + 1):
            # Calculate applications for this wave
            remaining_apps = selected_app_count - (wave_num - 1) * max_apps_per_wave
            apps_in_wave = min(max_apps_per_wave, remaining_apps)

            wave_start = start_date + timedelta(
                days=(wave_num - 1) * wave_duration_days
            )
            wave_end = wave_start + timedelta(days=wave_duration_days)

            wave = {
                "wave_id": f"wave_{wave_num}",
                "wave_number": wave_num,
                "wave_name": f"Wave {wave_num}",
                "application_count": apps_in_wave,
                "start_date": wave_start.isoformat(),
                "end_date": wave_end.isoformat(),
                "duration_days": wave_duration_days,
                "status": "planned",
                "description": f"Migration wave {wave_num} with {apps_in_wave} applications",
                "groups": [
                    {
                        "group_id": f"wave_{wave_num}_group_1",
                        "group_name": f"Wave {wave_num} - Primary Group",
                        "application_count": apps_in_wave,
                        "migration_strategy": "lift_and_shift",  # Default strategy
                    }
                ],
            }
            waves.append(wave)

        # Generate summary
        summary = {
            "total_waves": wave_count,
            "total_apps": selected_app_count,
            "total_groups": wave_count,  # One group per wave for now
            "estimated_duration_days": wave_count * wave_duration_days,
            "planning_date": datetime.now(timezone.utc).isoformat(),
            "configuration": {
                "max_apps_per_wave": max_apps_per_wave,
                "wave_duration_days": wave_duration_days,
            },
        }

        return {
            "waves": waves,
            "groups": [group for wave in waves for group in wave["groups"]],
            "summary": summary,
            "metadata": {
                "generated_by": "wave_planning_service",
                "version": "1.0.0",
                "generation_method": "simple_grouping",
                "future_enhancement": "CrewAI agent-based intelligent grouping",
            },
        }


async def execute_wave_planning_for_flow(
    db: AsyncSession,
    context: RequestContext,
    planning_flow_id: UUID,
    planning_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute wave planning for a planning flow.

    Args:
        db: Database session
        context: Request context
        planning_flow_id: UUID of the planning flow
        planning_config: Configuration for wave planning

    Returns:
        Dict containing wave plan execution result
    """
    service = WavePlanningService(db, context)
    return await service.execute_wave_planning(planning_flow_id, planning_config)
