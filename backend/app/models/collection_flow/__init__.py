"""
Collection Flow Model

This model represents the Collection Flow entity for the Adaptive Data Collection System.
This module has been modularized to improve maintainability while preserving
backward compatibility. All public APIs remain the same.
"""

# Import all SQLAlchemy models
from .models import (
    CollectionFlow,
    CollectionGapAnalysis,
    AdaptiveQuestionnaire,
)

# Import enums and schemas
from .schemas import (
    AutomationTier,
    CollectionFlowStatus,
    CollectionPhase,
    CollectionStatus,
    PlatformType,
    DataDomain,
    CollectionFlowState,
)

# Import validators and exceptions
from .validators import (
    CollectionFlowError,
)

# Maintain backward compatibility - export all public classes
__all__ = [
    # SQLAlchemy models
    "CollectionFlow",
    "CollectionGapAnalysis",
    "AdaptiveQuestionnaire",
    # Enums
    "AutomationTier",
    "CollectionFlowStatus",
    "CollectionPhase",
    "CollectionStatus",
    "PlatformType",
    "DataDomain",
    # State management
    "CollectionFlowState",
    # Validation
    "CollectionFlowError",
]
