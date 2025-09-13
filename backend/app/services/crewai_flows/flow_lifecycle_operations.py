"""
Flow Lifecycle Operations
Methods for handling flow lifecycle events (resume, complete, error handling, cleanup)
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from .persistence.postgres_store import PostgresFlowStateStore
from .persistence.secure_checkpoint_manager import SecureCheckpointManager
from .persistence.state_recovery import FlowStateRecovery, StateRecoveryError
from .flow_state_utils import (
    build_error_log_entry,
    build_completion_log_entry,
    build_resume_log_entry,
    sanitize_state_for_storage,
    build_recovery_context,
)

logger = logging.getLogger(__name__)


class FlowLifecycleOperations:
    """Handles flow lifecycle operations like resume, complete, error handling, cleanup"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.recovery = FlowStateRecovery(db, context)
        self.secure_checkpoint_manager = SecureCheckpointManager(context)

    async def resume_flow_state(
        self, flow_id: str, checkpoint_id: str, reason: str = "Manual resume"
    ) -> Dict[str, Any]:
        """Resume a flow from a specific checkpoint"""
        try:
            logger.info(f"🔄 Resuming flow {flow_id} from checkpoint {checkpoint_id}")

            # Load checkpoint data
            checkpoint_data = await self.secure_checkpoint_manager.load_checkpoint(
                checkpoint_id=checkpoint_id, flow_id=flow_id, context=self.context
            )

            if not checkpoint_data:
                raise StateRecoveryError(f"Checkpoint {checkpoint_id} not found")

            # Restore state from checkpoint
            restored_state = checkpoint_data.get("state", {})
            restored_state["status"] = "running"
            restored_state["updated_at"] = datetime.utcnow().isoformat()

            # Add resume log entry
            if "workflow_log" not in restored_state:
                restored_state["workflow_log"] = []

            resume_entry = build_resume_log_entry(checkpoint_id, reason)
            restored_state["workflow_log"].append(resume_entry)

            # Save restored state
            await self.store.save_state(
                flow_id=flow_id,
                state=restored_state,
                phase=restored_state.get("current_phase", "unknown"),
            )

            logger.info(f"✅ Flow {flow_id} resumed from checkpoint {checkpoint_id}")
            return {
                "flow_id": flow_id,
                "status": "resumed",
                "checkpoint_id": checkpoint_id,
                "resumed_at": resume_entry["resumed_at"],
                "current_phase": restored_state.get("current_phase"),
            }

        except Exception as e:
            logger.error(f"❌ Failed to resume flow {flow_id}: {e}")
            await self._log_recovery_attempt(flow_id, e)
            raise

    async def complete_phase(
        self,
        flow_id: str,
        phase: str,
        results: Dict[str, Any],
        next_phase: str = None,
    ) -> Dict[str, Any]:
        """Mark a phase as completed and optionally transition to next phase"""
        try:
            logger.info(f"🔄 Completing phase '{phase}' for flow {flow_id}")

            # Load current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise StateRecoveryError(f"No state found for flow {flow_id}")

            # Update phase completion
            if "phase_completion" not in current_state:
                current_state["phase_completion"] = {}

            current_state["phase_completion"][phase] = True
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # Add completion log entry
            if "workflow_log" not in current_state:
                current_state["workflow_log"] = []

            completion_entry = build_completion_log_entry(phase, results)
            current_state["workflow_log"].append(completion_entry)

            # Transition to next phase if specified
            if next_phase:
                current_state["current_phase"] = next_phase
                logger.info(f"🔄 Transitioning to phase '{next_phase}'")

            # Update progress percentage
            completed_phases = sum(
                1
                for completed in current_state["phase_completion"].values()
                if completed
            )
            total_phases = len(current_state["phase_completion"])
            current_state["progress_percentage"] = (
                completed_phases / total_phases
            ) * 100

            # Save updated state
            await self.store.save_state(
                flow_id=flow_id,
                state=current_state,
                phase=current_state.get("current_phase", phase),
            )

            # Create checkpoint for completed phase
            checkpoint_id = await self.secure_checkpoint_manager.create_checkpoint(
                flow_id=flow_id,
                phase=f"{phase}_completed",
                state=current_state,
                metadata={
                    "phase_completed": phase,
                    "results_summary": results.get("summary"),
                },
                context=self.context,
            )

            logger.info(f"✅ Phase '{phase}' completed for flow {flow_id}")
            return {
                "flow_id": flow_id,
                "phase": phase,
                "status": "completed",
                "next_phase": next_phase,
                "checkpoint_id": checkpoint_id,
                "progress_percentage": current_state["progress_percentage"],
                "completed_at": completion_entry["completed_at"],
            }

        except Exception as e:
            logger.error(
                f"❌ Failed to complete phase '{phase}' for flow {flow_id}: {e}"
            )
            raise

    async def handle_flow_error(
        self,
        flow_id: str,
        error: Exception,
        phase: str = None,
        recovery_options: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Handle flow errors with recovery options"""
        try:
            logger.error(f"🚨 Handling error for flow {flow_id}: {error}")

            # Load current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                current_state = {"flow_id": flow_id, "errors": [], "workflow_log": []}

            # Add error log entry
            error_entry = build_error_log_entry(type(error).__name__, str(error), phase)

            if "errors" not in current_state:
                current_state["errors"] = []
            if "workflow_log" not in current_state:
                current_state["workflow_log"] = []

            current_state["errors"].append(error_entry)
            current_state["workflow_log"].append(error_entry)
            current_state["status"] = "error"
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # Save error state
            await self.store.save_state(
                flow_id=flow_id,
                state=sanitize_state_for_storage(current_state),
                phase=phase or current_state.get("current_phase", "unknown"),
            )

            # Attempt recovery if options provided
            recovery_result = None
            if recovery_options:
                try:
                    recovery_context = build_recovery_context(
                        flow_id, error, self.context
                    )
                    recovery_result = await self.recovery.attempt_recovery(
                        flow_id=flow_id,
                        error=error,
                        context=recovery_context,
                        options=recovery_options,
                    )

                    if recovery_result.get("success"):
                        current_state["status"] = "recovered"
                        logger.info(f"✅ Flow {flow_id} recovered from error")

                except Exception as recovery_error:
                    logger.error(
                        f"❌ Recovery failed for flow {flow_id}: {recovery_error}"
                    )
                    recovery_result = {"success": False, "error": str(recovery_error)}

            logger.info(f"🔍 Error handled for flow {flow_id}")
            return {
                "flow_id": flow_id,
                "status": "error_handled",
                "error_logged": True,
                "recovery_attempted": recovery_options is not None,
                "recovery_result": recovery_result,
                "handled_at": error_entry["timestamp"],
            }

        except Exception as e:
            logger.error(f"❌ Failed to handle error for flow {flow_id}: {e}")
            raise

    async def cleanup_flow_state(
        self, flow_id: str, archive: bool = True, versions_to_keep: int = 3
    ) -> Dict[str, Any]:
        """Clean up flow state and optionally archive it"""
        try:
            logger.info(f"🧹 Cleaning up flow state: {flow_id}")

            # Load current state for archival
            current_state = None
            if archive:
                current_state = await self.store.load_state(flow_id)

            # Clean up old versions
            versions_cleaned = await self.store.cleanup_old_versions(
                flow_id=flow_id, versions_to_keep=versions_to_keep
            )

            # Archive current state if requested
            archive_id = None
            if archive and current_state:
                archive_id = await self.secure_checkpoint_manager.create_checkpoint(
                    flow_id=flow_id,
                    phase="archived",
                    state=sanitize_state_for_storage(current_state),
                    metadata={
                        "archived": True,
                        "cleaned_at": datetime.utcnow().isoformat(),
                    },
                    context=self.context,
                )

            logger.info(f"✅ Flow state cleaned up: {flow_id}")
            return {
                "flow_id": flow_id,
                "status": "cleaned",
                "versions_cleaned": versions_cleaned,
                "archived": archive,
                "archive_id": archive_id,
                "cleaned_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to clean up flow state for {flow_id}: {e}")
            raise

    async def _log_recovery_attempt(self, flow_id: str, error: Exception):
        """Log recovery attempt for monitoring"""
        try:
            recovery_context = build_recovery_context(flow_id, error, self.context)
            current_state = await self.store.load_state(flow_id) or {}

            if "workflow_log" not in current_state:
                current_state["workflow_log"] = []

            current_state["workflow_log"].append(
                {
                    "event": "recovery_attempted",
                    "recovery_error": str(error),
                    "recovery_status": "failed",
                    **recovery_context,
                }
            )

            await self.store.save_state(
                flow_id=flow_id,
                state=current_state,
                phase=current_state.get("current_phase", "unknown"),
            )
        except Exception as log_error:
            logger.error(f"Failed to log recovery attempt: {log_error}")
