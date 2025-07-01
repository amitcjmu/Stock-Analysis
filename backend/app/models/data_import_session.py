"""
Data Import Session model for session-level data isolation and tracking.
"""

try:
    from sqlalchemy import Column, String, Text, Boolean, DateTime, UUID, JSON, ForeignKey, Integer
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = Boolean = DateTime = UUID = JSON = ForeignKey = Integer = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import uuid
from datetime import datetime
from enum import Enum as PyEnum

try:
    from app.core.database import Base
except ImportError:
    Base = object


class SessionType(str, PyEnum):
    """Types of data import sessions."""
    DATA_IMPORT = "data_import"
    VALIDATION_RUN = "validation_run"
    INCREMENTAL_UPDATE = "incremental_update"
    COMPARISON_ANALYSIS = "comparison_analysis"
    CLEANUP_OPERATION = "cleanup_operation"


class SessionStatus(str, PyEnum):
    """Session status lifecycle."""
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


class DataImportSession(Base):
    """
    Data Import Session model for tracking discrete import operations within engagements.
    
    Sessions are auto-created for each data import with naming pattern:
    {client_name}-{engagement_name}-{timestamp}
    """
    
    __tablename__ = "data_import_sessions"
    
    # Primary Key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Multi-tenant context
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Session identification
    session_name = Column(String(255), nullable=False, index=True)  # Auto-generated: client-engagement-timestamp
    session_display_name = Column(String(255), nullable=True)  # Optional user-friendly name
    description = Column(Text)
    
    # Session management
    is_default = Column(Boolean, default=False, nullable=False, index=True)  # Whether this is the default session for the engagement
    parent_session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id', ondelete='SET NULL'), nullable=True)  # For tracking session merges
    
    # Session metadata
    session_type = Column(String(50), default=SessionType.DATA_IMPORT, nullable=False)
    auto_created = Column(Boolean, default=True, nullable=False)  # True for auto-created, False for manual
    source_filename = Column(String(255))  # Original filename that triggered session creation
    
    # Session status and tracking
    status = Column(String(20), default=SessionStatus.ACTIVE, nullable=False, index=True)
    progress_percentage = Column(Integer, default=0)
    
    # Processing statistics
    total_imports = Column(Integer, default=0)  # Number of data imports in this session
    total_assets_processed = Column(Integer, default=0)
    total_records_imported = Column(Integer, default=0)
    data_quality_score = Column(Integer, default=0)  # 0-100 quality score
    
    # Session configuration
    session_config = Column(JSON, default=lambda: {
        "deduplication_strategy": "engagement_level",  # session_level, engagement_level
        "quality_thresholds": {
            "minimum_completeness": 0.7,
            "minimum_accuracy": 0.8
        },
        "processing_preferences": {
            "auto_classify": True,
            "auto_deduplicate": True,
            "require_manual_review": False
        }
    })
    
    # Business context
    business_context = Column(JSON, default=lambda: {
        "import_purpose": "",  # "initial_discovery", "data_refresh", "validation", etc.
        "data_source_description": "",
        "expected_changes": [],
        "validation_notes": []
    })
    
    # Agent intelligence tracking
    agent_insights = Column(JSON, default=lambda: {
        "classification_confidence": 0.0,
        "data_quality_issues": [],
        "recommendations": [],
        "learning_outcomes": []
    })
    
    # Timeline tracking
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # User tracking
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    client_account = relationship("ClientAccount")
    engagement = relationship(
        "Engagement", 
        back_populates="sessions",
        foreign_keys=[engagement_id]
    )
    created_by_user = relationship("User")
    # Note: data_imports relationship removed as session_id was replaced with master_flow_id during database consolidation
    
    def __repr__(self):
        return f"<DataImportSession(id={self.id}, name='{self.session_name}', status='{self.status}', is_mock={self.is_mock})>"
    
    @classmethod
    def generate_session_name(cls, client_name: str, engagement_name: str, timestamp: datetime = None) -> str:
        """
        Generate auto session name in format: client-engagement-timestamp
        
        Args:
            client_name: Name of the client
            engagement_name: Name of the engagement
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            Formatted session name string
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Clean names for URL-safe format
        clean_client = client_name.lower().replace(" ", "-").replace("&", "and")[:20]
        clean_engagement = engagement_name.lower().replace(" ", "-")[:30]
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        
        return f"{clean_client}-{clean_engagement}-{timestamp_str}"
    
    def update_progress(self, progress: int, status: str = None):
        """Update session progress and optionally status."""
        self.progress_percentage = max(0, min(100, progress))
        self.last_activity_at = datetime.utcnow()
        
        if status:
            self.status = status
    
    def add_agent_insight(self, insight_type: str, insight_data: dict):
        """Add agent intelligence insight to session."""
        if not self.agent_insights:
            self.agent_insights = {"classification_confidence": 0.0, "data_quality_issues": [], "recommendations": [], "learning_outcomes": []}
        
        if insight_type not in self.agent_insights:
            self.agent_insights[insight_type] = []
        
        if isinstance(self.agent_insights[insight_type], list):
            self.agent_insights[insight_type].append({
                **insight_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            self.agent_insights[insight_type] = insight_data
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return self.status in [SessionStatus.ACTIVE, SessionStatus.PROCESSING]
    
    @property
    def is_completed(self) -> bool:
        """Check if session is completed."""
        return self.status == SessionStatus.COMPLETED
    
    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        if self.completed_at:
            delta = self.completed_at - self.started_at
        else:
            delta = datetime.utcnow() - self.started_at.replace(tzinfo=None)
        
        return int(delta.total_seconds() / 60) 