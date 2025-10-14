"""
Assessment Flow Models Package

This package provides a complete set of models for the assessment flow system,
organized by functionality for better maintainability and code organization.

Modules:
- enums_and_exceptions: Shared enums and exceptions
- in_memory_models: In-memory state models for CrewAI integration
- core_models: Primary database models (AssessmentFlow, EngagementArchitectureStandard)
- component_models: Component-related models (ApplicationComponent, etc.)
- analysis_models: Analysis models (TechDebtAnalysis, SixRDecision, etc.)
"""

# Import canonical AssessmentPhase from assessment_flow_state
from app.models.assessment_flow_state import AssessmentPhase

# Import all other enums and exceptions
from .enums_and_exceptions import (
    AssessmentFlowStatus,
    AssessmentStatus,
    ArchitectureRequirementType,
    ComponentType,
    TechDebtSeverity,
    AssessmentFlowError,
    CrewExecutionError,
)

# Import in-memory models
from .in_memory_models import (
    InMemorySixRDecision,
    AssessmentFlowState,
)

# Import core database models
from .core_models import (
    AssessmentFlow,
    EngagementArchitectureStandard,
)

# Import component models
from .component_models import (
    ApplicationArchitectureOverride,
    ApplicationComponent,
    ComponentTreatment,
)

# Import analysis models
from .analysis_models import (
    TechDebtAnalysis,
    SixRDecision,
    AssessmentLearningFeedback,
)

# Export all classes for easy import
__all__ = [
    # Enums and exceptions
    "AssessmentFlowStatus",
    "AssessmentPhase",
    "AssessmentStatus",
    "ArchitectureRequirementType",
    "ComponentType",
    "TechDebtSeverity",
    "AssessmentFlowError",
    "CrewExecutionError",
    # In-memory models
    "InMemorySixRDecision",
    "AssessmentFlowState",
    # Core database models
    "AssessmentFlow",
    "EngagementArchitectureStandard",
    # Component models
    "ApplicationArchitectureOverride",
    "ApplicationComponent",
    "ComponentTreatment",
    # Analysis models
    "TechDebtAnalysis",
    "SixRDecision",
    "AssessmentLearningFeedback",
]
