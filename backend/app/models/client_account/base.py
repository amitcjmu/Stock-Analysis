"""
ClientAccount model definition.
"""

from ._common import (
    Base,
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    PostgresUUID,
    String,
    Text,
    func,
    relationship,
    uuid,
)


class ClientAccount(Base):
    """
    Represents a client organization in the multi-tenant system.
    Each client account is a distinct, isolated entity with its own users, engagements, and data.
    """

    __tablename__ = "client_accounts"
    __table_args__ = {"extend_existing": True}

    id = Column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the client account.",
    )
    name = Column(
        String(255), nullable=False, comment="The official name of the client company."
    )
    slug = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="A URL-friendly slug for the client account, used for identification.",
    )
    description = Column(
        Text, comment="A detailed description of the client account and their business."
    )
    industry = Column(
        String(100),
        comment="The industry vertical of the client (e.g., Finance, Healthcare).",
    )
    company_size = Column(
        String(50),
        comment="The approximate size of the client's company (e.g., '1-50', '50-200').",
    )

    # Contact Information
    headquarters_location = Column(
        String(255), comment="The geographical location of the client's headquarters."
    )
    primary_contact_name = Column(
        String(255),
        comment="The name of the main point of contact at the client company.",
    )
    primary_contact_email = Column(
        String(255),
        comment="The email address of the main point of contact. Considered PII.",
    )
    primary_contact_phone = Column(
        String(50), comment="The phone number for the main point of contact."
    )
    contact_email = Column(
        String(255), comment="A general contact email for the client."
    )
    contact_phone = Column(
        String(50), comment="A general contact phone number for the client."
    )
    address = Column(Text, comment="The physical mailing address of the client.")
    timezone = Column(
        String(50),
        comment="The primary timezone for the client to assist in scheduling and timestamps.",
    )

    # Subscription & Billing
    subscription_tier = Column(
        String(50),
        default="standard",
        comment="The subscription level for the client (e.g., 'free', 'standard', 'enterprise').",
    )
    billing_contact_email = Column(
        String(255),
        comment="The email address for sending billing-related communications. Considered PII.",
    )
    subscription_start_date = Column(
        DateTime(timezone=True),
        comment="The date when the client's current subscription term began.",
    )
    subscription_end_date = Column(
        DateTime(timezone=True),
        comment="The date when the client's current subscription term ends.",
    )
    max_users = Column(
        Integer,
        comment="The maximum number of users allowed under the current subscription.",
    )
    max_engagements = Column(
        Integer, comment="The maximum number of concurrent engagements allowed."
    )
    features_enabled = Column(
        JSON,
        default=lambda: {},
        comment="A JSON blob to toggle specific features for this client (feature flags).",
    )
    agent_configuration = Column(
        JSON,
        default=lambda: {},
        comment="Custom configuration for CrewAI agents specific to this client.",
    )
    storage_quota_gb = Column(
        Integer,
        comment="The total data storage quota in gigabytes allocated to this client.",
    )
    api_quota_monthly = Column(
        Integer, comment="The monthly API request quota for this client."
    )

    # Settings
    settings = Column(
        JSON,
        default=lambda: {},
        comment="General-purpose settings for the client account as a JSON blob.",
    )
    branding = Column(
        JSON,
        default=lambda: {},
        comment="Client-specific branding information, such as logos and colors, for UI customization.",
    )

    # Enhanced Business Context
    business_objectives = Column(
        JSON,
        default=lambda: {
            "primary_goals": [],
            "timeframe": "",
            "success_metrics": [],
            "constraints": [],
        },
        comment="Stores the client's strategic business goals and success criteria for migrations.",
    )

    # IT Guidelines and Decision Criteria
    it_guidelines = Column(
        JSON,
        default=lambda: {},
        comment="Client's internal IT policies, standards, and guidelines for technology adoption.",
    )
    decision_criteria = Column(
        JSON,
        default=lambda: {},
        comment="The criteria the client uses to make migration decisions (e.g., cost, performance, security).",
    )

    # Agent Configuration Preferences
    agent_preferences = Column(
        JSON,
        default=lambda: {
            "discovery_depth": "comprehensive",
            "automation_level": "assisted",
            "risk_tolerance": "moderate",
            "preferred_clouds": [],
            "compliance_requirements": [],
            "custom_rules": [],
        },
        comment="Client-specific preferences for how the AI agents should operate during analysis.",
    )

    # Audit
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Timestamp of when the client account was created.",
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
        comment="Timestamp of the last update to the client account record.",
    )
    created_by = Column(
        PostgresUUID(as_uuid=True),
        nullable=True,
        comment="The user ID of the user who created this client account.",
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="A soft-delete flag. If false, the account is considered inactive.",
    )

    # Core relationships only
    engagements = relationship(
        "Engagement", back_populates="client_account", cascade="all, delete-orphan"
    )
    user_associations = relationship(
        "UserAccountAssociation",
        back_populates="client_account",
        cascade="all, delete-orphan",
    )

    # Data import relationships (string reference to avoid circular imports)
    data_imports = relationship(
        "DataImport",
        back_populates="client_account",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Feedback relationships (string reference to avoid circular imports)
    feedback = relationship(
        "Feedback",
        back_populates="client_account",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # LLM usage relationships (string reference to avoid circular imports)
    llm_usage_logs = relationship(
        "LLMUsageLog",
        back_populates="client_account",
        cascade="all, delete-orphan",
        lazy="select",
    )
    llm_usage_summaries = relationship(
        "LLMUsageSummary",
        back_populates="client_account",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Collection flow relationships REMOVED - Collection flow was removed

    # Canonical application relationships (string reference to avoid circular imports)
    canonical_applications = relationship(
        "CanonicalApplication",
        back_populates="client_account",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self):
        return f"<ClientAccount(id={self.id}, name='{self.name}')>"
