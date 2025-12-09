"""
Discovery Flow Cleanup Service - Utilities Module
⚠️ LEGACY COMPATIBILITY LAYER - MIGRATING TO V2 ARCHITECTURE

Utility methods for cleanup time estimation and recommendations.
"""

import logging
from typing import List

from app.models.discovery_flow import DiscoveryFlow

logger = logging.getLogger(__name__)


class CleanupUtilsMixin:
    """
    Mixin for cleanup utility functions
    Provides helper methods for time estimation and recommendations
    """

    def _calculate_cleanup_time(self, total_records: int) -> str:
        """Calculate estimated cleanup time based on record count"""
        if total_records > 10000:
            return "30-60 seconds"
        elif total_records > 5000:
            return "15-30 seconds"
        elif total_records > 1000:
            return "10-15 seconds"
        elif total_records > 100:
            return "5-10 seconds"
        else:
            return "< 5 seconds"

    def _get_deletion_warnings(
        self, flow: DiscoveryFlow, total_records: int
    ) -> List[str]:
        """Get warnings about flow deletion"""
        warnings = []

        if flow.status == "active":
            warnings.append("Flow is currently active - force delete required")

        if flow.progress_percentage > 80:
            warnings.append(
                "Flow is nearly complete - consider completing instead of deleting"
            )

        if total_records > 1000:
            warnings.append(
                f"Large amount of data will be deleted ({total_records} records)"
            )

        if flow.shared_memory_id:
            warnings.append(
                "Agent memory will be cleared - learning progress may be lost"
            )

        return warnings

    def _get_deletion_recommendations(self, flow: DiscoveryFlow) -> List[str]:
        """Get recommendations for flow deletion"""
        recommendations = []

        if flow.status == "paused":
            recommendations.append("Consider resuming flow instead of deleting")

        if flow.progress_percentage > 50:
            recommendations.append(
                "Flow has significant progress - export data before deletion"
            )

        if flow.errors:
            recommendations.append(
                "Review errors before deletion to prevent similar issues"
            )

        recommendations.append("Ensure all stakeholders are aware of the deletion")
        recommendations.append("Consider creating a backup of important data")

        return recommendations
