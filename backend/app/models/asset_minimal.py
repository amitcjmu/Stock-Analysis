"""
Minimal Asset model for testing database operations.
Only includes fields that exactly match the database schema.
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum as SQLEnum, Boolean, ForeignKey, Float
    from sqlalchemy.dialects.postgresql import UUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.types import TypeDecorator, VARCHAR
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
from datetime import datetime

try:
    from app.core.database import Base
except ImportError:
    Base = object


# Define the database ENUM types exactly as they exist
class AssetTypeEnum(str, enum.Enum):
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


class AssetStatusEnum(str, enum.Enum):
    """Asset status enumeration matching database assetstatus enum."""
    DISCOVERED = "discovered"
    ASSESSED = "assessed"
    PLANNED = "planned"
    MIGRATING = "migrating"
    MIGRATED = "migrated"
    FAILED = "failed"
    EXCLUDED = "excluded"


class SixRStrategyEnum(str, enum.Enum):
    """6R migration strategy enumeration matching database sixrstrategy enum."""
    REHOST = "rehost"
    REPLATFORM = "replatform"
    REFACTOR = "refactor"
    REARCHITECT = "rearchitect"
    RETIRE = "retire"
    RETAIN = "retain"


class AssetMinimal(Base):
    """
    Minimal Asset model for testing.
    Only includes essential fields that match database exactly.
    """
    
    __tablename__ = "assets"
    
    # Essential fields that we know work
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(Integer, ForeignKey("migrations.id"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetTypeEnum, name='assettype'), nullable=False)
    
    # Multi-tenant fields
    client_account_id = Column(UUID(as_uuid=True), nullable=True)
    engagement_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Optional fields for testing
    description = Column(Text, nullable=True)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    fqdn = Column(String(255), nullable=True)
    
    # Status fields
    status = Column(SQLEnum(AssetStatusEnum, name='assetstatus'), nullable=True)
    six_r_strategy = Column(SQLEnum(SixRStrategyEnum, name='sixrstrategy'), nullable=True)
    
    # Workflow status fields (these were added by our migration)
    discovery_status = Column(String(50), nullable=True)
    mapping_status = Column(String(50), nullable=True)
    cleanup_status = Column(String(50), nullable=True)
    assessment_readiness = Column(String(50), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    discovered_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<AssetMinimal(id={self.id}, name='{self.name}', type='{self.asset_type}')>"
    
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
            'client_account_id': str(self.client_account_id) if self.client_account_id else None,
            'engagement_id': str(self.engagement_id) if self.engagement_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
        } 