"""
Phase Managers for Collection Flow

This module exports all phase managers for the collection flow.
Each manager handles crew creation, execution, and state updates for its specific phase.
"""

from .automated_collection_manager import AutomatedCollectionManager
from .gap_analysis_manager import GapAnalysisManager
from .manual_collection_manager import ManualCollectionManager
from .platform_detection_manager import PlatformDetectionManager

__all__ = [
    "PlatformDetectionManager",
    "AutomatedCollectionManager",
    "GapAnalysisManager",
    "ManualCollectionManager",
]
