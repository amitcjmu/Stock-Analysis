"""
Collection Child Flow Service Module
Modularized for maintainability while preserving backward compatibility
"""

# Import main service class for backward compatibility
from .service import CollectionChildFlowService

# Preserve public API
__all__ = ["CollectionChildFlowService"]
