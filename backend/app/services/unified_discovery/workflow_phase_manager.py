"""
Workflow Phase Manager for Enhanced Collection Orchestrator

This module handles phase transitions, advancement logic, and phase-specific
initialization for the enhanced collection orchestrator.
"""

import logging
from datetime import datetime
from typing import Optional

from app.models.collection_flow import (
    CollectionFlowState,
    CollectionPhase,
    CollectionStatus,
)

from .workflow_models import QuestionnaireType, WorkflowPhase, WorkflowProgress

logger = logging.getLogger(__name__)


def _set_current_phase_state(
    state: CollectionFlowState, new_phase: CollectionPhase
) -> None:
    """
    Atomically set current phase in BOTH locations to prevent divergence.

    Bug #648 Fix: Ensures single source of truth by keeping state.current_phase
    attribute and state.phase_state["current_phase"] dict field synchronized.

    This is the CollectionFlowState (Pydantic/in-memory) version of the helper.

    Args:
        state: The CollectionFlowState instance to update
        new_phase: The new CollectionPhase enum value to set
    """
    state.current_phase = new_phase
    if state.phase_state is None:
        state.phase_state = {}
    state.phase_state["current_phase"] = new_phase.value


class WorkflowPhaseManager:
    """Manages workflow phase transitions and advancement logic"""

    def __init__(self):
        """Initialize workflow phase manager"""
        self.phase_progress_map = {
            WorkflowPhase.INITIAL: 10.0,
            WorkflowPhase.COLLECTING_BASIC: 30.0,
            WorkflowPhase.COLLECTING_DETAILED: 60.0,
            WorkflowPhase.REVIEWING: 85.0,
            WorkflowPhase.COMPLETE: 100.0,
        }

    def get_next_phase(
        self,
        current_phase: WorkflowPhase,
        progress: WorkflowProgress,
        force: bool = False,
    ) -> WorkflowPhase:
        """Determine the next workflow phase based on current state"""
        phase_transitions = {
            WorkflowPhase.INITIAL: WorkflowPhase.COLLECTING_BASIC,
            WorkflowPhase.COLLECTING_BASIC: WorkflowPhase.COLLECTING_DETAILED,
            WorkflowPhase.COLLECTING_DETAILED: WorkflowPhase.REVIEWING,
            WorkflowPhase.REVIEWING: WorkflowPhase.COMPLETE,
        }

        if current_phase == WorkflowPhase.COMPLETE:
            return WorkflowPhase.COMPLETE

        return phase_transitions.get(current_phase, WorkflowPhase.INITIAL)

    def can_advance_to_phase(
        self, progress: WorkflowProgress, target_phase: WorkflowPhase
    ) -> bool:
        """Check if workflow can advance to target phase"""
        current_phase = progress.workflow_phase

        # Can always stay in same phase or go backward
        if target_phase <= current_phase:
            return True

        # Phase-specific advancement rules
        if target_phase == WorkflowPhase.COLLECTING_BASIC:
            return current_phase == WorkflowPhase.INITIAL

        elif target_phase == WorkflowPhase.COLLECTING_DETAILED:
            return (
                current_phase == WorkflowPhase.COLLECTING_BASIC
                and progress.bootstrap_completed
            )

        elif target_phase == WorkflowPhase.REVIEWING:
            return (
                current_phase == WorkflowPhase.COLLECTING_DETAILED
                and progress.detailed_collection_started
            )

        elif target_phase == WorkflowPhase.COMPLETE:
            return (
                current_phase == WorkflowPhase.REVIEWING
                and progress.review_phase_entered
            )

        return False

    async def transition_to_phase(
        self,
        state: CollectionFlowState,
        progress: WorkflowProgress,
        target_phase: WorkflowPhase,
    ) -> None:
        """Perform workflow transition to target phase"""
        previous_phase = progress.workflow_phase
        progress.workflow_phase = target_phase
        progress.completed_phases.add(previous_phase)
        progress.last_progression_time = datetime.utcnow()

        # Phase-specific transition actions
        if target_phase == WorkflowPhase.COLLECTING_BASIC:
            await self._initialize_basic_collection(state, progress)

        elif target_phase == WorkflowPhase.COLLECTING_DETAILED:
            progress.detailed_collection_started = True
            await self._initialize_detailed_collection(state, progress)

        elif target_phase == WorkflowPhase.REVIEWING:
            progress.review_phase_entered = True
            await self._initialize_review_phase(state, progress)

        elif target_phase == WorkflowPhase.COMPLETE:
            await self._finalize_workflow(state, progress)

    async def _initialize_basic_collection(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> None:
        """Initialize basic collection phase"""
        logger.info(f"Initializing basic collection for flow {state.flow_id}")

        # Set collection status and phase
        state.status = CollectionStatus.COLLECTING_DATA
        # Bug #648 Fix: Use atomic phase setter to prevent divergence
        _set_current_phase_state(state, CollectionPhase.ASSET_SELECTION)

        # Initialize phase results if not exists
        if "basic_collection" not in state.phase_results:
            state.phase_results["basic_collection"] = {
                "started_at": datetime.utcnow().isoformat(),
                "questionnaire_type": QuestionnaireType.BOOTSTRAP.value,
                "collection_method": "automated_with_bootstrap",
            }

    async def _initialize_detailed_collection(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> None:
        """Initialize detailed collection phase"""
        logger.info(f"Initializing detailed collection for flow {state.flow_id}")

        # Update collection status
        state.status = CollectionStatus.GENERATING_QUESTIONNAIRES
        # Bug #648 Fix: Use atomic phase setter to prevent divergence
        _set_current_phase_state(state, CollectionPhase.QUESTIONNAIRE_GENERATION)

        # Initialize detailed collection results
        if "detailed_collection" not in state.phase_results:
            state.phase_results["detailed_collection"] = {
                "started_at": datetime.utcnow().isoformat(),
                "questionnaire_type": QuestionnaireType.DETAILED.value,
                "collection_method": "manual_with_detailed_questionnaires",
            }

    async def _initialize_review_phase(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> None:
        """Initialize review phase"""
        logger.info(f"Initializing review phase for flow {state.flow_id}")

        # Update status for review
        state.status = CollectionStatus.VALIDATING_DATA
        # Bug #648 Fix: Use atomic phase setter to prevent divergence
        _set_current_phase_state(state, CollectionPhase.DATA_VALIDATION)

        # Initialize review results
        if "review_phase" not in state.phase_results:
            state.phase_results["review_phase"] = {
                "started_at": datetime.utcnow().isoformat(),
                "review_type": "comprehensive_data_validation",
                "canonical_apps_integration": True,
            }

    async def _finalize_workflow(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> None:
        """Finalize workflow completion"""
        logger.info(f"Finalizing workflow for flow {state.flow_id}")

        # Update final status
        state.status = CollectionStatus.COMPLETED
        # Bug #648 Fix: Use atomic phase setter to prevent divergence
        _set_current_phase_state(state, CollectionPhase.FINALIZATION)
        state.completed_at = datetime.utcnow()
        state.assessment_ready = True

        # Finalize results
        if "workflow_completion" not in state.phase_results:
            state.phase_results["workflow_completion"] = {
                "completed_at": datetime.utcnow().isoformat(),
                "final_phase": WorkflowPhase.COMPLETE.value,
                "total_questionnaires": len(state.questionnaires or []),
                "canonical_apps_processed": True,
            }

    def update_collection_state_for_phase(
        self, state: CollectionFlowState, phase: WorkflowPhase
    ) -> None:
        """Update collection flow state based on workflow phase"""
        state.progress = self.phase_progress_map.get(phase, state.progress)
        state.updated_at = datetime.utcnow()

    async def check_auto_advancement(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> Optional[WorkflowPhase]:
        """
        Check and return next phase for automatic workflow advancement.

        Returns:
            Next phase if auto-advancement should occur, None otherwise
        """
        current_phase = progress.workflow_phase

        # Auto-advance from COLLECTING_BASIC if bootstrap completed
        if (
            current_phase == WorkflowPhase.COLLECTING_BASIC
            and progress.bootstrap_completed
        ):
            return WorkflowPhase.COLLECTING_DETAILED

        # Other auto-advancement rules can be added here
        return None
