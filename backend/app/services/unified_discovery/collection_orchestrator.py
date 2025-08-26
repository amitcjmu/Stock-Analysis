"""
Collection Orchestrator

Updated orchestrator for collection workflows with enhanced workflow progression
and questionnaire management. Integrates with the enhanced collection orchestrator
to prevent duplicate questionnaires and manage state transitions.

This module provides the core orchestration logic for collection flows
with bootstrap questionnaire detection and completion tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.context import RequestContext
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlowError,
    CollectionFlowState,
    CollectionPhase,
)
from app.services.unified_discovery.enhanced_collection_orchestrator import (
    EnhancedCollectionOrchestrator,
)
from app.services.unified_discovery.workflow_models import (
    QuestionnaireType,
)

logger = logging.getLogger(__name__)


class CollectionOrchestrator:
    """
    Main collection orchestrator with enhanced workflow management.

    Provides backward compatibility while integrating with the enhanced
    orchestrator for workflow progression and questionnaire management.
    """

    def __init__(
        self,
        db_session: Session,
        context: RequestContext,
        enhanced_orchestrator: Optional[EnhancedCollectionOrchestrator] = None,
    ):
        """Initialize collection orchestrator"""
        self.db_session = db_session
        self.context = context
        self.enhanced_orchestrator = (
            enhanced_orchestrator or EnhancedCollectionOrchestrator(db_session, context)
        )

    async def check_bootstrap_questionnaire_exists(
        self, state: CollectionFlowState
    ) -> bool:
        """
        Check if bootstrap questionnaire already exists for this flow.

        This method prevents regeneration of the same bootstrap questionnaire
        by checking both the flow state and completed submissions.

        Args:
            state: Current collection flow state

        Returns:
            True if bootstrap questionnaire exists, False otherwise
        """
        try:
            exists, _ = (
                await self.enhanced_orchestrator.check_bootstrap_questionnaire_exists(
                    state
                )
            )

            if exists:
                logger.info(
                    f"Bootstrap questionnaire already exists for flow {state.flow_id} - "
                    f"skipping regeneration"
                )
                return True

            # Additional check for questionnaires in current phase results
            questionnaire_results = state.phase_results.get(
                "questionnaire_generation", {}
            )
            if questionnaire_results.get("questionnaires"):
                existing_questionnaires = questionnaire_results["questionnaires"]

                # Check if any existing questionnaire is a bootstrap type
                for questionnaire in existing_questionnaires:
                    if (
                        questionnaire.get("type") == "bootstrap"
                        or questionnaire.get("questionnaire_type") == "bootstrap"
                        or "bootstrap" in questionnaire.get("name", "").lower()
                    ):

                        logger.info(
                            f"Found existing bootstrap questionnaire in phase results "
                            f"for flow {state.flow_id}"
                        )
                        return True

            return False

        except Exception as e:
            logger.error(f"Error checking bootstrap questionnaire: {e}")
            # On error, assume it doesn't exist to allow generation
            return False

    async def should_generate_questionnaire(
        self,
        state: CollectionFlowState,
        gap_results: Optional[Dict[str, Any]] = None,
        questionnaire_type: str = "bootstrap",
    ) -> Tuple[bool, str]:
        """
        Determine if a questionnaire should be generated based on current state.

        Args:
            state: Current collection flow state
            gap_results: Optional gap analysis results
            questionnaire_type: Type of questionnaire to check

        Returns:
            Tuple of (should_generate, reason)
        """
        try:
            # Map string type to enum
            q_type = QuestionnaireType.BOOTSTRAP
            if questionnaire_type.lower() == "detailed":
                q_type = QuestionnaireType.DETAILED
            elif questionnaire_type.lower() == "followup":
                q_type = QuestionnaireType.FOLLOWUP
            elif questionnaire_type.lower() == "validation":
                q_type = QuestionnaireType.VALIDATION

            # Check with enhanced orchestrator
            should_generate = (
                await self.enhanced_orchestrator.should_generate_questionnaire(
                    state, q_type
                )
            )

            if not should_generate:
                if q_type == QuestionnaireType.BOOTSTRAP:
                    return False, "Bootstrap questionnaire already completed or exists"
                elif q_type == QuestionnaireType.DETAILED:
                    return (
                        False,
                        "Bootstrap not completed or detailed collection already started",
                    )
                else:
                    return (
                        False,
                        f"Questionnaire of type {questionnaire_type} not needed",
                    )

            # Additional validation for gap-based questionnaires
            if gap_results:
                identified_gaps = gap_results.get("identified_gaps", [])
                if not identified_gaps and q_type != QuestionnaireType.BOOTSTRAP:
                    return False, "No gaps identified - questionnaire not needed"

            # Check automation tier restrictions
            if (
                state.automation_tier == AutomationTier.TIER_1
                and q_type != QuestionnaireType.BOOTSTRAP
            ):
                return False, "Tier 1 flows only support bootstrap questionnaires"

            return True, f"Questionnaire generation approved for {questionnaire_type}"

        except Exception as e:
            logger.error(f"Error checking questionnaire generation: {e}")
            return False, f"Error checking questionnaire: {str(e)}"

    async def detect_completion_status(
        self, state: CollectionFlowState
    ) -> Dict[str, Any]:
        """
        Detect if collection phases are complete and ready for progression.

        This method analyzes the current state to determine completion
        and readiness for next phase transitions.

        Args:
            state: Current collection flow state

        Returns:
            Dictionary with completion status and recommendations
        """
        try:
            # Get workflow status from enhanced orchestrator
            workflow_status = await self.enhanced_orchestrator.get_workflow_status(
                state
            )

            completion_analysis = {
                "flow_id": state.flow_id,
                "current_phase": (
                    state.current_phase.value if state.current_phase else None
                ),
                "workflow_phase": workflow_status["workflow_phase"],
                "overall_progress": state.progress,
                "completion_checks": {},
                "recommendations": [],
                "ready_for_next_phase": False,
                "assessment_ready": state.assessment_ready,
            }

            # Bootstrap completion check
            bootstrap_status = workflow_status["bootstrap_questionnaire"]
            completion_analysis["completion_checks"]["bootstrap"] = {
                "exists": bootstrap_status["exists"],
                "completed": bootstrap_status["completed"],
                "status": "complete" if bootstrap_status["completed"] else "pending",
            }

            # Detailed collection completion check
            completion_analysis["completion_checks"]["detailed_collection"] = {
                "started": workflow_status["detailed_collection_started"],
                "questionnaire_submissions": len(
                    workflow_status["questionnaire_submissions"]
                ),
                "status": (
                    "complete"
                    if workflow_status["detailed_collection_started"]
                    else "pending"
                ),
            }

            # Data validation completion check
            validation_results = state.validation_results or {}
            completion_analysis["completion_checks"]["data_validation"] = {
                "validation_complete": bool(validation_results),
                "quality_score": state.collection_quality_score or 0.0,
                "confidence_score": state.confidence_score or 0.0,
                "status": "complete" if validation_results else "pending",
            }

            # Assessment readiness check
            completion_analysis["completion_checks"]["assessment_readiness"] = {
                "apps_ready": len(state.apps_ready_for_assessment or []),
                "canonical_integration": bool(
                    workflow_status.get("canonical_integration", {}).get("processed_at")
                ),
                "status": "ready" if state.assessment_ready else "not_ready",
            }

            # Generate recommendations based on completion status
            completion_analysis["recommendations"] = (
                self._generate_completion_recommendations(
                    state, workflow_status, completion_analysis
                )
            )

            # Determine if ready for next phase
            completion_analysis["ready_for_next_phase"] = (
                self._assess_next_phase_readiness(state, completion_analysis)
            )

            return completion_analysis

        except Exception as e:
            logger.error(f"Error detecting completion status: {e}")
            raise CollectionFlowError(f"Failed to detect completion status: {e}")

    def _generate_completion_recommendations(
        self,
        state: CollectionFlowState,
        workflow_status: Dict[str, Any],
        completion_analysis: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on completion analysis"""
        recommendations = []

        # Bootstrap recommendations
        if not workflow_status["bootstrap_questionnaire"]["completed"]:
            if not workflow_status["bootstrap_questionnaire"]["exists"]:
                recommendations.append(
                    "Generate bootstrap questionnaire to begin data collection"
                )
            else:
                recommendations.append("Complete bootstrap questionnaire submission")

        # Detailed collection recommendations
        if (
            workflow_status["bootstrap_questionnaire"]["completed"]
            and not workflow_status["detailed_collection_started"]
        ):
            recommendations.append("Advance to detailed collection phase")

        # Data validation recommendations
        if (
            workflow_status["detailed_collection_started"]
            and not completion_analysis["completion_checks"]["data_validation"][
                "validation_complete"
            ]
        ):
            recommendations.append("Initiate comprehensive data validation")

        # Assessment readiness recommendations
        if (
            completion_analysis["completion_checks"]["data_validation"][
                "validation_complete"
            ]
            and not state.assessment_ready
        ):
            recommendations.append("Prepare assessment package for handoff")

        # Canonical integration recommendations
        if not workflow_status.get("canonical_integration", {}).get("processed_at"):
            recommendations.append(
                "Integrate collected applications with canonical system"
            )

        return recommendations

    def _assess_next_phase_readiness(
        self, state: CollectionFlowState, completion_analysis: Dict[str, Any]
    ) -> bool:
        """Assess if flow is ready for next phase progression"""
        current_phase = state.current_phase

        if not current_phase:
            return True  # Can always start

        checks = completion_analysis["completion_checks"]

        # Phase-specific readiness logic
        if current_phase == CollectionPhase.INITIALIZATION:
            return True  # Always ready to progress from initialization

        elif current_phase == CollectionPhase.AUTOMATED_COLLECTION:
            # Ready if bootstrap is completed or if no automated collection possible
            return (
                checks["bootstrap"]["completed"]
                or state.automation_tier == AutomationTier.TIER_1
            )

        elif current_phase == CollectionPhase.QUESTIONNAIRE_GENERATION:
            # Ready if questionnaires have been generated
            return len(state.questionnaires or []) > 0

        elif current_phase == CollectionPhase.MANUAL_COLLECTION:
            # Ready if submissions have been made
            return checks["detailed_collection"]["questionnaire_submissions"] > 0

        elif current_phase == CollectionPhase.DATA_VALIDATION:
            # Ready if validation is complete
            return checks["data_validation"]["validation_complete"]

        elif current_phase == CollectionPhase.FINALIZATION:
            # Ready if assessment package is prepared
            return checks["assessment_readiness"]["status"] == "ready"

        return False

    async def advance_to_next_phase(
        self, state: CollectionFlowState, force: bool = False
    ) -> Dict[str, Any]:
        """
        Advance collection flow to the next appropriate phase.

        Args:
            state: Current collection flow state
            force: Force advancement ignoring validation checks

        Returns:
            Dictionary with advancement results
        """
        try:
            # Check completion status first
            completion_status = await self.detect_completion_status(state)

            if not force and not completion_status["ready_for_next_phase"]:
                return {
                    "advanced": False,
                    "reason": "Current phase not ready for advancement",
                    "recommendations": completion_status["recommendations"],
                    "current_phase": (
                        state.current_phase.value if state.current_phase else None
                    ),
                }

            # Use enhanced orchestrator to advance workflow
            previous_phase = state.current_phase
            new_workflow_phase = await self.enhanced_orchestrator.advance_workflow(
                state, force=force
            )

            # Update progress based on new phase
            state.updated_at = datetime.utcnow()

            return {
                "advanced": True,
                "previous_phase": previous_phase.value if previous_phase else None,
                "new_phase": state.current_phase.value if state.current_phase else None,
                "workflow_phase": new_workflow_phase.value,
                "progress": state.progress,
                "recommendations": completion_status["recommendations"],
            }

        except Exception as e:
            logger.error(f"Error advancing to next phase: {e}")
            raise CollectionFlowError(f"Failed to advance phase: {e}")

    async def prevent_infinite_loops(
        self, state: CollectionFlowState, phase_name: str, max_iterations: int = 3
    ) -> bool:
        """
        Prevent infinite loops by tracking phase iterations.

        Args:
            state: Current collection flow state
            phase_name: Name of the phase to check
            max_iterations: Maximum allowed iterations

        Returns:
            True if phase should proceed, False if loop detected
        """
        try:
            # Initialize iteration tracking if not exists
            if not hasattr(state, "phase_iterations"):
                state.phase_iterations = {}

            # Track current phase iterations
            if phase_name not in state.phase_iterations:
                state.phase_iterations[phase_name] = 0

            state.phase_iterations[phase_name] += 1

            if state.phase_iterations[phase_name] > max_iterations:
                logger.warning(
                    f"Infinite loop detected in phase {phase_name} for flow {state.flow_id} "
                    f"- exceeded {max_iterations} iterations"
                )

                # Add error to state
                state.add_error(
                    phase_name, f"Phase exceeded maximum iterations ({max_iterations})"
                )

                return False

            return True

        except Exception as e:
            logger.error(f"Error in loop prevention: {e}")
            return True  # Allow execution on error to avoid blocking

    async def get_orchestration_status(
        self, state: CollectionFlowState
    ) -> Dict[str, Any]:
        """
        Get comprehensive orchestration status including workflow and completion info.

        Args:
            state: Current collection flow state

        Returns:
            Complete orchestration status
        """
        try:
            # Get enhanced orchestrator status
            workflow_status = await self.enhanced_orchestrator.get_workflow_status(
                state
            )

            # Get completion analysis
            completion_status = await self.detect_completion_status(state)

            # Combine into comprehensive status
            orchestration_status = {
                "flow_id": state.flow_id,
                "orchestration_timestamp": datetime.utcnow().isoformat(),
                "workflow_management": workflow_status,
                "completion_analysis": completion_status,
                "phase_iterations": getattr(state, "phase_iterations", {}),
                "error_count": len(state.errors or []),
                "last_updated": (
                    state.updated_at.isoformat() if state.updated_at else None
                ),
                "orchestrator_version": "v2.0_with_enhanced_workflow",
            }

            return orchestration_status

        except Exception as e:
            logger.error(f"Error getting orchestration status: {e}")
            raise CollectionFlowError(f"Failed to get orchestration status: {e}")

