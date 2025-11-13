"""
Collection Flow Phase Configurations

Modular phase configurations for the Collection Flow to maintain
clean separation of concerns and reduce file complexity.
"""

from .asset_selection_phase import get_asset_selection_phase
from .auto_enrichment_phase import (
    get_auto_enrichment_phase,
)  # NEW: Phase 2 enrichment timing fix
from .gap_analysis_phase import get_gap_analysis_phase
from .questionnaire_generation_phase import get_questionnaire_generation_phase
from .manual_collection_phase import get_manual_collection_phase
from .synthesis_phase import get_synthesis_phase

__all__ = [
    "get_asset_selection_phase",
    "get_auto_enrichment_phase",  # NEW: Phase 2 enrichment timing fix
    "get_gap_analysis_phase",
    "get_questionnaire_generation_phase",
    "get_manual_collection_phase",
    "get_synthesis_phase",
]
