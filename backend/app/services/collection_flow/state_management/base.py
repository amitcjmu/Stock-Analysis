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
    AUTO_ENRICHMENT = "auto_enrichment"
    GAP_ANALYSIS = "gap_analysis"
    QUESTIONNAIRE_GENERATION = "questionnaire_generation"
    MANUAL_COLLECTION = "manual_collection"
    DATA_VALIDATION = "data_validation"
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
                CollectionPhase.AUTO_ENRICHMENT.value,
                CollectionPhase.GAP_ANALYSIS.value,  # Skip enrichment
                CollectionPhase.FINALIZATION.value,  # Skip to finalization if complete
            ],
            CollectionPhase.AUTO_ENRICHMENT.value: [
                CollectionPhase.GAP_ANALYSIS.value,
            ],
            CollectionPhase.GAP_ANALYSIS.value: [
                CollectionPhase.QUESTIONNAIRE_GENERATION.value,
                CollectionPhase.FINALIZATION.value,  # Skip if no gaps
            ],
            CollectionPhase.QUESTIONNAIRE_GENERATION.value: [
                CollectionPhase.MANUAL_COLLECTION.value,
            ],
            CollectionPhase.MANUAL_COLLECTION.value: [
                CollectionPhase.DATA_VALIDATION.value,
            ],
            CollectionPhase.DATA_VALIDATION.value: [
                CollectionPhase.FINALIZATION.value,
            ],
            CollectionPhase.FINALIZATION.value: [],  # Terminal phase
        }

        return new_phase in valid_transitions.get(current_phase, [])

    @staticmethod
    def map_phase_to_status(phase: CollectionPhase) -> CollectionFlowStatus:
        """
        DEPRECATED per ADR-012. Status is independent of phase.
        Use explicit status management instead.

        This function violates ADR-012 (Flow Status Management Separation)
        which mandates that status reflects lifecycle state (INITIALIZED, RUNNING,
        PAUSED, COMPLETED) while phase reflects operational state (GAP_ANALYSIS,
        ASSET_SELECTION, etc.).

        Args:
            phase: Collection phase (ignored)

        Raises:
            NotImplementedError: Always raised to prevent usage

        See Also:
            /docs/adr/012-flow-status-management-separation.md
        """
        raise NotImplementedError(
            "Status should not be derived from phase per ADR-012. "
            "Set status explicitly based on lifecycle state:\n"
            "  - INITIALIZED: New flow created\n"
            "  - RUNNING: Flow actively executing\n"
            "  - PAUSED: Flow waiting for user input\n"
            "  - COMPLETED: Flow finished successfully\n"
            "See /docs/adr/012-flow-status-management-separation.md"
        )
