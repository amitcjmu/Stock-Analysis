"""
Wave Planning Service - Base Module

Contains base class initialization and configuration.

ADR Compliance:
- ADR-015: TenantScopedAgentPool for persistent agents
- ADR-024: TenantMemoryManager (CrewAI memory disabled)
- ADR-029: LLM JSON sanitization
- ADR-031: CallbackHandlerIntegration for observability

Issue: #1146 - Integrate wave_planning_specialist CrewAI agent
"""

import logging
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.planning_flow_repository import PlanningFlowRepository
from app.services.persistent_agents.tenant_scoped_agent_pool import (
    TenantScopedAgentPool,
)

logger = logging.getLogger(__name__)


class WavePlanningService:
    """Service for generating wave plans using CrewAI agents."""

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize wave planning service with database session and context.

        Args:
            db: Async database session
            context: Request context with tenant scoping
        """
        self.db = db
        self.context = context

        # Convert client_account_id and engagement_id to UUIDs (per migration 115)
        # NEVER convert tenant IDs to integers - they are UUIDs
        client_account_id = context.client_account_id
        if isinstance(client_account_id, str):
            client_account_uuid = UUID(client_account_id)
        else:
            client_account_uuid = client_account_id

        engagement_id = context.engagement_id
        if isinstance(engagement_id, str):
            engagement_uuid = UUID(engagement_id)
        else:
            engagement_uuid = engagement_id

        # Store UUID versions for use throughout service
        self.client_account_uuid = client_account_uuid
        self.engagement_uuid = engagement_uuid

        # Initialize repository with tenant scoping
        self.planning_repo = PlanningFlowRepository(
            db=db,
            client_account_id=client_account_uuid,
            engagement_id=engagement_uuid,
        )

        # Initialize agent pool for singleton agents (ADR-015)
        # This replaces direct crew instance creation per call
        self.agent_pool = TenantScopedAgentPool(
            client_account_id=str(client_account_uuid),
            engagement_id=str(engagement_uuid),
        )

    async def execute_wave_planning(
        self, planning_flow_id: UUID, planning_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute wave planning for the given planning flow using CrewAI agent.

        Args:
            planning_flow_id: UUID of the planning flow
            planning_config: Configuration for wave planning

        Returns:
            Dict containing wave plan data

        ADR Compliance:
        - ADR-015: Uses TenantScopedAgentPool (no direct crew instance creation)
        - ADR-024: memory=False in crew, use TenantMemoryManager
        - ADR-029: sanitize_for_json on agent output
        - ADR-031: CallbackHandlerIntegration for tracking
        """
        try:
            logger.info(
                f"Starting CrewAI wave planning execution for flow: {planning_flow_id}"
            )

            # Update phase status to in_progress
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
                current_phase="wave_planning",
                phase_status="in_progress",
            )

            # Get planning flow to access selected applications
            planning_flow = await self.planning_repo.get_planning_flow_by_id(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
            )

            if not planning_flow:
                raise ValueError(f"Planning flow not found: {planning_flow_id}")

            # Import wave logic components
            from .wave_logic import (
                fetch_application_details,
                fetch_application_dependencies,
            )

            # Fetch application details and dependencies
            applications = await fetch_application_details(planning_flow)
            dependencies = await fetch_application_dependencies(planning_flow)

            logger.info(
                f"Fetched {len(applications)} applications and "
                f"{len(dependencies)} dependencies for wave planning"
            )

            # Import agent integration
            from .agent_integration import generate_wave_plan_with_agent

            # Generate wave plan using CrewAI agent (ADR-015 compliant)
            wave_plan = await generate_wave_plan_with_agent(
                agent_pool=self.agent_pool,
                applications=applications,
                dependencies=dependencies,
                config=planning_config,
                planning_flow_id=planning_flow_id,
                client_account_uuid=self.client_account_uuid,
                engagement_uuid=self.engagement_uuid,
                db=self.db,
            )

            # Update planning flow with wave plan data
            await self.planning_repo.save_wave_plan_data(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
                wave_plan_data=wave_plan,
            )

            # Update phase status to completed
            await self.planning_repo.update_phase_status(
                planning_flow_id=planning_flow_id,
                client_account_id=self.client_account_uuid,
                engagement_id=self.engagement_uuid,
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
                "message": "Wave planning completed successfully with CrewAI agent",
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
                    client_account_id=self.client_account_uuid,
                    engagement_id=self.engagement_uuid,
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
