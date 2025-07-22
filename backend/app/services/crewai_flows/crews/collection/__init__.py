"""
Collection Flow Crews
ADCS: CrewAI crews for Collection flow phases
"""

from .automated_collection_crew import create_automated_collection_crew
from .data_synthesis_crew import create_data_synthesis_crew
from .gap_analysis_crew import create_gap_analysis_crew
from .manual_collection_crew import create_manual_collection_crew
from .platform_detection_crew import create_platform_detection_crew

__all__ = [
    "create_platform_detection_crew",
    "create_automated_collection_crew", 
    "create_gap_analysis_crew",
    "create_manual_collection_crew",
    "create_data_synthesis_crew"
]