"""
Agent API endpoints package.

This package contains all agent-related API endpoints organized into submodules.
"""

# Import the router to make it available when importing the package
from .router import router as agents_router

__all__ = ["agents_router"]
