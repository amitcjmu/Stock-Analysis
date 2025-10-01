"""
Flow State Manager - Transition Operations
Handles all state transition logic for flow phases
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.context import RequestContext
from app.core.flow_state_validator import FlowStateValidator

from ..persistence.postgres_store import PostgresFlowStateStore
from ..persistence.secure_checkpoint_manager import SecureCheckpointManager

logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when an invalid phase transition is attempted"""

    pass


class FlowStateTransitions:
    """Handles all state transition operations for flow phases"""

    def __init__(self, db: AsyncSession, context: RequestContext):
        self.db = db
        self.context = context
        self.store = PostgresFlowStateStore(db, context)
        self.validator = FlowStateValidator()
        self.secure_checkpoint_manager = SecureCheckpointManager(context)

    async def transition_phase(
        self,
        flow_id: str,
        new_phase: str,
        phase_data: Optional[Dict[str, Any]] = None,
        force_transition: bool = False,
    ) -> Dict[str, Any]:
        """Handle phase transitions with validation"""
        try:
            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found: {flow_id}")

            current_phase = current_state.get("current_phase", "unknown")

            # Add debug logging for phase transitions
            logger.info(f"🔄 Phase transition requested: {flow_id}")
            logger.info(f"  - current_phase: {current_phase}")
            logger.info(f"  - new_phase: {new_phase}")
            logger.info(f"  - force_transition: {force_transition}")

            # Validate phase transition unless forced (for resumption scenarios)
            if not force_transition and not self.validator.validate_phase_transition(
                current_state, new_phase
            ):
                logger.warning(
                    f"❌ Phase transition validation failed: {current_phase} -> {new_phase}"
                )
                raise InvalidTransitionError(
                    f"Invalid transition from {current_phase} to {new_phase}"
                )

            if force_transition:
                logger.info(
                    f"⚡ Forced phase transition allowed: {current_phase} -> {new_phase}"
                )

            # Create secure checkpoint before transition
            checkpoint_id = await self.secure_checkpoint_manager.create_checkpoint(
                flow_id=flow_id,
                phase=current_phase,
                state=current_state,
                metadata={"transition_from": current_phase, "transition_to": new_phase},
                context=self.context,
            )

            # Update state for new phase
            current_state["current_phase"] = new_phase
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # Add phase-specific data if provided
            if phase_data:
                phase_data_key = f"{new_phase}_data"
                current_state[phase_data_key] = phase_data

            # Update progress based on phase
            progress_mapping = {
                "initialization": 0.0,
                "data_import": 10.0,
                "field_mapping": 25.0,
                "data_cleansing": 40.0,
                "asset_creation": 55.0,
                "asset_inventory": 70.0,
                "dependency_analysis": 85.0,
                "tech_debt_analysis": 95.0,
                "completed": 100.0,
            }
            current_state["progress_percentage"] = progress_mapping.get(
                new_phase, current_state.get("progress_percentage", 0.0)
            )

            # Save updated state
            await self.store.save_state(
                flow_id=flow_id, state=current_state, phase=new_phase
            )

            logger.info(f"✅ Phase transition completed: {flow_id} -> {new_phase}")
            return {
                "flow_id": flow_id,
                "previous_phase": current_state.get("current_phase"),
                "new_phase": new_phase,
                "checkpoint_id": checkpoint_id,
                "progress_percentage": current_state["progress_percentage"],
                "transitioned_at": current_state["updated_at"],
            }

        except Exception as e:
            logger.error(f"❌ Phase transition failed for {flow_id}: {e}")
            raise

    async def resume_flow_state(
        self, flow_id: str, target_phase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resume flow state during flow resumption - uses force transition to handle edge cases
        """
        try:
            logger.info(f"🔄 Resuming flow state: {flow_id}")

            # Get current state
            current_state = await self.store.load_state(flow_id)
            if not current_state:
                raise ValueError(f"Flow state not found for resume: {flow_id}")

            current_phase = current_state.get("current_phase", "initialization")

            # If no target phase specified, stay in current phase
            if not target_phase:
                target_phase = current_phase

            # Update flow status to running
            current_state["status"] = "running"
            current_state["updated_at"] = datetime.utcnow().isoformat()

            # If we need to transition phases during resume, use force transition
            if target_phase != current_phase:
                logger.info(
                    f"🔄 Resume requires phase transition: {current_phase} -> {target_phase}"
                )
                return await self.transition_phase(
                    flow_id=flow_id,
                    new_phase=target_phase,
                    phase_data={
                        "resumed_from": current_phase,
                        "resume_reason": "flow_resumption",
                    },
                    force_transition=True,  # Allow transition during resume
                )
            else:
                # Save current state with updated status
                await self.store.save_state(
                    flow_id=flow_id, state=current_state, phase=current_phase
                )

                logger.info(f"✅ Flow state resumed in current phase: {current_phase}")
                return {
                    "flow_id": flow_id,
                    "current_phase": current_phase,
                    "status": "running",
                    "resumed_at": current_state["updated_at"],
                }

        except Exception as e:
            logger.error(f"❌ Failed to resume flow state for {flow_id}: {e}")
            raise
