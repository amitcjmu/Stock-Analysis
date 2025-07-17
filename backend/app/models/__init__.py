"""
AI Modernize Migration Platform - Database Models

V2 Discovery Flow Architecture:
- Uses CrewAI Flow ID as single source of truth
- Eliminates session_id confusion
- Multi-tenant isolation with context-aware repositories
- Unified flow state management
"""

# Core Models
from app.models.client_account import ClientAccount, Engagement, User, UserAccountAssociation

# User Flow Management Models
from app.models.user_active_flows import UserActiveFlow

# V2 Discovery Flow Models (Primary)
from app.models.discovery_flow import DiscoveryFlow

# Data Import Models
from app.models.data_import.core import DataImport, RawImportRecord
from app.models.data_import.mapping import ImportFieldMapping

# Assessment Models
from app.models.assessment import Assessment, WavePlan

# Assessment Flow Models (New)
from app.models.assessment_flow import (
    AssessmentFlow, 
    EngagementArchitectureStandard, 
    ApplicationArchitectureOverride,
    ApplicationComponent, 
    TechDebtAnalysis, 
    ComponentTreatment, 
    SixRDecision, 
    AssessmentLearningFeedback
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

# Migration Models
from app.models.migration import Migration

# RBAC Models
from app.models.rbac import UserRole, ClientAccess, AccessLevel

# Agent Communication Models
from app.models.agent_communication import AgentQuestion, DataItem, AgentInsight

# CrewAI Flow Models
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

# Flow Deletion Audit Models
from app.models.flow_deletion_audit import FlowDeletionAudit

# Feedback Models
from app.models.feedback import Feedback

# Security Audit Models
from app.models.security_audit import SecurityAuditLog, RoleChangeApproval

# Tags Models
from app.models.tags import Tag, AssetTag

# LLM Usage Models
from app.models.llm_usage import LLMUsageLog, LLMUsageSummary

# SixR Analysis Models
from app.models.sixr_analysis import SixRAnalysis


# V3 Models REMOVED - Using consolidated schema

# DEPRECATED MODELS (Legacy V1 - Use V2 Discovery Flow instead)
# from app.models.workflow_state import WorkflowState  # REMOVED - Use DiscoveryFlow
# from app.models.session_management import SessionManagement  # REMOVED - Use DiscoveryFlow

__all__ = [
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
    
    # Assessment Models
    "Assessment",
    "WavePlan",
    
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
    
    # SixR Analysis Models
    "SixRAnalysis"
] 