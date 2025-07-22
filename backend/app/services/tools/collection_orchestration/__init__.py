"""
Collection Orchestration Tools - Modular Structure

This package provides modular tools for automated data collection orchestration.
Generated with CC for modular backend architecture.
"""

# Core tool classes
from .adapter_manager import PlatformAdapterManager
from .base import BaseCollectionTool
from .error_recovery import ErrorRecoveryManager
from .progress_monitor import ProgressMonitor
from .quality_validator import QualityValidator
from .strategy_planner import CollectionStrategyPlanner

__all__ = [
    'BaseCollectionTool',
    'PlatformAdapterManager',
    'CollectionStrategyPlanner', 
    'ProgressMonitor',
    'QualityValidator',
    'ErrorRecoveryManager'
]