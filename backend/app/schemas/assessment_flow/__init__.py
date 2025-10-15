"""
Assessment Flow Pydantic schemas for API request/response validation.

This module provides backward-compatible imports after modularization
to maintain existing import paths across the codebase.

Original file (assessment_flow.py) was 572 lines and exceeded the
400-line limit. Split into logical modules on 2025-10-15.
"""

# Base data models (October 2025 refactor)
from .base import (
    ApplicationAssetGroup,
    AssessmentApplicationInfo,
    EnrichmentStatus,
    ReadinessSummary,
)

# Request schemas
from .requests import (
    AssessmentFinalization,
    AssessmentFlowCreateRequest,
    NavigateToPhaseRequest,
    ResumeFlowRequest,
)

# Response schemas
from .responses import (
    AppOnPageData,
    AppOnPageResponse,
    AssessmentFlowResponse,
    AssessmentFlowStatusResponse,
    AssessmentReport,
)

# Architecture standards
from .standards import (
    ApplicationOverrideCreate,
    ApplicationOverrideResponse,
    ArchitectureStandardCreate,
    ArchitectureStandardResponse,
    ArchitectureStandardsUpdateRequest,
    ArchitectureStandardUpdate,
)

# Component analysis and tech debt
from .components import (
    ComponentStructure,
    ComponentUpdate,
    SixRDecision,
    SixRDecisionUpdate,
    TechDebtAnalysis,
    TechDebtItem,
    TechDebtUpdates,
)

# Event streaming
from .events import (
    AgentProgressEvent,
    AssessmentFlowEvent,
)

__all__ = [
    # Base models
    "ApplicationAssetGroup",
    "AssessmentApplicationInfo",
    "EnrichmentStatus",
    "ReadinessSummary",
    # Requests
    "AssessmentFinalization",
    "AssessmentFlowCreateRequest",
    "NavigateToPhaseRequest",
    "ResumeFlowRequest",
    # Responses
    "AppOnPageData",
    "AppOnPageResponse",
    "AssessmentFlowResponse",
    "AssessmentFlowStatusResponse",
    "AssessmentReport",
    # Standards
    "ApplicationOverrideCreate",
    "ApplicationOverrideResponse",
    "ArchitectureStandardCreate",
    "ArchitectureStandardResponse",
    "ArchitectureStandardsUpdateRequest",
    "ArchitectureStandardUpdate",
    # Components & Tech Debt
    "ComponentStructure",
    "ComponentUpdate",
    "SixRDecision",
    "SixRDecisionUpdate",
    "TechDebtAnalysis",
    "TechDebtItem",
    "TechDebtUpdates",
    # Events
    "AgentProgressEvent",
    "AssessmentFlowEvent",
]
