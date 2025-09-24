"""
State Operations for Flow Lifecycle - Handles state preservation and restoration.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .base_operations import BaseFlowOperations

logger = logging.getLogger(__name__)


class StateOperations(BaseFlowOperations):
    """Handles flow state preservation and restoration operations."""

    async def preserve_flow_state(self, master_flow) -> None:
        """Preserve current flow state before pausing"""
        if "pause_state" not in master_flow.flow_persistence_data:
            master_flow.flow_persistence_data["pause_state"] = {}

        master_flow.flow_persistence_data["pause_state"] = {
            "preserved_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": master_flow.current_phase,
            "progress_percentage": master_flow.progress_percentage,
            "flow_status": master_flow.flow_status,
        }

    async def restore_and_resume_flow(
        self, master_flow, resume_context
    ) -> Dict[str, Any]:
        """Restore flow state and initiate resume using registered crew_class"""
        try:
            # Restore preserved state if available
            pause_state = master_flow.flow_persistence_data.get("pause_state")
            if pause_state:
                logger.info(f"Restoring flow state from pause: {master_flow.flow_id}")

            # Get the flow configuration from registry (MFO design pattern)
            flow_config = self.flow_registry.get_flow_config(master_flow.flow_type)

            # Create flow instance using crew_class if available (per MFO design)
            if flow_config.crew_class:
                flow_instance = await self._create_flow_instance(
                    master_flow, flow_config
                )
                return await self._execute_resume_logic(
                    master_flow, flow_instance, resume_context
                )
            else:
                # No crew_class registered - this is the actual problem we need to fix
                logger.warning(
                    f"No crew_class registered for flow type '{master_flow.flow_type}'"
                )
                return {
                    "status": "resumed",
                    "message": f"Flow type '{master_flow.flow_type}' resumed (no crew_class registered)",
                    "current_phase": master_flow.get_current_phase()
                    or "initialization",
                }

        except Exception as e:
            logger.error(
                f"Failed to restore and resume flow {master_flow.flow_id}: {e}"
            )
            raise

    async def _create_flow_instance(self, master_flow, flow_config):
        """Create flow instance using crew_class."""
        # Import and create CrewAI service for flow restoration
        from app.services.crewai_flow_service import CrewAIFlowService

        crewai_service = CrewAIFlowService()

        # UnifiedDiscoveryFlow requires crewai_service as first parameter
        # UnifiedCollectionFlow also requires db_session parameter
        return flow_config.crew_class(
            crewai_service,  # Required first parameter
            context=self.context,
            flow_id=master_flow.flow_id,
            initial_state=master_flow.flow_persistence_data,
            configuration=master_flow.flow_configuration,
            db_session=self.db,  # Required for UnifiedCollectionFlow
        )

    async def _execute_resume_logic(
        self, master_flow, flow_instance, resume_context
    ) -> Dict[str, Any]:
        """Execute the appropriate resume logic based on context."""
        # Check if we should force re-run instead of resume
        force_rerun = resume_context and resume_context.get("force_rerun", False)
        rerun_phase = resume_context and resume_context.get("rerun_phase")

        if force_rerun and rerun_phase:
            return await self._force_rerun_phase(
                master_flow, flow_instance, rerun_phase
            )
        elif hasattr(flow_instance, "resume_from_state"):
            return await flow_instance.resume_from_state(resume_context or {})
        elif hasattr(flow_instance, "resume_flow"):
            return await flow_instance.resume_flow(resume_context or {})
        else:
            # Fallback: mark as resumed but let next execute_phase handle actual work
            logger.info(
                f"Flow instance has no resume method, marking as running for {master_flow.flow_id}"
            )
            return {
                "status": "resumed",
                "message": "Flow marked as running, ready for phase execution",
                "current_phase": master_flow.get_current_phase() or "initialization",
            }

    async def _force_rerun_phase(
        self, master_flow, flow_instance, rerun_phase
    ) -> Dict[str, Any]:
        """Force re-run a specific phase."""
        # Use PhaseController to force re-run a specific phase
        logger.info(
            f"🔄 Force re-running phase {rerun_phase} for flow {master_flow.flow_id}"
        )

        from app.services.crewai_flows.unified_discovery_flow.phase_controller import (
            PhaseController,
            FlowPhase,
        )

        phase_controller = PhaseController(flow_instance)

        # Map string phase name to FlowPhase enum
        phase_map = {
            "field_mapping": FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            "field_mapping_suggestions": FlowPhase.FIELD_MAPPING_SUGGESTIONS,
            "field_mapping_approval": FlowPhase.FIELD_MAPPING_APPROVAL,
            "data_cleansing": FlowPhase.DATA_CLEANSING,
            "asset_inventory": FlowPhase.ASSET_INVENTORY,
        }

        target_phase = phase_map.get(rerun_phase)
        if target_phase:
            result = await phase_controller.force_rerun_phase(
                phase=target_phase, use_existing_data=True
            )

            return {
                "status": "phase_rerun_completed",
                "message": f"Successfully re-ran phase {rerun_phase}",
                "phase": rerun_phase,
                "phase_result": result.data,
                "requires_user_input": result.requires_user_input,
            }
        else:
            return {
                "status": "error",
                "message": f"Unknown phase for re-run: {rerun_phase}",
            }
