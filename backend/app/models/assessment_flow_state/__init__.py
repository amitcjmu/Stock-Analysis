"""
Assessment Flow State Models - Public API
Maintains backward compatibility by re-exporting all public models from modular structure.
"""

# Enums
from .enums import (
    AssessmentFlowStatus,
    AssessmentPhase,
    ComponentType,
    OverrideType,
    TechDebtSeverity,
)

# Import SixRStrategy from canonical location (app.models.asset.enums)
from app.models.asset.enums import SixRStrategy

# Architecture Models
from .architecture_models import (
    ApplicationArchitectureOverride,
    ArchitectureRequirement,
)

# Component Models
from .component_models import (
    ApplicationComponent,
    ComponentTreatment,
    TechDebtItem,
)

# Decision Models
from .decision_models import (
    AssessmentLearningFeedback,
    SixRDecision,
)

# Flow State Models
from .flow_state_models import (
    AssessmentFlowState,
    AssessmentFlowSummary,
    AssessmentPhaseResult,
    AssessmentValidationResult,
)

# Public API - maintain exact same exports as original file
__all__ = [
    # Enums
    "SixRStrategy",
    "AssessmentPhase",
    "AssessmentFlowStatus",
    "TechDebtSeverity",
    "ComponentType",
    "OverrideType",
    # Architecture Models
    "ArchitectureRequirement",
    "ApplicationArchitectureOverride",
    # Component Models
    "ApplicationComponent",
    "TechDebtItem",
    "ComponentTreatment",
    # Decision Models
    "SixRDecision",
    "AssessmentLearningFeedback",
    # Flow State Models
    "AssessmentFlowState",
    "AssessmentFlowSummary",
    "AssessmentPhaseResult",
    "AssessmentValidationResult",
]
