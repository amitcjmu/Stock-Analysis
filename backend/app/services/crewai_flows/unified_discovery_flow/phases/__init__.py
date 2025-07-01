"""
Discovery Flow Phases

This package contains individual phase implementations for the Unified Discovery Flow.
Each phase is a self-contained module that can be tested and maintained independently.
"""

from .data_validation import DataValidationPhase
from .field_mapping import FieldMappingPhase
from .data_cleansing import DataCleansingPhase
from .asset_inventory import AssetInventoryPhase
from .dependency_analysis import DependencyAnalysisPhase
from .tech_debt_assessment import TechDebtAssessmentPhase

__all__ = [
    'DataValidationPhase',
    'FieldMappingPhase', 
    'DataCleansingPhase',
    'AssetInventoryPhase',
    'DependencyAnalysisPhase',
    'TechDebtAssessmentPhase'
]