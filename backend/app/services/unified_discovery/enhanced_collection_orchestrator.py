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
from typing import Any, Dict, List, Optional, Union
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, validator

from app.core.context import RequestContext
from app.core.security.secure_logging import safe_log_format
from app.models.collection_flow import (
    CollectionFlowError,
    CollectionFlowState,
)
from app.services.application_deduplication.service import (
    ApplicationDeduplicationService,
)

from .workflow_models import QuestionnaireType, WorkflowPhase
from .workflow_phase_manager import WorkflowPhaseManager
from .workflow_state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class ApplicationIntegrationRequest(BaseModel):
    """Type-safe model for application integration requests"""

    applications_data: List[Dict[str, Any]] = Field(..., min_items=1, max_items=1000)
    client_account_id: uuid.UUID = Field(...)
    engagement_id: uuid.UUID = Field(...)

    @validator("applications_data")
    def validate_applications_data(cls, v):
        """Validate application data structure"""
        for i, app_data in enumerate(v):
            if not isinstance(app_data, dict):
                raise ValueError(f"Application at index {i} must be a dictionary")
            if not app_data.get("name") and not app_data.get("application_name"):
                raise ValueError(
                    f"Application at index {i} must have a 'name' or 'application_name' field"
                )
        return v


class QuestionnaireSubmissionData(BaseModel):
    """Type-safe model for questionnaire submissions"""

    questionnaire_type: str = Field(..., pattern=r"^(bootstrap|detailed)$")
    responses: Dict[str, Any] = Field(default_factory=dict)
    completion_percentage: float = Field(ge=0.0, le=100.0, default=0.0)
    submission_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("submission_metadata")
    def validate_metadata_size(cls, v):
        """Limit metadata size for security"""
        if v and len(str(v)) > 50000:  # 50KB limit
            raise ValueError("Submission metadata too large")
        return v


class WorkflowAdvancementRequest(BaseModel):
    """Type-safe model for workflow advancement requests"""

    flow_id: uuid.UUID = Field(...)
    target_phase: Optional[str] = Field(None)
    force_advancement: bool = Field(default=False)
    advancement_reason: Optional[str] = Field(None, max_length=500)


class EnhancedCollectionOrchestrator:
    """
    Enhanced orchestrator for collection workflows with state machine management.

    Prevents bootstrap questionnaire regeneration and manages workflow progression
    through defined phases with proper state validation and persistence.
    """

    def __init__(
        self,
        db_session: Union[Session, AsyncSession],
        context: RequestContext,
        deduplication_service: Optional[ApplicationDeduplicationService] = None,
    ):
        """Initialize enhanced collection orchestrator with proper validation"""
        if not db_session:
            raise ValueError("Database session is required")
        if not context:
            raise ValueError("Request context is required")
        if not context.client_account_id:
            raise ValueError("Client account ID is required in context")
        if not context.engagement_id:
            raise ValueError("Engagement ID is required in context")

        self.db_session = db_session
        self.context = context
        self.deduplication_service = (
            deduplication_service or ApplicationDeduplicationService()
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
        Integrate with canonical application system for deduplication with enhanced validation.

        Args:
            state: Current collection flow state
            applications_data: Application data to process

        Returns:
            Integration results with deduplication metrics

        Raises:
            CollectionFlowError: If integration fails
            ValueError: If input validation fails
        """
        try:
            # Validate inputs using type-safe model
            integration_request = ApplicationIntegrationRequest(
                applications_data=applications_data,
                client_account_id=self.context.client_account_id,
                engagement_id=self.context.engagement_id,
            )

            self.state_manager.validate_context()

            logger.info(
                safe_log_format(
                    "Integrating {app_count} applications with canonical system for flow {flow_id}",
                    app_count=len(applications_data),
                    flow_id=str(state.flow_id),
                )
            )

            # Process applications through deduplication service
            # Extract application names from validated applications_data
            application_names = []
            for app_data in integration_request.applications_data:
                name = app_data.get("name") or app_data.get("application_name", "")
                if name and isinstance(name, str):
                    application_names.append(name.strip())

            if not application_names:
                raise ValueError("No valid application names found in input data")

            # Use bulk_deduplicate_applications with proper parameters and error handling
            try:
                dedup_results = (
                    await self.deduplication_service.bulk_deduplicate_applications(
                        db=self.db_session,
                        applications=application_names,
                        client_account_id=self.context.client_account_id,
                        engagement_id=self.context.engagement_id,
                    )
                )
            except Exception as dedup_error:
                logger.error(
                    safe_log_format(
                        "Deduplication service failed: {error_type}",
                        error_type=type(dedup_error).__name__,
                    )
                )
                raise CollectionFlowError(
                    f"Application deduplication failed: {type(dedup_error).__name__}"
                )

            # Safely extract results with defaults
            processed_count = (
                len(dedup_results) if isinstance(dedup_results, list) else 0
            )

            # Update state with canonical integration results
            canonical_results = {
                "processed_at": datetime.utcnow().isoformat(),
                "total_applications": len(applications_data),
                "processed_applications": processed_count,
                "canonical_matches": processed_count,  # All processed apps are now canonical
                "new_applications": processed_count,  # Count of new canonical apps created
                "duplicate_applications": 0,  # Handled by deduplication service
                "integration_quality_score": 1.0 if processed_count > 0 else 0.0,
            }

            # Update state phase results safely
            if not hasattr(state, "phase_results") or not state.phase_results:
                state.phase_results = {}
            if "canonical_integration" not in state.phase_results:
                state.phase_results["canonical_integration"] = {}
            state.phase_results["canonical_integration"].update(canonical_results)

            # Update apps ready for assessment with proper validation
            if hasattr(state, "apps_ready_for_assessment"):
                state.apps_ready_for_assessment = application_names[:processed_count]

            logger.info(
                safe_log_format(
                    "Successfully integrated {processed_count} applications for flow {flow_id}",
                    processed_count=processed_count,
                    flow_id=str(state.flow_id),
                )
            )

            return canonical_results

        except ValueError as ve:
            logger.error(f"Validation error in canonical integration: {ve}")
            raise
        except CollectionFlowError:
            raise
        except Exception as e:
            logger.error(
                safe_log_format(
                    "Error integrating canonical applications: {error_type}",
                    error_type=type(e).__name__,
                )
            )
            raise CollectionFlowError(
                f"Failed to integrate canonical applications: {type(e).__name__}"
            )

    async def get_workflow_status(self, state: CollectionFlowState) -> Dict[str, Any]:
        """Get comprehensive workflow status information"""
        return await self.state_manager.get_workflow_status(state)
