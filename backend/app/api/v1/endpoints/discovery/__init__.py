"""
Discovery endpoints package
"""

# Import the router for discovery flow endpoints
from .router import router

# Make this directory a proper Python package
# Note: discovery_main.py was removed as legacy dead code
# Unified discovery functionality is handled by unified_discovery.py
# Basic discovery flow endpoints are handled by router.py

__all__ = ["router"]
