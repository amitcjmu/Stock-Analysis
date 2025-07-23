"""
Assessment Flow Repository - Backward Compatibility Module

This file maintains backward compatibility by re-exporting the modularized
AssessmentFlowRepository from the assessment_flow_repository package.

The original 787-line monolithic repository has been refactored into:
- assessment_flow_repository/base_repository.py: Main repository with delegation
- assessment_flow_repository/commands/: Write operations (flow, architecture, components, decisions, feedback)
- assessment_flow_repository/queries/: Read operations (flows, analytics, state construction)
- assessment_flow_repository/specifications/: Utility methods and specifications

All existing imports will continue to work without modification.
"""

# Import from the modularized package
from .assessment_flow_repository import AssessmentFlowRepository

# Re-export for backward compatibility
__all__ = ["AssessmentFlowRepository"]
