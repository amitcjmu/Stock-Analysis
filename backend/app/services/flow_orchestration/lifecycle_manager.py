"""
Flow Lifecycle Manager

Handles core flow operations including create, delete, pause, resume, and state transitions.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.exceptions import FlowError, FlowNotFoundError, InvalidFlowStateError
from app.core.logging import get_logger
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from app.repositories.crewai_flow_state_extensions_repository import (
    CrewAIFlowStateExtensionsRepository,
)

from .state_transition_utils import FlowStateTransitionValidator

logger = get_logger(__name__)


class FlowLifecycleManager:
    """
    Manages the lifecycle of flows including creation, state transitions, and deletion.
    """

    def __init__(
        self,
        db: AsyncSession,
        context: RequestContext,
        master_repo: CrewAIFlowStateExtensionsRepository,
    ):
        """
        Initialize the Flow Lifecycle Manager

        Args:
            db: Database session
            context: Request context with tenant information
            master_repo: Repository for master flow operations
        """
        self.db = db
        self.context = context
        self.master_repo = master_repo

        logger.info(
            f"✅ Flow Lifecycle Manager initialized for client {context.client_account_id}"
        )

    async def create_flow_record(
        self,
        flow_id: str,
        flow_type: str,
        flow_name: str,
        flow_configuration: Dict[str, Any],
        initial_state: Dict[str, Any],
    ) -> CrewAIFlowStateExtensions:
        """
        Create a new flow record in the database

        Args:
            flow_id: Unique flow identifier
            flow_type: Type of flow (discovery, assessment, etc.)
            flow_name: Human-readable name for the flow
            flow_configuration: Flow-specific configuration
            initial_state: Initial state data

        Returns:
            Created master flow record

        Raises:
            FlowError: If flow creation fails
        """
        try:
            # Create master flow record with immediate commit for foreign key visibility
            # This ensures the master flow is immediately available for foreign key references
            master_flow = await self.master_repo.create_master_flow(
                flow_id=flow_id,
                flow_type=flow_type,
                user_id=self.context.user_id or "system",
                flow_name=flow_name,
                flow_configuration=flow_configuration,
                initial_state=initial_state,
                auto_commit=True,  # Commit immediately to ensure foreign key visibility
            )

            logger.info(
                f"✅ Master flow record created and committed for foreign key visibility: {flow_id}"
            )
            # No need to flush since auto_commit=True already committed

            return master_flow

        except Exception as e:
            logger.error(f"❌ Failed to create flow record {flow_id}: {e}")
            raise FlowError(
                message=f"Failed to create flow record: {str(e)}",
                flow_id=flow_id,
                details={"flow_type": flow_type, "original_error": type(e).__name__},
            )

    async def update_flow_status(
        self,
        flow_id: str,
        status: str,
        phase_data: Optional[Dict[str, Any]] = None,
        collaboration_entry: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update flow status and related data

        Args:
            flow_id: Flow identifier
            status: New status for the flow
            phase_data: Optional phase data to update
            collaboration_entry: Optional collaboration log entry

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.master_repo.update_flow_status(
                flow_id=flow_id,
                status=status,
                phase_data=phase_data,
                collaboration_entry=collaboration_entry,
            )

            logger.info(f"✅ Updated flow {flow_id} status to: {status}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to update flow status {flow_id}: {e}")
            return False

    async def pause_flow(
        self, flow_id: str, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pause a running flow

        Args:
            flow_id: Flow identifier
            reason: Optional reason for pausing

        Returns:
            Pause operation result

        Raises:
            ValueError: If flow cannot be paused
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            # Validate flow can be paused - use valid statuses from DB constraint
            if master_flow.flow_status not in ["active", "processing", "initialized"]:
                raise ValueError(
                    f"Cannot pause flow in status: {master_flow.flow_status}"
                )

            # Update flow status
            await self.update_flow_status(
                flow_id=flow_id,
                status="paused",
                phase_data={
                    "pause_reason": reason or "user_requested",
                    "paused_at": datetime.utcnow().isoformat(),
                },
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_paused",
                    "reason": reason or "user_requested",
                },
            )

            logger.info(f"⏸️ Paused flow {flow_id}: {reason}")

            return {
                "flow_id": flow_id,
                "status": "paused",
                "reason": reason or "user_requested",
                "paused_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to pause flow {flow_id}: {e}")
            raise RuntimeError(f"Failed to pause flow: {str(e)}")

    async def resume_flow(
        self, flow_id: str, resume_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resume a paused flow

        Args:
            flow_id: Flow identifier
            resume_context: Optional context for resuming

        Returns:
            Resume operation result

        Raises:
            FlowNotFoundError: If flow not found
            InvalidFlowStateError: If flow cannot be resumed
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise FlowNotFoundError(flow_id)

            # Use the centralized validation utility for comprehensive flow resume checking
            resume_validation = FlowStateTransitionValidator.safe_resume_flow(
                master_flow=master_flow, target_status="active"
            )

            if not resume_validation["success"]:
                logger.error(
                    f"❌ Flow resume validation failed: {resume_validation['error']}"
                )
                raise InvalidFlowStateError(
                    current_state=master_flow.flow_status,
                    target_state="active",
                    flow_id=flow_id,
                )

            logger.info(
                f"✅ Flow {flow_id} resume validation passed: {resume_validation['result']['reason']}"
            )

            # Update flow status - use 'active' instead of 'resumed' for DB constraint
            # Clear awaiting user approval flag when resuming
            resume_phase_data = {
                "resumed_at": datetime.utcnow().isoformat(),
                "resume_context": resume_context,
                "awaiting_user_approval": False,  # Clear approval flag
            }

            await self.update_flow_status(
                flow_id=flow_id,
                status="active",  # Changed from "resumed" to match DB constraint
                phase_data=resume_phase_data,
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "flow_resumed",
                    "cleared_approval_flag": True,
                },
            )

            logger.info(f"▶️ Resumed flow {flow_id}")

            return {
                "flow_id": flow_id,
                "status": "active",  # Changed from "resumed" to match what's stored in DB
                "resumed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to resume flow {flow_id}: {e}")

            # Re-raise known exceptions
            if isinstance(e, (FlowNotFoundError, InvalidFlowStateError)):
                raise

            # Wrap unknown exceptions
            raise FlowError(
                message=f"Failed to resume flow: {str(e)}",
                flow_id=flow_id,
                details={"operation": "resume", "original_error": type(e).__name__},
            )

    async def delete_flow(
        self, flow_id: str, soft_delete: bool = True, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a flow (soft delete by default)

        Args:
            flow_id: Flow identifier
            soft_delete: Whether to soft delete (default) or hard delete
            reason: Optional reason for deletion

        Returns:
            Delete operation result

        Raises:
            ValueError: If flow not found
            RuntimeError: If deletion fails
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                raise ValueError(f"Flow not found: {flow_id}")

            if soft_delete:
                # Soft delete - use 'cancelled' instead of 'deleted' for DB constraint
                await self.update_flow_status(
                    flow_id=flow_id,
                    status="cancelled",  # Changed from "deleted" to match DB constraint
                    phase_data={
                        "deleted_at": datetime.utcnow().isoformat(),
                        "deletion_reason": reason or "user_requested",
                        "soft_delete": True,
                    },
                    collaboration_entry={
                        "timestamp": datetime.utcnow().isoformat(),
                        "action": "flow_deleted",
                        "soft_delete": True,
                        "reason": reason,
                    },
                )

                logger.info(f"🗑️ Soft deleted flow {flow_id}")

            else:
                # Hard delete - remove from database
                success = await self.master_repo.delete_master_flow(flow_id)
                if not success:
                    raise RuntimeError("Failed to delete flow from database")

                logger.info(f"💀 Hard deleted flow {flow_id}")

            return {
                "flow_id": flow_id,
                "deleted": True,
                "soft_delete": soft_delete,
                "deleted_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
            raise RuntimeError(f"Failed to delete flow: {str(e)}")

    async def transition_flow_state(
        self,
        flow_id: str,
        from_state: str,
        to_state: str,
        transition_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Perform a state transition with validation

        Args:
            flow_id: Flow identifier
            from_state: Current expected state
            to_state: Target state
            transition_data: Optional data for the transition

        Returns:
            True if transition successful, False otherwise
        """
        try:
            # Get current flow state
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                logger.error(f"Flow not found for state transition: {flow_id}")
                return False

            # Validate current state matches expected
            if master_flow.flow_status != from_state:
                logger.error(
                    f"State mismatch for flow {flow_id}: expected {from_state}, got {master_flow.flow_status}"
                )
                return False

            # Perform state transition
            phase_data = {
                "previous_state": from_state,
                "transition_timestamp": datetime.utcnow().isoformat(),
                "transition_data": transition_data or {},
            }

            success = await self.update_flow_status(
                flow_id=flow_id,
                status=to_state,
                phase_data=phase_data,
                collaboration_entry={
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": "state_transition",
                    "from_state": from_state,
                    "to_state": to_state,
                },
            )

            if success:
                logger.info(
                    f"✅ State transition successful for flow {flow_id}: {from_state} -> {to_state}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to transition flow state {flow_id}: {e}")
            return False

    async def validate_flow_state(
        self, flow_id: str, expected_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate the current state of a flow

        Args:
            flow_id: Flow identifier
            expected_state: Optional expected state to validate against

        Returns:
            Validation result with flow state information
        """
        try:
            # Get flow
            master_flow = await self.master_repo.get_by_flow_id(flow_id)
            if not master_flow:
                return {
                    "valid": False,
                    "error": f"Flow not found: {flow_id}",
                    "current_state": None,
                }

            current_state = master_flow.flow_status

            # If expected state provided, validate it matches
            if expected_state:
                state_matches = current_state == expected_state
                return {
                    "valid": state_matches,
                    "current_state": current_state,
                    "expected_state": expected_state,
                    "error": (
                        None
                        if state_matches
                        else f"State mismatch: expected {expected_state}, got {current_state}"
                    ),
                }

            # Otherwise, just return current state info
            return {
                "valid": True,
                "current_state": current_state,
                "last_updated": (
                    master_flow.updated_at.isoformat()
                    if master_flow.updated_at
                    else None
                ),
                "error": None,
            }

        except Exception as e:
            logger.error(f"Failed to validate flow state {flow_id}: {e}")
            return {"valid": False, "error": str(e), "current_state": None}
