"""
Asset models for infrastructure discovery and inventory management.
Comprehensive Asset Inventory Model for Migration Assessment
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean, ForeignKey, Float
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = Float = UUID = object
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
    """Asset type enumeration."""
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
    """Asset migration status enumeration."""
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategy(str, enum.Enum):
    """6R migration strategy enumeration."""
    REHOST = "rehost"          # Lift and shift
    REPLATFORM = "replatform"  # Lift, tinker, and shift
    REFACTOR = "refactor"      # Re-architect
    REARCHITECT = "rearchitect" # Rebuild
    RETIRE = "retire"          # Decommission
    RETAIN = "retain"          # Keep as-is


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
    Stores all discovered attributes, workflow progress, and migration intelligence.
    """
    
    __tablename__ = "assets"
    
    # Primary identification
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(255), unique=True, nullable=True, index=True)
    migration_id = Column(Integer, ForeignKey("migrations.id"), nullable=True)
    
    # Multi-tenant support
    client_account_id = Column(UUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Core Asset Information
    name = Column(String(255), nullable=False, index=True)
    asset_name = Column(String(255), nullable=True, index=True)  # For persistence compatibility
    hostname = Column(String(255), nullable=True, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    intelligent_asset_type = Column(String(100), nullable=True, index=True)  # AI-enhanced classification
    description = Column(Text)
    
    # Infrastructure Details
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    fqdn = Column(String(255))
    operating_system = Column(String(255), nullable=True)
    os_version = Column(String(100), nullable=True)
    hardware_type = Column(String(100), nullable=True)
    
    # Migration Critical Attributes (20+ fields)
    environment = Column(String(50), nullable=True, index=True)  # Production, Development, Test
    business_owner = Column(String(255), nullable=True)
    technical_owner = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    business_criticality = Column(String(50), nullable=True, index=True)  # Critical, High, Medium, Low
    
    # Location and environment (preserved from original)
    datacenter = Column(String(100))
    rack_location = Column(String(50))
    availability_zone = Column(String(50))
    
    # Application Specific
    application_id = Column(String(255), nullable=True, index=True)
    application_version = Column(String(100), nullable=True)
    programming_language = Column(String(100), nullable=True)
    framework = Column(String(100), nullable=True)
    database_type = Column(String(100), nullable=True)
    
    # Technical specifications (enhanced)
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    network_interfaces = Column(JSON)  # Network interface details
    
    # Cloud Readiness Assessment
    cloud_readiness_score = Column(Float, nullable=True)
    modernization_complexity = Column(String(50), nullable=True)  # Low, Medium, High, Complex
    tech_debt_score = Column(Float, nullable=True)
    compliance_requirements = Column(Text, nullable=True)
    
    # Dependencies (enhanced)
    dependencies = Column(JSON)  # List of dependent asset IDs
    dependents = Column(JSON)    # List of assets that depend on this one
    server_dependencies = Column(JSON, nullable=True)  # List of dependent servers
    application_dependencies = Column(JSON, nullable=True)  # List of dependent applications
    database_dependencies = Column(JSON, nullable=True)  # List of dependent databases
    network_dependencies = Column(JSON, nullable=True)  # Network requirements
    
    # Financial Information
    current_monthly_cost = Column(Float)
    estimated_cloud_cost = Column(Float)
    cost_optimization_potential = Column(Float)
    estimated_monthly_cost = Column(Float, nullable=True)
    license_cost = Column(Float, nullable=True)
    support_cost = Column(Float, nullable=True)
    
    # Security & Compliance
    security_classification = Column(String(50), nullable=True)
    compliance_frameworks = Column(JSON, nullable=True)  # List of compliance requirements
    vulnerability_score = Column(Float, nullable=True)
    security_findings = Column(JSON)    # Security vulnerabilities and issues
    
    # Migration details (enhanced)
    status = Column(Enum(AssetStatus), default=AssetStatus.DISCOVERED)
    six_r_strategy = Column(Enum(SixRStrategy))
    sixr_ready = Column(String(50), nullable=True)  # For persistence compatibility
    migration_priority = Column(String(50), nullable=True)  # High, Medium, Low
    migration_complexity = Column(String(50), nullable=True)  # Simple, Medium, Complex
    estimated_migration_effort = Column(String(100), nullable=True)  # Person-days
    migration_wave = Column(Integer)  # Migration batch number
    
    # 6R Strategy Assessment
    recommended_6r_strategy = Column(String(50), nullable=True)  # Rehost, Replatform, etc.
    strategy_confidence = Column(Float, nullable=True)  # 0.0 to 1.0
    strategy_rationale = Column(Text, nullable=True)
    
    # Workflow Status Tracking
    discovery_status = Column(String(50), default='discovered', index=True)  # discovered, mapped, cleaned, validated
    mapping_status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, failed
    cleanup_status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, failed
    assessment_readiness = Column(String(50), default='not_ready', index=True)  # not_ready, partial, ready
    
    # Data Quality Metrics
    completeness_score = Column(Float, nullable=True)  # Percentage of required fields filled
    quality_score = Column(Float, nullable=True)  # Overall data quality score
    missing_critical_fields = Column(JSON, nullable=True)  # List of missing required fields
    data_quality_issues = Column(JSON, nullable=True)  # List of identified issues
    
    # Assessment data (enhanced)
    risk_score = Column(Float)  # 0-100 risk assessment score
    performance_metrics = Column(JSON)  # CPU, memory, disk, network utilization
    compatibility_issues = Column(JSON) # Cloud compatibility problems
    
    # AI insights (enhanced)
    ai_recommendations = Column(JSON)  # AI-generated migration recommendations
    confidence_score = Column(Float)   # AI confidence in recommendations (0-1)
    ai_analysis_result = Column(JSON, nullable=True)  # AI agent analysis results
    ai_confidence_score = Column(Float, nullable=True)  # AI confidence in analysis
    last_ai_analysis = Column(DateTime, nullable=True)  # When AI last analyzed this asset
    
    # Discovery metadata (enhanced)
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_scanned = Column(DateTime(timezone=True))
    discovery_method = Column(String(50))  # e.g., "network_scan", "agent", "manual"
    discovery_source = Column(String(100))  # Tool or system that discovered the asset
    
    # Source Information
    source_system = Column(String(100), nullable=True)  # CMDB, Discovery Tool, Manual
    source_file = Column(String(255), nullable=True)  # Original import file
    import_batch_id = Column(String(255), nullable=True, index=True)  # Batch import tracking
    
    # Custom Attributes (Organization-specific)
    custom_attributes = Column(JSON, nullable=True)  # Flexible custom field storage
    
    # Audit Trail
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    
    # Relationships
    migration = relationship("Migration", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}', status='{self.status}')>"
    
    @property
    def is_migrated(self) -> bool:
        """Check if asset has been successfully migrated."""
        return self.status == AssetStatus.MIGRATED
    
    @property
    def has_dependencies(self) -> bool:
        """Check if asset has dependencies."""
        return bool(self.dependencies and len(self.dependencies) > 0)
    
    @property
    def has_dependents(self) -> bool:
        """Check if other assets depend on this one."""
        return bool(self.dependents and len(self.dependents) > 0)
    
    def get_migration_readiness_score(self) -> float:
        """Calculate migration readiness score based on various factors."""
        score = 100.0
        
        # Reduce score based on risk
        if self.risk_score:
            score -= (self.risk_score * 0.3)
        
        # Reduce score based on complexity
        complexity_penalties = {"high": 30, "medium": 15, "low": 5}
        if self.migration_complexity in complexity_penalties:
            score -= complexity_penalties[self.migration_complexity]
        
        # Reduce score based on dependencies
        if self.has_dependencies:
            score -= 10
        
        # Reduce score if no 6R strategy assigned
        if not self.six_r_strategy:
            score -= 20
        
        return max(0.0, min(100.0, score))


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

# Add workflow_progress relationship to Asset
Asset.workflow_progress = relationship("WorkflowProgress", back_populates="asset") 