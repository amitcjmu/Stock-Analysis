"""Agentic critical attributes route modules."""

from .analysis_routes import router as analysis_router
from .suggestion_routes import router as suggestion_router
from .feedback_routes import router as feedback_router

__all__ = [
    'analysis_router',
    'suggestion_router',
    'feedback_router'
]