"""
Migration models for the AI Force Migration Platform.
Defines database schema for migration projects and related entities.
"""

try:
    from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum, Boolean, ForeignKey, UUID
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for type hints
    Column = Integer = String = DateTime = Text = JSON = Enum = Boolean = ForeignKey = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

from datetime import datetime
import enum
import uuid

try:
    from app.core.database import Base
except ImportError:
    Base = object


class MigrationStatus(str, enum.Enum):
    """Migration project status enumeration."""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class MigrationPhase(str, enum.Enum):
    """Migration phase enumeration."""
    DISCOVERY = "discovery"
    ASSESS = "assess"
    PLAN = "plan"
    EXECUTE = "execute"
    MODERNIZE = "modernize"
    FINOPS = "finops"
    OBSERVABILITY = "observability"
    DECOMMISSION = "decommission"


class Migration(Base):
    """Migration project model."""
    
    __tablename__ = "migrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Status and phase tracking
    status = Column(Enum(MigrationStatus), default=MigrationStatus.PLANNING)
    current_phase = Column(Enum(MigrationPhase), default=MigrationPhase.DISCOVERY)
    
    # Timeline
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    start_date = Column(DateTime(timezone=True))
    target_completion_date = Column(DateTime(timezone=True))
    actual_completion_date = Column(DateTime(timezone=True))
    
    # Migration configuration
    source_environment = Column(String(100))  # e.g., "on-premises", "aws", "azure"
    target_environment = Column(String(100))  # e.g., "aws", "azure", "gcp"
    migration_strategy = Column(String(50))   # e.g., "lift-and-shift", "re-platform"
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    total_assets = Column(Integer, default=0)
    migrated_assets = Column(Integer, default=0)
    
    # AI insights and metadata
    ai_recommendations = Column(JSON)  # Store AI-generated recommendations
    risk_assessment = Column(JSON)     # Risk analysis data
    cost_estimates = Column(JSON)      # Cost projections
    
    # Configuration and settings
    settings = Column(JSON)  # Project-specific settings
    
    # Relationships
    assets = relationship("Asset", back_populates="migration", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="migration", cascade="all, delete-orphan")
    sixr_analyses = relationship("SixRAnalysis", back_populates="migration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Migration(id={self.id}, name='{self.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if migration is currently active."""
        return self.status in [MigrationStatus.PLANNING, MigrationStatus.IN_PROGRESS]
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage based on migrated assets."""
        if self.total_assets == 0:
            return 0.0
        return (self.migrated_assets / self.total_assets) * 100
    
    def update_progress(self):
        """Update progress based on current asset migration status."""
        # This will be implemented when we have asset migration tracking
        pass


class MigrationLog(Base):
    """Migration activity log model."""
    
    __tablename__ = "migration_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    migration_id = Column(UUID(as_uuid=True), ForeignKey("migrations.id"), nullable=False)
    
    # Log details
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR, DEBUG
    message = Column(Text, nullable=False)
    details = Column(JSON)  # Additional structured data
    
    # Context
    phase = Column(Enum(MigrationPhase))
    user_id = Column(String(100))  # User who triggered the action
    action = Column(String(100))   # Action type (e.g., "asset_discovered", "assessment_completed")
    
    # Relationships
    migration = relationship("Migration")
    
    def __repr__(self):
        return f"<MigrationLog(id={self.id}, migration_id={self.migration_id}, level='{self.level}')>" 