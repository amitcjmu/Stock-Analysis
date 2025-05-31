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
from .feedback import Feedback, FeedbackSummary

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