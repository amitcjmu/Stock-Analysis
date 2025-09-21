"""
Collection flows API endpoints.

This module maintains backward compatibility while delegating to the
modularized collection_flows package for better code organization.
"""

# Import all public items from the modularized package
from .collection_flows import *  # noqa: F401, F403

# Explicitly import the router for external use
from .collection_flows import router

__all__ = ["router"]
