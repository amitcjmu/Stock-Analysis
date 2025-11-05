"""
Decommission Child Flow Service

Service for managing decommission flow child operations following ADR-025.
Implements safe system decommissioning with data preservation and compliance.

Reference:
- ADR-025: Child Flow Service Pattern
- /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 4.0
- Pattern: backend/app/services/child_flow_services/collection.py

Created: Issue #937 (Phase 3 of Decommission Flow Implementation)
"""

import logging
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.repositories.decommission_flow_repository import DecommissionFlowRepository
from app.services.child_flow_services.base import BaseChildFlowService

logger = logging.getLogger(__name__)


class DecommissionChildFlowService(BaseChildFlowService):
    """
    Service for decommission flow child operations.

    Implements ADR-025 pattern with execute_phase() routing to three phase handlers:
    1. decommission_planning: Dependency analysis, risk assessment, cost analysis
    2. data_migration: Data retention policies, archival jobs
    3. system_shutdown: Pre-validation, shutdown, post-validation, cleanup

    NO crew_class usage (deprecated per ADR-025) - uses TenantScopedAgentPool instead.
    """

    def __init__(self, db: AsyncSession, context: RequestContext):
        """
        Initialize decommission child flow service with tenant-scoped repository.

        Args:
            db: Async database session
            context: Request context with client_account_id and engagement_id
        """
        super().__init__(db, context)
        # Initialize repository with explicit tenant scoping (per ADR-025)
        self.repository = DecommissionFlowRepository(
            db=self.db,
            client_account_id=str(context.client_account_id),
            engagement_id=str(context.engagement_id),
        )

    async def get_child_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get decommission flow child status.

        Args:
            flow_id: Master flow identifier (UUID string)

        Returns:
            Child flow status dictionary with operational state, or None if not found
        """
        try:
            child_flow = await self.repository.get_by_master_flow_id(UUID(flow_id))
            if not child_flow:
                logger.warning(f"Decommission flow not found for master flow {flow_id}")
                return None

            # Convert selected_system_ids safely (handles ARRAY type)
            system_ids = child_flow.selected_system_ids
            system_ids_list = (
                [str(sys_id) for sys_id in system_ids] if system_ids else []
            )

            return {
                "status": child_flow.status,
                "current_phase": child_flow.current_phase,
                "system_count": child_flow.system_count,
                "selected_system_ids": system_ids_list,
                "decommission_strategy": child_flow.decommission_strategy,
                "total_systems_decommissioned": child_flow.total_systems_decommissioned,
                "estimated_annual_savings": (
                    float(child_flow.estimated_annual_savings)
                    if child_flow.estimated_annual_savings
                    else None
                ),
                "compliance_score": (
                    float(child_flow.compliance_score)
                    if child_flow.compliance_score
                    else None
                ),
                # Phase statuses per ADR-027
                "decommission_planning_status": child_flow.decommission_planning_status,
                "data_migration_status": child_flow.data_migration_status,
                "system_shutdown_status": child_flow.system_shutdown_status,
            }
        except Exception as e:
            logger.warning(f"Failed to get decommission child flow status: {e}")
            return None

    async def get_by_master_flow_id(self, flow_id: str):
        """
        Get decommission flow by master flow ID.

        Args:
            flow_id: Master flow identifier (UUID string)

        Returns:
            Decommission flow entity or None if not found
        """
        try:
            return await self.repository.get_by_master_flow_id(UUID(flow_id))
        except Exception as e:
            logger.warning(f"Failed to get decommission flow by master ID: {e}")
            return None

    async def execute_phase(
        self,
        flow_id: str,
        phase_name: str,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute phase using persistent agents via TenantScopedAgentPool.

        Routes to phase-specific handlers per ADR-027 phase names:
        - decommission_planning: Dependency analysis, risk assessment, cost analysis
        - data_migration: Data retention policies, archival jobs
        - system_shutdown: Pre-validation, shutdown, post-validation, cleanup

        Args:
            flow_id: Master flow identifier (UUID string)
            phase_name: Phase to execute
            phase_input: Optional input data for the phase

        Returns:
            Phase execution result dictionary

        Raises:
            ValueError: If decommission flow not found for master flow ID
        """
        child_flow = await self.get_by_master_flow_id(flow_id)
        if not child_flow:
            raise ValueError(f"Decommission flow not found for master flow {flow_id}")

        logger.info(
            f"Executing decommission phase '{phase_name}' for flow {flow_id} "
            f"(child_flow.flow_id={child_flow.flow_id})"
        )

        # Route to phase-specific handler
        if phase_name == "decommission_planning":
            return await self._execute_decommission_planning(child_flow, phase_input)
        elif phase_name == "data_migration":
            return await self._execute_data_migration(child_flow, phase_input)
        elif phase_name == "system_shutdown":
            return await self._execute_system_shutdown(child_flow, phase_input)
        else:
            raise ValueError(
                f"Unknown phase: {phase_name}. Valid phases: "
                "decommission_planning, data_migration, system_shutdown"
            )

    async def _execute_decommission_planning(
        self,
        child_flow,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute decommission planning phase.

        Analyzes system dependencies, assesses risks, and calculates cost savings.
        Uses DecommissionAgentPool for planning crew.

        Args:
            child_flow: DecommissionFlow entity
            phase_input: Optional input data

        Returns:
            Phase execution result dictionary
        """
        logger.info(
            f"Executing decommission_planning phase for flow {child_flow.flow_id}"
        )

        try:
            # Update phase status to running
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="decommission_planning",
                phase_status="running",
            )

            # TODO: Call DecommissionAgentPool for planning crew
            # agent_pool = DecommissionAgentPool()
            # result = await agent_pool.execute_decommission_planning_crew(
            #     client_account_id=self.context.client_account_id,
            #     engagement_id=self.context.engagement_id,
            #     system_ids=child_flow.selected_system_ids,
            # )

            # STUB: Return placeholder for now
            logger.warning(
                "DecommissionAgentPool not yet integrated - returning placeholder"
            )

            # Update phase status to completed
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="decommission_planning",
                phase_status="completed",
            )

            # Update flow status to data_migration
            await self.repository.update_status(
                flow_id=child_flow.flow_id,
                status="data_migration",
                current_phase="data_migration",
            )

            return {
                "status": "success",
                "phase": "decommission_planning",
                "execution_type": "stub",
                "message": "Planning phase pending agent integration",
                "next_phase": "data_migration",
            }

        except Exception as e:
            logger.error(
                f"Error in decommission_planning phase: {e}",
                exc_info=True,
            )
            # Try to mark phase as failed (but don't fail if this fails)
            try:
                await self.repository.update_phase_status(
                    flow_id=child_flow.flow_id,
                    phase_name="decommission_planning",
                    phase_status="failed",
                )
            except Exception as update_error:
                logger.error(f"Failed to update phase status to failed: {update_error}")
            return {
                "status": "failed",
                "phase": "decommission_planning",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _execute_data_migration(
        self,
        child_flow,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute data migration phase.

        Creates data retention policies and initiates archival jobs.
        Uses DecommissionAgentPool for data migration crew.

        Args:
            child_flow: DecommissionFlow entity
            phase_input: Optional input data

        Returns:
            Phase execution result dictionary
        """
        logger.info(f"Executing data_migration phase for flow {child_flow.flow_id}")

        try:
            # Update phase status to running
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="data_migration",
                phase_status="running",
            )

            # TODO: Call DecommissionAgentPool for data migration crew
            # agent_pool = DecommissionAgentPool()
            # result = await agent_pool.execute_data_migration_crew(
            #     client_account_id=self.context.client_account_id,
            #     engagement_id=self.context.engagement_id,
            #     flow_id=child_flow.flow_id,
            # )

            # STUB: Return placeholder for now
            logger.warning(
                "DecommissionAgentPool not yet integrated - returning placeholder"
            )

            # Update phase status to completed
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="data_migration",
                phase_status="completed",
            )

            # Update flow status to system_shutdown
            await self.repository.update_status(
                flow_id=child_flow.flow_id,
                status="system_shutdown",
                current_phase="system_shutdown",
            )

            return {
                "status": "success",
                "phase": "data_migration",
                "execution_type": "stub",
                "message": "Data migration phase pending agent integration",
                "next_phase": "system_shutdown",
            }

        except Exception as e:
            logger.error(
                f"Error in data_migration phase: {e}",
                exc_info=True,
            )
            # Try to mark phase as failed (but don't fail if this fails)
            try:
                await self.repository.update_phase_status(
                    flow_id=child_flow.flow_id,
                    phase_name="data_migration",
                    phase_status="failed",
                )
            except Exception as update_error:
                logger.error(f"Failed to update phase status to failed: {update_error}")
            return {
                "status": "failed",
                "phase": "data_migration",
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def _execute_system_shutdown(
        self,
        child_flow,
        phase_input: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute system shutdown phase.

        Performs pre-validation, shutdown, post-validation, and cleanup.
        Uses DecommissionAgentPool for shutdown crew.

        Args:
            child_flow: DecommissionFlow entity
            phase_input: Optional input data

        Returns:
            Phase execution result dictionary
        """
        logger.info(f"Executing system_shutdown phase for flow {child_flow.flow_id}")

        try:
            # Update phase status to running
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="system_shutdown",
                phase_status="running",
            )

            # TODO: Call DecommissionAgentPool for shutdown crew
            # agent_pool = DecommissionAgentPool()
            # result = await agent_pool.execute_system_shutdown_crew(
            #     client_account_id=self.context.client_account_id,
            #     engagement_id=self.context.engagement_id,
            #     flow_id=child_flow.flow_id,
            # )

            # STUB: Return placeholder for now
            logger.warning(
                "DecommissionAgentPool not yet integrated - returning placeholder"
            )

            # Update phase status to completed
            await self.repository.update_phase_status(
                flow_id=child_flow.flow_id,
                phase_name="system_shutdown",
                phase_status="completed",
            )

            # Update flow status to completed
            await self.repository.update_status(
                flow_id=child_flow.flow_id,
                status="completed",
                current_phase="completed",
            )

            return {
                "status": "success",
                "phase": "system_shutdown",
                "execution_type": "stub",
                "message": "Shutdown phase pending agent integration",
                "next_phase": "completed",
            }

        except Exception as e:
            logger.error(
                f"Error in system_shutdown phase: {e}",
                exc_info=True,
            )
            # Try to mark phase as failed (but don't fail if this fails)
            try:
                await self.repository.update_phase_status(
                    flow_id=child_flow.flow_id,
                    phase_name="system_shutdown",
                    phase_status="failed",
                )
            except Exception as update_error:
                logger.error(f"Failed to update phase status to failed: {update_error}")
            return {
                "status": "failed",
                "phase": "system_shutdown",
                "error": str(e),
                "error_type": type(e).__name__,
            }
