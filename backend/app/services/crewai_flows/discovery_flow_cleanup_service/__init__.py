"""
Discovery Flow Cleanup Service
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Handles comprehensive cleanup of discovery flows including CrewAI Flow state,
agent memory, database records, and associated data with proper audit trail.

Migrating from WorkflowState to DiscoveryFlow V2 architecture.

This module has been modularized to comply with the 400-line file limit.
The original monolithic file has been split into:
- base.py: Base class with initialization
- cleanup_operations.py: Main deletion and cleanup methods
- impact_analysis.py: Impact analysis and counting operations
- utils.py: Utility methods for time estimation and recommendations
"""

from .base import DiscoveryFlowCleanupServiceBase
from .cleanup_operations import CleanupOperationsMixin
from .impact_analysis import ImpactAnalysisMixin
from .utils import CleanupUtilsMixin


class DiscoveryFlowCleanupService(
    CleanupOperationsMixin,
    ImpactAnalysisMixin,
    CleanupUtilsMixin,
    DiscoveryFlowCleanupServiceBase,
):
    """
    ⚠️ LEGACY COMPATIBILITY LAYER - Use DiscoveryFlowService.delete_flow() for new development

    Comprehensive cleanup service for discovery flows
    Handles deletion of all associated data with proper audit trail

    This class combines functionality from multiple mixins:
    - CleanupOperationsMixin: Main deletion operations
    - ImpactAnalysisMixin: Impact analysis and counting
    - CleanupUtilsMixin: Time estimation and recommendations
    - DiscoveryFlowCleanupServiceBase: Base initialization
    """

    pass


# Preserve backward compatibility by re-exporting the main class
__all__ = ["DiscoveryFlowCleanupService"]
