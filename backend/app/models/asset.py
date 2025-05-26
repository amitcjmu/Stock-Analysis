"""
Asset models for infrastructure discovery and inventory management.
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean, ForeignKey, Float
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = Float = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import enum

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


class Asset(Base):
    """Infrastructure asset model."""
    
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(Integer, ForeignKey("migrations.id"), nullable=False)
    
    # Basic asset information
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(Enum(AssetType), nullable=False)
    description = Column(Text)
    
    # Asset identification
    hostname = Column(String(255))
    ip_address = Column(String(45))  # Supports IPv6
    fqdn = Column(String(255))
    asset_id = Column(String(100))  # External system ID
    
    # Location and environment
    environment = Column(String(50))  # e.g., "production", "staging", "development"
    datacenter = Column(String(100))
    rack_location = Column(String(50))
    availability_zone = Column(String(50))
    
    # Technical specifications
    operating_system = Column(String(100))
    os_version = Column(String(50))
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)
    network_interfaces = Column(JSON)  # Network interface details
    
    # Migration details
    status = Column(Enum(AssetStatus), default=AssetStatus.DISCOVERED)
    six_r_strategy = Column(Enum(SixRStrategy))
    migration_priority = Column(Integer, default=5)  # 1-10 scale
    migration_complexity = Column(String(20))  # "low", "medium", "high"
    migration_wave = Column(Integer)  # Migration batch number
    
    # Dependencies
    dependencies = Column(JSON)  # List of dependent asset IDs
    dependents = Column(JSON)    # List of assets that depend on this one
    
    # Discovery metadata
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_scanned = Column(DateTime(timezone=True))
    discovery_method = Column(String(50))  # e.g., "network_scan", "agent", "manual"
    discovery_source = Column(String(100))  # Tool or system that discovered the asset
    
    # Assessment data
    risk_score = Column(Float)  # 0-100 risk assessment score
    business_criticality = Column(String(20))  # "low", "medium", "high", "critical"
    compliance_requirements = Column(JSON)  # Compliance and regulatory requirements
    
    # Cost and sizing
    current_monthly_cost = Column(Float)
    estimated_cloud_cost = Column(Float)
    cost_optimization_potential = Column(Float)
    
    # Technical assessment
    performance_metrics = Column(JSON)  # CPU, memory, disk, network utilization
    security_findings = Column(JSON)    # Security vulnerabilities and issues
    compatibility_issues = Column(JSON) # Cloud compatibility problems
    
    # AI insights
    ai_recommendations = Column(JSON)  # AI-generated migration recommendations
    confidence_score = Column(Float)   # AI confidence in recommendations (0-1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
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
    """Asset dependency relationship model."""
    
    __tablename__ = "asset_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    source_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    target_asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    
    # Dependency details
    dependency_type = Column(String(50))  # e.g., "network", "database", "application"
    description = Column(Text)
    criticality = Column(String(20))  # "low", "medium", "high", "critical"
    
    # Discovery metadata
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    discovery_method = Column(String(50))
    confidence_level = Column(Float)  # 0-1 confidence in dependency accuracy
    
    # Relationships
    source_asset = relationship("Asset", foreign_keys=[source_asset_id])
    target_asset = relationship("Asset", foreign_keys=[target_asset_id])
    
    def __repr__(self):
        return f"<AssetDependency(source={self.source_asset_id}, target={self.target_asset_id}, type='{self.dependency_type}')>" 