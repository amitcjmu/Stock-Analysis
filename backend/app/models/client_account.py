"""
Client Account models for multi-tenant data segregation.
"""

try:
    from sqlalchemy import Column, String, Text, Boolean, DateTime, UUID, JSON, ForeignKey, UniqueConstraint, Integer
    from sqlalchemy.orm import relationship
    from sqlalchemy.ext.associationproxy import association_proxy
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
    __table_args__ = {'extend_existing': True}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    industry = Column(String(100))
    company_size = Column(String(50))
    
    # Contact Information
    headquarters_location = Column(String(255))
    primary_contact_name = Column(String(255))
    primary_contact_email = Column(String(255))
    primary_contact_phone = Column(String(50))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)
    timezone = Column(String(50))
    # Subscription & Billing
    subscription_tier = Column(String(50), default='standard')
    billing_contact_email = Column(String(255))
    subscription_start_date = Column(DateTime(timezone=True))
    subscription_end_date = Column(DateTime(timezone=True))
    max_users = Column(Integer)
    max_engagements = Column(Integer)
    features_enabled = Column(JSON, default=lambda: {})
    agent_configuration = Column(JSON, default=lambda: {})
    storage_quota_gb = Column(Integer)
    api_quota_monthly = Column(Integer)
    
    # Settings
    settings = Column(JSON, default=lambda: {})
    branding = Column(JSON, default=lambda: {})
    
    # Enhanced Business Context
    business_objectives = Column(JSON, default=lambda: {
        "primary_goals": [],
        "timeframe": "",
        "success_metrics": [],
        "constraints": []
    })
    
    # IT Guidelines and Decision Criteria
    it_guidelines = Column(JSON, default=lambda: {})
    decision_criteria = Column(JSON, default=lambda: {})
    
    # Agent Configuration Preferences
    agent_preferences = Column(JSON, default=lambda: {
        "discovery_depth": "comprehensive",
        "automation_level": "assisted",
        "risk_tolerance": "moderate",
        "preferred_clouds": [],
        "compliance_requirements": [],
        "custom_rules": []
    })
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Core relationships only
    engagements = relationship("Engagement", back_populates="client_account", cascade="all, delete-orphan")
    user_associations = relationship("UserAccountAssociation", back_populates="client_account", cascade="all, delete-orphan")
    
    # Data import relationships (string reference to avoid circular imports)
    data_imports = relationship("DataImport", back_populates="client_account", cascade="all, delete-orphan", lazy="select")
    
    # Feedback relationships (string reference to avoid circular imports)
    feedback = relationship("Feedback", back_populates="client_account", cascade="all, delete-orphan", lazy="select")
    
    # LLM usage relationships (string reference to avoid circular imports)
    llm_usage_logs = relationship("LLMUsageLog", back_populates="client_account", cascade="all, delete-orphan", lazy="select")
    llm_usage_summaries = relationship("LLMUsageSummary", back_populates="client_account", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<ClientAccount(id={self.id}, name='{self.name}')>"


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
    
    # Enhanced Engagement Context
    migration_scope = Column(JSON, default=lambda: {
        "target_clouds": [],
        "migration_strategies": [],
        "excluded_systems": [],
        "included_environments": [],
        "business_units": [],
        "geographic_scope": [],
        "timeline_constraints": {}
    })
    
    team_preferences = Column(JSON, default=lambda: {
        "stakeholders": [],
        "decision_makers": [],
        "technical_leads": [],
        "communication_style": "formal",
        "reporting_frequency": "weekly",
        "preferred_meeting_times": [],
        "escalation_contacts": [],
        "project_methodology": "agile"
    })
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Core relationships only
    client_account = relationship("ClientAccount", back_populates="engagements")
    engagement_lead = relationship("User", foreign_keys=[engagement_lead_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    # Asset relationships (string reference to avoid circular imports)
    assets = relationship("Asset", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # Data import relationships (string reference to avoid circular imports)
    data_imports = relationship("DataImport", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # Feedback relationships (string reference to avoid circular imports)
    feedback = relationship("Feedback", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # LLM usage relationships (string reference to avoid circular imports)
    llm_usage_logs = relationship("LLMUsageLog", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    llm_usage_summaries = relationship("LLMUsageSummary", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # Data import session relationships removed - legacy functionality
    
    def __repr__(self):
        return f"<Engagement(id={self.id}, name='{self.name}', client_account_id={self.client_account_id})>"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # User Status
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Default Context (for faster context establishment)
    default_client_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True)
    default_engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    user_associations = relationship("UserAccountAssociation", foreign_keys="[UserAccountAssociation.user_id]", back_populates="user", cascade="all, delete-orphan")
    default_client = relationship("ClientAccount", foreign_keys=[default_client_id])
    default_engagement = relationship("Engagement", foreign_keys=[default_engagement_id])
    client_accounts = association_proxy(
        "user_associations", "client_account",
        creator=lambda client_account: UserAccountAssociation(client_account=client_account)
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class UserAccountAssociation(Base):
    """Association between users and client accounts with roles."""
    
    __tablename__ = "user_account_associations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Role within the client account
    role = Column(String(50), nullable=False, default='member')
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="user_associations", foreign_keys=[user_id])
    client_account = relationship("ClientAccount", back_populates="user_associations")
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __init__(self, *args, **kwargs):
        # Allow creating association with a ClientAccount object
        if 'client_account' in kwargs and isinstance(kwargs['client_account'], ClientAccount):
            super().__init__(*args, **kwargs)
        # Allow creating association with a dict that can be used to make a ClientAccount
        elif 'client_account' in kwargs and isinstance(kwargs['client_account'], dict):
            account_data = kwargs.pop('client_account')
            # Ensure we don't pass unexpected arguments to ClientAccount
            allowed_keys = {c.name for c in ClientAccount.__table__.columns}
            filtered_data = {k: v for k, v in account_data.items() if k in allowed_keys}
            kwargs['client_account'] = ClientAccount(**filtered_data)
            super().__init__(*args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    # Unique constraint for user_id and client_account_id
    __table_args__ = (
        UniqueConstraint('user_id', 'client_account_id', name='_user_client_account_uc'),
    )
    
    def __repr__(self):
        return f"<UserAccountAssociation(user_id={self.user_id}, client_account_id={self.client_account_id}, role='{self.role}')>" 