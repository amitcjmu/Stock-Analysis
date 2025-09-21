"""
Response mapping service for collection gaps.

This module maintains backward compatibility while delegating to the
modularized response_mapping_service package for better code organization.
"""

# Import all public items from the modularized package
from .response_mapping_service import *  # noqa: F401, F403

# Explicitly import the main service class for external use
from .response_mapping_service import ResponseMappingService

__all__ = ["ResponseMappingService"]
