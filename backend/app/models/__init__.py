"""
AI Modernize Migration Platform - Database Models

V2 Discovery Flow Architecture:
- Uses CrewAI Flow ID as single source of truth
- Eliminates session_id confusion
- Multi-tenant isolation with context-aware repositories
- Unified flow state management
"""

# Import base models first to avoid circular dependencies
# Agent Communication Models
from app.models.agent_communication import AgentInsight, AgentQuestion, DataItem
from app.models.agent_discovered_patterns import AgentDiscoveredPatterns
from app.models.agent_performance_daily import AgentPerformanceDaily

# Agent Observability Models
from app.models.agent_task_history import AgentTaskHistory

# Collection Gaps Models (Phase 1)
from app.models.vendor_products_catalog import (
    VendorProductsCatalog,
    ProductVersionsCatalog,
    TenantVendorProducts,
    TenantProductVersions,
    LifecycleMilestones,
    AssetProductLinks,
)
from app.models.asset_resilience import (
    AssetResilience,
    AssetComplianceFlags,
    AssetVulnerabilities,
    AssetLicenses,
)
from app.models.maintenance_windows import (
    MaintenanceWindows,
    BlackoutPeriods,
)
from app.models.governance import (
    ApprovalRequests,
    MigrationExceptions,
)

# Assessment Models
from app.models.assessment import Assessment, WavePlan

# Planning Flow Models (New - Migration 112-114)
from app.models.planning import (
    PlanningFlow,
    ProjectTimeline,
    ResourceAllocation,
    ResourcePool,
    ResourceSkill,
    TimelineMilestone,
    TimelinePhase,
)

# Assessment Flow Models (New)
from app.models.assessment_flow import (
    ApplicationArchitectureOverride,
    ApplicationComponent,
    AssessmentFlow,
    AssessmentLearningFeedback,
    ComponentTreatment,
    EngagementArchitectureStandard,
    SixRDecision,
    TechDebtAnalysis,
)

# Assessment Flow State Models (New) - Temporarily disabled due to SQLAlchemy compatibility issue
# from app.models.assessment_flow_state import (
#     AssessmentFlowState,
#     SixRStrategy,
#     AssessmentPhase,
#     AssessmentFlowStatus,
#     TechDebtSeverity,
#     ComponentType,
#     OverrideType,
#     ArchitectureRequirement,
#     ApplicationArchitectureOverride as ApplicationArchitectureOverrideState,
#     ApplicationComponent as ApplicationComponentState,
#     TechDebtItem,
#     ComponentTreatment as ComponentTreatmentState,
#     SixRDecision as SixRDecisionState,
#     AssessmentLearningFeedback as AssessmentLearningFeedbackState,
#     AssessmentFlowSummary,
#     AssessmentPhaseResult,
#     AssessmentValidationResult
# )
# Asset Models
from app.models.asset import Asset, AssetDependency
from app.models.base import Base, TimestampMixin

# Core Models
from app.models.client_account import (
    ClientAccount,
    Engagement,
    User,
    UserAccountAssociation,
)
from app.models.collected_data_inventory import CollectedDataInventory
from app.models.collection_data_gap import CollectionDataGap

# Collection Flow Models (needed by ClientAccount)
from app.models.collection_flow import (
    AutomationTier,
    CollectionFlow,
    CollectionFlowStatus,
)
from app.models.collection_questionnaire_response import CollectionQuestionnaireResponse

# Decommission Flow Models (New - Issue #932)
from app.models.decommission_flow import (
    DecommissionFlow,
    DecommissionPlan,
    DataRetentionPolicy,
    ArchiveJob,
    DecommissionExecutionLog,
    DecommissionValidationCheck,
)

# Canonical Applications Models
from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
    CollectionFlowApplication,
    MatchMethod,
    VerificationSource,
)

# CrewAI Flow Models
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

# Data Import Models
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping

# Data Cleansing Models
from app.models.data_cleansing import DataCleansingRecommendation

# V2 Discovery Flow Models (Primary)
from app.models.discovery_flow import DiscoveryFlow

# Feedback Models
from app.models.feedback import Feedback

# Flow Deletion Audit Models
from app.models.flow_deletion_audit import FlowDeletionAudit

# LLM Usage Models
from app.models.llm_usage import LLMUsageLog, LLMUsageSummary

# Migration Models
from app.models.migration import Migration

# Platform Models (needed by Collection Flow)
from app.models.platform_adapter import AdapterStatus, PlatformAdapter
from app.models.platform_credentials import (
    CredentialAccessLog,
    CredentialPermission,
    CredentialRotationHistory,
    CredentialStatus,
    CredentialType,
    PlatformCredential,
)

# RBAC Models
from app.models.rbac import AccessLevel, ClientAccess, UserRole

# Security Audit Models
from app.models.security_audit import RoleChangeApproval, SecurityAuditLog

# SixR Analysis Models REMOVED - Replaced by Assessment Flow (Phase 4, Issue #840)
# from app.models.sixr_analysis import SixRAnalysis

# Tags Models
from app.models.tags import AssetTag, Tag

# User Flow Management Models
from app.models.user_active_flows import UserActiveFlow

# V3 Models REMOVED - Using consolidated schema

# DEPRECATED MODELS (Legacy V1 - Use V2 Discovery Flow instead)
# from app.models.workflow_state import WorkflowState  # REMOVED - Use DiscoveryFlow
# from app.models.session_management import SessionManagement  # REMOVED - Use DiscoveryFlow

__all__ = [
    # Base Models
    "Base",
    "TimestampMixin",
    # Core Models
    "ClientAccount",
    "Engagement",
    "User",
    # User Flow Management Models
    "UserActiveFlow",
    # V2 Discovery Flow Models (Primary)
    "DiscoveryFlow",
    # Data Import Models
    "DataImport",
    "RawImportRecord",
    "ImportFieldMapping",
    # Data Cleansing Models
    "DataCleansingRecommendation",
    # Assessment Models
    "Assessment",
    "WavePlan",
    # Planning Flow Models
    "PlanningFlow",
    "ProjectTimeline",
    "TimelinePhase",
    "TimelineMilestone",
    "ResourcePool",
    "ResourceAllocation",
    "ResourceSkill",
    # Assessment Flow Models (SQLAlchemy)
    "AssessmentFlow",
    "EngagementArchitectureStandard",
    "ApplicationArchitectureOverride",
    "ApplicationComponent",
    "TechDebtAnalysis",
    "ComponentTreatment",
    "SixRDecision",
    "AssessmentLearningFeedback",
    # Assessment Flow State Models (Pydantic) - Temporarily disabled
    # "AssessmentFlowState",
    # "SixRStrategy",
    # "AssessmentPhase",
    # "AssessmentFlowStatus",
    # "TechDebtSeverity",
    # "ComponentType",
    # "OverrideType",
    # "ArchitectureRequirement",
    # "ApplicationArchitectureOverrideState",
    # "ApplicationComponentState",
    # "TechDebtItem",
    # "ComponentTreatmentState",
    # "SixRDecisionState",
    # "AssessmentLearningFeedbackState",
    # "AssessmentFlowSummary",
    # "AssessmentPhaseResult",
    # "AssessmentValidationResult",
    # Asset Models
    "Asset",
    "AssetDependency",
    # Migration Models
    "Migration",
    # RBAC Models
    "UserRole",
    "ClientAccess",
    "AccessLevel",
    "UserAccountAssociation",
    # Agent Communication Models
    "AgentQuestion",
    "DataItem",
    "AgentInsight",
    # CrewAI Flow Models
    "CrewAIFlowStateExtensions",
    # Flow Deletion Audit Models
    "FlowDeletionAudit",
    # Feedback Models
    "Feedback",
    # Security Audit Models
    "SecurityAuditLog",
    "RoleChangeApproval",
    # Tags Models
    "Tag",
    "AssetTag",
    # LLM Usage Models
    "LLMUsageLog",
    "LLMUsageSummary",
    # SixR Analysis Models REMOVED - Replaced by Assessment Flow (Phase 4, Issue #840)
    # "SixRAnalysis",
    # Collection Flow Models
    "CollectionFlow",
    "AutomationTier",
    "CollectionFlowStatus",
    "CollectedDataInventory",
    "CollectionDataGap",
    "CollectionQuestionnaireResponse",
    # Decommission Flow Models
    "DecommissionFlow",
    "DecommissionPlan",
    "DataRetentionPolicy",
    "ArchiveJob",
    "DecommissionExecutionLog",
    "DecommissionValidationCheck",
    # Canonical Applications Models
    "CanonicalApplication",
    "ApplicationNameVariant",
    "CollectionFlowApplication",
    "MatchMethod",
    "VerificationSource",
    # Platform Models
    "PlatformAdapter",
    "AdapterStatus",
    "PlatformCredential",
    "CredentialAccessLog",
    "CredentialRotationHistory",
    "CredentialPermission",
    "CredentialStatus",
    "CredentialType",
    # Agent Observability Models
    "AgentTaskHistory",
    "AgentPerformanceDaily",
    "AgentDiscoveredPatterns",
    # Collection Gaps Models (Phase 1)
    "VendorProductsCatalog",
    "ProductVersionsCatalog",
    "TenantVendorProducts",
    "TenantProductVersions",
    "LifecycleMilestones",
    "AssetProductLinks",
    "AssetResilience",
    "AssetComplianceFlags",
    "AssetVulnerabilities",
    "AssetLicenses",
    "MaintenanceWindows",
    "BlackoutPeriods",
    "ApprovalRequests",
    "MigrationExceptions",
]
