"""
Handler modules for 6R analysis API endpoints.

This package contains modularized endpoint handlers:
- analysis_handlers: Core analysis creation, retrieval, and listing
- parameter_handlers: Parameter updates, question responses, iterations
- recommendation_handlers: Recommendation retrieval
- bulk_handlers: Bulk analysis operations
"""

from .analysis_handlers import (
    create_sixr_analysis,
    get_analysis,
    list_sixr_analyses,
)
from .parameter_handlers import (
    update_sixr_parameters,
    submit_qualifying_responses,
    create_analysis_iteration,
    submit_inline_answers,
)
from .recommendation_handlers import get_sixr_recommendation
from .bulk_handlers import create_bulk_analysis

__all__ = [
    # Analysis handlers
    "create_sixr_analysis",
    "get_analysis",
    "list_sixr_analyses",
    # Parameter handlers
    "update_sixr_parameters",
    "submit_qualifying_responses",
    "create_analysis_iteration",
    "submit_inline_answers",
    # Recommendation handlers
    "get_sixr_recommendation",
    # Bulk handlers
    "create_bulk_analysis",
]
