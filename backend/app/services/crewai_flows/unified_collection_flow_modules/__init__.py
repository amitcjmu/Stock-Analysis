"""
Unified Collection Flow Package

This package contains the modularized implementation of the Collection Flow.
"""

from .flow_context import FlowContext
from .service_initializer import ServiceInitializer
from .flow_utilities import (
    requires_user_approval,
    get_available_adapters,
    get_previous_phase,
    extract_questions_from_sections,
    extract_gap_categories,
    save_questionnaires_to_db
)

# Export phase handlers
from .phase_handlers import (
    InitializationHandler,
    PlatformDetectionHandler,
    AutomatedCollectionHandler,
    GapAnalysisHandler,
    QuestionnaireGenerationHandler,
    ManualCollectionHandler,
    ValidationHandler,
    FinalizationHandler
)

__all__ = [
    # Core classes
    'FlowContext',
    'ServiceInitializer',
    
    # Utility functions
    'requires_user_approval',
    'get_available_adapters',
    'get_previous_phase',
    'extract_questions_from_sections',
    'extract_gap_categories',
    'save_questionnaires_to_db',
    
    # Phase handlers
    'InitializationHandler',
    'PlatformDetectionHandler',
    'AutomatedCollectionHandler',
    'GapAnalysisHandler',
    'QuestionnaireGenerationHandler',
    'ManualCollectionHandler',
    'ValidationHandler',
    'FinalizationHandler'
]