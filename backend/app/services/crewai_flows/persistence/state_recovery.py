"""
State recovery mechanisms for failed flows
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .postgres_store import PostgresFlowStateStore, StateRecoveryError

logger = logging.getLogger(__name__)


class FlowStateRecovery:
    """Handles recovery scenarios for flow states"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()

    async def recover_failed_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        Recover a failed flow to last known good state
        """
        try:
            logger.info(f"🔄 Starting recovery for failed flow: {flow_id}")

            # Get flow record
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                raise StateRecoveryError(f"No flow record found for {flow_id}")

            # Check if recovery is needed
            current_state = record.flow_state_data or {}
            status = current_state.get("status", "unknown")

            if status not in ["failed", "paused", "error"]:
                return {
                    "status": "no_recovery_needed",
                    "flow_id": flow_id,
                    "current_status": status,
                    "message": "Flow is not in a failed state",
                }

            # Find last good checkpoint
            checkpoint_data = await self._find_last_good_checkpoint(flow_id)

            if checkpoint_data:
                # Recover from checkpoint
                recovered_state = checkpoint_data["state_snapshot"]

                # Validate recovered state
                validation_result = self.validator.validate_complete_state(
                    recovered_state
                )

                if not validation_result.valid:
                    logger.warning(
                        f"⚠️ Checkpoint state validation failed: {validation_result.errors}"
                    )
                    # Try to repair the state
                    recovered_state = await self._repair_corrupted_state(
                        recovered_state
                    )

                # Update flow status to recovered
                recovered_state["status"] = "running"
                recovered_state["updated_at"] = datetime.utcnow().isoformat()
                recovered_state["recovery_info"] = {
                    "recovered_at": datetime.utcnow().isoformat(),
                    "recovery_method": "checkpoint",
                    "checkpoint_id": checkpoint_data["checkpoint_id"],
                    "previous_status": status,
                }

                # Save recovered state
                await self.store.save_state(
                    flow_id=flow_id,
                    state=recovered_state,
                    phase=recovered_state.get("current_phase", "unknown"),
                )

                logger.info(f"✅ Flow recovered from checkpoint: {flow_id}")
                return {
                    "status": "recovered_from_checkpoint",
                    "flow_id": flow_id,
                    "checkpoint_id": checkpoint_data["checkpoint_id"],
                    "recovery_phase": recovered_state.get("current_phase"),
                    "recovered_at": datetime.utcnow().isoformat(),
                }

            else:
                # No checkpoints available, attempt state repair
                logger.info(
                    f"🔧 No checkpoints available, attempting state repair for {flow_id}"
                )

                repaired_state = await self._repair_corrupted_state(current_state)

                if repaired_state:
                    # Save repaired state
                    await self.store.save_state(
                        flow_id=flow_id,
                        state=repaired_state,
                        phase=repaired_state.get("current_phase", "unknown"),
                    )

                    logger.info(f"✅ Flow repaired: {flow_id}")
                    return {
                        "status": "repaired",
                        "flow_id": flow_id,
                        "repair_phase": repaired_state.get("current_phase"),
                        "repaired_at": datetime.utcnow().isoformat(),
                    }
                else:
                    # Complete reset to initial state
                    logger.warning(f"⚠️ Complete reset required for {flow_id}")
                    return await self._reset_to_initial_state(flow_id, current_state)

        except Exception as e:
            logger.error(f"❌ Flow recovery failed for {flow_id}: {e}")
            raise StateRecoveryError(f"Recovery failed: {e}")

    async def handle_corrupted_state(self, flow_id: str) -> None:
        """
        Handle corrupted state scenarios
        """
        try:
            logger.warning(f"⚠️ Handling corrupted state for flow: {flow_id}")

            # Get current state
            current_state = await self.store.load_state(flow_id)

            if current_state:
                # Archive corrupted state for forensics
                await self._archive_corrupted_state(flow_id, current_state)

                # Attempt repair
                repaired_state = await self._repair_corrupted_state(current_state)

                if repaired_state:
                    await self.store.save_state(
                        flow_id=flow_id,
                        state=repaired_state,
                        phase=repaired_state.get("current_phase", "initialization"),
                    )
                    logger.info(f"✅ Corrupted state repaired for {flow_id}")
                else:
                    # Reset to initial state
                    await self._reset_to_initial_state(flow_id, current_state)
                    logger.warning(f"⚠️ Corrupted state reset for {flow_id}")

            # Notify administrators
            await self._notify_administrators(flow_id, "corrupted_state_handled")

        except Exception as e:
            logger.error(f"❌ Failed to handle corrupted state for {flow_id}: {e}")
            await self._notify_administrators(
                flow_id, f"corrupted_state_handling_failed: {e}"
            )

    async def _find_last_good_checkpoint(
        self, flow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find the most recent valid checkpoint"""
        try:
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                return None

            persistence_data = record.flow_persistence_data or {}
            checkpoints = persistence_data.get("checkpoints", [])

            # Sort checkpoints by creation time (newest first)
            checkpoints.sort(key=lambda x: x.get("created_at", ""), reverse=True)

            # Find first valid checkpoint
            for checkpoint in checkpoints:
                state_snapshot = checkpoint.get("state_snapshot", {})
                validation_result = self.validator.validate_complete_state(
                    state_snapshot
                )

                if validation_result.valid:
                    logger.info(
                        f"✅ Found valid checkpoint: {checkpoint.get('checkpoint_id')}"
                    )
                    return checkpoint

            logger.warning(f"⚠️ No valid checkpoints found for {flow_id}")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to find checkpoints for {flow_id}: {e}")
            return None

    async def _repair_corrupted_state(
        self, corrupted_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to repair a corrupted state"""
        try:
            repaired_state = corrupted_state.copy()

            # Fix missing required fields
            if not repaired_state.get("flow_id"):
                repaired_state["flow_id"] = corrupted_state.get("session_id", "unknown")

            if not repaired_state.get("current_phase"):
                repaired_state["current_phase"] = "initialization"

            if not repaired_state.get("status"):
                repaired_state["status"] = "running"

            # Fix invalid phase
            if repaired_state.get("current_phase") not in self.validator.VALID_PHASES:
                repaired_state["current_phase"] = "initialization"

            # Fix invalid status
            if repaired_state.get("status") not in self.validator.VALID_STATUSES:
                repaired_state["status"] = "running"

            # Fix progress percentage
            progress = repaired_state.get("progress_percentage", 0)
            if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
                repaired_state["progress_percentage"] = 0.0

            # Ensure phase_completion exists and is valid
            if not isinstance(repaired_state.get("phase_completion"), dict):
                repaired_state["phase_completion"] = {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_creation": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False,
                }

            # Fix timestamps
            now = datetime.utcnow().isoformat()
            if not repaired_state.get("created_at"):
                repaired_state["created_at"] = now
            if not repaired_state.get("updated_at"):
                repaired_state["updated_at"] = now

            # Ensure collections exist
            list_fields = [
                "errors",
                "warnings",
                "agent_insights",
                "user_clarifications",
                "workflow_log",
            ]
            for field in list_fields:
                if not isinstance(repaired_state.get(field), list):
                    repaired_state[field] = []

            # Ensure dictionaries exist
            dict_fields = ["agent_confidences", "crew_status", "metadata"]
            for field in dict_fields:
                if not isinstance(repaired_state.get(field), dict):
                    repaired_state[field] = {}

            # Add repair metadata
            repaired_state["repair_info"] = {
                "repaired_at": now,
                "repair_method": "automated_repair",
                "original_corruption_detected": True,
            }

            # Validate repaired state
            validation_result = self.validator.validate_complete_state(repaired_state)

            if validation_result.valid:
                logger.info("✅ State successfully repaired")
                return repaired_state
            else:
                logger.error(f"❌ State repair failed: {validation_result.errors}")
                return None

        except Exception as e:
            logger.error(f"❌ State repair failed: {e}")
            return None

    async def _reset_to_initial_state(
        self, flow_id: str, original_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reset flow to initial state"""
        try:
            # Create minimal valid initial state
            initial_state = {
                "flow_id": flow_id,
                "session_id": original_state.get("session_id", flow_id),
                "client_account_id": original_state.get("client_account_id", ""),
                "engagement_id": original_state.get("engagement_id", ""),
                "user_id": original_state.get("user_id", ""),
                "current_phase": "initialization",
                "status": "running",
                "progress_percentage": 0.0,
                "phase_completion": {
                    "data_import": False,
                    "field_mapping": False,
                    "data_cleansing": False,
                    "asset_creation": False,
                    "asset_inventory": False,
                    "dependency_analysis": False,
                    "tech_debt_analysis": False,
                },
                "crew_status": {},
                "raw_data": original_state.get("raw_data", []),
                "metadata": original_state.get("metadata", {}),
                "errors": [],
                "warnings": [],
                "agent_insights": [],
                "user_clarifications": [],
                "workflow_log": [],
                "agent_confidences": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "reset_info": {
                    "reset_at": datetime.utcnow().isoformat(),
                    "reset_reason": "state_corruption_recovery",
                    "original_state_archived": True,
                },
            }

            # Save initial state
            await self.store.save_state(
                flow_id=flow_id, state=initial_state, phase="initialization"
            )

            logger.info(f"✅ Flow reset to initial state: {flow_id}")
            return {
                "status": "reset_to_initial",
                "flow_id": flow_id,
                "reset_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ Failed to reset flow to initial state: {e}")
            raise StateRecoveryError(f"Reset failed: {e}")

    async def _archive_corrupted_state(
        self, flow_id: str, corrupted_state: Dict[str, Any]
    ):
        """Archive corrupted state for forensic analysis"""
        try:
            archive_data = {
                "flow_id": flow_id,
                "archived_at": datetime.utcnow().isoformat(),
                "corruption_type": "validation_failure",
                "corrupted_state": corrupted_state,
            }

            # Store in flow_persistence_data as archived_states
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if record:
                persistence_data = record.flow_persistence_data or {}
                archived_states = persistence_data.get("archived_states", [])
                archived_states.append(archive_data)

                # Keep only last 5 archived states
                if len(archived_states) > 5:
                    archived_states = archived_states[-5:]

                persistence_data["archived_states"] = archived_states

                update_stmt = (
                    update(CrewAIFlowStateExtensions)
                    .where(CrewAIFlowStateExtensions.id == record.id)
                    .values(
                        flow_persistence_data=persistence_data,
                        updated_at=datetime.utcnow(),
                    )
                )
                await self.db.execute(update_stmt)
                await self.db.commit()

                logger.info(f"✅ Corrupted state archived for {flow_id}")

        except Exception as e:
            logger.error(f"❌ Failed to archive corrupted state: {e}")

    async def _notify_administrators(self, flow_id: str, event: str):
        """Notify system administrators of state recovery events"""
        try:
            # Log the event
            logger.warning(f"🚨 ADMIN ALERT: {event} for flow {flow_id}")

            # In a real system, this would send alerts to monitoring systems
            # For now, we'll just ensure it's properly logged

        except Exception as e:
            logger.error(f"❌ Failed to notify administrators: {e}")

    async def get_recovery_status(self, flow_id: str) -> Dict[str, Any]:
        """Get recovery status and history for a flow"""
        try:
            stmt = select(CrewAIFlowStateExtensions).where(
                and_(
                    CrewAIFlowStateExtensions.flow_id == flow_id,
                    CrewAIFlowStateExtensions.client_account_id
                    == self.context.client_account_id,
                )
            )
            result = await self.db.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                return {"status": "not_found", "flow_id": flow_id}

            current_state = record.flow_state_data or {}
            persistence_data = record.flow_persistence_data or {}

            return {
                "status": "found",
                "flow_id": flow_id,
                "current_status": current_state.get("status"),
                "recovery_history": {
                    "checkpoints_available": len(
                        persistence_data.get("checkpoints", [])
                    ),
                    "archived_states": len(persistence_data.get("archived_states", [])),
                    "last_recovery": current_state.get("recovery_info"),
                    "last_repair": current_state.get("repair_info"),
                    "last_reset": current_state.get("reset_info"),
                },
                "validation_status": self.validator.validate_complete_state(
                    current_state
                ),
            }

        except Exception as e:
            logger.error(f"❌ Failed to get recovery status for {flow_id}: {e}")
            return {"status": "error", "error": str(e)}
