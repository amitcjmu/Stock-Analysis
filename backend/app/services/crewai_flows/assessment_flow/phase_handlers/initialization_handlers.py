"""
Initialization phase handlers for Assessment Flow.

Contains the initialization phase logic that loads selected applications
and architecture standards.
"""

import logging
from typing import Any, Dict

from app.models.assessment_flow import (
    AssessmentFlowStatus,
    AssessmentPhase,
)

logger = logging.getLogger(__name__)


class InitializationHandlers:
    """Mixin class for initialization phase handling."""

    async def handle_initialization(self) -> Dict[str, Any]:
        """
        Phase 1: Initialize the assessment flow.
        Load selected applications and prepare for assessment.
        """
        logger.info(
            f"🚀 Starting assessment initialization for flow {self.flow.flow_id}"
        )

        try:
            # Update phase and progress
            self.flow.state.transition_to_phase(AssessmentPhase.INITIALIZATION)
            self.flow.state.update_phase_progress(
                AssessmentPhase.INITIALIZATION.value, 10.0
            )

            # Load selected applications
            selected_apps = await self.flow.data_helper.load_selected_applications()
            self.flow.state.application_components = selected_apps

            # Load engagement architecture standards
            standards = await self.flow.data_helper.load_engagement_standards()
            if not standards:
                # Initialize default standards if none exist
                standards = await self.flow.data_helper.initialize_default_standards()

            self.flow.state.architecture_standards = standards

            # Update progress
            self.flow.state.update_phase_progress(
                AssessmentPhase.INITIALIZATION.value, 100.0
            )

            # Save state
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )

            logger.info(
                f"✅ Assessment initialization completed for {len(selected_apps)} applications"
            )

            return {
                "phase": AssessmentPhase.INITIALIZATION.value,
                "applications_loaded": len(selected_apps),
                "standards_loaded": len(standards),
                "next_phase": AssessmentPhase.ARCHITECTURE_MINIMUMS.value,
                "requires_user_input": True,
                "user_input_prompt": "Please review and confirm the architecture standards for this engagement.",
            }

        except Exception as e:
            logger.error(f"❌ Assessment initialization failed: {str(e)}")
            self.flow.state.last_error = str(e)
            self.flow.state.status = AssessmentFlowStatus.ERROR
            await self.flow.flow_state_manager.save_state(
                self.flow.flow_id, self.flow.state.to_dict()
            )
            raise
