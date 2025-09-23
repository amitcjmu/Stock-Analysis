"""
Collection Agent Questionnaire Endpoints
Modularized implementation for agent-driven questionnaire generation.

This module preserves the public API of the original collection_agent_questionnaires.py file
while organizing the code into logical modules for better maintainability.

Modules:
- router.py: Main API endpoints for questionnaire status and generation
- helpers.py: Utility functions for building context and managing state
- generation.py: Agent-driven questionnaire generation logic
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
from .generation import generate_questionnaire_with_agent
from .bootstrap import get_bootstrap_questionnaire

# Define public API for export
__all__ = [
    "router",
    "build_agent_context",
    "mark_generation_failed",
    "calculate_completeness",
    "identify_gaps",
    "generate_questionnaire_with_agent",
    "get_bootstrap_questionnaire",
]
