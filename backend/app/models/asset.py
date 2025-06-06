"""
Asset models for infrastructure discovery and inventory management.
Comprehensive Asset Inventory Model for Migration Assessment
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum as SQLEnum, Boolean, ForeignKey, Float
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = SQLEnum = Boolean = ForeignKey = Float = UUID = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import enum
import uuid
from datetime import datetime

try:
    from app.core.database import Base
except ImportError:
    Base = object


class AssetType(str, enum.Enum):
    """Asset type enumeration matching database assettype enum."""
    SERVER = "server"
    DATABASE = "database"
    APPLICATION = "application"
    NETWORK = "network"
    STORAGE = "storage"
    CONTAINER = "container"
    VIRTUAL_MACHINE = "virtual_machine"
    LOAD_BALANCER = "load_balancer"
    SECURITY_GROUP = "security_group"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    """Asset migration status enumeration matching database assetstatus enum."""
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategy(str, enum.Enum):
    """6R migration strategy enumeration matching database sixrstrategy enum."""
    REHOST = "rehost"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REARCHITECT = "rearchitect"
    RETIRE = "retire"
    RETAIN = "retain"


class WorkflowStatus(str, enum.Enum):
    """Workflow phase status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AssessmentReadiness(str, enum.Enum):
    """Assessment readiness status enumeration."""
    NOT_READY = "not_ready"
    PARTIAL = "partial"
    READY = "ready"


class Asset(Base):
    """
    Comprehensive asset inventory model for migration assessment.
    Aligned with actual database schema (74 columns).
    """
    
    __tablename__ = "assets"
    
    # Primary identification - matches database exactly
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(Integer, ForeignKey("migrations.id"), nullable=True)  # Made nullable for testing
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType, name='assettype'), nullable=False)
    description = Column(Text, nullable=True)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    fqdn = Column(String(255), nullable=True)
    asset_id = Column(String(100), nullable=True)
    
    # Environment and location
    environment = Column(String(50), nullable=True)
    datacenter = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)  # Added for compatibility
    rack_location = Column(String(50), nullable=True)
    availability_zone = Column(String(50), nullable=True)
    
    # Technical specifications
    operating_system = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    cpu_cores = Column(Integer, nullable=True)
    memory_gb = Column(Float, nullable=True)  # double precision
    storage_gb = Column(Float, nullable=True)  # double precision
    network_interfaces = Column(JSON, nullable=True)  # JSON field
    
    # Asset status and migration
    status = Column(SQLEnum(AssetStatus, name='assetstatus'), nullable=True)
    six_r_strategy = Column(SQLEnum(SixRStrategy, name='sixrstrategy'), nullable=True)
    migration_priority = Column(Integer, nullable=True)
    migration_complexity = Column(String(20), nullable=True)
    migration_wave = Column(Integer, nullable=True)
    
    # Dependencies - JSON fields
    dependencies = Column(JSON, nullable=True)
    dependents = Column(JSON, nullable=True)
    
    # Discovery metadata
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_scanned = Column(DateTime(timezone=True), nullable=True)
    discovery_method = Column(String(50), nullable=True)
    discovery_source = Column(String(100), nullable=True)
    
    # Risk and security
    risk_score = Column(Float, nullable=True)
    business_criticality = Column(String(20), nullable=True)
    compliance_requirements = Column(JSON, nullable=True)  # JSON field
    
    # Cost analysis  
    current_monthly_cost = Column(Float, nullable=True)
    estimated_cloud_cost = Column(Float, nullable=True)
    cost_optimization_potential = Column(Float, nullable=True)
    
    # Performance and quality
    performance_metrics = Column(JSON, nullable=True)  # JSON field
    security_findings = Column(JSON, nullable=True)    # JSON field
    compatibility_issues = Column(JSON, nullable=True) # JSON field
    
    # AI insights
    ai_recommendations = Column(JSON, nullable=True)    # JSON field
    confidence_score = Column(Float, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)  # Added for compatibility
    
    # Workflow status fields (added by migration)
    discovery_status = Column(String(50), server_default='discovered', nullable=True)
    mapping_status = Column(String(50), server_default='pending', nullable=True)
    cleanup_status = Column(String(50), server_default='pending', nullable=True)
    assessment_readiness = Column(String(50), server_default='not_ready', nullable=True)
    completeness_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    
    # Additional database fields to match schema exactly
    source_system = Column(String(100), nullable=True)
    asset_name = Column(String(255), nullable=True)
    intelligent_asset_type = Column(String(100), nullable=True)
    hardware_type = Column(String(100), nullable=True)
    business_owner = Column(String(100), nullable=True)
    technical_owner = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    application_id = Column(String(100), nullable=True)
    application_name = Column(String(255), nullable=True)  # Added for compatibility
    application_version = Column(String(50), nullable=True)
    programming_language = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    database_type = Column(String(100), nullable=True)
    technology_stack = Column(String(255), nullable=True)  # Added for compatibility
    cloud_readiness_score = Column(Float, nullable=True)
    modernization_complexity = Column(String(20), nullable=True)
    tech_debt_score = Column(Float, nullable=True)
    estimated_monthly_cost = Column(Float, nullable=True)
    license_cost = Column(Float, nullable=True)
    support_cost = Column(Float, nullable=True)
    security_classification = Column(String(50), nullable=True)
    vulnerability_score = Column(Float, nullable=True)
    sixr_ready = Column(String(20), nullable=True)
    estimated_migration_effort = Column(String(20), nullable=True)
    recommended_6r_strategy = Column(String(20), nullable=True)
    strategy_confidence = Column(Float, nullable=True)
    strategy_rationale = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)
    last_ai_analysis = Column(DateTime(timezone=True), nullable=True)
    source_file = Column(String(255), nullable=True)
    import_batch_id = Column(String(100), nullable=True)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Relationships
    migration = relationship("Migration", back_populates="assets")
    workflow_progress = relationship("WorkflowProgress", back_populates="asset")
    engagement = relationship("Engagement", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
    
    @property
    def is_migrated(self) -> bool:
        """Check if asset has been successfully migrated."""
        return self.status == AssetStatus.MIGRATED
    
    @property
    def criticality(self) -> str:
        """Alias for business_criticality for backward compatibility."""
        return self.business_criticality
    
    @property
    def has_dependencies(self) -> bool:
        """Check if asset has any dependencies."""
        return bool(self.dependencies)
    
    @property
    def has_dependents(self) -> bool:
        """Check if asset has any dependents."""
        return bool(self.dependents)
    
    def get_migration_readiness_score(self) -> float:
        """
        Calculate overall migration readiness score.
        Combines completeness, quality, and assessment readiness.
        """
        scores = []
        
        # Completeness score (0-100)
        if self.completeness_score is not None:
            scores.append(self.completeness_score)
        
        # Quality score (0-100)  
        if self.quality_score is not None:
            scores.append(self.quality_score)
            
        # Assessment readiness as score
        readiness_scores = {
            'not_ready': 0,
            'partial': 50,
            'ready': 100
        }
        if self.assessment_readiness in readiness_scores:
            scores.append(readiness_scores[self.assessment_readiness])
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'migration_id': self.migration_id,
            'name': self.name,
            'asset_type': self.asset_type.value if self.asset_type else None,
            'description': self.description,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'fqdn': self.fqdn,
            'status': self.status.value if self.status else None,
            'six_r_strategy': self.six_r_strategy.value if self.six_r_strategy else None,
            'discovery_status': self.discovery_status,
            'mapping_status': self.mapping_status,
            'cleanup_status': self.cleanup_status,
            'assessment_readiness': self.assessment_readiness,
            'completeness_score': self.completeness_score,
            'quality_score': self.quality_score,
            'migration_readiness_score': self.get_migration_readiness_score(),
            'client_account_id': str(self.client_account_id) if self.client_account_id else None,
            'engagement_id': str(self.engagement_id) if self.engagement_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AssetDependency(Base):
    """
    Asset dependency mapping for application-to-server relationships
    """
    __tablename__ = "asset_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Source and target assets
    source_asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    target_asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    
    # Dependency details
    dependency_type = Column(String(100), nullable=False)  # database, service, network, etc.
    dependency_strength = Column(String(50), nullable=True)  # Critical, Important, Optional
    port_number = Column(Integer, nullable=True)
    protocol = Column(String(50), nullable=True)
    description = Column(Text)
    criticality = Column(String(20))  # "low", "medium", "high", "critical"
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Discovery metadata
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    discovery_method = Column(String(50))
    confidence_level = Column(Float)  # 0-1 confidence in dependency accuracy
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    source_asset = relationship("Asset", foreign_keys=[source_asset_id])
    target_asset = relationship("Asset", foreign_keys=[target_asset_id])
    
    def __repr__(self):
        return f"<AssetDependency(source={self.source_asset_id}, target={self.target_asset_id}, type='{self.dependency_type}')>"


class WorkflowProgress(Base):
    """
    Track workflow progress for assets through migration phases
    """
    __tablename__ = "workflow_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey('assets.id'), nullable=False)
    
    # Workflow phases
    phase = Column(String(50), nullable=False)  # discovery, mapping, cleanup, assessment
    status = Column(String(50), nullable=False)  # pending, in_progress, completed, failed
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    
    # Details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    errors = Column(JSON, nullable=True)  # Any errors encountered
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="workflow_progress")
    
    def __repr__(self):
        return f"<WorkflowProgress(asset_id={self.asset_id}, phase='{self.phase}', status='{self.status}')>" 