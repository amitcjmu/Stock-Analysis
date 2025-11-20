"""
Collection Agent Questionnaire Endpoints
Status polling endpoint for agent-driven questionnaire generation.

DEPRECATION NOTICE (Nov 2025):
- generation.py module REMOVED (dead code per ADR-035)
- POST /questionnaires/generate endpoint REMOVED (never used by frontend)
- Per ADR-035: Use MFO auto-progression or _start_agent_generation instead
- Only GET /questionnaires/status remains (actively used by QuestionnaireGenerationModal.tsx)

Remaining modules:
- router.py: Questionnaire status polling endpoint
- helpers.py: Utility functions for building context and managing state
- bootstrap.py: Fallback questionnaire generation
"""

# Import the router for FastAPI route registration
from .router import router

# Import key functions to maintain backward compatibility
from .helpers import (
    build_agent_context,
    mark_generation_failed,
    calculate_completeness,
    identify_gaps,
)
from .bootstrap import get_bootstrap_questionnaire

# Define public API for export
# REMOVED: generate_questionnaire_with_agent (deprecated per ADR-035)
__all__ = [
    "router",
    "build_agent_context",
    "mark_generation_failed",
    "calculate_completeness",
    "identify_gaps",
    "get_bootstrap_questionnaire",
]
