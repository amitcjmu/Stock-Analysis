"""
CMDB Asset models for multi-tenant asset management.
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean, ForeignKey, Float
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = Float = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import enum
import uuid

try:
    from app.core.database import Base
except ImportError:
    Base = object


class AssetType(str, enum.Enum):
    """Asset type enumeration based on Azure Migrate metadata."""
    # Core Infrastructure
    SERVER = "server"
    DATABASE = "database"
    APPLICATION = "application"
    
    # Network Devices
    NETWORK = "network"
    LOAD_BALANCER = "load_balancer"
    
    # Storage Devices
    STORAGE = "storage"
    
    # Security Devices
    SECURITY_GROUP = "security_group"
    
    # Virtualization
    VIRTUAL_MACHINE = "virtual_machine"
    CONTAINER = "container"
    
    # Other/Unknown
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    """Asset discovery and migration status."""
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategy(str, enum.Enum):
    """6R migration strategy based on AWS/Azure/GCP recommendations."""
    REHOST = "rehost"          # Lift and shift
    REPLATFORM = "replatform"  # Lift, tinker, and shift
    REFACTOR = "refactor"      # Re-architect
    REARCHITECT = "rearchitect" # Rebuild
    REPLACE = "replace"        # Replace with SaaS or cloud-native
    REPURCHASE = "repurchase"  # Drop and shop
    RETIRE = "retire"          # Decommission
    RETAIN = "retain"          # Keep as-is


class Asset(Base):
    """Unified Asset model with multi-tenant support and Azure Migrate compatibility."""
    
    __tablename__ = "assets"
    
    # Primary Key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Session tracking (Task 1.1.5)
    session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id', ondelete='CASCADE'), nullable=True, index=True)
    migration_id = Column(PostgresUUID(as_uuid=True), ForeignKey('migrations.id'), nullable=True)
    
    # Master Flow Coordination (Phase 2)
    master_flow_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    discovery_flow_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    assessment_flow_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    planning_flow_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    execution_flow_id = Column(PostgresUUID(as_uuid=True), nullable=True, index=True)
    
    # Multi-Phase Tracking (Phase 2)
    source_phase = Column(String(50), default='discovery', index=True)
    current_phase = Column(String(50), default='discovery', index=True)
    phase_context = Column(JSON, default=dict)
    
    # Basic asset information (based on Azure Migrate metadata)
    name = Column(String(255), nullable=False, index=True)
    asset_name = Column(String(255), nullable=True)
    hostname = Column(String(255), index=True)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    description = Column(Text)
    
    # Network information
    ip_address = Column(String(45))  # Supports IPv6
    fqdn = Column(String(255))
    mac_address = Column(String(17))
    
    # Location and environment
    environment = Column(String(50), index=True)  # Production, Development, Test, etc.
    location = Column(String(100))
    datacenter = Column(String(100))
    rack_location = Column(String(50))
    availability_zone = Column(String(50))
    
    # Technical specifications (from Azure Migrate)
    operating_system = Column(String(100))
    os_version = Column(String(50))
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    
    # Business information
    business_owner = Column(String(255))
    technical_owner = Column(String(255))
    department = Column(String(100))
    application_name = Column(String(255))
    technology_stack = Column(String(255))
    criticality = Column(String(20))  # Low, Medium, High, Critical
    business_criticality = Column(String(20))  # Business criticality label (low, medium, high, critical)
    custom_attributes = Column(JSON)  # Arbitrary custom attributes captured during import
    
    # Migration assessment
    six_r_strategy = Column(Enum(SixRStrategy))
    mapping_status = Column(String(20), index=True)  # pending, in_progress, completed
    migration_priority = Column(Integer, default=5)  # 1-10 scale
    migration_complexity = Column(String(20))  # Low, Medium, High
    migration_wave = Column(Integer)
    sixr_ready = Column(String(50)) # e.g., 'Ready', 'Needs Analysis', 'Not Applicable'

    # Status and ownership
    status = Column(String(50), default='active', index=True) # Operational status
    migration_status = Column(Enum(AssetStatus), default=AssetStatus.DISCOVERED, index=True)
    
    # Dependencies and relationships
    dependencies = Column(JSON)  # List of dependent asset IDs or names
    related_assets = Column(JSON)  # Related CI items
    
    # Discovery metadata
    discovery_method = Column(String(50))  # network_scan, agent, manual, import
    discovery_source = Column(String(100))  # Tool or system that discovered the asset
    discovery_timestamp = Column(DateTime(timezone=True))
    
    # Performance and utilization (from Azure Migrate)
    cpu_utilization_percent = Column(Float)
    memory_utilization_percent = Column(Float)
    disk_iops = Column(Float)
    network_throughput_mbps = Column(Float)
    
    # Data quality metrics
    completeness_score = Column(Float)
    quality_score = Column(Float)
    
    # Cost information
    current_monthly_cost = Column(Float)
    estimated_cloud_cost = Column(Float)
    
    # Import and processing metadata
    imported_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    imported_at = Column(DateTime(timezone=True))
    source_filename = Column(String(255))
    raw_data = Column(JSON)  # Original imported data
    field_mappings_used = Column(JSON)  # Field mappings applied during import
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    updated_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    client_account = relationship("ClientAccount")
    migration = relationship("Migration", back_populates="assets")
    engagement = relationship("Engagement", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.asset_type}', is_mock={self.is_mock})>"
    
    @property
    def is_migrated(self) -> bool:
        """Check if asset has been successfully migrated."""
        return self.status == AssetStatus.MIGRATED
    
    @property
    def has_dependencies(self) -> bool:
        """Check if asset has dependencies."""
        return bool(self.dependencies and len(self.dependencies) > 0)
    
    def get_migration_readiness_score(self) -> float:
        """Calculate migration readiness score based on various factors."""
        score = 100.0
        
        # Reduce score based on complexity
        complexity_penalties = {"high": 30, "medium": 15, "low": 5}
        if self.migration_complexity and self.migration_complexity.lower() in complexity_penalties:
            score -= complexity_penalties[self.migration_complexity.lower()]
        
        # Reduce score based on dependencies
        if self.has_dependencies:
            score -= 10
        
        # Reduce score if no 6R strategy assigned
        if not self.six_r_strategy:
            score -= 20
        
        # Reduce score for unknown asset types
        if self.asset_type == AssetType.OTHER:
            score -= 25
        
        return max(0.0, min(100.0, score))


class AssetDependency(Base):
    """Defines the relationship between two assets."""
    __tablename__ = 'asset_dependencies'
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(PostgresUUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    depends_on_asset_id = Column(PostgresUUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    dependency_type = Column(String(50), nullable=False)  # e.g., 'database', 'application', 'storage'
    description = Column(Text)
    is_mock = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    asset = relationship("Asset", foreign_keys=[asset_id])
    depends_on = relationship("Asset", foreign_keys=[depends_on_asset_id])

class WorkflowProgress(Base):
    """Tracks the workflow progress of an asset through different stages."""
    __tablename__ = 'workflow_progress'
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(PostgresUUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), nullable=False)
    stage = Column(String(50), nullable=False)  # e.g., 'Discovery', 'Assessment', 'Migration'
    status = Column(String(50), nullable=False)  # e.g., 'Not Started', 'In Progress', 'Completed'
    notes = Column(Text)
    is_mock = Column(Boolean, default=False, nullable=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    asset = relationship("Asset")

class CMDBSixRAnalysis(Base):
    """6R Analysis results for CMDB assets."""
    
    __tablename__ = "cmdb_sixr_analyses"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Analysis metadata
    analysis_name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='in_progress', index=True)
    
    # Analysis results
    total_assets = Column(Integer, default=0)
    rehost_count = Column(Integer, default=0)
    replatform_count = Column(Integer, default=0)
    refactor_count = Column(Integer, default=0)
    rearchitect_count = Column(Integer, default=0)
    retire_count = Column(Integer, default=0)
    retain_count = Column(Integer, default=0)
    
    # Cost estimates
    total_current_cost = Column(Float)
    total_estimated_cost = Column(Float)
    potential_savings = Column(Float)
    
    # Analysis details
    analysis_results = Column(JSON)  # Detailed results per asset
    recommendations = Column(JSON)  # Overall recommendations
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f"<CMDBSixRAnalysis(id={self.id}, name='{self.analysis_name}', total_assets={self.total_assets}, is_mock={self.is_mock})>"


class MigrationWave(Base):
    """Migration wave planning for phased migrations."""
    
    __tablename__ = "migration_waves"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant isolation
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Wave information
    wave_number = Column(Integer, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='planned', index=True)
    
    # Timeline
    planned_start_date = Column(DateTime(timezone=True))
    planned_end_date = Column(DateTime(timezone=True))
    actual_start_date = Column(DateTime(timezone=True))
    actual_end_date = Column(DateTime(timezone=True))
    
    # Wave details
    total_assets = Column(Integer, default=0)
    completed_assets = Column(Integer, default=0)
    failed_assets = Column(Integer, default=0)
    
    # Cost and effort
    estimated_cost = Column(Float)
    actual_cost = Column(Float)
    estimated_effort_hours = Column(Float)
    actual_effort_hours = Column(Float)
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f"<MigrationWave(id={self.id}, wave_number={self.wave_number}, name='{self.name}', is_mock={self.is_mock})>" 