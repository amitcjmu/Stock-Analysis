"""
Collection Orchestration Tools for automated data collection
Tools required by the CollectionOrchestratorAgent

MODULAR STRUCTURE:
- Platform adapter management: ./collection_orchestration/adapter_manager.py
- Strategy planning: ./collection_orchestration/strategy_planner.py
- Progress monitoring: ./collection_orchestration/progress_monitor.py
- Quality validation: ./collection_orchestration/quality_validator.py
- Error recovery: ./collection_orchestration/error_recovery.py

Generated with CC for modular backend architecture.
"""

import logging
from datetime import timedelta

# For backward compatibility - re-export all classes
from typing import Any, Dict, List, Optional

# Import modular components
from .collection_orchestration import (
    CollectionStrategyPlanner,
    ErrorRecoveryManager,
    PlatformAdapterManager,
    ProgressMonitor,
    QualityValidator,
)

logger = logging.getLogger(__name__)


# Backward compatibility: Keep existing classes available but delegate to modular components
# This allows existing imports to continue working while enabling modular structure

# All classes are now imported from the modular structure above
# Existing code can continue to use:
# from collection_orchestration_tool import PlatformAdapterManager, CollectionStrategyPlanner
# from collection_orchestration_tool import ProgressMonitor, QualityValidator, ErrorRecoveryManager

# Import timedelta for completion estimation compatibility
from datetime import timedelta