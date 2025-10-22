"""
Analysis service for 6R analysis business logic.
This is the main facade/orchestrator that delegates to background task modules.

ARCHITECTURE: Modularized Oct 2024 (file was 619 lines, now ~180 lines)
- Main service remains as public API facade
- Background tasks extracted to background_tasks/ subdirectory
- All security fixes preserved in task modules (see initial_analysis_task.py)
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.sixr_engine_modular import SixRDecisionEngine

from .background_tasks import (
    process_question_responses as _process_question_responses,
    run_bulk_analysis as _run_bulk_analysis,
    run_initial_analysis as _run_initial_analysis,
    run_iteration_analysis as _run_iteration_analysis,
    run_parameter_update_analysis as _run_parameter_update_analysis,
)

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service class for handling 6R analysis business logic.

    This class acts as a facade/orchestrator that delegates to specialized
    background task modules while maintaining a stable public API.
    """

    def __init__(self, crewai_service=None, require_ai: bool = False):
        """
        Initialize the analysis service with decision engine.

        Args:
            crewai_service: Optional CrewAI service for AI-powered analysis.
                           If None, engine uses fallback heuristic mode.
            require_ai: If True, raises ValueError when AI is required but unavailable.
                       Reference: Bug #666 - Phase 2 (Qodo Bot security concern)
        """
        self.decision_engine = SixRDecisionEngine(
            crewai_service=crewai_service, require_ai=require_ai
        )

    async def run_initial_analysis(
        self,
        analysis_id: int,
        parameters: Dict[str, Any],
        user: str,
        client_account_id: Optional[int] = None,
        engagement_id: Optional[int] = None,
    ):
        """
        Run initial 6R analysis in background.

        Delegates to initial_analysis_task module which contains the full implementation
        including CRITICAL SECURITY FIXES for tenant scoping (Qodo Bot review).

        Args:
            analysis_id: Analysis ID
            parameters: Analysis parameters
            user: User who initiated the analysis
            client_account_id: Client account ID for tenant scoping (SECURITY FIX)
            engagement_id: Engagement ID for tenant scoping (SECURITY FIX)
        """
        return await _run_initial_analysis(
            decision_engine=self.decision_engine,
            analysis_id=analysis_id,
            parameters=parameters,
            user=user,
            client_account_id=client_account_id,
            engagement_id=engagement_id,
        )

    async def run_parameter_update_analysis(
        self, analysis_id: int, parameters: Dict[str, Any], user: str
    ):
        """
        Run analysis after parameter update.

        Delegates to parameter_update_task module.

        Args:
            analysis_id: Analysis ID
            parameters: Updated parameters
            user: User who initiated the update
        """
        return await _run_parameter_update_analysis(
            decision_engine=self.decision_engine,
            analysis_id=analysis_id,
            parameters=parameters,
            user=user,
        )

    async def process_question_responses(
        self, analysis_id: int, responses: List[Dict[str, Any]], user: str
    ):
        """
        Process qualifying question responses and update analysis.

        Delegates to question_processing_task module.

        Args:
            analysis_id: Analysis ID
            responses: List of question responses
            user: User who provided responses
        """
        return await _process_question_responses(
            decision_engine=self.decision_engine,
            analysis_id=analysis_id,
            responses=responses,
            user=user,
        )

    async def run_iteration_analysis(
        self,
        analysis_id: int,
        iteration_number: int,
        request_data: Dict[str, Any],
        user: str,
    ):
        """
        Run analysis iteration with updated parameters.

        Delegates to iteration_analysis_task module.

        Args:
            analysis_id: Analysis ID
            iteration_number: Iteration number
            request_data: Request data including parameters and notes
            user: User who initiated the iteration
        """
        return await _run_iteration_analysis(
            decision_engine=self.decision_engine,
            analysis_id=analysis_id,
            iteration_number=iteration_number,
            request_data=request_data,
            user=user,
        )

    async def run_bulk_analysis(
        self, analysis_ids: List[int], batch_size: int, user: str
    ):
        """
        Run bulk analysis for multiple applications.

        Delegates to bulk_analysis_task module.

        Args:
            analysis_ids: List of analysis IDs to process
            batch_size: Batch size for parallel processing
            user: User who initiated bulk analysis
        """
        return await _run_bulk_analysis(
            decision_engine=self.decision_engine,
            analysis_ids=analysis_ids,
            batch_size=batch_size,
            user=user,
        )


# Bug #666 - Phase 2: DEPRECATED singleton instance removed
# All endpoints should create AnalysisService per-request with TenantScopedAgentPool
# Example: service = AnalysisService(crewai_service=TenantScopedAgentPool)
