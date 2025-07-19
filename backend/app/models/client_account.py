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
    """
    Represents a client organization in the multi-tenant system.
    Each client account is a distinct, isolated entity with its own users, engagements, and data.
    """
    
    __tablename__ = "client_accounts"
    __table_args__ = {'extend_existing': True}
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, comment="Unique identifier for the client account.")
    name = Column(String(255), nullable=False, comment="The official name of the client company.")
    slug = Column(String(100), unique=True, nullable=False, index=True, comment="A URL-friendly slug for the client account, used for identification.")
    description = Column(Text, comment="A detailed description of the client account and their business.")
    industry = Column(String(100), comment="The industry vertical of the client (e.g., Finance, Healthcare).")
    company_size = Column(String(50), comment="The approximate size of the client's company (e.g., '1-50', '50-200').")
    
    # Contact Information
    headquarters_location = Column(String(255), comment="The geographical location of the client's headquarters.")
    primary_contact_name = Column(String(255), comment="The name of the main point of contact at the client company.")
    primary_contact_email = Column(String(255), comment="The email address of the main point of contact. Considered PII.")
    primary_contact_phone = Column(String(50), comment="The phone number for the main point of contact.")
    contact_email = Column(String(255), comment="A general contact email for the client.")
    contact_phone = Column(String(50), comment="A general contact phone number for the client.")
    address = Column(Text, comment="The physical mailing address of the client.")
    timezone = Column(String(50), comment="The primary timezone for the client to assist in scheduling and timestamps.")
    # Subscription & Billing
    subscription_tier = Column(String(50), default='standard', comment="The subscription level for the client (e.g., 'free', 'standard', 'enterprise').")
    billing_contact_email = Column(String(255), comment="The email address for sending billing-related communications. Considered PII.")
    subscription_start_date = Column(DateTime(timezone=True), comment="The date when the client's current subscription term began.")
    subscription_end_date = Column(DateTime(timezone=True), comment="The date when the client's current subscription term ends.")
    max_users = Column(Integer, comment="The maximum number of users allowed under the current subscription.")
    max_engagements = Column(Integer, comment="The maximum number of concurrent engagements allowed.")
    features_enabled = Column(JSON, default=lambda: {}, comment="A JSON blob to toggle specific features for this client (feature flags).")
    agent_configuration = Column(JSON, default=lambda: {}, comment="Custom configuration for CrewAI agents specific to this client.")
    storage_quota_gb = Column(Integer, comment="The total data storage quota in gigabytes allocated to this client.")
    api_quota_monthly = Column(Integer, comment="The monthly API request quota for this client.")
    
    # Settings
    settings = Column(JSON, default=lambda: {}, comment="General-purpose settings for the client account as a JSON blob.")
    branding = Column(JSON, default=lambda: {}, comment="Client-specific branding information, such as logos and colors, for UI customization.")
    
    # Enhanced Business Context
    business_objectives = Column(JSON, default=lambda: {
        "primary_goals": [],
        "timeframe": "",
        "success_metrics": [],
        "constraints": []
    }, comment="Stores the client's strategic business goals and success criteria for migrations.")
    
    # IT Guidelines and Decision Criteria
    it_guidelines = Column(JSON, default=lambda: {}, comment="Client's internal IT policies, standards, and guidelines for technology adoption.")
    decision_criteria = Column(JSON, default=lambda: {}, comment="The criteria the client uses to make migration decisions (e.g., cost, performance, security).")
    
    # Agent Configuration Preferences
    agent_preferences = Column(JSON, default=lambda: {
        "discovery_depth": "comprehensive",
        "automation_level": "assisted",
        "risk_tolerance": "moderate",
        "preferred_clouds": [],
        "compliance_requirements": [],
        "custom_rules": []
    }, comment="Client-specific preferences for how the AI agents should operate during analysis.")
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp of when the client account was created.")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Timestamp of the last update to the client account record.")
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True, comment="The user ID of the user who created this client account.")
    is_active = Column(Boolean, default=True, nullable=False, index=True, comment="A soft-delete flag. If false, the account is considered inactive.")
    
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
    
    # Collection flow relationships (string reference to avoid circular imports)
    collection_flows = relationship("CollectionFlow", back_populates="client_account", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<ClientAccount(id={self.id}, name='{self.name}')>"


class Engagement(Base):
    """
    Represents a specific project or migration initiative for a client account.
    All work, such as data imports and analyses, is scoped to an engagement.
    """
    
    __tablename__ = "engagements"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, comment="Unique identifier for the engagement.")
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True, comment="Foreign key linking this engagement to its parent client account.")
    
    name = Column(String(255), nullable=False, comment="The official name of the engagement (e.g., 'US-East Datacenter Migration').")
    slug = Column(String(100), nullable=False, comment="A URL-friendly slug for the engagement.")
    description = Column(Text, comment="A detailed description of the engagement's goals and scope.")
    
    # Engagement Details
    engagement_type = Column(String(50), default='migration', comment="The type of engagement (e.g., 'migration', 'discovery', 'assessment').")
    status = Column(String(50), default='active', index=True, comment="The current status of the engagement (e.g., 'planning', 'active', 'completed', 'on-hold').")
    priority = Column(String(20), default='medium', comment="The priority of the engagement (e.g., 'low', 'medium', 'high').")
    
    # Timeline
    start_date = Column(DateTime(timezone=True), comment="The official start date of the engagement.")
    target_completion_date = Column(DateTime(timezone=True), comment="The planned completion date for the engagement.")
    actual_completion_date = Column(DateTime(timezone=True), comment="The actual date the engagement was completed.")
    
    # Team & Contacts
    engagement_lead_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, comment="The user ID of the person leading the engagement.")
    client_contact_name = Column(String(255), comment="The name of the primary contact on the client's side for this engagement.")
    client_contact_email = Column(String(255), comment="The email of the primary client contact for this engagement. Considered PII.")
    
    # Settings
    settings = Column(JSON, default=lambda: {}, comment="A JSON blob for any engagement-specific settings.")
    
    # Enhanced Engagement Context
    migration_scope = Column(JSON, default=lambda: {
        "target_clouds": [],
        "migration_strategies": [],
        "excluded_systems": [],
        "included_environments": [],
        "business_units": [],
        "geographic_scope": [],
        "timeline_constraints": {}
    }, comment="Defines the scope of the migration, including targets, strategies, and exclusions.")
    
    team_preferences = Column(JSON, default=lambda: {
        "stakeholders": [],
        "decision_makers": [],
        "technical_leads": [],
        "communication_style": "formal",
        "reporting_frequency": "weekly",
        "preferred_meeting_times": [],
        "escalation_contacts": [],
        "project_methodology": "agile"
    }, comment="Stores preferences for team collaboration and communication styles for this engagement.")
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp of when the engagement was created.")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="Timestamp of the last update to the engagement record.")
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, comment="The user ID of the person who created the engagement.")
    is_active = Column(Boolean, default=True, index=True, comment="A soft-delete flag. If false, the engagement is considered inactive.")
    
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
    
    # User active flows relationships
    user_active_flows = relationship("UserActiveFlow", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # Collection flow relationships (string reference to avoid circular imports)
    collection_flows = relationship("CollectionFlow", back_populates="engagement", cascade="all, delete-orphan", lazy="select")
    
    # Data import session relationships removed - legacy functionality
    
    def __repr__(self):
        return f"<Engagement(id={self.id}, name='{self.name}', client_account_id={self.client_account_id})>"


class User(Base):
    """
    Represents a user of the platform. Users can be associated with multiple client accounts.
    """
    
    __tablename__ = "users"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, comment="Unique identifier for the user.")
    email = Column(String(255), unique=True, nullable=False, index=True, comment="The user's email address, used for login. This is PII.")
    password_hash = Column(String(255), nullable=True, comment="Stores the salted and hashed password for the user.")
    first_name = Column(String(100), comment="The user's first name. This is PII.")
    last_name = Column(String(100), comment="The user's last name. This is PII.")
    
    # User Status
    is_active = Column(Boolean, default=True, index=True, comment="A soft-delete flag. If false, the user cannot log in.")
    is_verified = Column(Boolean, default=False, comment="Indicates if the user has verified their email address.")
    
    # Default Context (for faster context establishment)
    default_client_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id'), nullable=True, comment="The default client account to use for the user upon login.")
    default_engagement_id = Column(PostgresUUID(as_uuid=True), ForeignKey('engagements.id'), nullable=True, comment="The default engagement to use for the user upon login.")
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp of when the user account was created.")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Timestamp of the last update to the user record.")
    last_login = Column(DateTime(timezone=True), comment="Timestamp of the user's last login.")
    
    # Relationships
    user_associations = relationship("UserAccountAssociation", foreign_keys="[UserAccountAssociation.user_id]", back_populates="user", cascade="all, delete-orphan")
    default_client = relationship("ClientAccount", foreign_keys=[default_client_id])
    default_engagement = relationship("Engagement", foreign_keys=[default_engagement_id])
    active_flows = relationship("UserActiveFlow", back_populates="user", cascade="all, delete-orphan")
    collection_flows = relationship("CollectionFlow", back_populates="user", cascade="all, delete-orphan", lazy="select")
    client_accounts = association_proxy(
        "user_associations", "client_account",
        creator=lambda client_account: UserAccountAssociation(client_account=client_account)
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class UserAccountAssociation(Base):
    """
    Association table linking Users to ClientAccounts, defining their role within that account.
    This is the basis of the multi-tenancy authorization model.
    """
    
    __tablename__ = "user_account_associations"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="Unique identifier for the association record.")
    user_id = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment="Foreign key to the users table.")
    client_account_id = Column(PostgresUUID(as_uuid=True), ForeignKey('client_accounts.id', ondelete='CASCADE'), nullable=False, index=True, comment="Foreign key to the client_accounts table.")
    
    # Role within the client account
    role = Column(String(50), nullable=False, default='member', comment="The user's role within this specific client account (e.g., 'admin', 'member', 'viewer').")
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Timestamp of when the association was created.")
    created_by = Column(PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=True, comment="The user ID of the user who created this association (typically an admin).")
    
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
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<UserAccountAssociation(user_id={self.user_id}, client_account_id={self.client_account_id}, role='{self.role}')>"