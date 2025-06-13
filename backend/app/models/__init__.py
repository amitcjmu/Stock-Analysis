"""
Models package initialization.
Imports all models to ensure they are registered with SQLAlchemy.
"""

from .migration import Migration, MigrationLog, MigrationStatus, MigrationPhase
from .asset import Asset, AssetDependency, AssetType, AssetStatus, SixRStrategy, MigrationWave, WorkflowProgress
from .assessment import Assessment, WavePlan, AssessmentType, AssessmentStatus, RiskLevel
from .sixr_analysis import (
    SixRIteration, SixRRecommendation,
    SixRQuestion, SixRQuestionResponse, SixRAnalysis, SixRAnalysisParameters
)

# New multi-tenant models (primary imports)
try:
    from .client_account import ClientAccount, Engagement, User, UserAccountAssociation
    CLIENT_ACCOUNT_AVAILABLE = True
except ImportError:
    CLIENT_ACCOUNT_AVAILABLE = False
    ClientAccount = None
    Engagement = None
    User = None
    UserAccountAssociation = None

from .tags import Tag, AssetEmbedding, AssetTag
from .data_import import (
    DataImport,
    RawImportRecord,
    ImportFieldMapping,
)
from .data_import_session import DataImportSession
from .feedback import Feedback, FeedbackSummary

# RBAC models (conditional import)
try:
    from .rbac import UserProfile, UserRole, ClientAccess, EngagementAccess, AccessAuditLog
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False
    UserProfile = None
    UserRole = None
    ClientAccess = None
    EngagementAccess = None
    AccessAuditLog = None

# Enhanced RBAC models (conditional import)
try:
    from .rbac_enhanced import EnhancedUserProfile, RolePermissions, SoftDeletedItems, EnhancedAccessAuditLog
    ENHANCED_RBAC_AVAILABLE = True
except ImportError:
    ENHANCED_RBAC_AVAILABLE = False
    EnhancedUserProfile = None
    RolePermissions = None
    SoftDeletedItems = None
    EnhancedAccessAuditLog = None

# LLM Usage tracking models (conditional import)
try:
    from .llm_usage import LLMUsageLog, LLMModelPricing, LLMUsageSummary
    LLM_USAGE_AVAILABLE = True
except ImportError:
    LLM_USAGE_AVAILABLE = False
    LLMUsageLog = None
    LLMModelPricing = None
    LLMUsageSummary = None

# Learning Pattern models are now part of data_import

__all__ = [
    # Migration models
    "Migration",
    "MigrationLog", 
    "MigrationStatus",
    "MigrationPhase",
    
    # Asset models
    "Asset",
    "AssetDependency",
    "AssetType", 
    "AssetStatus",
    "SixRStrategy",
    "MigrationWave",
    "WorkflowProgress",
    
    # Assessment models
    "Assessment",
    "WavePlan",
    "AssessmentType",
    "AssessmentStatus", 
    "RiskLevel",
    
    # 6R Analysis models
    "SixRAnalysis",
    "SixRAnalysisParameters",
    "SixRIteration",
    "SixRRecommendation",
    "SixRQuestion",
    "SixRQuestionResponse",
    
    # Tags and embeddings
    "Tag",
    "AssetEmbedding",
    "AssetTag",
    
    # Data Import models
    "DataImport",
    "RawImportRecord",
    "ImportFieldMapping",
    "DataImportSession",
    
    # Feedback models
    "Feedback",
    "FeedbackSummary",
]

# Add client account models only if available
if CLIENT_ACCOUNT_AVAILABLE:
    __all__.extend([
        "ClientAccount",
        "Engagement", 
        "User",
        "UserAccountAssociation"
    ])

# Add RBAC models only if available
if RBAC_AVAILABLE:
    __all__.extend([
        "UserProfile",
        "UserRole",
        "ClientAccess", 
        "EngagementAccess",
        "AccessAuditLog"
    ])

# Add Enhanced RBAC models only if available
if ENHANCED_RBAC_AVAILABLE:
    __all__.extend([
        "EnhancedUserProfile",
        "RolePermissions",
        "SoftDeletedItems",
        "EnhancedAccessAuditLog"
    ])

# Add LLM Usage models only if available
if LLM_USAGE_AVAILABLE:
    __all__.extend([
        "LLMUsageLog",
        "LLMModelPricing", 
        "LLMUsageSummary"
    ]) 