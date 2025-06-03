"""
Client Account models for multi-tenant data segregation.
"""

try:
    from sqlalchemy import Column, String, Text, Boolean, DateTime, UUID, JSON, ForeignKey
    from sqlalchemy.orm import relationship
    from sqlalchemy.sql import func
    from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = String = Text = Boolean = DateTime = UUID = JSON = ForeignKey = object
    def relationship(*args, **kwargs):
        return None
    class func:
        @staticmethod
        def now():
            return None

import uuid

try:
    from app.core.database import Base
except ImportError:
    Base = object


class ClientAccount(Base):
    """Client Account model for multi-tenant data segregation."""
    
    __tablename__ = "client_accounts"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    industry = Column(String(100))
    company_size = Column(String(50))
    
    # Subscription & Billing
    subscription_tier = Column(String(50), default='standard')
    billing_contact_email = Column(String(255))
    
    # Settings
    settings = Column(JSON, default=lambda: {})
    branding = Column(JSON, default=lambda: {})
    
    # Enhanced Business Context (Task 1.1.1)
    business_objectives = Column(JSON, default=lambda: {
        "primary_goals": [],
        "timeframe": "",
        "success_metrics": [],
        "budget_constraints": "",
        "compliance_requirements": []
    })
    
    it_guidelines = Column(JSON, default=lambda: {
        "architecture_patterns": [],
        "security_requirements": [],
        "compliance_standards": [],
        "technology_preferences": [],
        "cloud_strategy": "",
        "data_governance": {}
    })
    
    decision_criteria = Column(JSON, default=lambda: {
        "risk_tolerance": "medium",  # low, medium, high
        "cost_sensitivity": "medium",  # low, medium, high
        "innovation_appetite": "moderate",  # conservative, moderate, aggressive
        "timeline_pressure": "medium",  # low, medium, high
        "quality_vs_speed": "balanced",  # quality, balanced, speed
        "technical_debt_tolerance": "low"  # low, medium, high
    })
    
    agent_preferences = Column(JSON, default=lambda: {
        "confidence_thresholds": {
            "field_mapping": 0.8,
            "data_classification": 0.75,
            "risk_assessment": 0.85,
            "migration_strategy": 0.9
        },
        "learning_preferences": ["conservative", "accuracy_focused"],
        "custom_prompts": {},
        "notification_preferences": {
            "confidence_alerts": True,
            "learning_updates": False,
            "error_notifications": True
        }
    })
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    engagements = relationship("Engagement", back_populates="client_account", cascade="all, delete-orphan")
    user_associations = relationship("UserAccountAssociation", back_populates="client_account", cascade="all, delete-orphan")
    cmdb_assets = relationship("CMDBAsset", back_populates="client_account", cascade="all, delete-orphan")
    data_imports = relationship("DataImport", back_populates="client_account", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="client_account", cascade="all, delete-orphan")
    llm_usage_logs = relationship("LLMUsageLog", back_populates="client_account", cascade="all, delete-orphan")
    llm_usage_summaries = relationship("LLMUsageSummary", back_populates="client_account", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ClientAccount(id={self.id}, name='{self.name}', slug='{self.slug}', is_mock={self.is_mock})>"


class Engagement(Base):
    """Engagement model for migration projects within client accounts."""
    
    __tablename__ = "engagements"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Engagement Details
    engagement_type = Column(String(50), default='migration')
    status = Column(String(50), default='active', index=True)
    priority = Column(String(20), default='medium')
    
    # Timeline
    start_date = Column(DateTime(timezone=True))
    target_completion_date = Column(DateTime(timezone=True))
    actual_completion_date = Column(DateTime(timezone=True))
    
    # Team & Contacts
    engagement_lead_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    client_contact_name = Column(String(255))
    client_contact_email = Column(String(255))
    
    # Settings
    settings = Column(JSON, default=lambda: {})
    
    # Enhanced Engagement Context (Task 1.1.2)
    migration_scope = Column(JSON, default=lambda: {
        "target_clouds": [],  # ["AWS", "Azure", "GCP"]
        "migration_strategies": [],  # 6R strategies preferred for this engagement
        "excluded_systems": [],
        "included_environments": [],  # ["Production", "Development", "Staging"]
        "business_units": [],
        "geographic_scope": [],
        "timeline_constraints": {}
    })
    
    team_preferences = Column(JSON, default=lambda: {
        "stakeholders": [],  # [{"name": "", "role": "", "email": "", "decision_authority": ""}]
        "decision_makers": [],
        "technical_leads": [],
        "communication_style": "formal",  # formal, informal, technical
        "reporting_frequency": "weekly",  # daily, weekly, monthly
        "preferred_meeting_times": [],
        "escalation_contacts": [],
        "project_methodology": "agile"  # agile, waterfall, hybrid
    })
    
    # Current Session Reference
    current_session_id = Column(PostgresUUID(as_uuid=True), ForeignKey('data_import_sessions.id'), nullable=True)
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    client_account = relationship("ClientAccount", back_populates="engagements")
    engagement_lead = relationship("User", foreign_keys=[engagement_lead_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    cmdb_assets = relationship("CMDBAsset", back_populates="engagement", cascade="all, delete-orphan")
    data_imports = relationship("DataImport", back_populates="engagement", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="engagement", cascade="all, delete-orphan")
    llm_usage_logs = relationship("LLMUsageLog", back_populates="engagement", cascade="all, delete-orphan")
    llm_usage_summaries = relationship("LLMUsageSummary", back_populates="engagement", cascade="all, delete-orphan")
    
    # Session relationships (Task 1.1.3)
    sessions = relationship(
        "DataImportSession", 
        back_populates="engagement", 
        foreign_keys="DataImportSession.engagement_id",
        cascade="all, delete-orphan"
    )
    current_session_ref = relationship(
        "DataImportSession", 
        foreign_keys=[current_session_id], 
        post_update=True
    )
    
    def __repr__(self):
        return f"<Engagement(id={self.id}, name='{self.name}', client_account_id={self.client_account_id}, is_mock={self.is_mock})>"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # Nullable for future SSO users
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # User Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', is_mock={self.is_mock})>"


class UserAccountAssociation(Base):
    """Association between users and client accounts with roles."""
    
    __tablename__ = "user_account_associations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Role within the client account
    role = Column(String(50), nullable=False, default='member')
    
    # Mock data flag
    is_mock = Column(Boolean, default=False, nullable=False, index=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    client_account = relationship("ClientAccount", back_populates="user_associations")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<UserAccountAssociation(user_id={self.user_id}, client_account_id={self.client_account_id}, role='{self.role}', is_mock={self.is_mock})>" 