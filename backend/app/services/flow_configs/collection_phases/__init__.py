"""
Collection Flow Phase Configurations

Modular phase configurations for the Collection Flow to maintain
clean separation of concerns and reduce file complexity.
"""

from .platform_detection_phase import get_platform_detection_phase
from .automated_collection_phase import get_automated_collection_phase
from .gap_analysis_phase import get_gap_analysis_phase
from .questionnaire_generation_phase import get_questionnaire_generation_phase
from .manual_collection_phase import get_manual_collection_phase
from .synthesis_phase import get_synthesis_phase

__all__ = [
    "get_platform_detection_phase",
    "get_automated_collection_phase",
    "get_gap_analysis_phase",
    "get_questionnaire_generation_phase",
    "get_manual_collection_phase",
    "get_synthesis_phase",
]
