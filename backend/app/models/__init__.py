"""
AI Force Migration Platform - Database Models

V2 Discovery Flow Architecture:
- Uses CrewAI Flow ID as single source of truth
- Eliminates session_id confusion
- Multi-tenant isolation with context-aware repositories
- Unified flow state management
"""

# Core Models
from app.models.client_account import ClientAccount, Engagement, User

# V2 Discovery Flow Models (Primary)
from app.models.discovery_flow import DiscoveryFlow
from app.models.discovery_asset import DiscoveryAsset

# Data Import Models
from app.models.data_import.core import DataImport
from app.models.data_import_session import DataImportSession

# Assessment Models
from app.models.assessment import Assessment, WavePlan

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

# DEPRECATED MODELS (Legacy V1 - Use V2 Discovery Flow instead)
# from app.models.workflow_state import WorkflowState  # REMOVED - Use DiscoveryFlow
# from app.models.session_management import SessionManagement  # REMOVED - Use DiscoveryFlow

__all__ = [
    # Core Models
    "ClientAccount",
    "Engagement", 
    "User",
    
    # V2 Discovery Flow Models (Primary)
    "DiscoveryFlow",
    "DiscoveryAsset",
    
    # Data Import Models
    "DataImport",
    "DataImportSession",
    
    # Assessment Models
    "Assessment",
    "WavePlan",
    
    # Asset Models
    "Asset",
    "AssetDependency",
    
    # Migration Models
    "Migration",
    
    # RBAC Models
    "UserRole",
    "ClientAccess", 
    "AccessLevel",
    
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