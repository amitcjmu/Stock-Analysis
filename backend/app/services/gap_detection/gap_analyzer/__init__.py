"""
GapAnalyzer - Orchestrates all 5 inspectors for comprehensive gap analysis.

Modularized structure:
- base.py: Class initialization and inspector instances
- orchestration.py: Main analyze_asset orchestration logic
- requirements.py: RequirementsEngine integration
- calculations.py: Weighted completeness calculations
- prioritization.py: Gap prioritization by business impact
- readiness.py: Assessment readiness determination

Performance: <50ms per asset (target from implementation plan)
Part of Issue #980: Intelligent Multi-Layer Gap Detection System
"""

from app.services.gap_detection.gap_analyzer.base import GapAnalyzerBase
from app.services.gap_detection.gap_analyzer.calculations import CalculationsMixin
from app.services.gap_detection.gap_analyzer.orchestration import OrchestrationMixin
from app.services.gap_detection.gap_analyzer.prioritization import PrioritizationMixin
from app.services.gap_detection.gap_analyzer.readiness import ReadinessMixin
from app.services.gap_detection.gap_analyzer.requirements import RequirementsMixin


class GapAnalyzer(
    GapAnalyzerBase,
    OrchestrationMixin,
    RequirementsMixin,
    CalculationsMixin,
    PrioritizationMixin,
    ReadinessMixin,
):
    """
    Orchestrates all 5 inspectors to produce comprehensive gap analysis.

    This service is the single entry point for gap detection across all data layers.
    It coordinates inspector execution, calculates weighted completeness, prioritizes
    gaps by business impact, and determines assessment readiness.

    Performance Target: <50ms per asset
    GPT-5 Recommendations Applied:
    - #1: Tenant scoping (client_account_id, engagement_id)
    - #3: Async consistency (all methods are async)
    - #8: JSON safety (clamp overall_completeness to [0.0, 1.0])

    Usage:
        analyzer = GapAnalyzer()
        report = await analyzer.analyze_asset(
            asset=asset_obj,
            application=app_obj,
            client_account_id="uuid",
            engagement_id="uuid",
            db=db_session,
        )

    Modular Architecture:
        - Inherits from 6 mixins for maintainability
        - Each mixin handles a specific responsibility
        - Preserves backward compatibility with original API
    """

    pass  # All functionality inherited from mixins


__all__ = ["GapAnalyzer"]
