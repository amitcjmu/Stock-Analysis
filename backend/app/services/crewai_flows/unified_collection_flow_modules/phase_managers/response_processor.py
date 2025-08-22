"""
Response Processor for Manual Collection

Handles response processing, validation, and gap analysis.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.models.collection_flow import CollectionPhase
from app.services.manual_collection import (
    ProgressTrackingService,
    QuestionnaireValidationService,
)

logger = logging.getLogger(__name__)


class ResponseProcessor:
    """Processes and validates manual collection responses."""

    def __init__(self, flow_context, state_manager):
        """Initialize response processor."""
        self.flow_context = flow_context
        self.state_manager = state_manager

        # Initialize services
        self.validation_service = QuestionnaireValidationService()
        self.progress_tracking = ProgressTrackingService(
            flow_context.db_session, flow_context
        )

    async def process_responses(
        self,
        crew_results: Dict[str, Any],
        user_responses: Dict[str, Any],
        identified_gaps: List[Dict],
        client_requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Process and validate manual collection responses"""
        logger.info("🔧 Processing manual collection responses")

        # Extract responses from crew results
        responses = crew_results.get("responses", [])
        validation_results = crew_results.get("validation", {})

        # Validate responses
        validated_responses = (
            await self.validation_service.validate_questionnaire_responses(
                responses=responses,
                validation_rules=client_requirements.get("validation_rules", {}),
                gap_context=identified_gaps,
            )
        )

        # Identify remaining gaps
        remaining_gaps = self._identify_remaining_gaps(
            validated_responses, identified_gaps
        )

        # Calculate completion metrics
        completion_metrics = self._calculate_completion_metrics(
            validated_responses, identified_gaps
        )

        return {
            "responses": validated_responses,
            "validation_results": {
                "pass_rate": validation_results.get("pass_rate", 0.0),
                "validation_details": validation_results,
                "failed_validations": validation_results.get("failed", []),
            },
            "remaining_gaps": remaining_gaps,
            "completion_metrics": completion_metrics,
            "crew_output": crew_results,
        }

    async def update_progress_tracking(
        self, flow_state, validated_responses: Dict[str, Any]
    ):
        """Update progress tracking for manual collection"""
        logger.info("📊 Updating progress tracking")

        # Track questionnaire completion
        questionnaire_progress = {
            "total_questionnaires": len(flow_state.questionnaires),
            "completed_questionnaires": len(validated_responses["responses"]),
            "completion_percentage": (
                len(validated_responses["responses"])
                / len(flow_state.questionnaires)
                * 100
                if flow_state.questionnaires
                else 100
            ),
        }

        # Track gap resolution
        gap_progress = {
            "initial_gaps": len(
                flow_state.gap_analysis_results.get("identified_gaps", [])
            ),
            "remaining_gaps": len(validated_responses["remaining_gaps"]),
            "gaps_resolved": len(
                flow_state.gap_analysis_results.get("identified_gaps", [])
            )
            - len(validated_responses["remaining_gaps"]),
        }

        # Update progress service
        await self.progress_tracking.update_collection_progress(
            flow_id=self.flow_context.flow_id,
            phase="manual_collection",
            progress_data={
                "questionnaire_progress": questionnaire_progress,
                "gap_progress": gap_progress,
                "validation_pass_rate": validated_responses["validation_results"][
                    "pass_rate"
                ],
            },
        )

    async def update_flow_state(
        self,
        flow_state,
        validated_responses: Dict[str, Any],
        crew_results: Dict[str, Any],
    ):
        """Update flow state with manual collection results"""
        logger.info("💾 Updating flow state with manual collection results")

        # Store manual responses
        flow_state.manual_responses = validated_responses["responses"]

        # Store phase results
        flow_state.phase_results["manual_collection"] = {
            "responses": validated_responses["responses"],
            "validation_results": validated_responses["validation_results"],
            "remaining_gaps": validated_responses["remaining_gaps"],
            "completion_metrics": validated_responses["completion_metrics"],
            "collection_timestamp": datetime.utcnow().isoformat(),
        }

        # Update progress
        flow_state.progress = 85.0
        flow_state.next_phase = CollectionPhase.DATA_VALIDATION

        # Persist state
        await self.state_manager.save_state(flow_state.to_dict())

    def _identify_remaining_gaps(
        self, validated_responses: List[Dict], initial_gaps: List[Dict]
    ) -> List[Dict]:
        """Identify gaps that remain after manual collection"""
        remaining_gaps = []

        # Create a map of responses by gap ID
        response_map = {}
        for response in validated_responses:
            gap_id = response.get("gap_id")
            if gap_id:
                response_map[gap_id] = response

        # Check each initial gap
        for gap in initial_gaps:
            gap_id = gap.get("id")
            if gap_id not in response_map:
                # Gap not addressed
                remaining_gaps.append(gap)
            else:
                response = response_map[gap_id]
                # Check if response adequately addresses the gap
                if not self._is_gap_resolved(gap, response):
                    gap["partial_resolution"] = True
                    gap["response_quality"] = response.get("quality_score", 0.0)
                    remaining_gaps.append(gap)

        return remaining_gaps

    def _is_gap_resolved(self, gap: Dict, response: Dict) -> bool:
        """Check if a response adequately resolves a gap"""
        # Check response completeness
        if response.get("completeness", 0.0) < 0.8:
            return False

        # Check response quality
        if response.get("quality_score", 0.0) < 0.7:
            return False

        # Check if all required fields are present
        required_fields = gap.get("required_fields", [])
        response_fields = response.get("fields", {})

        for field in required_fields:
            if field not in response_fields or not response_fields[field]:
                return False

        return True

    def _calculate_completion_metrics(
        self, validated_responses: List[Dict], initial_gaps: List[Dict]
    ) -> Dict[str, float]:
        """Calculate completion metrics for manual collection"""
        if not initial_gaps:
            return {
                "overall_completion": 100.0,
                "quality_score": 100.0,
                "coverage_score": 100.0,
            }

        # Calculate completion rate
        responses_count = len(validated_responses)
        gaps_count = len(initial_gaps)
        completion_rate = (responses_count / gaps_count * 100) if gaps_count > 0 else 0

        # Calculate average quality score
        quality_scores = [r.get("quality_score", 0.0) for r in validated_responses]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        # Calculate coverage score (how well responses cover gap requirements)
        coverage_scores = []
        for response in validated_responses:
            required = response.get("required_fields_count", 1)
            provided = response.get("provided_fields_count", 0)
            coverage = (provided / required) if required > 0 else 0
            coverage_scores.append(coverage)

        avg_coverage = (
            sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
        )

        return {
            "overall_completion": completion_rate,
            "quality_score": avg_quality * 100,
            "coverage_score": avg_coverage * 100,
        }
