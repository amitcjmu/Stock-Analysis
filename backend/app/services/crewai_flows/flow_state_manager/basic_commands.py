"""
Flow State Manager - Basic Command Operations
Handles create, update, complete, error, and cleanup operations
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator

from ..persistence.postgres_store import (
    ConcurrentModificationError,
    PostgresFlowStateStore,
    StateValidationError,
)
from ..persistence.secure_checkpoint_manager import SecureCheckpointManager
from ..persistence.state_recovery import FlowStateRecovery, StateRecoveryError
from ..flow_state_utils import create_initial_state_structure

logger = logging.getLogger(__name__)


class FlowStateBasicCommands:
    """Handles basic write/update operations for flow state"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
        self.recovery = FlowStateRecovery(db, context)
        self.secure_checkpoint_manager = SecureCheckpointManager(context)

    async def create_flow_state(
        self, flow_id: str, initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new flow state"""
        try:
            logger.info(f"🔄 Creating new flow state: {flow_id}")

            # Create initial state structure using helper function
            flow_state = create_initial_state_structure(
                self.context, flow_id, initial_data
            )

            # Validate initial state
            validation_result = self.validator.validate_complete_state(flow_state)
            if not validation_result["valid"]:
                raise StateValidationError(
                    f"Invalid initial state: {validation_result['errors']}"
                )

            # Save to PostgreSQL
            await self.store.save_state(
                flow_id=flow_id, state=flow_state, phase="initialization"
            )

            # Create initial secure checkpoint
            checkpoint_id = await self.secure_checkpoint_manager.create_checkpoint(
                flow_id=flow_id,
                phase="initialization",
                state=flow_state,
                metadata={"initial_creation": True},
                context=self.context,
            )

            logger.info(f"✅ Flow state created: {flow_id}")
            return {
                "flow_id": flow_id,
                "status": "created",
                "checkpoint_id": checkpoint_id,
                "created_at": flow_state["created_at"],
            }

        except Exception as e:
            logger.error(f"❌ Failed to create flow state for {flow_id}: {e}")
            raise

    async def update_flow_state(
        self, flow_id: str, state_updates: Dict[str, Any], version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update flow state with validation"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")

            # Apply updates
            updated_state = current_state.copy()
            updated_state.update(state_updates)
            updated_state["updated_at"] = datetime.utcnow().isoformat()

            # Validate updated state
            validation_result = self.validator.validate_complete_state(updated_state)
            if not validation_result["valid"]:
                raise StateValidationError(
                    f"Invalid state update: {validation_result['errors']}"
                )

            # Save updated state
            await self.store.save_state(
                flow_id=flow_id,
                state=updated_state,
                phase=updated_state.get("current_phase", "unknown"),
                version=version,
            )

            logger.info(f"✅ Flow state updated: {flow_id}")
            return {
                "flow_id": flow_id,
                "status": "updated",
                "updated_at": updated_state["updated_at"],
            }

        except ConcurrentModificationError as e:
            logger.warning(f"⚠️ Concurrent modification detected for {flow_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to update flow state for {flow_id}: {e}")
            raise

    async def complete_phase(
        self, flow_id: str, phase: str, results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mark a phase as completed with results"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")

            # Update phase completion
            if "phase_completion" not in current_state:
                current_state["phase_completion"] = {}

            current_state["phase_completion"][phase] = True
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # Store phase results
            results_key = f"{phase}_results"
            current_state[results_key] = results

            # Add to workflow log
            if "workflow_log" not in current_state:
                current_state["workflow_log"] = []

            current_state["workflow_log"].append(
                {
                    "timestamp": current_state["updated_at"],
                    "event": "phase_completed",
                    "phase": phase,
                    "results_summary": {
                        "status": results.get("status"),
                        "records_processed": results.get("records_processed", 0),
                        "errors": len(results.get("errors", [])),
                        "warnings": len(results.get("warnings", [])),
                    },
                }
            )

            # Create secure checkpoint after completion
            checkpoint_id = await self.secure_checkpoint_manager.create_checkpoint(
                flow_id=flow_id,
                phase=phase,
                state=current_state,
                metadata={
                    "phase_completed": True,
                    "results_summary": results.get("status"),
                },
                context=self.context,
            )

            # Save updated state
            await self.store.save_state(
                flow_id=flow_id, state=current_state, phase=phase
            )

            logger.info(f"✅ Phase completed: {flow_id} -> {phase}")
            return {
                "flow_id": flow_id,
                "phase": phase,
                "checkpoint_id": checkpoint_id,
                "completed_at": current_state["updated_at"],
                "results": results,
            }

        except Exception as e:
            logger.error(f"❌ Failed to complete phase {phase} for {flow_id}: {e}")
            raise

    async def handle_flow_error(
        self,
        flow_id: str,
        error: str,
        phase: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Handle flow errors with automatic recovery attempts"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")

            # Add error to state
            if "errors" not in current_state:
                current_state["errors"] = []

            error_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase,
                "error": error,
                "details": details or {},
            }
            current_state["errors"].append(error_entry)

            # Update status
            current_state["status"] = "failed"
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # Save error state
            await self.store.save_state(
                flow_id=flow_id, state=current_state, phase=phase
            )

            # Attempt automatic recovery
            try:
                recovery_result = await self.recovery.recover_failed_flow(flow_id)
                logger.info(
                    f"✅ Automatic recovery attempted for {flow_id}: {recovery_result['status']}"
                )

                return {
                    "flow_id": flow_id,
                    "error_logged": True,
                    "recovery_attempted": True,
                    "recovery_result": recovery_result,
                    "handled_at": current_state["updated_at"],
                }

            except StateRecoveryError as recovery_error:
                logger.error(
                    f"❌ Automatic recovery failed for {flow_id}: {recovery_error}"
                )

                return {
                    "flow_id": flow_id,
                    "error_logged": True,
                    "recovery_attempted": False,
                    "recovery_error": str(recovery_error),
                    "handled_at": current_state["updated_at"],
                }

        except Exception as e:
            logger.error(f"❌ Failed to handle error for {flow_id}: {e}")
            raise

    async def cleanup_flow_state(
        self, flow_id: str, archive: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up flow state with optional archiving

        FIXED: Use secure_checkpoint_manager instead of store.create_checkpoint,
        and load current state before creating checkpoint.
        """
        try:
            checkpoint_id = None
            if archive:
                # Load current state first
                current_state = await self.store.load_state(flow_id)
                if current_state:
                    # Create final checkpoint before cleanup using secure checkpoint manager
                    checkpoint_id = (
                        await self.secure_checkpoint_manager.create_checkpoint(
                            flow_id=flow_id,
                            phase="cleanup",
                            state=current_state,
                            metadata={"cleanup_archive": True},
                            context=self.context,
                        )
                    )
                    logger.info(f"✅ Created cleanup checkpoint: {checkpoint_id}")
                else:
                    logger.warning(f"⚠️ No state found for {flow_id}, skipping archive")

            # Clean up old versions (keep last 2)
            cleaned_versions = await self.store.cleanup_old_versions(
                flow_id, keep_versions=2
            )

            logger.info(
                f"✅ Flow state cleaned up: {flow_id}, removed {cleaned_versions} old versions"
            )
            return {
                "flow_id": flow_id,
                "archived": archive,
                "checkpoint_id": checkpoint_id,
                "versions_cleaned": cleaned_versions,
                "cleaned_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to cleanup flow state for {flow_id}: {e}")
            raise
