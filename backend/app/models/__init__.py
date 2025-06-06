"""
Models package initialization.
Imports all models to ensure they are registered with SQLAlchemy.
"""

from .migration import Migration, MigrationLog, MigrationStatus, MigrationPhase
from .asset import Asset, AssetDependency, AssetType as LegacyAssetType, AssetStatus as LegacyAssetStatus, SixRStrategy as LegacySixRStrategy
from .assessment import Assessment, WavePlan, AssessmentType, AssessmentStatus, RiskLevel
from .sixr_analysis import (
    SixRAnalysis as LegacySixRAnalysis, SixRParameters, SixRIteration, SixRRecommendation,
    SixRQuestion, SixRQuestionResponse
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

from .cmdb_asset import CMDBAsset, CMDBSixRAnalysis, MigrationWave, AssetType, AssetStatus, SixRStrategy
from .tags import Tag, CMDBAssetEmbedding, AssetTag
from .data_import import (
    DataImport, RawImportRecord, ImportProcessingStep, ImportFieldMapping, 
    DataQualityIssue, ImportStatus, ImportType
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

__all__ = [
    # Migration models
    "Migration",
    "MigrationLog", 
    "MigrationStatus",
    "MigrationPhase",
    
    # Legacy Asset models
    "Asset",
    "AssetDependency",
    "LegacyAssetType", 
    "LegacyAssetStatus",
    "LegacySixRStrategy",
    
    # Assessment models
    "Assessment",
    "WavePlan",
    "AssessmentType",
    "AssessmentStatus", 
    "RiskLevel",
    
    # Legacy 6R Analysis models
    "LegacySixRAnalysis",
    "SixRParameters",
    "SixRIteration",
    "SixRRecommendation",
    "SixRQuestion",
    "SixRQuestionResponse",
    
    # CMDB models (always available)
    "CMDBAsset",
    "CMDBSixRAnalysis",  # This is the new one from cmdb_asset.py
    "MigrationWave",
    "AssetType",     # This is the new one from cmdb_asset.py
    "AssetStatus",   # This is the new one from cmdb_asset.py
    "SixRStrategy",  # This is the new one from cmdb_asset.py
    
    # Tags and embeddings
    "Tag",
    "CMDBAssetEmbedding",
    "AssetTag",
    
    # Data Import models
    "DataImport",
    "RawImportRecord",
    "ImportProcessingStep",
    "ImportFieldMapping",
    "DataQualityIssue",
    "ImportStatus",
    "ImportType",
    "DataImportSession",
    
    # Feedback models
    "Feedback",
    "FeedbackSummary"
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