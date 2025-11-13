"""
Base constants, data classes, and validation for phase persistence.

Contains shared constants, data structures, and validation logic
used across the phase persistence system.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

# API phase names to database phase names mapping (SINGLE SOURCE OF TRUTH)
# Used when reading phases_completed from FlowHandler (Issue #557 fix)
# Per ADR-027: Discovery v3.0.0 has only 5 phases
API_TO_DB_PHASE_MAP = {
    "data_import": "data_import",
    "data_validation": "data_validation",
    "attribute_mapping": "field_mapping",
    "data_cleansing": "data_cleansing",
    "inventory": "asset_inventory",
}

# Reverse mapping: Database phase names to API phase names
# Used to convert current_phase from DB format to API format
DB_TO_API_PHASE_MAP = {v: k for k, v in API_TO_DB_PHASE_MAP.items()}

# Phase flag mapping for completion tracking
# Derived from API_TO_DB_PHASE_MAP to avoid duplication
PHASE_FLAG_MAP = {
    db_phase: f"{db_phase}_completed" for db_phase in set(API_TO_DB_PHASE_MAP.values())
}

# Valid phase transitions - defines the state machine
# Per ADR-027: Discovery v3.0.0 has 5 phases
# (data_import, data_validation, field_mapping, data_cleansing, asset_inventory)
VALID_PHASE_TRANSITIONS = {
    None: {"data_import"},  # Initial state
    "data_import": {"data_validation"},
    "data_validation": {"field_mapping"},
    "field_mapping": {"data_cleansing"},
    "data_cleansing": {"asset_inventory"},
    "asset_inventory": set(),  # Terminal state - Discovery v3.0.0 ends here
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
