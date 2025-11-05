"""
Decommission Flow Repository - Enterprise Data Access Layer

Provides CRUD operations for decommission flows with automatic multi-tenant scoping
and context-aware operations. Follows ADR-006 two-table pattern integration with
Master Flow Orchestrator.

Reference:
- /docs/planning/DECOMMISSION_FLOW_SOLUTION.md Section 3.2
- Pattern: backend/app/repositories/collection_flow_repository.py
- Base: backend/app/repositories/context_aware_repository.py

Created: Issue #933 (Phase 1 of Decommission Flow Implementation)
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decommission_flow import DecommissionFlow
from app.repositories.context_aware_repository import ContextAwareRepository

logger = logging.getLogger(__name__)


class DecommissionFlowRepository(ContextAwareRepository[DecommissionFlow]):
    """
    Decommission flow repository with context-aware operations and flow-specific methods.

    Provides enterprise-grade CRUD operations with:
    - Automatic multi-tenant scoping (client_account_id + engagement_id)
    - Master Flow Orchestrator integration via master_flow_id
    - Phase status tracking and updates
    - Atomic transactions with proper error handling
    - Type-safe async/await throughout

    SECURITY NOTE: All queries automatically scoped by client_account_id and
    engagement_id to prevent cross-tenant data access.
    """

    def __init__(
        self,
        db: AsyncSession,
        client_account_id: Optional[str] = None,
        engagement_id: Optional[str] = None,
    ):
        """
        Initialize decommission flow repository with context.

        Args:
            db: Async database session
            client_account_id: Client account UUID for multi-tenant scoping
            engagement_id: Engagement UUID for project scoping

        Raises:
            ValueError: If client_account_id is None (required for security)
        """
        super().__init__(db, DecommissionFlow, client_account_id, engagement_id)

    async def create(
        self,
        flow_name: str,
        selected_system_ids: List[uuid.UUID],
        created_by: str,
        decommission_strategy: Optional[Dict[str, Any]] = None,
        master_flow_id: Optional[uuid.UUID] = None,
        **kwargs,
    ) -> DecommissionFlow:
        """
        Create a new decommission flow with Master Flow Orchestrator (MFO) integration.

        CRITICAL: This method should be called AFTER master flow creation via MFO.
        The master_flow_id parameter links this child flow to its master flow.

        Args:
            flow_name: Human-readable flow name
            selected_system_ids: List of Asset IDs to decommission
            created_by: User ID of flow creator
            decommission_strategy: Strategy configuration (priority, execution_mode, etc.)
            master_flow_id: UUID of master flow in crewai_flow_state_extensions
            **kwargs: Additional flow attributes (flow_id, runtime_state, etc.)

        Returns:
            Created DecommissionFlow instance (flushed but not committed)

        Raises:
            ValueError: If master_flow_id is None (required for MFO integration)
            SQLAlchemyError: On database errors
        """
        if master_flow_id is None:
            raise ValueError(
                "master_flow_id is required. Create master flow via MFO first."
            )

        # Generate flow_id if not provided
        flow_id = kwargs.get("flow_id") or uuid.uuid4()

        # Prepare flow data
        flow_data = {
            "flow_id": flow_id,
            "flow_name": flow_name,
            "selected_system_ids": selected_system_ids,
            "system_count": len(selected_system_ids),
            "created_by": created_by,
            "status": kwargs.get("status", "initialized"),
            "current_phase": kwargs.get("current_phase", "decommission_planning"),
            "decommission_strategy": decommission_strategy or {},
            "runtime_state": kwargs.get("runtime_state", {}),
            "master_flow_id": master_flow_id,
            "client_account_id": self.client_account_id,
            "engagement_id": self.engagement_id,
            **kwargs,
        }

        # Use parent class create method with no commit (Service Registry pattern)
        decommission_flow = await super().create(commit=False, **flow_data)

        logger.info(
            f"✅ Decommission flow created with MFO integration: "
            f"flow_id={flow_id}, master_flow_id={master_flow_id}, "
            f"systems={len(selected_system_ids)}"
        )

        return decommission_flow

    async def get_by_flow_id(self, flow_id: uuid.UUID) -> Optional[DecommissionFlow]:
        """
        Get decommission flow by flow_id with context filtering.

        CRITICAL: Returns single object, not List (per architectural pattern from
        collection-flow-id-resolver-fix memory).

        Args:
            flow_id: Primary key UUID of decommission flow

        Returns:
            DecommissionFlow instance or None if not found

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            flows = await self.get_by_filters(flow_id=flow_id)
            return flows[0] if flows else None
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_flow_id: {e}")
            raise

    async def get_by_master_flow_id(
        self, master_flow_id: uuid.UUID
    ) -> Optional[DecommissionFlow]:
        """
        Get decommission flow by master flow ID with context filtering.

        CRITICAL: Returns single object, not List (per architectural pattern).
        Master flow ID is used for MFO coordination and cross-flow queries.

        Args:
            master_flow_id: UUID of master flow in crewai_flow_state_extensions

        Returns:
            DecommissionFlow instance or None if not found

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            flows = await self.get_by_filters(master_flow_id=master_flow_id)
            return flows[0] if flows else None
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_master_flow_id: {e}")
            raise

    async def update_status(
        self,
        flow_id: uuid.UUID,
        status: str,
        current_phase: Optional[str] = None,
    ) -> Optional[DecommissionFlow]:
        """
        Update decommission flow status and current phase.

        Per ADR-012: Child flow status represents operational state (initialized,
        decommission_planning, data_migration, system_shutdown, completed, failed).

        Args:
            flow_id: Flow UUID to update
            status: New status (must match check constraint)
            current_phase: Optional new phase (decommission_planning, data_migration,
                          system_shutdown, completed)

        Returns:
            Updated DecommissionFlow instance or None if not found

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            # Get existing flow with tenant scoping
            flow = await self.get_by_flow_id(flow_id)
            if not flow:
                logger.warning(
                    f"Flow {flow_id} not found for status update in tenant "
                    f"{self.client_account_id}/{self.engagement_id}"
                )
                return None

            # Prepare update data
            update_data = {"status": status}
            if current_phase:
                update_data["current_phase"] = current_phase

            # Use parent class update method
            updated_flow = await self.update(flow.flow_id, commit=False, **update_data)

            logger.info(
                f"✅ Updated flow {flow_id} status: {status}, phase: {current_phase}"
            )

            return updated_flow

        except SQLAlchemyError as e:
            logger.error(f"Database error in update_status: {e}")
            raise

    async def update_phase_status(
        self,
        flow_id: uuid.UUID,
        phase_name: str,
        phase_status: str,
    ) -> Optional[DecommissionFlow]:
        """
        Update specific phase status (e.g., decommission_planning_status).

        ALIGNED WITH FlowTypeConfig per ADR-027: Each phase has a dedicated
        status column (decommission_planning_status, data_migration_status,
        system_shutdown_status).

        Args:
            flow_id: Flow UUID to update
            phase_name: Phase name (decommission_planning, data_migration, system_shutdown)
            phase_status: New status (pending, running, completed, failed)

        Returns:
            Updated DecommissionFlow instance or None if not found

        Raises:
            ValueError: If phase_name is invalid
            SQLAlchemyError: On database errors
        """
        # Validate phase name
        valid_phases = ["decommission_planning", "data_migration", "system_shutdown"]
        if phase_name not in valid_phases:
            raise ValueError(
                f"Invalid phase_name: {phase_name}. "
                f"Must be one of: {', '.join(valid_phases)}"
            )

        try:
            # Get existing flow with tenant scoping
            flow = await self.get_by_flow_id(flow_id)
            if not flow:
                logger.warning(
                    f"Flow {flow_id} not found for phase status update in tenant "
                    f"{self.client_account_id}/{self.engagement_id}"
                )
                return None

            # Construct phase status column name
            phase_status_col = f"{phase_name}_status"

            # Update phase status
            update_data = {phase_status_col: phase_status}
            updated_flow = await self.update(flow.flow_id, commit=False, **update_data)

            logger.info(
                f"✅ Updated flow {flow_id} phase {phase_name} status: {phase_status}"
            )

            return updated_flow

        except SQLAlchemyError as e:
            logger.error(f"Database error in update_phase_status: {e}")
            raise

    async def list_by_tenant(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[DecommissionFlow]:
        """
        List all decommission flows for current tenant (client_account_id + engagement_id).

        Automatically scoped by ContextAwareRepository to current tenant context.

        Args:
            limit: Maximum number of flows to return
            offset: Number of flows to skip (for pagination)

        Returns:
            List of DecommissionFlow instances

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            flows = await self.get_all(limit=limit, offset=offset)
            logger.debug(
                f"Retrieved {len(flows)} decommission flows for tenant "
                f"{self.client_account_id}/{self.engagement_id}"
            )
            return flows

        except SQLAlchemyError as e:
            logger.error(f"Database error in list_by_tenant: {e}")
            raise

    async def delete(
        self,
        flow_id: uuid.UUID,
    ) -> bool:
        """
        Delete decommission flow by flow_id with tenant scoping.

        CRITICAL: Deletion is scoped by client_account_id + engagement_id for security.
        Will cascade delete to related plans, archive jobs, execution logs, and
        validation checks per SQLAlchemy relationship configuration.

        Args:
            flow_id: Flow UUID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            # Get flow first to verify tenant scoping
            flow = await self.get_by_flow_id(flow_id)
            if not flow:
                logger.warning(
                    f"Flow {flow_id} not found for deletion in tenant "
                    f"{self.client_account_id}/{self.engagement_id}"
                )
                return False

            # Use parent class delete method (no commit - Service Registry pattern)
            deleted = await super().delete(flow.flow_id, commit=False)

            if deleted:
                logger.info(
                    f"✅ Deleted decommission flow {flow_id} in tenant "
                    f"{self.client_account_id}/{self.engagement_id}"
                )

            return deleted

        except SQLAlchemyError as e:
            logger.error(f"Database error in delete: {e}")
            raise

    async def get_by_status(self, status: str) -> List[DecommissionFlow]:
        """
        Get decommission flows by status with context filtering.

        Args:
            status: Flow status (initialized, decommission_planning, data_migration,
                   system_shutdown, completed, failed)

        Returns:
            List of matching DecommissionFlow instances

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            return await self.get_by_filters(status=status)
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_status: {e}")
            raise

    async def get_active_flows(self) -> List[DecommissionFlow]:
        """
        Get all active (non-completed/failed) decommission flows.

        Active flows are those in initialized, decommission_planning, data_migration,
        or system_shutdown status.

        Returns:
            List of active DecommissionFlow instances

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            all_flows = await self.get_all()
            active_statuses = [
                "initialized",
                "decommission_planning",
                "data_migration",
                "system_shutdown",
            ]
            return [flow for flow in all_flows if flow.status in active_statuses]
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_active_flows: {e}")
            raise

    async def get_by_system_id(self, system_id: uuid.UUID) -> List[DecommissionFlow]:
        """
        Get decommission flows containing a specific system ID.

        Useful for checking if a system is already scheduled for decommission.

        Args:
            system_id: Asset UUID to search for

        Returns:
            List of DecommissionFlow instances containing this system

        Raises:
            SQLAlchemyError: On database errors
        """
        try:
            # Query with PostgreSQL array contains operator
            stmt = select(DecommissionFlow).where(
                and_(
                    DecommissionFlow.selected_system_ids.contains([system_id]),
                    DecommissionFlow.client_account_id == self.client_account_id,
                    DecommissionFlow.engagement_id == self.engagement_id,
                )
            )

            result = await self.db.execute(stmt)
            flows = result.scalars().all()

            logger.debug(
                f"Found {len(flows)} decommission flows containing system {system_id}"
            )

            return flows

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_by_system_id: {e}")
            raise
