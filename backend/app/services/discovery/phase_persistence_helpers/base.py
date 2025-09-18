"""
Base constants, data classes, and validation for phase persistence.

Contains shared constants, data structures, and validation logic
used across the phase persistence system.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# Phase flag mapping for completion tracking
PHASE_FLAG_MAP = {
    "data_import": "data_import_completed",
    "field_mapping": "field_mapping_completed",
    "data_cleansing": "data_cleansing_completed",
    "asset_inventory": "asset_inventory_completed",
    "dependency_analysis": "dependency_analysis_completed",
    "tech_debt_assessment": "tech_debt_assessment_completed",
}

# Valid phase transitions - defines the state machine
VALID_PHASE_TRANSITIONS = {
    None: {"data_import"},  # Initial state
    "data_import": {"field_mapping"},
    "field_mapping": {"data_cleansing"},
    "data_cleansing": {"asset_inventory"},
    "asset_inventory": {"dependency_analysis"},
    "dependency_analysis": {"tech_debt_assessment"},
    "tech_debt_assessment": set(),  # Terminal state
}


@dataclass
class PhaseTransitionResult:
    """Result of a phase transition operation."""

    success: bool
    was_idempotent: bool
    prior_phase: Optional[str]
    warnings: List[str]

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the result."""
        self.warnings.append(warning)


def is_valid_transition(from_phase: Optional[str], to_phase: str) -> bool:
    """
    Validate phase transition using state machine.

    Args:
        from_phase: Current phase (None for initial state)
        to_phase: Target phase

    Returns:
        True if transition is valid
    """
    valid_next_phases = VALID_PHASE_TRANSITIONS.get(from_phase, set())
    return to_phase in valid_next_phases
