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

# Canonical Applications Models
from app.models.canonical_applications import (
    CanonicalApplication,
    ApplicationNameVariant,
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

# Stock Analysis Models
from app.models.stock import Stock, StockAnalysis
from app.models.watchlist import Watchlist

# User Flow Management Models
from app.models.user_active_flows import UserActiveFlow

# V3 Models REMOVED - Using consolidated schema

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
    # Canonical Applications Models
    "CanonicalApplication",
    "ApplicationNameVariant",
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
    # Stock Analysis Models
    "Stock",
    "StockAnalysis",
    "Watchlist",
]
