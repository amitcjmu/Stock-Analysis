"""
Base classes and enums for Collection Flow State Management
"""

from enum import Enum

from app.models.collection_flow import CollectionFlowStatus


class CollectionPhase(str, Enum):
    """Collection Flow phases"""

    INITIALIZATION = "initialization"
    ASSET_SELECTION = (
        "asset_selection"  # Replaces platform_detection and automated_collection
    )
    GAP_ANALYSIS = "gap_analysis"
    MANUAL_COLLECTION = "manual_collection"
    FINALIZATION = "finalization"


class CollectionPhaseUtils:
    """Utility methods for Collection Flow phases"""

    @staticmethod
    def is_valid_transition(current_phase: str, new_phase: str) -> bool:
        """
        Check if phase transition is valid.

        Args:
            current_phase: Current phase
            new_phase: New phase

        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            CollectionPhase.INITIALIZATION.value: [
                CollectionPhase.ASSET_SELECTION.value
            ],
            CollectionPhase.ASSET_SELECTION.value: [
                CollectionPhase.GAP_ANALYSIS.value,
                CollectionPhase.MANUAL_COLLECTION.value,  # Skip gap analysis if no gaps
                CollectionPhase.FINALIZATION.value,  # Skip to finalization if complete
            ],
            CollectionPhase.GAP_ANALYSIS.value: [
                CollectionPhase.MANUAL_COLLECTION.value,
                CollectionPhase.FINALIZATION.value,  # Skip manual if no gaps
            ],
            CollectionPhase.MANUAL_COLLECTION.value: [
                CollectionPhase.FINALIZATION.value
            ],
            CollectionPhase.FINALIZATION.value: [],  # Terminal phase
        }

        return new_phase in valid_transitions.get(current_phase, [])

    @staticmethod
    def map_phase_to_status(phase: CollectionPhase) -> CollectionFlowStatus:
        """
        Map phase to Collection Flow status.

        Args:
            phase: Collection phase

        Returns:
            Corresponding CollectionFlowStatus
        """
        phase_status_map = {
            CollectionPhase.INITIALIZATION: CollectionFlowStatus.INITIALIZED,
            CollectionPhase.ASSET_SELECTION: CollectionFlowStatus.ASSET_SELECTION,
            CollectionPhase.GAP_ANALYSIS: CollectionFlowStatus.GAP_ANALYSIS,
            CollectionPhase.MANUAL_COLLECTION: CollectionFlowStatus.MANUAL_COLLECTION,
            CollectionPhase.FINALIZATION: CollectionFlowStatus.COMPLETED,
        }

        return phase_status_map.get(phase, CollectionFlowStatus.INITIALIZED)
