# flake8: noqa: F401
"""
Collection Flow Cleanup Service

This file maintains backward compatibility while the actual implementation
has been modularized into the collection_flow_cleanup_service/ subdirectory.
"""

from .collection_flow_cleanup_service import CollectionFlowCleanupService

__all__ = ["CollectionFlowCleanupService"]
