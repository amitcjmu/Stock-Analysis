"""
Assessment Input Builders - Base Class

Core input builder class with shared functionality.
Per ADR-024: Inputs prepared for TenantMemoryManager-based agents.
"""

from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.repositories.assessment_data_repository import AssessmentDataRepository

from .readiness_builder import ReadinessBuilderMixin
from .complexity_builder import ComplexityBuilderMixin
from .dependency_builder import DependencyBuilderMixin
from .tech_debt_builder import TechDebtBuilderMixin
from .risk_builder import RiskBuilderMixin
from .recommendation_builder import RecommendationBuilderMixin

logger = get_logger(__name__)


class AssessmentInputBuilders(
    ReadinessBuilderMixin,
    ComplexityBuilderMixin,
    DependencyBuilderMixin,
    TechDebtBuilderMixin,
    RiskBuilderMixin,
    RecommendationBuilderMixin,
):
    """
    Build agent inputs for each assessment phase.

    Combines user input, repository context data, and previous phase results
    into structured inputs that assessment agents can consume.

    Each builder method returns a dictionary with:
    - flow_id: Assessment flow UUID
    - client_account_id: Tenant identifier
    - engagement_id: Project identifier
    - phase_name: Current phase name
    - user_input: Input from UI/API
    - context_data: Data from repository
    - previous_phase_results: Results from prior phases
    - metadata: Timestamps, versions, etc.
    """

    def __init__(self, data_repository: AssessmentDataRepository):
        """
        Initialize input builders with data repository.

        Args:
            data_repository: Repository for fetching assessment data
        """
        self.data_repo = data_repository
        logger.debug("Initialized AssessmentInputBuilders")

    # === HELPER METHODS ===

    def _build_fallback_input(
        self, flow_id: str, phase_name: str, user_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build minimal fallback input when data fetching fails.

        Ensures agents can still execute with basic information even if
        repository queries fail.

        Args:
            flow_id: Assessment flow UUID
            phase_name: Current phase name
            user_input: Optional user input

        Returns:
            Minimal input structure with tenant scoping
        """
        from datetime import datetime

        return {
            "flow_id": flow_id,
            "client_account_id": str(self.data_repo.client_account_id),
            "engagement_id": str(self.data_repo.engagement_id),
            "phase_name": phase_name,
            "user_input": user_input or {},
            "context_data": {},
            "previous_phase_results": {},
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "phase_version": "1.0.0",
                "builder": phase_name,
                "fallback": True,
                "error": "Failed to fetch context data",
            },
        }

    def enrich_with_previous_results(
        self, input_data: Dict[str, Any], previous_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enrich input data with results from previous phases.

        Called by execution engine to add prior phase results after they complete.

        Args:
            input_data: Base input data
            previous_results: Dictionary of phase_name -> results

        Returns:
            Enriched input data with previous_phase_results updated
        """
        if "previous_phase_results" not in input_data:
            input_data["previous_phase_results"] = {}

        input_data["previous_phase_results"].update(previous_results)
        return input_data
