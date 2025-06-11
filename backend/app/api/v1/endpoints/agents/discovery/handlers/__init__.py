"""
Discovery agent handlers package.

This package contains all the handler modules for discovery agent endpoints.
"""

from .status import router as status_router
from .analysis import router as analysis_router
from .learning import router as learning_router
from .dependencies import router as dependencies_router

__all__ = [
    "status_router",
    "analysis_router",
    "learning_router",
    "dependencies_router"
]
