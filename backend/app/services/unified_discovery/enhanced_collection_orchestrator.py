"""
Enhanced Collection Orchestrator

This module implements a workflow progression system for the collection flow
to prevent bootstrap questionnaire regeneration and manage workflow state transitions.

Features:
- Workflow state machine with defined phases
- Prevents duplicate bootstrap questionnaire generation
- Tracks questionnaire submissions and completions
- Integrates with canonical application system
- Multi-tenant safe operations
- Production-ready error handling
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.core.context import RequestContext
from app.models.collection_flow import (
    CollectionFlowError,
    CollectionFlowState,
)
from app.services.application_deduplication_service import (
    ApplicationDeduplicationService,
)

from .workflow_models import QuestionnaireType, WorkflowPhase, WorkflowProgress
from .workflow_phase_manager import WorkflowPhaseManager
from .workflow_state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class EnhancedCollectionOrchestrator:
    """
    Enhanced orchestrator for collection workflows with state machine management.

    Prevents bootstrap questionnaire regeneration and manages workflow progression
    through defined phases with proper state validation and persistence.
    """

    def __init__(
        self,
        db_session: Session,
        context: RequestContext,
        deduplication_service: Optional[ApplicationDeduplicationService] = None,
    ):
        """Initialize enhanced collection orchestrator"""
        self.db_session = db_session
        self.context = context
        self.deduplication_service = (
            deduplication_service or ApplicationDeduplicationService(db_session)
        )

        # Initialize managers
        self.state_manager = WorkflowStateManager(context)
        self.phase_manager = WorkflowPhaseManager()

        # Workflow configuration
        self.phase_timeouts = {
            WorkflowPhase.INITIAL: timedelta(hours=1),
            WorkflowPhase.COLLECTING_BASIC: timedelta(days=3),
            WorkflowPhase.COLLECTING_DETAILED: timedelta(days=7),
            WorkflowPhase.REVIEWING: timedelta(days=2),
        }

    async def check_bootstrap_questionnaire_exists(
        self, state: CollectionFlowState
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if bootstrap questionnaire already exists and has submissions.

        Returns:
            Tuple of (exists, questionnaire_data)
        """
        return await self.state_manager.check_bootstrap_questionnaire_exists(state)

    async def should_generate_questionnaire(
        self, state: CollectionFlowState, questionnaire_type: QuestionnaireType
    ) -> bool:
        """
        Determine if a new questionnaire should be generated based on workflow state.

        Args:
            state: Current collection flow state
            questionnaire_type: Type of questionnaire to check

        Returns:
            True if questionnaire should be generated, False otherwise
        """
        return await self.state_manager.should_generate_questionnaire(
            state, questionnaire_type
        )

    async def advance_workflow(
        self,
        state: CollectionFlowState,
        target_phase: Optional[WorkflowPhase] = None,
        force: bool = False,
    ) -> WorkflowPhase:
        """
        Advance workflow to the next phase or specified target phase.

        Args:
            state: Current collection flow state
            target_phase: Optional specific phase to advance to
            force: Force advancement ignoring validation checks

        Returns:
            New workflow phase after advancement
        """
        try:
            self.state_manager.validate_context()
            progress = self.state_manager.get_workflow_progress(state)
            current_phase = progress.workflow_phase

            logger.info(
                f"Advancing workflow from {current_phase} for flow {state.flow_id}"
            )

            # Determine next phase
            if target_phase:
                next_phase = target_phase
            else:
                next_phase = self.phase_manager.get_next_phase(
                    current_phase, progress, force
                )

            # Validate phase transition
            if not force and not self.phase_manager.can_advance_to_phase(
                progress, next_phase
            ):
                logger.warning(
                    f"Cannot advance to phase {next_phase} from {current_phase} "
                    f"for flow {state.flow_id}"
                )
                return current_phase

            # Perform phase transition
            await self.phase_manager.transition_to_phase(state, progress, next_phase)

            # Update collection flow state
            self.phase_manager.update_collection_state_for_phase(state, next_phase)
            self.state_manager.save_workflow_progress(state, progress)

            logger.info(
                f"Successfully advanced workflow to {next_phase} for flow {state.flow_id}"
            )

            return next_phase

        except Exception as e:
            logger.error(f"Error advancing workflow: {e}")
            raise CollectionFlowError(f"Failed to advance workflow: {e}")

    async def record_questionnaire_submission(
        self,
        state: CollectionFlowState,
        questionnaire_type: QuestionnaireType,
        submission_data: Dict[str, Any],
    ) -> None:
        """Record questionnaire submission and update workflow progress"""
        await self.state_manager.record_questionnaire_submission(
            state, questionnaire_type, submission_data
        )

        # Check for auto-advancement
        progress = self.state_manager.get_workflow_progress(state)
        next_phase = await self.phase_manager.check_auto_advancement(state, progress)

        if next_phase:
            await self.advance_workflow(state, next_phase)

    async def integrate_canonical_applications(
        self, state: CollectionFlowState, applications_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Integrate with canonical application system for deduplication.

        Args:
            state: Current collection flow state
            applications_data: Application data to process

        Returns:
            Integration results with deduplication metrics
        """
        try:
            self.state_manager.validate_context()

            logger.info(
                f"Integrating {len(applications_data)} applications with canonical system "
                f"for flow {state.flow_id}"
            )

            # Process applications through deduplication service
            dedup_results = await self.deduplication_service.process_applications(
                applications_data, engagement_id=self.context.engagement_id
            )

            # Update state with canonical integration results
            canonical_results = {
                "processed_at": datetime.utcnow().isoformat(),
                "total_applications": len(applications_data),
                "canonical_matches": dedup_results.get("matches", 0),
                "new_applications": dedup_results.get("new_applications", 0),
                "duplicate_applications": dedup_results.get("duplicates", 0),
                "integration_quality_score": dedup_results.get("quality_score", 0.0),
            }

            # Update state phase results
            if "canonical_integration" not in state.phase_results:
                state.phase_results["canonical_integration"] = {}
            state.phase_results["canonical_integration"].update(canonical_results)

            # Update apps ready for assessment
            state.apps_ready_for_assessment = dedup_results.get("assessment_ready", [])

            return canonical_results

        except Exception as e:
            logger.error(f"Error integrating canonical applications: {e}")
            raise CollectionFlowError(
                f"Failed to integrate canonical applications: {e}"
            )

    async def get_workflow_status(self, state: CollectionFlowState) -> Dict[str, Any]:
        """Get comprehensive workflow status information"""
        return await self.state_manager.get_workflow_status(state)
