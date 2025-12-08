"""
Assessment Flow Phase Handlers Package

This package provides modularized phase handlers for the Assessment Flow.
The main AssessmentPhaseHandlers class combines all handler mixins to provide
a complete set of phase handling functionality.

Backward Compatibility:
    The public API is preserved - imports like:
        from app.services.crewai_flows.assessment_flow.phase_handlers import AssessmentPhaseHandlers
    will continue to work as before.

Module Organization:
    - base.py: Base class with shared helper methods
    - initialization_handlers.py: Initialization phase logic
    - compliance_handlers.py: Architecture compliance validation (ADR-039)
    - analysis_handlers.py: Technical debt analysis
    - recommendation_handlers.py: 6R strategies, App on Page, finalization
"""

from .analysis_handlers import AnalysisHandlers
from .base import AssessmentPhaseHandlers as BaseHandlers
from .compliance_handlers import ComplianceHandlers
from .initialization_handlers import InitializationHandlers
from .recommendation_handlers import RecommendationHandlers


class AssessmentPhaseHandlers(
    BaseHandlers,
    InitializationHandlers,
    ComplianceHandlers,
    AnalysisHandlers,
    RecommendationHandlers,
):
    """
    Complete phase handlers for Assessment Flow.

    This class combines all phase handling mixins using multiple inheritance
    to provide the full set of phase handler methods. The base class
    (BaseHandlers) provides shared helper methods that all mixins can use.

    Phase Methods:
        - handle_initialization: Load applications and standards
        - handle_architecture_minimums: Validate compliance (ADR-039)
        - handle_technical_debt_analysis: Analyze debt with compliance context
        - handle_sixr_strategies: Determine migration strategies
        - handle_app_on_page_generation: Generate assessment reports
        - handle_finalization: Complete assessment flow

    Usage:
        handlers = AssessmentPhaseHandlers(flow_instance)
        result = await handlers.handle_initialization()
    """

    pass


# Explicit exports for backward compatibility
__all__ = [
    "AssessmentPhaseHandlers",
    "BaseHandlers",
    "InitializationHandlers",
    "ComplianceHandlers",
    "AnalysisHandlers",
    "RecommendationHandlers",
]
