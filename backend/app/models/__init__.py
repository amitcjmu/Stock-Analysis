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
from app.models.data_import import DataImport
from app.models.data_import_session import DataImportSession

# Assessment Models
from app.models.assessment import Assessment, WavePlan

# Asset Models
from app.models.asset import Asset, AssetDependency

# Migration Models
from app.models.migration import Migration

# RBAC Models
from app.models.rbac import UserRole, ClientAccess, PermissionLevel

# Agent Communication Models
from app.models.agent_communication import AgentCommunication

# CrewAI Flow Models
from app.models.crewai_flow_state_extensions import CrewAIFlowStateExtensions

# Field Mapping Models
from app.models.field_mapping import FieldMapping

# Learning Models
from app.models.learning_pattern import LearningPattern

# Tech Debt Models
from app.models.tech_debt_analysis import TechDebtAnalysis

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
    "PermissionLevel",
    
    # Agent Communication Models
    "AgentCommunication",
    
    # CrewAI Flow Models
    "CrewAIFlowStateExtensions",
    
    # Field Mapping Models
    "FieldMapping",
    
    # Learning Models
    "LearningPattern",
    
    # Tech Debt Models
    "TechDebtAnalysis"
] 