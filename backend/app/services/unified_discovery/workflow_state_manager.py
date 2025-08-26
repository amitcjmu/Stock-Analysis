"""
Workflow State Manager for Enhanced Collection Orchestrator

This module handles state validation, persistence, and questionnaire
existence checking for the enhanced collection orchestrator.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.context import RequestContext
from app.models.collection_flow import (
    CollectionFlowError,
    CollectionFlowState,
)

from .workflow_models import QuestionnaireType, WorkflowProgress

logger = logging.getLogger(__name__)


class WorkflowStateManager:
    """Manages workflow state validation, persistence, and questionnaire tracking"""

    def __init__(self, context: RequestContext):
        """Initialize workflow state manager"""
        self.context = context

    def validate_context(self) -> None:
        """Validate request context for multi-tenant safety"""
        if not self.context.client_account_id:
            raise CollectionFlowError("Missing client_account_id in context")
        if not self.context.engagement_id:
            raise CollectionFlowError("Missing engagement_id in context")

    def get_workflow_progress(self, state: CollectionFlowState) -> WorkflowProgress:
        """Extract workflow progress from collection flow state"""
        workflow_data = state.phase_state.get("workflow_progress", {})
        return WorkflowProgress.from_dict(workflow_data)

    def save_workflow_progress(
        self, state: CollectionFlowState, progress: WorkflowProgress
    ) -> None:
        """Save workflow progress to collection flow state"""
        if not state.phase_state:
            state.phase_state = {}
        state.phase_state["workflow_progress"] = progress.to_dict()
        state.updated_at = datetime.utcnow()

    async def check_bootstrap_questionnaire_exists(
        self, state: CollectionFlowState
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if bootstrap questionnaire already exists and has submissions.

        Returns:
            Tuple of (exists, questionnaire_data)
        """
        try:
            self.validate_context()

            progress = self.get_workflow_progress(state)

            # Check for existing bootstrap submissions
            bootstrap_submissions = progress.questionnaire_submissions.get(
                QuestionnaireType.BOOTSTRAP.value, {}
            )

            if bootstrap_submissions and progress.bootstrap_completed:
                logger.info(
                    f"Bootstrap questionnaire already completed for flow {state.flow_id}"
                )
                return True, bootstrap_submissions

            # Check for existing questionnaires in state
            existing_questionnaires = state.questionnaires or []
            bootstrap_questionnaires = [
                q
                for q in existing_questionnaires
                if q.get("type") == QuestionnaireType.BOOTSTRAP.value
            ]

            if bootstrap_questionnaires:
                logger.info(
                    f"Found {len(bootstrap_questionnaires)} bootstrap questionnaires "
                    f"for flow {state.flow_id}"
                )
                return True, bootstrap_questionnaires[0]

            return False, None

        except Exception as e:
            logger.error(f"Error checking bootstrap questionnaire: {e}")
            raise CollectionFlowError(f"Failed to check bootstrap questionnaire: {e}")

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
        try:
            progress = self.get_workflow_progress(state)

            # Bootstrap questionnaire logic
            if questionnaire_type == QuestionnaireType.BOOTSTRAP:
                if progress.bootstrap_completed:
                    logger.info(
                        f"Bootstrap questionnaire already completed for flow {state.flow_id}"
                    )
                    return False

                exists, _ = await self.check_bootstrap_questionnaire_exists(state)
                if exists:
                    logger.info(
                        f"Bootstrap questionnaire already exists for flow {state.flow_id}"
                    )
                    return False

                return True

            # Detailed questionnaire logic
            elif questionnaire_type == QuestionnaireType.DETAILED:
                if not progress.bootstrap_completed:
                    logger.warning(
                        f"Cannot generate detailed questionnaire - bootstrap not completed "
                        f"for flow {state.flow_id}"
                    )
                    return False

                if progress.detailed_collection_started:
                    logger.info(
                        f"Detailed collection already started for flow {state.flow_id}"
                    )
                    return False

                return True

            # Followup questionnaire logic
            elif questionnaire_type == QuestionnaireType.FOLLOWUP:
                from .workflow_models import WorkflowPhase

                if progress.workflow_phase not in [
                    WorkflowPhase.COLLECTING_DETAILED,
                    WorkflowPhase.REVIEWING,
                ]:
                    logger.warning(
                        f"Cannot generate followup questionnaire - wrong phase "
                        f"{progress.workflow_phase} for flow {state.flow_id}"
                    )
                    return False

                return True

            return True

        except Exception as e:
            logger.error(f"Error checking questionnaire generation: {e}")
            return False

    async def record_questionnaire_submission(
        self,
        state: CollectionFlowState,
        questionnaire_type: QuestionnaireType,
        submission_data: Dict[str, Any],
    ) -> None:
        """Record questionnaire submission and update workflow progress"""
        try:
            progress = self.get_workflow_progress(state)

            # Record submission
            if questionnaire_type.value not in progress.questionnaire_submissions:
                progress.questionnaire_submissions[questionnaire_type.value] = {}

            progress.questionnaire_submissions[questionnaire_type.value].update(
                {
                    "submitted_at": datetime.utcnow().isoformat(),
                    "submission_id": str(uuid.uuid4()),
                    "data_fields_count": len(submission_data.get("responses", {})),
                    "completion_percentage": submission_data.get(
                        "completion_percentage", 0.0
                    ),
                }
            )

            # Update workflow state based on submission type
            if questionnaire_type == QuestionnaireType.BOOTSTRAP:
                if submission_data.get("completion_percentage", 0.0) >= 80.0:
                    progress.bootstrap_completed = True
                    logger.info(
                        f"Bootstrap questionnaire completed for flow {state.flow_id}"
                    )

            # Save progress
            self.save_workflow_progress(state, progress)

        except Exception as e:
            logger.error(f"Error recording questionnaire submission: {e}")
            raise CollectionFlowError(f"Failed to record submission: {e}")

    async def get_workflow_status(self, state: CollectionFlowState) -> Dict[str, Any]:
        """Get comprehensive workflow status information"""
        try:
            progress = self.get_workflow_progress(state)

            # Check for bootstrap questionnaire
            bootstrap_exists, bootstrap_data = (
                await self.check_bootstrap_questionnaire_exists(state)
            )

            return {
                "flow_id": state.flow_id,
                "workflow_phase": progress.workflow_phase.value,
                "collection_phase": (
                    state.current_phase.value if state.current_phase else None
                ),
                "collection_status": state.status.value if state.status else None,
                "progress_percentage": state.progress,
                "bootstrap_questionnaire": {
                    "exists": bootstrap_exists,
                    "completed": progress.bootstrap_completed,
                    "data": bootstrap_data,
                },
                "questionnaire_submissions": progress.questionnaire_submissions,
                "completed_phases": [
                    phase.value for phase in progress.completed_phases
                ],
                "detailed_collection_started": progress.detailed_collection_started,
                "review_phase_entered": progress.review_phase_entered,
                "assessment_ready": state.assessment_ready,
                "last_progression_time": (
                    progress.last_progression_time.isoformat()
                    if progress.last_progression_time
                    else None
                ),
                "canonical_integration": state.phase_results.get(
                    "canonical_integration", {}
                ),
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            raise CollectionFlowError(f"Failed to get workflow status: {e}")
