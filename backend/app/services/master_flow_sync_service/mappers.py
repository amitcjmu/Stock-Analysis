"""
Status and phase mapping utilities for flow synchronization
"""

import logging

logger = logging.getLogger(__name__)


class FlowStatusMapper:
    """Handles status and phase mapping between master and child flows"""

    @staticmethod
    def status_compatible(master_status: str, child_status: str) -> bool:
        """
        Check if master and child flow statuses are compatible.

        This prevents conflicts where the child flow is more advanced than the master flow,
        which would indicate a synchronization issue.
        """
        # CC FIX: Define status hierarchy using ONLY valid enum values
        # Valid collection flow enum: initialized, running, paused, completed, failed, cancelled
        # Other values (gap_analysis, asset_selection, etc.) are PHASES, not statuses
        status_hierarchy = {
            "pending": 0,
            "initialized": 1,
            "running": 2,
            "paused": 3,
            "completed": 4,
            "failed": 5,
            "cancelled": 5,
        }

        master_level = status_hierarchy.get(master_status, 0)
        child_level = status_hierarchy.get(child_status, 0)

        # Compatible if master is at same level or more advanced
        return master_level >= child_level

    @staticmethod
    def child_status_more_advanced(master_status: str, child_status: str) -> bool:
        """Check if child status is more advanced than master status"""
        return not FlowStatusMapper.status_compatible(master_status, child_status)

    @staticmethod
    def map_child_to_master_status(child_status: str) -> str:
        """Map collection flow status to master flow status"""
        # CC FIX: Map ONLY valid collection flow enum values
        # Valid collection flow enum: initialized, running, paused, completed, failed, cancelled
        status_mapping = {
            "initialized": "pending",
            "running": "running",
            "paused": "paused",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
        }
        return status_mapping.get(child_status, "pending")

    @staticmethod
    def map_assessment_to_master_status(assessment_status: str) -> str:
        """Map assessment flow status to master flow status"""
        status_mapping = {
            "initialization": "pending",
            "analysis": "running",
            "planning": "running",
            "assessment": "running",
            "completed": "completed",
            "failed": "failed",
        }
        return status_mapping.get(assessment_status, "pending")

    @staticmethod
    def map_child_to_master_phase(child_phase: str) -> str:
        """Map collection flow phase to master flow phase"""
        # FIXED: Removed "automated_collection" which doesn't exist in enum
        phase_mapping = {
            "platform_detection": "discovery",
            "asset_selection": "collection",
            "manual_collection": "collection",
            "data_validation": "validation",
            "gap_analysis": "analysis",
            "finalization": "completion",
        }
        return phase_mapping.get(child_phase, "discovery")

    @staticmethod
    def map_assessment_to_master_phase(assessment_phase: str) -> str:
        """Map assessment flow phase to master flow phase"""
        phase_mapping = {
            "initialization": "discovery",
            "analysis": "analysis",
            "planning": "planning",
            "assessment": "assessment",
        }
        return phase_mapping.get(assessment_phase, "discovery")

    @staticmethod
    def map_master_to_child_status(master_status: str) -> str:
        """
        Map master flow LIFECYCLE status to child flow STATUS.

        IMPORTANT (Per ADR-012): This maps lifecycle STATUS to STATUS, NOT status to phase.
        - Master flow tracks: pending → running → completed/failed (lifecycle envelope)
        - Child flows track phases in current_phase column (gap_analysis, manual_collection, etc.)

        Child flows OWN their current_phase progression. This function only maps
        the high-level lifecycle status for monitoring and coordination.

        Valid child flow STATUSES (enum values): initialized, running, paused, completed, failed, cancelled
        Valid child flow PHASES (varchar): asset_selection, gap_analysis, manual_collection, etc.
        """
        # CC FIX: Map to valid enum values only
        # Status goes to status column (enum), phase goes to current_phase column (varchar)
        status_mapping = {
            "running": "running",  # Map to valid enum value
            "completed": "completed",
            "failed": "failed",
            "paused": "paused",  # Map to valid enum value
            "pending": "initialized",
        }
        return status_mapping.get(master_status, "initialized")

    @staticmethod
    def extract_progress_from_metadata(flow_metadata: dict) -> float:
        """Extract progress percentage from flow metadata"""
        if not flow_metadata:
            return 0.0

        # Check various possible metadata keys for progress
        progress_keys = [
            "discovery_progress",
            "collection_progress",
            "progress",
            "progress_percentage",
            "completion_percentage",
        ]

        for key in progress_keys:
            if key in flow_metadata and flow_metadata[key] is not None:
                try:
                    return float(flow_metadata[key])
                except (ValueError, TypeError):
                    continue

        return 0.0

    @staticmethod
    def extract_phase_from_metadata(flow_metadata: dict) -> str:
        """Extract current phase from flow metadata"""
        if not flow_metadata:
            return "initialized"

        # Check various possible metadata keys for phase
        phase_keys = [
            "discovery_phase",
            "collection_phase",
            "current_phase",
            "phase",
            "stage",
        ]

        for key in phase_keys:
            if key in flow_metadata and flow_metadata[key]:
                return str(flow_metadata[key])

        return "initialized"
